# -*- coding:utf-8 -*-
'''
Function:
    批量下载抖音视频
Author:
    Charles
微信公众号:
    Charles的皮卡丘
'''
import os
import re
import sys
import time
import click
import execjs
import warnings
import requests
import prettytable
from lxml import etree
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
                html = response.text
                for key, value in self.font_dict.items():
                    if key in html:
                        html = html.replace(key, value)
                assert 'dytk' in html
            except:
                print('[Warning]: 用户ID' + userid + '输入有误.')
                break
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
            userid = fp.readline()

    '''下载目标用户的所有视频'''

    def __downloadUserVideos(self, userid, dytk, tac, nickname):
        # 获取signature
        signature = self.ctx.call('get_sign', userid, tac, self.headers['User-Agent'])
        # 获取视频作品列表
        params = {
            'user_id': userid,
            'sec_uid': '',
            'count': '1000',
            'max_cursor': '0',
            'aid': '1128',
            '_signature': signature,
            'dytk': dytk
        }
        response = self.session.get(self.video_url, headers=self.headers, params=params)
        response_json = response.json()
        all_items = response_json['aweme_list']
        # print(all_items)
        # 开始下载
        for item in all_items:
            savename = item['desc']
            download_url = item['video']['play_addr']['url_list'][0]
            self.__download(download_url, savename, str(userid), nickname)

    '''视频下载'''

    def __download(self, download_url, savename, savedir, nickname):
        print('[INFO]: 正在下载 ——> %s' % savename)
        # 视频文件保存位置
        path = "./download/" + str(nickname).strip() + savedir.strip() + "/"
        if not os.path.exists(path):
            os.makedirs(path)
        try:
            # 下载方式一:
            # with closing(self.session.get(download_url, headers=self.ios_headers, stream=True, verify=False)) as response:
            #     total_size = int(response.headers['content-length'])
            #     if response.status_code == 200:
            #         label = '[FileSize]:%0.2f MB' % (total_size / (1024 * 1024))
            #         with click.progressbar(length=total_size, label=label) as progressbar:
            #             with open(os.path.join(savedir, savename + '.mp4'), "wb") as fp:
            #                 for chunk in response.iter_content(chunk_size=1024):
            #                     if chunk:
            #                         fp.write(chunk)
            #                         progressbar.update(1024)

            # 下载方式二：
            response = self.session.get(url=download_url, headers=self.ios_headers, stream=True, verify=False)
            total_size = response.headers["content-length"]
            p = 0
            if response.status_code == 200:
                print("[文件大小]: %.2f MB" % (int(total_size) / 1024 / 1024))
                with open(os.path.join(path, savename + '.mp4'), "wb") as f:
                    # 开始下载每次请求1024字节
                    for i in response.iter_content(chunk_size=1024):
                        p += len(i)
                        f.write(i)
                        done = 50 * p / int(total_size)
                        sys.stdout.write("\r[%s%s] %.2f%%" % ('█' * int(done), '' * int(50 - done), done + done))
                    sys.stdout.flush()
                print("\n")
        except Exception as e:
            print(e)


'''run'''
if __name__ == '__main__':
    start_time = time.time()
    client = Douyin()
    client.run()
    print("\033[5;37;40m总耗时：{}s \033[0m".format(int(time.time() - start_time)))
