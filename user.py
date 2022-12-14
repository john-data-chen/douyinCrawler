# -*- coding:utf-8 -*-
import json
import os
import re
import sys
import time
import warnings
from random import randint

import execjs
import prettytable
import requests
from lxml import etree

warnings.filterwarnings('ignore')

'''批量下载抖音视频'''

RANDOM_MAX_DELAY = 3
WAIT_MIN = 10
WAIT_MAX = 60
DEFAULT_MAX_VIDEO = 50

FILEPATH = './userList.txt'

proxies = {
    # 'http': 'http://115.238.65.118:80',
    # 'https': 'https://103.105.58.84:3128',
}

def random_pc_user_agent():
    userAgents = [
        'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:33.0) Gecko/20120101 Firefox/33.0',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10; rv:33.0) Gecko/20100101 Firefox/33.0',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.102 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10; rv:33.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.102 Safari/537.36'
    ]
    return userAgents[randint(0, len(userAgents)-1)]

def random_ios_user_agent():
    userAgents = [
        'Mozilla/5.0 (iPhone; CPU iPhone OS 12_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148',
        'Mozilla/5.0 (iPhone; CPU iPhone OS 12_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/12.1 Mobile/15E148 Safari/604.1',
        'Mozilla/5.0 (iPhone; CPU iPhone OS 12_1_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/16D57',
        'Mozilla/5.0 (iPhone; CPU iPhone OS 13_3_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.0.5 Mobile/15E148 Safari/604.1'
    ]
    return userAgents[randint(0, len(userAgents)-1)]

# add downloaded percentage check
def downloaded_checker(num_videos, path):
    # check num_videos is valid, if not set to 0
    try:
        num_videos = int(num_videos)
    except:
        print("num_videos is not valid: " + num_videos)
        num_videos = 0
    # if num_videos of id is incorrect, set a default value
    if num_videos <= 0:
        num_videos = DEFAULT_MAX_VIDEO
    # total of downloaded videos
    downloaded_videos = len([name for name in os.listdir(path) if os.path.isfile(os.path.join(path, name))])
        # check downloaded percentage
    downloaded_percentage = downloaded_videos / num_videos
    return downloaded_percentage

