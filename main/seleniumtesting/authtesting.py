import pytest
from selenium import webdriver
from selenium.webdriver.common.by import By
import time

@pytest.fixture(scope="module")
def driver():
    driver = webdriver.Chrome()
    driver.maximize_window()
    yield driver
    driver.quit()

def test_register_login(driver):
    register_url = 'http://127.0.0.1:8000/register'

    username = 'seleniumtest'
    email = 'seleniumtest@gmail.com'
    password = 'seleniumtesting123'
    confirm_pw = 'seleniumtesting123'
    phone = '85831818176'

    driver.get(register_url)

    username_field = driver.find_element(By.XPATH, '//input[@name="username"]')
    email_field = driver.find_element(By.XPATH, '//input[@name="email"]')
    password_field = driver.find_element(By.XPATH, '//input[@name="password"]')
    confirm_field = driver.find_element(By.XPATH, '//input[@name="confirm_password"]')
    phone_field = driver.find_element(By.XPATH, '//input[@name="phone_number"]')
    register_button = driver.find_element(By.XPATH, '//button[@type="submit"]')

    username_field.send_keys(username)
    time.sleep(2)
    email_field.send_keys(email)
    time.sleep(2)
    password_field.send_keys(password)
    time.sleep(2)
    confirm_field.send_keys(confirm_pw)
    time.sleep(2)
    phone_field.send_keys(phone)
    time.sleep(2)
    register_button.click()
    time.sleep(2)

    current_url = driver.current_url

    if '/login' in current_url:
        assert True, "Login berhasil"

        username_field = driver.find_element(By.XPATH, '//input[@name="username"]')
        password_field = driver.find_element(By.XPATH, '//input[@name="password"]')
        login_button = driver.find_element(By.XPATH, '//button[@type="submit"]')

        time.sleep(3)
        username_field.send_keys(username)
        time.sleep(2)
        password_field.send_keys(password)
        time.sleep(2)
        login_button.click()
        time.sleep(2)

        assert '/home' in driver.current_url, "login berhasil"

    elif '/register' in current_url:
        assert False, "register gagal karena autentikasi"
    elif '/login' in current_url:
        assert False, "register gagal karena autentikasi"
    else:
        assert False, "Login gagal karena kesalahan tidak dikenal"
