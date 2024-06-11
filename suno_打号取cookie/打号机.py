"""
基于selenium的Outlook自动注册脚本，每个IP只能注册3个邮箱，没有实现代理IP池，所以需要手动更换IP。
未实现通过验证码注册，需要手动进行验证码识别。

Author: Eli Lee
Version: 1.0
Reference: https://github.com/EricProgrammerBLM/Outlook-Email-Sign-Up
Export: outlook.csv

"""

import csv
import random

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.edge.options import Options
from selenium.webdriver.edge.service import Service
from selenium.webdriver.support.ui import Select
from webdriver_manager.microsoft import EdgeChromiumDriverManager


def shuffle(arr):
    random.shuffle(arr)
    return arr


def register(prefix, password, first_name, last_name, year, month, day):
    options = Options()
    options.add_argument("--inprivate")  # 启用Edge浏览器无痕模式

    service = Service(executable_path=EdgeChromiumDriverManager().install())
    driver = webdriver.Edge(service=service, options=options)

    driver.get(
        'https://signup.live.com/newuser.aspx?contextid=A34663E86ABA02E6&uiflavor=web&lic=1&mkt=EN-US&lc=1033&uaid'
        '=412e188e23334594ad53f1a33880cf67')
    driver.implicitly_wait(20)
    driver.find_element(By.ID, 'liveSwitch').click()
    driver.find_element(By.NAME, 'MemberName').send_keys(prefix)  # Email
    driver.find_element(By.ID, 'iSignupAction').click()
    driver.implicitly_wait(20)
    driver.find_element(By.ID, 'PasswordInput').send_keys(password)  # Password
    driver.find_element(By.ID, 'iSignupAction').click()
    driver.implicitly_wait(20)
    driver.find_element(By.NAME, 'FirstName').send_keys(first_name)
    driver.find_element(By.NAME, 'LastName').send_keys(last_name)
    driver.find_element(By.ID, 'iSignupAction').click()
    driver.implicitly_wait(20)

    # Choosing Birth Month
    opt = driver.find_element(By.XPATH, '//*[@id="BirthMonth"]')
    dropdown = Select(opt)
    dropdown.select_by_index(month)
    # Choosing Birth Day
    opt = driver.find_element(By.XPATH, '//*[@id="BirthDay"]')
    dropdown = Select(opt)
    dropdown.select_by_index(day)
    # Typing in Birth Year
    driver.find_element(By.XPATH, '//*[@id="BirthYear"]').send_keys(year)
    driver.find_element(By.ID, 'iSignupAction').click()
    return driver


# 随机生成生日年份
def random_brith_year():
    return random.randint(1980, 2003)


# 随机生成生日月份
def random_brith_month():
    months = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]
    return shuffle(months)[0]


# 随机生成生日日期
def random_brith_day():
    days = [1, 3, 6, 12, 16, 20, 25, 26, 2]
    return shuffle(days)[0]


# 随机生成FirstName
def random_firstname():
    first_name = ['John', 'James', 'Robert', 'Michael', 'William', 'David', 'Richard', 'Charles', 'Joseph', 'Thomas',
                  'Christopher', 'Daniel', 'Paul', 'Mark', 'Donald', 'George', 'Kenneth', 'Steven', 'Edward', 'Brian',
                  'Ronald', 'Anthony', 'Kevin', 'Jason', 'Matthew', 'Gary', 'Timothy', 'Jose', 'Larry', 'Jeffrey',
                  'Frank', 'Scott', 'Eric']
    return shuffle(first_name)[0]


# 随机生成LastName
def random_lastname():
    last_name = ['Smith', 'Johnson', 'Williams', 'Jones', 'Brown', 'Davis', 'Miller', 'Wilson', 'Moore', 'Taylor',
                 'Anderson', 'Thomas', 'Jackson', 'White', 'Harris', 'Martin', 'Thompson', 'Garcia', 'Martinez',
                 'Robinson', 'Clark', 'Rodriguez', 'Lewis', 'Lee', 'Walker', 'Hall', 'Allen', 'Young', 'Hernandez',
                 'King', 'Wright', 'Lopez', 'Hill', 'Scott', 'Green', 'Adams', 'Baker', 'Gonzalez', 'Nelson', 'Carter',
                 'Mitchell', 'Perez', 'Roberts', 'Turner', 'Phillips', 'Campbell', 'Parker', 'Evans', 'Edwards',
                 'Collins']
    return shuffle(last_name)[0]


# 随机生成16位密码
def random_password():
    password = ''.join(random.choice('abcdefghijklmnopqrstuvwxyz0123456789') for _ in range(16))
    return password


# 随机生成 16位邮箱前缀
def random_email_prefix():
    char = random.choice('abcdefghijklmnopqrstuvwxyz')
    # 邮箱前缀必须以字母开头
    prefix = char + ''.join(random.choice('abcdefghijklmnopqrstuvwxyz0123456789') for _ in range(15))
    return prefix


def main():
    while True:
        prefix = random_email_prefix()
        password = random_password()
        first_name = random_firstname()
        last_name = random_lastname()
        year = random_brith_year()
        month = random_brith_month()
        day = random_brith_day()

        driver = None
        try:
            driver = register(prefix, password, first_name, last_name, year, month, day)
            # ask customer to confirm if operation was successful
            while True:
                confirm = input("Was operation successful? (y/n): ")
                if confirm.lower() == 'y':
                    # write registration details to a csv file
                    with open('outlook.csv', 'a', newline='') as csv_file:
                        writer = csv.writer(csv_file)
                        writer.writerow([prefix + '@outlook.com', password])
                    break
                elif confirm.lower() == 'n':
                    break
                else:
                    logging.info("Invalid input. Please enter 'y' or 'n'.")
        except Exception as e:
            logging.info(f"Error: {e}")
            continue
        finally:
            if driver is not None:
                try:
                    driver.quit()
                except Exception as ex:
                    logging.info("Error occurred while quitting: ", ex)


if __name__ == '__main__':
    main()
