# -*- coding: utf-8 -*-

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import json
import time
import re
import random
from selenium.webdriver.chrome.options import Options
import sys
import pymongo
from pymongo import MongoClient
import tesserocr
from PIL import Image
import pytesseract
from fake_useragent import UserAgent
from selenium.webdriver.common.keys import Keys

db = MongoClient().fayi
ncase = db.case

# load docids
with open('') as nplist:
    ldata = json.load(nplist)
    alldocid = [i['docid'] for i in ldata]

reg = re.compile(r'<[^>]+>', re.S)

# driver settings
ua = UserAgent()
userAgent = ua.random
chrome_options = Options()
# chrome_options.add_argument("--headless") # enable headless chrome
chrome_options.add_argument(f'user-agent={userAgent}')
# prefs = {"profile.managed_default_content_settings.images": 2} # disable images
# chrome_options.add_experimental_option("prefs", prefs)


class fayi():
    def __init__(self):
        self.url = 'http://www.lawyee.org/'

    def loginpage(self):
        self.driver = webdriver.Chrome(
            executable_path=r'', options=chrome_options)  # add chrome driver path
        self.driver.maximize_window()
        self.driver.set_page_load_timeout(120)
        self.driver.get('http://www.lawyee.org/')
        time.sleep(3)
        self.driver.find_element_by_class_name('logo-font').click()
        self.driver.get_screenshot_as_file('pictures/screenshot.png')
        pict = self.driver.find_element_by_id('img_validate')
        # solve captcha using tesserocr
        left = int(pict.location['x'])
        top = int(pict.location['y'])
        right = int(pict.location['x'] + pict.size['width'])
        bottom = int(pict.location['y'] + pict.size['height'])
        im = Image.open('pictures/screenshot.png')
        im = im.crop((left, top, right, bottom))
        time.sleep(3)
        im.save('pictures/code.png')
        im = Image.open('pictures/code.png')
        code = tesserocr.image_to_text(im)
        self.driver.find_element_by_id('UserName').send_keys(
            '')  # enter username/password
        self.driver.find_element_by_id('PassWord').send_keys(
            '')  # enter username/password
        self.driver.find_element_by_id(
            'ValidateCode').send_keys(code)
        self.driver.find_element_by_id(
            'ValidateCode').send_keys(Keys.ENTER)

    def gettext(self):
        self.loginpage()
        for doc in alldocid:
            while True:
                try:
                    time.sleep(random.randrange(1, 3))
                    self.driver.get(
                        f'http://www.lawyee.org/PubPage/Detail?DataID={doc}&PageID=41&RowNum=1&IsRecord=true')
                    WebDriverWait(self.driver, 30).until(
                        EC.frame_to_be_available_and_switch_to_it((By.NAME, 'frmContent')))
                    allcontent = WebDriverWait(self.driver, 20).until(
                        EC.presence_of_element_located((By.ID, "content")))
                    fulltext = allcontent.text
                    html = allcontent.get_attribute('outerHTML')
                    names = re.findall(
                        r'<a type=\"dir\" name=\"(.*?)\"', html, re.S)
                    case = dict()
                    case['docid'] = doc
                    for n in names[0:-1]:
                        name = reg.sub('', re.search(
                            fr'(<a type=\"dir\" name=\"{n}\".*?)<a type', html, re.S).group(1))
                        case[n] = name
                    lastkey = names[-1]
                    lastvalue = reg.sub('', re.search(
                        fr'(<a type=\"dir\" name=\"{lastkey}\".*?)</div>', html, re.S).group(1))
                    case[lastkey] = lastvalue
                    case['fulltext'] = fulltext
                    ncase.insert_one(case)
                except TimeoutException:
                    print(doc, 'TimeoutException')
                    time.sleep(5)
                    self.driver.refresh()
                    continue
                except Exception as e:
                    print(doc, e)
                    time.sleep(5)
                    self.driver.refresh()
                    continue
                else:
                    if doc == alldocid[-1]:
                        self.driver.delete_all_cookies()
                        self.driver.quit()
                    break


if __name__ == '__main__':
    fy = fayi()
    fy.gettext()
