# coding: utf-8
#
###############################
#
# pip install pytest
# pip install selenium
# pip install webdriver-manager
#
###############################

DEFAULT_URL = 'https://www.movapp.cz/'

import os
import os.path
import requests

os.environ['WDM_LOCAL'] = '1'

import pytest
from selenium import webdriver

from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager

from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import *
from selenium.webdriver import ActionChains

from random import choice



def check_url(url):
    import re
    regex = re.compile(
            r'^(?:http|ftp)s?://' # http:// or https://
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|' #domain...
            r'localhost|' #localhost...
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})' # ...or ip
            r'(?::\d+)?' # optional port
            r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    if re.match(regex, url) is None:
        return False
    return True

class MoveAppTest():

    def __init__(self, url=DEFAULT_URL):
        if not check_url(url):
            exit('Neplatná adresa URL %s' % url)
        if url[-1] != '/':
            url += '/'
        self.url = url
        self.links=[self.url]
        self.files=[]


    def click_expand_buttons(self, buttons):
        for el in (buttons[0],choice(buttons),buttons[-1]):
            el.click()
            # print("\t\t %s" % el.get_attribute('id'))

    def click_sound_buttons(self, driver, buttons):
        for el in (buttons[0],choice(buttons),buttons[-4]):
            try:
                webdriver.ActionChains(driver).move_to_element(el).click(el).perform()
                #print('button', el.get_attribute('aria-label'))
            except Exception as ex:
                print(ex)
            try:
                audio = driver.find_element(By.CSS_SELECTOR,
                                   '[aria-label="%s"] audio' % el.get_attribute('aria-label') )
                WebDriverWait(driver, 3).until(lambda d: audio.get_attribute('currentTime')!='0')
            except NoSuchElementException: # není <audio>
                pass
            except TimeoutException:
                print('Chyba zvuku %s' % audio.get_attribute('src') )



    def check_page(self, driver, path = ''):

        if path=='':
            path=self.url
        x = requests.get(path)
        try:
            assert x.ok
        except AssertionError:
            print('Chyba stránky %s.' % path)
            return
        driver.get(path)
        print('\t%s' % path)

        # check buttons
        buttons = driver.find_elements(By.CSS_SELECTOR, 'button[aria-expanded=false]')
        if len(buttons)>0:
            self.click_expand_buttons(buttons)

        # check images

        # check sounds
        buttons = driver.find_elements(By.CSS_SELECTOR, 'button[aria-label]')
        if len(buttons)>0:
            self.click_sound_buttons(driver, buttons)

        # check links
        links = []
        ActionChains(driver).move_by_offset(0,0).perform()
        for el in driver.find_elements(By.CSS_SELECTOR, 'a'):
            l = el.get_attribute('href')
            if l is None:
                print(el.text)
                continue
            if (l[-4:] == '.pdf') or (l[-4:] == '.txt'):
                if (l not in self.files):
                    self.files.append(l)
                    try:
                        webdriver.ActionChains(driver).move_to_element(el).click(el).perform()
                    except Exception as ex:
                        print(el.get_attribute('href'))
                        print(ex)
            elif check_url(l):
                links.append(l)
            else:
                print('Špatný URL %s' % l)
        for l in links:
            if l not in self.links:
                self.links.append(l)
                if self.url not in l: # externí odkaz
                    x = requests.get(l)
                    try:
                        assert x.ok
                    except AssertionError:
                        print('Nesprávný externí odkaz %s.' % l)
                else:
                    self.check_page(driver, l)

    def check_downloads(self):
        for l in self.files:
            filename = l.split('/')[-1]
            try:
                os.remove(os.path.join(files_dir, filename))
            except FileNotFoundError:
                print('Chyba stahování souboru %s' % l)


if __name__ == '__main__':
    from sys import argv


    print('test')
    if len(argv)>1:
        mt = MoveAppTest(argv[1])
    else:
        mt = MoveAppTest()

    files_dir = os.path.join(os.getcwd(),'files')
    if not os.path.exists(files_dir):
        os.mkdir(files_dir)
    service=ChromeService(executable_path=ChromeDriverManager().install())
    options = webdriver.ChromeOptions()
    options.add_experimental_option("excludeSwitches", ["enable-logging"])
    options.add_experimental_option("prefs", {"download.default_directory": files_dir})
    options.add_argument("--mute-audio")
    driver = webdriver.Chrome(options=options, service=service)
    mt.check_page(driver)
    mt.check_downloads()
    driver.quit()