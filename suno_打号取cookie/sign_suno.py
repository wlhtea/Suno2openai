
import csv
from time import sleep

import numpy as np
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.edge.options import Options
from selenium.webdriver.edge.service import Service
from selenium.webdriver.support.ui import Select
import random

from webdriver_manager.microsoft import EdgeChromiumDriverManager
def create_cookie_string(cookies):
    return '; '.join([f"{cookie['name']}={cookie['value']}" for cookie in cookies])
def register(i,j):
    options = Options()
    options.add_argument("--inprivate")  # 启用Edge浏览器无痕模式

    service = Service(executable_path=EdgeChromiumDriverManager().install())
    driver = webdriver.Edge(service=service, options=options)
    driver.implicitly_wait(20)
    driver.get('https://suno.com/')
    driver.find_element(By.XPATH,'/html/body/div[1]/div[1]/nav/div[3]/div[2]/div/div/a').click()
    sleep(2)
    try:
        driver.find_element(By.XPATH,'/html/body/div[5]/div/div/div/div/div[3]/div[1]/button[4]').click()
    except:
        driver.find_element(By.XPATH, '/html/body/div[5]/div/div/div/div/div[3]/div[1]/button[3]').click()
    driver.find_element(By.XPATH,'/html/body/div/form[1]/div/div/div[2]/div[1]/div/div/div/div/div[1]/div[3]/div/div/div/div[2]/div[2]/div/input[1]').send_keys(i)
    driver.find_element(By.XPATH,'/html/body/div/form[1]/div/div/div[2]/div[1]/div/div/div/div/div[1]/div[3]/div/div/div/div[4]/div/div/div/div[2]/input').click()
    driver.find_element(By.XPATH,'/html/body/div[1]/div/div/div/div[2]/div[1]/div/div/div/div/div[2]/div[2]/div/form/div[3]/div/div/input').send_keys(j)
    driver.find_element(By.XPATH,'/html/body/div[1]/div/div/div/div[2]/div[1]/div/div/div/div/div[2]/div[2]/div/form/div[5]/div/div/div/div/button').click()
    save_information = driver.find_element(By.XPATH,'/html/body/div[1]/div/div/div/div[2]/div[1]/div/div/div/div/div[2]/div[2]/div/form/div[3]/div[2]/div/div[1]/button')
    if save_information:
        save_information.click()
    try:
        driver.find_element(By.XPATH,'/html/body/div[1]/div/div/div[2]/div/div[1]/div[2]/div/div[2]/form/div/div/div/div[2]/input').click()
    except:
        pass
    sleep(3)
    # 导航到其他页面
    driver.get('https://clerk.suno.com/v1/client?_clerk_js_version=4.72.0-snapshot.vc141245')
    cookies_values = []
    cookie_string = None
    new_cookies = driver.get_cookies()
    for cookie in new_cookies:
        cookies_values.append(cookie)
    cookie_string = create_cookie_string(cookies_values)

    if cookie_string is not None:
        print(f'"""{cookie_string}""",')
    else:
        print('false to get cookie')
email_data = pd.read_csv('outlook.csv',header=None)
counts = np.array(email_data.iloc[:,0])
mm = np.array(email_data.iloc[:,1])
for i,j in zip(counts,mm):
    register(i,j)


