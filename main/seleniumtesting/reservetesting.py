import pytest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select, WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from datetime import datetime, timedelta
import time
import os
import random
import string

@pytest.fixture(scope="module")
def driver():
    driver = webdriver.Chrome()
    driver.maximize_window()
    yield driver
    driver.quit()

def test_reserve(driver):
    try:
        login_url = 'http://127.0.0.1:8000/login'
        gambar = os.path.abspath("main/static/main/car4.png")
        username = 'seleniumtest'
        password = 'seleniumtesting123'
        row_index = 1
        # Generate 3 huruf kapital acak, contoh: 'ABC'
        random_letters = ''.join(random.choices(string.ascii_uppercase, k=3))

        # ==== 1. Login ====
        driver.get(login_url)
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.NAME, "username")))
        driver.find_element(By.NAME, "username").send_keys(username)
        time.sleep(2)
        driver.find_element(By.NAME, "password").send_keys(password)
        time.sleep(2)
        driver.find_element(By.XPATH, '//button[@type="submit"]').click()
        time.sleep(2)

        # ==== 2. Ke halaman reservation ====
        link_reserve = driver.find_element(By.XPATH, '//a[@href="/reservation/"]')
        link_reserve.click()
        time.sleep(2)

        # ==== 3. Isi form reservation ====
        besok = datetime.now() + timedelta(days=1)
        tanggal_str = besok.strftime('%m/%d/%Y')

        # Set tanggal
        driver.execute_script("""
            const el = document.getElementById('default-datepicker');
            el.value = arguments[0];
            el.dispatchEvent(new Event('change'));
        """, tanggal_str)
        time.sleep(2)

        # pilihslot
        Select(driver.find_element(By.ID, "slot")).select_by_value("1")
        time.sleep(2)
        # pilih from
        Select(driver.find_element(By.ID, "start")).select_by_value("09:00")
        time.sleep(2)
        # pilih until
        Select(driver.find_element(By.ID, "end")).select_by_value("12:00")
        time.sleep(2)
        # submit
        driver.find_element(By.XPATH, '//button[@type="submit"]').click()
        time.sleep(2)

        # ==== 4. Isi data mobil ====
        Select(driver.find_element(By.ID, "id_dropdown1")).select_by_value("Toyota")
        time.sleep(2)
        Select(driver.find_element(By.ID, "id_dropdown2")).select_by_value("Agya")
        time.sleep(2)
        Select(driver.find_element(By.ID, "color")).select_by_value("White")
        time.sleep(2)

        Select(driver.find_element(By.ID, "plate1")).select_by_value("BP")
        time.sleep(2)
        driver.find_element(By.NAME, "plate2").send_keys("123")
        time.sleep(2)
        driver.find_element(By.NAME, "plate3").send_keys(random_letters)
        time.sleep(2)

        driver.find_element(By.ID, "imageUpload").send_keys(gambar)
        time.sleep(2)

        # ==== 5. Klik tombol "Reserve" → buka modal ====
        reserve_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, '//button[contains(text(), "Reserve")]'))
        )
        driver.execute_script("arguments[0].click();", reserve_button)
        time.sleep(2)

        # Tunggu modal muncul
        WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located((By.ID, "confirmModal"))
        )

        # Klik tombol Continue
        continue_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, '//div[@id="confirmModal"]//button[contains(text(), "Continue")]'))
        )
        continue_button.click()
        time.sleep(3)

        # pergi ke halaman reservations
        link_reserve = driver.find_element(By.XPATH, '//a[@href="/history/"]')
        link_reserve.click()
        time.sleep(2)

        # pilih view
        view_button_xpath = f'(//table//tbody/tr)[{row_index}]//button[contains(text(), "View")]'
        view_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, view_button_xpath))
        )
        view_button.click()

        # 2. Tunggu modal muncul (gunakan attribute data-modal-target untuk ambil ID)
        modal_id = view_button.get_attribute("data-modal-target")
        modal_xpath = f'//div[@id="{modal_id}"]'

        WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located((By.XPATH, modal_xpath))
        )
        time.sleep(4)

        # 3. Klik tombol "X" untuk menutup modal
        close_button_xpath = f'//div[@id="{modal_id}"]//button[@data-modal-hide="{modal_id}"]'
        close_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, close_button_xpath))
        )
        close_button.click()
        time.sleep(2)

        # tekan tombol cancel
        cancel_button_xpath = f'(//table//tbody/tr)[{row_index}]//button[contains(text(), "Cancel")]'
        cancel_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, cancel_button_xpath))
        )
        cancel_button.click()

        time.sleep(2)

        # 2. Ambil ID modal dari atribut data-modal-target
        modal_id = cancel_button.get_attribute("data-modal-target") 
        modal_xpath = f'//div[@id="{modal_id}"]'

        WebDriverWait(driver, 10).until( 
            EC.visibility_of_element_located((By.XPATH, modal_xpath))
        )

        time.sleep(2)

        # 3. Klik tombol "No" (membatalkan cancel)
        yes_button_xpath = f'//div[@id="{modal_id}"]//button[contains(text(), "Yes")]'
        yes_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, yes_button_xpath))
        )
        yes_button.click()

        time.sleep(3)

    except Exception as e:
        pytest.fail(f"Terjadi kesalahan: {e}")
