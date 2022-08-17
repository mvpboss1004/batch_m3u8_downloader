from typing import Optional
from requests import Session
from selenium.webdriver import Firefox

def get_session(url:str) -> Session:
    browser = Firefox(service_log_path=None)
    browser.get(url)
    input('Press any key to continue')
    sess = Session()
    for c in browser.get_cookies():
        sess.cookies[c['name']] = c['value']
    sess.headers['User-Agent'] = browser.execute_script('return navigator.userAgent')
    browser.close()
    return sess

def format_title(title:str, idx:Optional[str]=None) -> str:
    path = title
    for c,r in [
        ('(','（'), (')','）'),('|',' | '),('!','！'),('?','？'),
        ('[','【'),(']','】'),(':','：'),('/','-'),('\\','-')
    ]:
        path = path.replace(c,r)
    if idx:
        path = f'{idx}.{path}'
    return path