from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC

import pandas as pd
import time

# ======================
# SETUP DRIVER
# ======================
service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service)
wait = WebDriverWait(driver, 30)

# ======================
# LOGIN
# ======================
driver.get("https://fasih-sm.bps.go.id/oauth_login.html")

driver.find_element(By.XPATH, '//*[@id="login-in"]/a[2]').click()

wait.until(EC.presence_of_element_located(
    (By.ID, "username"))).send_keys("") #username
driver.find_element(By.ID, "password").send_keys("") #password
driver.find_element(By.ID, "kc-login").click()

wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
print("Login sukses")

time.sleep(5)

# ======================
# HALAMAN COLLECT
# ======================
driver.get(
    "https://fasih-sm.bps.go.id/survey-collection/collect/8712a6fc-a996-4a8f-ad6f-56a278c19288")#ganti

time.sleep(3)

# ======================
# AMBIL YANG SUDAH SUBMIT
# ======================
submit_button = wait.until(
    EC.element_to_be_clickable(
        (By.XPATH, '//button[contains(text(),"SUBMITTED BY Pencacah")]'))
)
submit_button.click()

time.sleep(2)

all_data = []

# ======================
# LOOP DATA
# ======================
wait.until(
    EC.invisibility_of_element_located(
        (By.XPATH, '//div[@id="assignmentDatatable_processing"]')
    )
)

# Set jumlah data per halaman ke 100
length_select = wait.until(
    EC.element_to_be_clickable((By.NAME, 'assignmentDatatable_length'))
)

length_select.click()

option_100 = wait.until(
    EC.element_to_be_clickable((
        By.XPATH,
            '//select[@name="assignmentDatatable_length"]/option[text()="100"]'
        ))
    )
option_100.click()

wait.until(
    EC.invisibility_of_element_located(
        (By.XPATH, '//div[@id="assignmentDatatable_processing"]')
    )
)

#Ambil data per halaman dan klik next sampai habis
while True:
    rows = wait.until(
        EC.presence_of_all_elements_located(
            (By.XPATH, '//table[@id="assignmentDatatable"]/tbody/tr')
        )
    )

    for row in rows:
        try:
            cols = row.find_elements(By.TAG_NAME, 'td')

            if len(cols) >= 2:
                data = {
                    "Nama Kepala Keluarga": cols[2].text.strip(),
                    "Nama Anggota Keluarga": cols[3].text.strip(),
                    "Alamat": cols[4].text.strip(),
                    "Keberadaan Keluarga": cols[5].text.strip(),
                    "User": cols[7].text.strip(),
                }

            all_data.append(data)

        except Exception as e:
            print(f"Error: {e}")
            continue
    
    try:
        next_btn = driver.find_element(By.XPATH, '//a[@id="assignmentDatatable_next"]')

        if "disabled" in next_btn.get_attribute("class"):
            break

        next_btn.click()

        wait.until(
            EC.invisibility_of_element_located(
                (By.XPATH, '//div[@id="assignmentDatatable_processing"]')
            )
        )
    except Exception as e:
        print(f"Selesai atau Tombol Next tidak ditemukan: {e}")
        break

# ======================
# SIMPAN DATA
# ======================
df = pd.DataFrame(all_data)
df.to_excel("fasih_semua_data.xlsx", index=False)

print("Selesai scraping:", len(df), "baris data")

driver.quit()
