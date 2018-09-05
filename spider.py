# 使用selenium+Chrome/PhantomJS   爬取淘宝美食数据
import re

from selenium import webdriver
#引入异常处理
from selenium.common.exceptions import TimeoutException
#参考http://selenium-python.readthedocs.io/waits.html

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
#解析
from pyquery import PyQuery
from config import *
#引入配置文件
import pymongo

client=pymongo.MongoClient(MONGO_URL)
db=client[MONGO_DB]

browser = webdriver.Chrome()
wait = WebDriverWait(browser, 10)
# 搜索关键字
def search():
    try:
        browser.get('https://www.taobao.com')
        input = wait.until(  # 输入框
            EC.presence_of_element_located((By.CSS_SELECTOR, '#q'))
        )
        # 提交按钮
        submit = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR,
                                                        '#J_TSearchForm > div.search-button > button')))
        input.send_keys(KEY_WORD)
        submit.click()
        total = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR,
                                                       '#mainsrp-pager > div > div > div > div.total')))
        get_products()
        return total.text
    except TimeoutException:
        return search()

# 翻页
def next_page(page_num):
    try:
        input = wait.until(  # 输入框
            EC.presence_of_element_located((By.CSS_SELECTOR, '#mainsrp-pager > div > div > div > div.form > input'))
        )
        submit = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR,
                                                        '#mainsrp-pager > div > div > div > div.form > span.btn.J_Submit')))
        input.clear()
        input.send_keys(page_num)
        submit.click()
        wait.until(EC.text_to_be_present_in_element(
            (By.CSS_SELECTOR, '#mainsrp-pager > div > div > div > ul > li.item.active > span'), str(page_num)))
        get_products()
    except:
        next_page(page_num)

# 获取商品信息
def get_products():
    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '#mainsrp-itemlist .items .item')))
    html = browser.page_source  # 整个网页
    doc = PyQuery(html)
    items = doc('#mainsrp-itemlist .items .item').items()
    for item in items:
        product = {
            'image': item.find('.pic .img').attr('src'),
            'price': item.find('.price').text(),
            'deal': item.find('.deal-cnt').text()[:-3],
            'title': item.find('.title').text(),
            'shop': item.find('.shop').text(),
            'location': item.find('.location').text()
        }
        print(product)
        # save_to_mongo(product)

def save_to_mongo(result):
    try:
        if db[MONGO_TABLE].insert(result):
            print('保存成功')
    except Exception:
        print('保存失败')
# 主函数
def main():
    total = search()
    total = int(re.compile('(\d+)').search(total).group(1))
    for i in range(2, 10):
        next_page(i)


if __name__ == '__main__':
    main()
