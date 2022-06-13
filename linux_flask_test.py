from flask import Flask, request
from flask_cors import CORS
import sys

from selenium import webdriver
import time
from bs4 import BeautifulSoup
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.keys import Keys
import account_info
import xerox
from pyvirtualdisplay import Display
from datetime import datetime, date
import pandas as pd
import numpy as np
import tensorflow as tf

app = Flask(__name__)
CORS(app)
@app.route("/tospring")
def spring():
    return "hello"

brand_rank = {
    "BBQ": 1,
    "맘스터치": 2,
    "굽네치킨": 3,
    "교촌치킨": 4,
    "BHC": 5,
    "60계치킨": 6,
    "푸라닭": 7,
    "자담치킨": 8,
    "네네치킨": 9,
    "노랑통닭": 10,
    "바른치킨": 11,
    "호식이두마리치킨": 12,
    "처갓집양념치킨": 13,
    "지코바치킨": 14,
    "아웃닭": 15,
    "깐부치킨": 16,
    "페리카나": 17,
    "순수치킨": 18,
    "또래오래": 19,
    "부어치킨": 20,
    "땅땅치킨": 21,
    "또봉이통닭": 22,
    "오븐마루": 23,
    "멕시칸치킨": 24,
    "디디치킨": 25,
    "훌랄라치킨": 26,
    "마파치킨": 27,
    "웰덤치킨": 28
}

tf_model = tf.keras.models.load_model('/home/ubuntu/autoOrder/Capstone-DNN/tf_dnn_model/1')

@app.route("/getExpectedTime", methods=['POST'])
def getExpectedTime():
    params = request.get_json()
    r_name = params['rName']
    hh = int(params['orderTime'].split(":")[0])
    mm = int(params['orderTime'].split(":")[1])
    if mm >= 30:
        hh += 1
    order_time = hh
    day = date.today().weekday()
    rank = 30
    for key in brand_rank.keys():
        if key in r_name:
            rank = brand_rank[key]
    
    x1 = day
    x2 = order_time
    x3 = rank
    
    x1_lst = [x1]
    x2_lst = [x2]
    x3_lst = [x3]
    df = pd.DataFrame((zip(x1_lst, x2_lst, x3_lst)), columns=['x1', 'x2', 'x3'])
    predict = tf_model.predict(df)
    return str(round(predict[0][0]))

