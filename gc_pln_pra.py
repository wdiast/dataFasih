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
    (By.ID, "username"))).send_keys("Widiaastuti") #username
driver.find_element(By.ID, "password").send_keys("Sotoenak23") #password
driver.find_element(By.ID, "kc-login").click()

wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
print("Login sukses")

# ======================
# HALAMAN COLLECT
# ======================
driver.get(
    "https://fasih-sm.bps.go.id/survey-collection/collect/2395b67d-d1af-4739-9ef8-c0cc0aa9ce9a")#ganti

time.sleep(5)

# ======================
# BUKA FILTER
# ======================

submit_button = wait.until(
    EC.element_to_be_clickable(
        (By.XPATH, '//button[contains(text(),"SUBMITTED BY Pencacah")]'))
    )
submit_button.click()

time.sleep(2)

filter_button = wait.until(
    EC.element_to_be_clickable(
        (By.XPATH, '//button[contains(text(),"Filter")]'))
)
filter_button.click()

time.sleep(2)

# ======================
# PILIH PROVINSI
# ======================
dropdown = wait.until(
    EC.element_to_be_clickable(
        (By.XPATH, "//ngx-select[@name='region1Id']//div[contains(@class,'ngx-select__toggle')]"))
)
dropdown.click()

prov = wait.until(
    EC.element_to_be_clickable(
        (By.XPATH, "//span[contains(text(),'[52] JAWA TENGAH')]"))
)
prov.click()

# ======================
# PILIH KABUPATEN
# ======================
dropdown = wait.until(
    EC.element_to_be_clickable(
        (By.XPATH, "//ngx-select[@name='region2Id']//div[contains(@class,'ngx-select__toggle')]"))
)
dropdown.click()

kab = wait.until(
    EC.element_to_be_clickable(
        (By.XPATH, "//span[contains(text(),'[52300] SEMARANG')]"))
)
kab.click()

# ======================
# PILIH ULP
# ======================

list_ulp = {"[52305] KENDAL", "[52309] WELERI", "[52310] BOJA"}

all_data = []

# ======================
# LOOP ULP
# ======================
for i, ulp in enumerate(list_ulp):

    print(f"{i+1}. Memproses:", ulp)

    try:
        # =========================
        # RESET ULP
        # =========================
        driver.execute_script("""
        let ulps = document.querySelector('ngx-select[name="region3Id"]');
        if (ulps && ulps.__ngContext__) {
            let comp = ulps.__ngContext__[8];
            if (comp && comp.writeValue) {
                comp.writeValue(null);
            }
        }
        """)

        # =========================
        # BUKA FILTER
        # =========================
        try:
            filter_button = wait.until(
                EC.element_to_be_clickable(
                    (By.XPATH, '//button[contains(text(),"Filter")]'))
            )
            filter_button.click()
        except:
            pass

        # =========================
        # BUKA DROPDOWN ULP
        # =========================
        ulp_dropdown = wait.until(
            EC.element_to_be_clickable((
                By.XPATH,
                "//ngx-select[@name='region3Id']//div[contains(@class,'ngx-select__toggle')]"
            ))
        )
        ulp_dropdown.click()

        wait.until(
            EC.presence_of_element_located((By.XPATH, '//ngx-select-choices'))
        )

        # =========================
        # PILIH ULP
        # =========================
        ulp_click = wait.until(
            EC.element_to_be_clickable((
                By.XPATH,
                f'//ngx-select-choices//a[normalize-space()="{ulp}"]'
            ))
        )

        driver.execute_script("arguments[0].scrollIntoView(true);", ulp_click)
        ulp_click.click()

        # tutup dropdown
        driver.find_element(By.TAG_NAME, "body").click()

        wait.until(
            EC.invisibility_of_element_located((By.XPATH, '//ngx-select-choices'))
        )

        # =========================
        # KLIK FILTER DATA
        # =========================
        filter_button = wait.until(
            EC.element_to_be_clickable((By.XPATH, '//button[contains(.,"Filter Data")]'))
        )

        driver.execute_script(
            "arguments[0].scrollIntoView({block: 'center'});", filter_button
        )

        filter_button.click()

        # =========================
        # TUNGGU LOADING
        # =========================
        wait.until(
            EC.invisibility_of_element_located(
                (By.XPATH, '//div[@id="assignmentDatatable_processing"]')
            )
        )

        # =========================
        # SET 100 DATA
        # =========================
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

        # =========================
        # LOOP SEMUA HALAMAN
        # =========================
        while True:
            rows = wait.until(
                EC.presence_of_all_elements_located(
                    (By.XPATH, '//table[@id="assignmentDatatable"]/tbody/tr')
                )
            )

            for row in rows:
                cols = row.find_elements(By.TAG_NAME, 'td')

                if len(cols) >= 2:
                    data = {
                        "No_Meter": cols[2].text.strip(),
                        "Nama": cols[3].text.strip(),
                        "Id_Pelanggan": cols[4].text.strip(),
                        "Alamat": cols[5].text.strip(),
                        "Hasil_Pendataan": cols[6].text.strip(),
                        "user_saat_ini": cols[8].text.strip(),
                    }

                    all_data.append(data)

            next_btn = driver.find_element(By.XPATH, '//a[@id="assignmentDatatable_next"]')

            if "disabled" in next_btn.get_attribute("class"):
                break

            next_btn.click()

            wait.until(
                EC.invisibility_of_element_located(
                    (By.XPATH, '//div[@id="assignmentDatatable_processing"]')
                )
            )

        # pastikan posisi aman
        driver.execute_script("window.scrollTo(0, 0);")

        # klik filter data (fix)
        filter_button = wait.until(
            EC.element_to_be_clickable(
                (By.XPATH, '//button[contains(text(),"Filter")]'))
        )
        filter_button.click()
        
    except Exception as e:
        print("Error di ULP:", ulp, e)
        continue


# ======================
# SIMPAN DATA
# ======================
df = pd.DataFrame(all_data)
df.to_excel("fasih_semua_pra.xlsx", index=False)

print("Selesai scraping:", len(df), "baris data")

driver.quit()
