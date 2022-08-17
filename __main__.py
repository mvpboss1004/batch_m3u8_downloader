import asyncio
import logging
import os
from optparse import OptionParser
from traceback import format_exc

import pandas as pd
from tqdm import tqdm, trange

from downloaders import HTTP, M3U8
from playlist_generator import DeDao, format_title, get_session

logger = logging.getLogger(__name__)

if __name__ == '__main__':
    parser = OptionParser()
    parser.add_option('-o', '--output', dest='output', help='输出文件（夹）')
    parser.add_option('-r', '--retry', dest='retry', help='重试失败项', action='store_true', default=False)
    parser.add_option('-l', '--login', dest='login', help='需要登录', action='store_true', default=False)
    parser.add_option('-g', '--generator', dest='generator', help='播放列表生成器：dedao/ximalaya/bilibili')
    opts, args = parser.parse_args()

    if opts.generator:
        generators = {
            'dedao': DeDao,
        }
        try:
            generator = generators[opts.generator]
        except KeyError:
            raise Exception(f"播放列表生成器必须是以下之一： {'/'.join(generators.keys())}")
        if opts.login:
            sess = get_session(generator.HOST)
        else:
            sess = None
        if not os.path.exists(opts.output):
            os.mkdir(opts.output)
        if opts.retry: # 重试失败项
            playlist = pd.read_excel(opts.output+'.xlsx').to_records(index=False)
        else: # 新拉取播放列表
            playlist = generator(sess).generate(*args)
            digit = f'%0{len(str(len(playlist)))}d'
            for i in trange(len(playlist), desc='下载播放列表'):
                title,url = playlist[i]
                if url:
                    ext = os.path.splitext(url)[-1]
                    if ext == '.m3u8':
                        ext = '.ts'
                    path = os.path.join(opts.output, format_title(title+ext, digit%i))
                    playlist[i] = path,url        
                else:
                    playlist[i] = None
            playlist = list(filter(None, playlist))
        failed = []
        m3u8_downloader = M3U8(sess)
        http_downloader = HTTP(sess)
        for path,url in tqdm(playlist):
            downloader = m3u8_downloader if url.endswith('.m3u8') else http_downloader
            try:
                asyncio.run(downloader.download(url, path))
                logger.info(f'{path} done.')
            except:
                logger.warning(format_exc())
                failed.append((path, url))
        
        if failed:
            df = pd.DataFrame(failed, columns=['path','url'])
            df.to_excel(opts.output+'.xlsx', index=False)
            logger.info(f'Failed: {len(failed)}/{len(playlist)}')
    else:
        pass
