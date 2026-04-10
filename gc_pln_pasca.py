from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC

import pandas as pd
import time
from datetime import datetime

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
    "https://fasih-sm.bps.go.id/survey-collection/collect/2e31188c-a617-4163-8056-edccf93d8d79")#ganti

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
ulp = input("Masukan keyword pencarian: ")
print(ulp)

list_ulp = {"[52305] KENDAL", "[52309] WELERI", "[52310] BOJA"}
if ulp=="kendal":
    ulp="[52305] KENDAL"
    rbm_first="[GEAKDAC] GEAKDAC"
elif ulp=="weleri":
    ulp="[52309] WELERI"
    rbm_first="[GJAGHAA] GJAGHAA"
elif ulp=="boja":
    ulp="[52310] BOJA"
    rbm_first="[GKAAMRH] GKAAMRH"
else:
    print("Keyword tidak ditemukan, pastikan memasukan keyword dengan benar (kendal/weleri/boja)")
    driver.quit()
    exit()

dropdown = wait.until(
    EC.element_to_be_clickable(
        (By.XPATH, "//ngx-select[@name='region3Id']//div[contains(@class,'ngx-select__toggle')]"))
)
dropdown.click()

kec = wait.until(
    EC.element_to_be_clickable(
        (By.XPATH, f"//span[contains(text(),'{ulp}')]"))
)
kec.click()

time.sleep(2)

# ======================
# AMBIL LIST RBM
# ======================
rbm_dropdown = wait.until(
    EC.element_to_be_clickable(
        (By.XPATH, '//ngx-select[@name="region4Id"]//div[contains(@class,"ngx-select__toggle")]'))
)
rbm_dropdown.click()

rbm_list = wait.until(
    EC.presence_of_all_elements_located((By.XPATH, '//ngx-select-choices//a'))
)

rbm_texts = [rbm.text.strip() for rbm in rbm_list if rbm.text.strip() != ""]
print("Jumlah RBM:", len(rbm_texts))

rbm_klik = wait.until(
    EC.element_to_be_clickable(
        (By.XPATH,f"//span[contains(text(),'{rbm_first}')]") #Ganti RBM Pertama sesuai dengan lokus wilayah
    )
)
rbm_klik.click()


all_data = []

# ======================
# LOOP RBM
# ======================
for i, rbm_text in enumerate(rbm_texts):

    print(f"{i+1}. Memproses:", rbm_text)

    try:
        # =========================
        # RESET RBM
        # =========================
        driver.execute_script("""
        let rbm = document.querySelector('ngx-select[name="region4Id"]');
        if (rbm && rbm.__ngContext__) {
            let comp = rbm.__ngContext__[8];
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
        # BUKA DROPDOWN RBM
        # =========================
        rbm_dropdown = wait.until(
            EC.element_to_be_clickable((
                By.XPATH,
                "//ngx-select[@name='region4Id']//div[contains(@class,'ngx-select__toggle')]"
            ))
        )
        rbm_dropdown.click()

        wait.until(
            EC.presence_of_element_located((By.XPATH, '//ngx-select-choices'))
        )

        # =========================
        # PILIH RBM
        # =========================
        rbm = wait.until(
            EC.element_to_be_clickable((
                By.XPATH,
                f'//ngx-select-choices//a[normalize-space()="{rbm_text}"]'
            ))
        )

        driver.execute_script("arguments[0].scrollIntoView(true);", rbm)
        rbm.click()

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

                if len(cols) >= 12:
                    data = {
                        "rbm": rbm_text,
                        # "kode_identitas": cols[1].text.strip(),
                        "id_pelanggan": cols[2].text.strip(),
                        "nama": cols[3].text.strip(),
                        "no_meter": cols[4].text.strip(),
                        "alamat": cols[5].text.strip(),
                        "is_prelist": cols[6].text.strip(),
                        # "kddk": cols[7].text.strip(),
                        # "status_alias": cols[8].text.strip(),
                        "user_saat_ini": cols[10].text.strip(),
                        # "mode": cols[10].text.strip(),
                        # "keterangan": cols[11].text.strip(),
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
        print("Error di RBM:", rbm_text, e)
        continue


# ======================
# SIMPAN DATA
# ======================
df = pd.DataFrame(all_data)

waktu_sekarang = datetime.now().strftime("%Y%m%d_%H%M%S")
nama_file = f"fasih_semua_rbm_{waktu_sekarang}.xlsx"

# Simpan ke Excel
df.to_excel(nama_file, index=False)

print("Selesai scraping:", len(df), "baris data")

driver.quit()
