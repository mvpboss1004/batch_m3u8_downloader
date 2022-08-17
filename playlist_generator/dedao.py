import logging
from typing import List, Optional, Tuple

from benedict import benedict
from requests import Session
from tqdm import tqdm

logger = logging.getLogger(__name__)

class DeDao:
    HOST = 'https://www.dedao.cn'
    PURCHASE_ARTICLE_LIST = '/pc/bauhinia/pc/class/purchase/article_list'
    FREE_ARTICLE_LIST = '/pc/bauhinia/pc/class/free_article_list'

    def __init__(self, sess:Optional[Session]=None):
        if sess:
            self.sess = sess
            self.article_url = DeDao.PURCHASE_ARTICLE_LIST
        else:
            self.sess = Session()
            self.article_url = DeDao.FREE_ARTICLE_LIST
        self.sess.verify = False
            
    def generate(self, detail_id:str, *args, **kwargs) -> List[Tuple[str,Optional[str]]]:
        url = DeDao.HOST + self.article_url
        playlist = []
        max_id = 0
        data = {
            'chapter_id':'', 'count':30,
            'detail_id':detail_id,
            'include_edge':False, 'is_unlearn':False,
            'max_order_num':0,
            'reverse':False, 'since_id':0,
            'since_order_num':0,
            'unlearn_switch':False
        }
        with tqdm(desc='加载播放列表') as pbar:
            while max_id is not None:
                data['max_id'] = max_id
                r = self.sess.post(url, json=data).json()
                article_list = benedict(r).get('c.article_list')
                if article_list:
                    for article in article_list:
                        playlist.append((article['title'], benedict(article).get('audio.mp3_play_url')))
                    max_id = article['id']
                    pbar.update(len(article_list))

                else:
                    max_id = None
        return playlist
