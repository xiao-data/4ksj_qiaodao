#!/opt/conda/bin/python3.9
import httpx
import re
import sys
import time
import logging
from logging.handlers import RotatingFileHandler
from urllib.parse import urlencode

# global variables
uname = ''         # username
upassword = ''   # password
loginhash = ''
logpath = '/home/anaconda/4ksj.log'
r = httpx.Client(http2=True)
#r = httpx.Client(http2=True, proxsies='http://127.0.0.1:8080', verify=False)
headers = {'Host':'www.4ksj.com',
'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:106.0) Gecko/20100101 Firefox/106.0',
'Accept':'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
'Accept-Language':'zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2',
'Accept-Encoding':'gzip, deflate',
'Upgrade-Insecure-Requests':'1',
'Sec-Fetch-Dest':'document',
'Sec-Fetch-Mode':'navigate',
'Sec-Fetch-Site':'same-origin',
'Sec-Fetch-User':'?1',
'Te':'trailers'
}

def getK(spaceurl):
    logger = logging.getLogger('4ksj')
    ret = r.get(spaceurl, headers = headers).text
    time.sleep(1)
    K_now = re.findall(r'<li><em>K币</em>(.*?) 个</li>', ret)[0]
    logger.info('当前K币: ' + str(K_now) + '个')
    return K_now

def login(uname, upassword, formhash):
    logger = logging.getLogger('4ksj')
    headers['Referer'] = 'https://www.4ksj.com/'
    ret = r.get(r'https://www.4ksj.com/member.php?mod=logging&action=login', headers=headers).text
    time.sleep(1)
    loginhash = re.findall(r'layer_login1_(.*?)"', ret)[0]
    logger.debug('loginhash' + loginhash)

    headers['Origin'] = 'https://www.4ksj.com'
    headers['Referer'] = 'https://www.4ksj.com/member.php?mod=logging&action=login'
    headers['Sec-Fetch-Dest'] = 'iframe'
    headers['Content-Type'] = 'application/x-www-form-urlencoded'
    data = {'formhash':formhash, 'referer':'https://www.4ksj.com/', 'username':uname, 'password':upassword, 'questionid':'0', 'answer':''}
    ret = r.post('https://www.4ksj.com/member.php?mod=logging&action=login&loginsubmit=yes&loginhash='+loginhash+'&inajax=1', headers = headers, data=urlencode(data)).text
    time.sleep(1)

    if 'succeedmessage' in ret:
        logger.info('登录成功')
    else:
        logger.error(re.findall(r'errorhandle_\(\'(.*?)\', {', ret)[0])
        return False, False

    del headers['Origin']
    del headers['Content-Type']
    headers['Sec-Fetch-Dest'] = 'document'
    ret = r.get('https://www.4ksj.com', headers=headers).text
    spaceurl, nickname = re.findall(r'<p class="username"><a href="(.*?)">(.*?)</a>', ret)[0]
    logger.info('nickname: ' + nickname + ', spaceurl: ' + spaceurl)
    return nickname, spaceurl

def qiandao(nickname):
    logger = logging.getLogger('4ksj')
    headers['Referer'] = spaceurl
    ret = r.get('https://www.4ksj.com/qiandao/', headers = headers).text
    time.sleep(1)
    formhash = re.findall(r'action=logout&amp;formhash=(.*?)"', ret)[0]
    logger.debug('formhash2: ' + formhash)

    headers['Referer'] = 'https://www.4ksj.com/qiandao/'
    headers['Sec-Fetch-Dest'] = 'empty'
    headers['Sec-Fetch-Mode'] = 'cors'
    headers['Accept'] = '*/*'
    headers['X-Requested-With'] = 'XMLHttpRequest'
    del headers['Upgrade-Insecure-Requests']
    ret = r.get('https://www.4ksj.com//qiandao/?mod=sign&operation=list&inajax=1&ajaxtarget=ranklist', headers = headers).text
    time.sleep(1)

    ret = r.get('https://www.4ksj.com//qiandao/?mod=sign&operation=qiandao&formhash=' + formhash + '&format=empty&inajax=1&ajaxtarget=', headers = headers).text
    time.sleep(1)
    if '今日已签' in ret:
        logger.info('今日已签')
    if '<root><![CDATA[]]></root>' in ret:
        logger.info('签到成功')

def logout(formhash):
    logger = logging.getLogger('4ksj')
    ret = r.get('https://www.4ksj.com/member.php?mod=logging&action=logout&formhash=' + formhash, headers = headers).text


if __name__ == '__main__':
    logger = logging.getLogger('4ksj')
    rh = RotatingFileHandler(logpath, maxBytes=100*1024, backupCount=3)
    rh.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
    logger.addHandler(rh)
    logger.setLevel(logging.INFO)
    #logger.setLevel(logging.DEBUG)
    
    for i in range(5): # retry for 5 times
        if i > 0:
            logger.warn('retrying for ' + str(i) + 'times')
        try:
            ret = r.get('https://www.4ksj.com', headers=headers).text
            time.sleep(1)
            formhash = re.findall(r'action=logout&amp;formhash=(.*?)"', ret)[0]
            logger.debug('formhash1: ' + formhash)
            nickname, spaceurl = login(uname, upassword, formhash)
            if not nickname:
                sys.exit(0) # exit if login failed
            headers['Referer'] = 'https://www.4ksj.com/'
            #getK(spaceurl)

            qiandao(nickname)

            headers['Referer'] = 'https://www.4ksj.com/qiandao/'
            headers['Accept']='text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8'
            headers['Sec-Fetch-Dest'] = 'document'
            headers['Sec-Fetch-Mode'] = 'navigate'
            headers['Upgrade-Insecure-Requests'] = '1'
            del headers['X-Requested-With']
            
            getK(spaceurl)

            logout(formhash)
            sys.exit(0)
        except Exception as e:
            logger.critical('line: ' + str(e.__traceback__.tb_lineno) + ' ' + repr(e))
            time.sleep(10)