class Douyin():
    def __init__(self):
        self.user_url = 'https://www.amemv.com/share/user/{}'
        self.video_url = 'https://www.iesdouyin.com/web/api/v2/aweme/post/'
        self.session = requests.Session()
        self.headers = {
            'User-Agent': random_pc_user_agent()
        }
        self.ios_headers = {
            'User-Agent': random_ios_user_agent()
        }
        fp = open('./encrypt.js', 'r', encoding='utf-8')
        self.ctx = execjs.compile(fp.read())
        self.font_dict = {" &#xe603; ": "0", " &#xe60d; ": "0", " &#xe616; ": "0",
                          " &#xe602; ": "1", " &#xe60e; ": "1", " &#xe618; ": "1",
                          " &#xe605; ": "2", " &#xe610; ": "2", " &#xe617; ": "2",
                          " &#xe604; ": "3", " &#xe611; ": "3", " &#xe61a; ": "3",
                          " &#xe606; ": "4", " &#xe60c; ": "4", " &#xe619; ": "4",
                          " &#xe607; ": "5", " &#xe60f; ": "5", " &#xe61b; ": "5",
                          " &#xe608; ": "6", " &#xe612; ": "6", " &#xe61f; ": "6",
                          " &#xe60a; ": "7", " &#xe613; ": "7", " &#xe61c; ": "7",
                          " &#xe60b; ": "8", " &#xe614; ": "8", " &#xe61d; ": "8",
                          " &#xe609; ": "9", " &#xe615; ": "9", " &#xe61e; ": "9"}

    '''外部调用'''

    def run(self):
        # read id from txt
        fp = open(FILEPATH, "r")
        lines = fp.readlines()
 
        for userid in lines:
            # remove space of string
            userid = userid.strip()
            # 获取用户主页信息
            try:
                response = self.session.get(self.user_url.format(userid), headers=self.headers, proxies=proxies)
                # sleep 1~3 secs
                time.sleep(randint(1, RANDOM_MAX_DELAY))
                html = response.text
                for key, value in self.font_dict.items():
                    if key in html:
                        html = html.replace(key, value)
                assert 'dytk' in html
            except:
                print('[Warning]: 用户ID ' + userid + '输入有误.')
                time.sleep(randint(1, RANDOM_MAX_DELAY))
                continue
            dytk = re.findall(r"dytk: '(.*?)'", html)[0]
            tac = re.findall(r"<script>tac='(.*?)'</script>", html)[0]
            html = etree.HTML(html)
            nickname = html.xpath('//p[@class="nickname"]/text()')[0]
            douyinid = ''.join(html.xpath('//p[@class="shortid"]/i/text()'))
            num_followers = ''.join(html.xpath('//span[@class="follower block"]/span[1]//text()')).strip()
            num_videos = ''.join(html.xpath('//div[@class="user-tab active tab get-list"]/span/i/text()'))

            # 视频文件保存位置
            path = "./download/" + str(nickname).strip() + str(userid).strip() + "/"
            # create folder if not exists
            if not os.path.exists(path):
                os.makedirs(path)
            # check downloaded percentage
            downloaded_percentage = downloaded_checker(num_videos, path)
            if downloaded_percentage < 0.9:
                print("downloaded percentage < 90%: " + str(nickname).strip() + str(userid).strip())
            else:
                print("downloaded percentage > 90%: " + str(nickname).strip() + str(userid))
                # if this is last id, exit
                if userid.strip() == lines[-1]:
                    break
                else:
                    continue
            # 打印用户主页信息供使用者确认
            tb = prettytable.PrettyTable()
            tb.field_names = ['昵称', '抖音ID', '粉丝数量', '作品数量']
            tb.add_row([nickname, douyinid, num_followers, num_videos])
            print('目标用户的信息如下:')
            print(tb)
            self.__downloadUserVideos(userid, dytk, tac, path, nickname, downloaded_percentage)
            # next id
            userid = fp.readline()

    '''下载目标用户的所有视频'''

    def __downloadUserVideos(self, userid, dytk, tac, path, nickname, num_videos):
        # 获取signature
        signature = self.ctx.call('get_sign', userid, tac, self.headers['User-Agent'])
        # 获取视频作品列表
        params = {
            'user_id': userid,
            # 加密 uid，本接口下默认为空
            'sec_uid': '',
            # 请求数量，固定值不变
            'count': '1000',
            # 本次请求视频最大值，可从上一次请求的 response 中获取，初始为 0
            'max_cursor': '0',
            # appid 固定不变
            'aid': '1128',
            # 加密签名
            '_signature': signature,
            # 用户 token
            'dytk': dytk
        }
        counter = 0
        while True:
            try:
                response = self.session.get(self.video_url, headers=self.headers, params=params, proxies=proxies)
            except:
                print(f"请求视频接口异常已跳过，当前请求参数为{params}")
                time.sleep(randint(1, RANDOM_MAX_DELAY))
                continue
            response_json = response.json()
            # print(json.dumps(response_json, indent=4))
            all_items = response_json['aweme_list']
            # if retry 6 times and download 90% videos, then skip to next id
            if counter > 5:
                # check downloaded percentage
                downloaded_percentage = downloaded_checker(num_videos, path)
                if downloaded_percentage < 0.9:
                    print("downloaded percentage < 90%: " + str(nickname).strip() + str(userid).strip())
                else:
                    print("downloaded percentage > 90%: " + str(nickname).strip() + str(userid))
                    break
            # 获取 max_cursor 为下次请求做准备
            try:
                max_cursor = response_json['max_cursor']
            except:
                print("no max_cursor")
                print(json.dumps(response_json, indent=4))
                time.sleep(randint(WAIT_MIN, WAIT_MAX))
                counter += 1
                continue
            # 获取 has_more 参数，判断是否为最后一条请求
            try:
                has_more = response_json['has_more']
                params['max_cursor'] = max_cursor
            except:
                print("no has_more")
                print(json.dumps(response_json, indent=4))
                time.sleep(randint(WAIT_MIN, WAIT_MAX))
                counter += 1
                continue
            # 开始下载
            for item in all_items:
                savename = item['desc']
                download_url = item['video']['play_addr']['url_list'][0]
                try:
                    self.__download(download_url, savename, path)
                except:
                    print("download " + savename + " fail")
                    time.sleep(randint(1, 3))
                    continue

    '''视频下载'''

    def __download(self, download_url, savename, path):
        print('[INFO]: checking ——> %s' % savename)
        response = self.session.get(url=download_url, headers=self.ios_headers, stream=True, verify=False, proxies=proxies)
        # check download size, if incorrect meaning blocked, sleep randomly
        if (response.headers["content-length"]):
            total_size = response.headers["content-length"]
        if (response.headers["Content-Length"]):
            total_size = response.headers["Content-Length"]
        if (int(total_size) == 0):
            print("invalid total_size, sleep...")
            time.sleep(randint(WAIT_MIN, WAIT_MAX))
        else:
            p = 0
            if response.status_code == 200:
                print("[文件大小]: %.2f MB" % (int(total_size) / 1024 / 1024))
            # check video file exists
            if not (os.path.isfile(os.path.join(path, savename + '.mp4'))):
            # sleep 1~3 secs
                time.sleep(randint(1,3))
                with open(os.path.join(path, savename + '.mp4'), "wb") as f:
                    # 开始下载每次请求1024字节
                    for i in response.iter_content(chunk_size=1024):
                        p += len(i)
                        f.write(i)
                        done = 50 * p / int(total_size)
                        sys.stdout.write("\r[%s%s] %.2f%%" % ('█' * int(done), '' * int(50 - done), done + done))
                        sys.stdout.flush()
                print("\n")
            else:
                print(os.path.join(path, savename + '.mp4') + ' is downloaded')

'''run'''
if __name__ == '__main__':
    start_time = time.time()
    client = Douyin()
    client.run()
    print("\033[5;37;40m总耗时：{}s \033[0m".format(int(time.time() - start_time)))
