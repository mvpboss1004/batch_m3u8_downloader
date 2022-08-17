
import asyncio
import logging
from typing import Optional

import aiofiles as aos
import m3u8
from aiofiles.tempfile import NamedTemporaryFile, TemporaryDirectory
from aiohttp import ClientSession
from aiohttp_retry import ExponentialRetry, RetryClient
from Crypto.Cipher import AES
from requests import Session

logger = logging.getLogger(__name__)

class HTTP:
    def __init__(self, sess:Optional[Session]=None):
        self.sess = sess

    async def download(self, url:str, output:str):
        async with ClientSession() as sess, aos.open(output, 'wb') as f:
            async with RetryClient(sess, retry_options=ExponentialRetry(3)) as client:
                async with client.get(url, verify_ssl=False) as r:
                    async for chunk in r.content.iter_chunked(1<<10):
                        await f.write(chunk)

class M3U8:
    def __init__(self, sess:Optional[Session]=None):
        self.sess = sess

    async def download_segment(self, segment:m3u8.Segment, temp_dir:Optional[str]=None) -> str:
        async with ClientSession() as sess, NamedTemporaryFile('wb', dir=temp_dir, delete=False) as f:
            async with RetryClient(sess, retry_options=ExponentialRetry(3)) as client:
                async with client.get(segment.uri, verify_ssl=False) as r:
                    ts = await r.read()
                if segment.key:
                    async with client.get(segment.key.uri, verify_ssl=False) as r:
                        key = await r.read()
                        method = segment.key.method.split('-')[0]
                        if method == 'AES':
                            if segment.key.iv:
                                if len(segment.key.iv)==16:
                                    iv = segment.key.iv.encode()
                                elif segment.key.iv.startswith('0x'):
                                    iv = bytes.fromhex(segment.key.iv[2:])
                                else:
                                    raise Exception(f'Unsupported iv: {segment.key.iv}')
                            else:
                                iv = None
                            ts = AES.new(key, AES.MODE_CBC, iv).decrypt(ts)
                await f.write(ts)
                name = f.name
        return name
                
    async def download(self, url:str, output:str):
        playlist = m3u8.load(url)
        async with TemporaryDirectory() as temp_dir, aos.open(output, 'wb') as fout:
            tasks = [self.download_segment(seg,temp_dir) for seg in playlist.segments]
            for name in await asyncio.gather(*tasks):
                async with aos.open(name, 'rb') as fin:
                    await fout.write(await fin.read())