@app.route("/autoOrder", methods=['POST'])
def autoOrder():
    display = Display(visible=0, size=(1024,768))
    display.start()
    params = request.get_json()
    pl_road_address = params['plRoadAddress']
    pl_name = params['plName']
    orderer_phone = params['ordererPhone']
    order_url = params['orderUrl']
    order_list_string = params['orderList']
    
    order_list = []
    temp_order_list = order_list_string.split(" AND ")
    temp_order_list.pop()
    for order in temp_order_list:
        temp_dict = dict()
        temp_dict["menu"] = order.split("menu=")[1].split("}")[0]
        temp_dict["price"] = int(order.split("price=")[1].split(",")[0])

        try:
            temp_dict["request"] = order.split("request=")[1].split(",")[0]
        except IndexError:
            temp_dict["request"] = ""
        order_list.append(temp_dict)
   
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument("--single-process")
    chrome_options.add_argument("--disable-dev-shm-usage")
    path='/home/ubuntu/autoOrder/chromedriver'
    driver = webdriver.Chrome(path, chrome_options=chrome_options)
    url = "https://www.yogiyo.co.kr/"
    driver.get(url)
    driver.maximize_window()
    time.sleep(2)

    xpath = '''//*[@id="search"]/div/form/input'''
    element = driver.find_element_by_xpath(xpath)
    time.sleep(2)

    element.clear()
    element.send_keys(pl_road_address)
    time.sleep(2)
    search_xpath = '''//*[@id="button_search_address"]/button[2]'''
    driver.find_element_by_xpath(search_xpath).click()
    time.sleep(3)

    try:
        no_result_xpath = '//*[@id="search"]/div/form/ul/li[1]'
        no_result = driver.find_element_by_xpath(no_result_xpath)
        time.sleep(2)
    except NoSuchElementException:
        time.sleep(2)

    driver.get(order_url)
    time.sleep(2)

    html = driver.page_source
    soup = BeautifulSoup(html, 'html.parser')

    menu_list = []
    lst = soup.select('table > tbody > tr > td.menu-text > div.menu-name.ng-binding')
    for s in lst:
        menu_list.append(s.get_text())

    basic_xpath1 = '//*[@id="menu"]/div/div['
    basic_xpath2 = ']/div[2]/div/ul/li['

    cut_index = 0
    index1 = 1
    index2 = 1
    xpath_list = []
    while True:
        xpath = basic_xpath1
        add_str = str(index1) + basic_xpath2 + str(index2) + ']'
        xpath += add_str
        while True:
            try:
                xpath = basic_xpath1
                add_str = str(index1) + basic_xpath2 + str(index2) + ']'
                xpath += add_str
                element = driver.find_element_by_xpath(xpath)
                xpath_list.append(xpath)
                if index1 == 1:
                    cut_index += 1
                index2 += 1
            except:
                index2 = 1
                break
        index1 += 1
        try:
            name = driver.find_element_by_xpath(basic_xpath1 + str(index1) + basic_xpath2 + '1]')
        except:
            break

    menu_name_list = menu_list[cut_index:]
    menu_xpath_list = xpath_list[cut_index:]

    tabs_xpath1 = '//*[@id="menu"]/div/div['
    tabs_xpath2 = ']/div[1]/h4/a'
    index = 3
    while True:
        tabs_xpath = tabs_xpath1 + str(index) + tabs_xpath2
        try:
            driver.find_element_by_xpath(tabs_xpath).click()
            time.sleep(2)
            index += 1
        except:
            break

    try:
        processed_menu_name_list = []
        for menu_name in menu_name_list:
            processed_menu_name_list.append(menu_name.lower().replace(' ', ''))

        for order in order_list:
            processed_menu_name = order['menu'].lower().replace(' ', '')
            if processed_menu_name in processed_menu_name_list:
                driver.find_element_by_xpath(menu_xpath_list[processed_menu_name_list.index(processed_menu_name)]).click()
                time.sleep(2)
                driver.find_element_by_xpath('/html/body/div[10]/div/div[3]/button[1]').click() 
                time.sleep(2)

        driver.find_element_by_xpath('//*[@id="content"]/div[2]/div[2]/ng-include/div/div[2]/div[5]/a[2]').click()
        time.sleep(2)

        driver.find_element_by_xpath('//*[@id="content"]/div/form[1]/div[1]/div[2]/div[1]/div[2]/div/div/div[2]/div/input').send_keys(pl_name)
        time.sleep(2)
        driver.find_element_by_xpath('//*[@id="content"]/div/form[1]/div[1]/div[2]/div[1]/div[2]/div/div/div[3]/div/div/input').send_keys(orderer_phone)
        time.sleep(2)
        requests = ''
        for order in order_list:
            if order['request'] == "":
                continue
            add_str = order['menu'] + ' - ' + order['request']
            requests += add_str + '\n'
        driver.find_element_by_xpath('//*[@id="content"]/div/form[1]/div[1]/div[2]/div[2]/div[2]/div/textarea').send_keys(requests)
        time.sleep(2)

        driver.find_element_by_xpath('//*[@id="content"]/div/form[1]/div[1]/div[2]/div[3]/div[2]/div/div[1]/div[2]/label[3]').click()
        time.sleep(2)

        driver.find_element_by_xpath('//*[@id="content"]/div/form[1]/div[2]/div/button').click()
        time.sleep(2)

        naver_id = account_info.naver_id
        naver_pw = account_info.naver_pw

        time.sleep(2)
        elem_id = driver.find_element_by_id('id')
        elem_id.click()
        time.sleep(2)
        xerox.copy(naver_id)
        time.sleep(2)
        elem_id.send_keys(Keys.CONTROL, 'v')
        time.sleep(2)

        elem_pw = driver.find_element_by_id('pw')
        elem_pw.click()
        time.sleep(2)
        xerox.copy(naver_pw)
        time.sleep(2)
        elem_pw.send_keys(Keys.CONTROL, 'v')
        time.sleep(2)

        driver.find_element_by_id('log.login').click()
        time.sleep(2)
   
        time.sleep(5)
        cur_url = driver.current_url
    
    except:
        cur_url = ""

    print("cur_url: " + cur_url)
    driver.close()
    return cur_url

if __name__ == '__main__':
    app.run("0.0.0.0", port=5000)
    
