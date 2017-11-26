#!/usr/bin/env python
import time
import os
import json

import requests
from selenium import webdriver
from selenium.common.exceptions import InvalidElementStateException
from bs4 import BeautifulSoup as BS

from tweet import send_tweet

with open('weibo_account.json', 'r') as f:
    ACCOUNT = json.load(f)

LOGIN_URL = 'https://passport.weibo.cn/signin/login'
PHANTOM_JS_PATH = '/bin/phantomjs'
COOKIE_PATH = 'cookie'
URL = 'https://weibo.cn/dagudu?filter=0&page=1'

headers = requests.utils.default_headers()
UA = {
    'User-Agent':
    'Mozilla/5.0 (Windows NT 5.1; rv:11.0) Gecko/20100101 Firefox/11.0'
}
headers.update(UA)


def get_cookie_str(account_id, account_password):
    if os.path.exists(COOKIE_PATH):
        with open(COOKIE_PATH) as f:
            return f.read()

    phantom_js_driver_file = os.path.abspath(PHANTOM_JS_PATH)
    if os.path.exists(phantom_js_driver_file):
        try:
            print('loading PhantomJS from {}'.format(phantom_js_driver_file))
            driver = webdriver.PhantomJS(phantom_js_driver_file)
            # must set window size or will not find element
            driver.set_window_size(1640, 688)
            driver.get(LOGIN_URL)
            print("loading login page")
            # wait for page render
            time.sleep(2)
            driver.find_element_by_xpath('//input[@id="loginName"]').send_keys(
                account_id)
            driver.find_element_by_xpath(
                '//input[@id="loginPassword"]').send_keys(account_password)
            # driver.find_element_by_xpath('//input[@id="loginPassword"]').send_keys(Keys.RETURN)
            print('account id: {}'.format(account_id))
            print('account password: {}'.format(account_password))

            driver.find_element_by_xpath('//a[@id="loginAction"]').click()
        except InvalidElementStateException as e:
            print(e)
            print("Failed to load login page")

        try:
            cookie_list = driver.get_cookies()
            cookie_str = ''
            for cookie in cookie_list:
                if 'name' in cookie and 'value' in cookie:
                    cookie_str += cookie['name'] + '=' + cookie['value'] + ';'

            if 'SSOLoginState' in cookie_str:
                print("Login succeed")

                with open(COOKIE_PATH, 'w') as f:
                    f.write(cookie_str)
                return cookie_str
            else:
                print("Login failed")

        except Exception as e:
            print(e)

    else:
        print("go get PhantomJS")


def parse_raw(raw_html):
    is_repost = raw_html.find('span', class_='cmt')
    # tweet_time = raw_html.find('span', class_='ct').extract()
    if is_repost:
        original_status = raw_html.find('span', class_='ctt').text
        comment = raw_html.findAll('div')[1]
        comment = comment.contents[1]
        status = str(comment) + "转发微博: " + original_status
    else:
        status = raw_html.find('span', class_='ctt').text

    status = status.strip().replace('\u200b', '').replace('\xa0', ' ')

    ret = []
    if len(status) > 150:
        num_tweet = len(status) // 140 + 1
        i = 1
        while len(status) > 140:
            ret.append("(%d/%d) %s" % (i, num_tweet, status[:140]))
            status = status[140:]
            i += 1
        ret.append("(%d/%d) %s" % (i, num_tweet, status))
    else:
        ret.append(status)
    return ret


cookie = {"Cookie": get_cookie_str(ACCOUNT['id'], ACCOUNT['password'])}
resp = requests.get(URL, cookies=cookie, headers=headers)
soup = BS(resp.text, "lxml")
raw_statuses = soup.findAll('div', class_='c')[1:-2]
statuses = [x for xs in (map(parse_raw, raw_statuses)) for x in xs]

sent_tweets = []
if os.path.exists('sent.json'):
    with open('sent.json', 'r') as f:
        sent_tweets = json.load(f)

for status in statuses[::-1]:
    if status not in sent_tweets:
        send_tweet(status)

with open('sent.json', 'w') as f:
    json.dump(statuses, f)
