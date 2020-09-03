# -*- coding:utf-8 -*-
import os
import re
import sys
import time
import json
import click
import execjs
import warnings
import requests
import prettytable
from lxml import etree
from random import randint
from contextlib import closing

warnings.filterwarnings('ignore')

'''批量下载抖音视频'''

class Douyin():
    def __init__(self):
        self.user_url = 'https://www.amemv.com/share/user/{}'
        self.video_url = 'https://www.iesdouyin.com/web/api/v2/aweme/post/'
        self.session = requests.Session()
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.89 Safari/537.36'
        }
        self.ios_headers = {
            'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 9_2 like Mac OS X) AppleWebKit/601.1.46 (KHTML, like Gecko) Version/9.0 Mobile/13C75 Safari/601.1'
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
        filepath = './idList.txt'
        fp = open(filepath, "r")
        userid = fp.readline()
 
        ## 用 while 逐行讀取檔案內容，直至檔案結尾
        while userid:
            # remove space of string
            userid = userid.strip()
            # 获取用户主页信息
            try:
                response = self.session.get(self.user_url.format(userid), headers=self.headers)
                # sleep 1~3 secs
                time.sleep(randint(1,3))
                html = response.text
                for key, value in self.font_dict.items():
                    if key in html:
                        html = html.replace(key, value)
                assert 'dytk' in html
            except:
                print('[Warning]: 用户ID ' + userid + '输入有误.')
                time.sleep(randint(1,3))
                continue
            dytk = re.findall(r"dytk: '(.*?)'", html)[0]
            tac = re.findall(r"<script>tac='(.*?)'</script>", html)[0]
            html = etree.HTML(html)
            nickname = html.xpath('//p[@class="nickname"]/text()')[0]
            douyinid = ''.join(html.xpath('//p[@class="shortid"]/i/text()'))
            num_followers = ''.join(html.xpath('//span[@class="follower block"]/span[1]//text()')).strip()
            num_videos = ''.join(html.xpath('//div[@class="user-tab active tab get-list"]/span/i/text()'))
            # 打印用户主页信息供使用者确认
            tb = prettytable.PrettyTable()
            tb.field_names = ['昵称', '抖音ID', '粉丝数量', '作品数量']
            tb.add_row([nickname, douyinid, num_followers, num_videos])
            print('目标用户的信息如下:')
            print(tb)
            self.__downloadUserVideos(userid, dytk, tac, nickname)
            # next id
            userid = fp.readline()

    '''下载目标用户的所有视频'''

    def __downloadUserVideos(self, userid, dytk, tac, nickname):
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
        while True:
            try:
                response = self.session.get(self.video_url, headers=self.headers, params=params)
            except:
                print(f"请求视频接口异常已跳过，当前请求参数为{params}")
                time.sleep(randint(1,3))
                continue
            response_json = response.json()
            # print(json.dumps(response_json, indent=4))
            all_items = response_json['aweme_list']
            # 获取 max_cursor 为下次请求做准备
            try:
                max_cursor = response_json['max_cursor']
            except:
                print("no max_cursor counter: " + retry)
                print(json.dumps(response_json, indent=4))
                time.sleep(randint(1,60))
                continue
            # 获取 has_more 参数，判断是否为最后一条请求
            try:
                has_more = response_json['has_more']
                params['max_cursor'] = max_cursor
            except:
                print("no has_more")
                print(json.dumps(response_json, indent=4))
                time.sleep(randint(1,60))
                continue
            # 开始下载
            for item in all_items:
                savename = item['desc']
                download_url = item['video']['play_addr']['url_list'][0]
                try:
                    self.__download(download_url, savename, str(userid), nickname)
                except:
                    print("download " + savename + " fail")
                    time.sleep(randint(1, 3))
                    continue

    '''视频下载'''

    def __download(self, download_url, savename, savedir, nickname):
        print('[INFO]: checking ——> %s' % savename)
        # 视频文件保存位置
        path = "./download/" + str(nickname).strip() + savedir.strip() + "/"
        if not os.path.exists(path):
            os.makedirs(path)
        response = self.session.get(url=download_url, headers=self.ios_headers, stream=True, verify=False)
        total_size = response.headers["content-length"]
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
