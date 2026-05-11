from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC

import pandas as pd
import json
import os
import time
import traceback
import logging
from datetime import datetime

# ======================
# KONFIGURASI
# ======================
USERNAME    = "widiaastuti"           # isi username
PASSWORD    = "Sotoenak23"           # isi password
SURVEY_URL  = "https://fasih-sm.bps.go.id/survey-collection/collect/8712a6fc-a996-4a8f-ad6f-56a278c19288"

# File checkpoint & output — nama tetap agar resume bisa ditemukan
CHECKPOINT_FILE = "checkpoint_pbi_kendal.json"
OUTPUT_FILE     = "pbi_kendal_hasil.xlsx"
TEMP_FILE       = "pbi_kendal_TEMP.xlsx"

# ======================
# SETUP LOGGING
# ======================
waktu_mulai = datetime.now().strftime("%Y%m%d_%H%M%S")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(f"log_pbi_{waktu_mulai}.txt", encoding="utf-8"),
        logging.StreamHandler()
    ]
)
log = logging.getLogger(__name__)
log.info("=" * 60)
log.info("SCRAPING PBI KENDAL - dengan fitur Resume")
log.info("=" * 60)


# ======================
# CHECKPOINT FUNCTIONS
# ======================

def simpan_checkpoint(kec_idx, desa_idx, kecamatan_list, desa_list_per_kec):
    """Simpan posisi terakhir ke file JSON."""
    data = {
        "kec_idx"            : kec_idx,
        "desa_idx"           : desa_idx,
        "kecamatan_list"     : kecamatan_list,
        "desa_list_per_kec"  : desa_list_per_kec,
        "updated_at"         : datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }
    with open(CHECKPOINT_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    log.debug(f"Checkpoint disimpan: kec_idx={kec_idx}, desa_idx={desa_idx}")


def load_checkpoint():
    """Load checkpoint jika ada. Return dict atau None."""
    if not os.path.exists(CHECKPOINT_FILE):
        return None
    try:
        with open(CHECKPOINT_FILE, "r", encoding="utf-8") as f:
            cp = json.load(f)
        log.info(f"Checkpoint ditemukan: terakhir di kec_idx={cp['kec_idx']}, desa_idx={cp['desa_idx']} ({cp['updated_at']})")
        return cp
    except Exception as e:
        log.warning(f"Gagal load checkpoint: {e}")
        return None


def hapus_checkpoint():
    """Hapus checkpoint setelah selesai semua."""
    if os.path.exists(CHECKPOINT_FILE):
        os.remove(CHECKPOINT_FILE)
        log.info("Checkpoint dihapus (scraping selesai).")


def auto_save(all_data):
    """Simpan data sementara ke TEMP file."""
    if not all_data:
        return
    try:
        pd.DataFrame(all_data).to_excel(TEMP_FILE, index=False)
        log.info(f"  [AUTO-SAVE] {len(all_data)} baris → {TEMP_FILE}")
    except Exception as e:
        log.warning(f"  Auto-save gagal: {e}")


def load_existing_data():
    """Load data yang sudah tersimpan di TEMP file (untuk resume)."""
    if not os.path.exists(TEMP_FILE):
        return []
    try:
        df = pd.read_excel(TEMP_FILE)
        data = df.to_dict("records")
        log.info(f"Data lama dimuat: {len(data)} baris dari {TEMP_FILE}")
        return data
    except Exception as e:
        log.warning(f"Gagal load data lama: {e}")
        return []


# ======================
# SETUP DRIVER
# ======================
service = Service(ChromeDriverManager().install())
driver  = webdriver.Chrome(service=service)
wait    = WebDriverWait(driver, 30)


# ======================
# HELPER SELENIUM
# ======================

def ss(nama):
    path = f"ss_{nama}_{datetime.now().strftime('%H%M%S')}.png"
    driver.save_screenshot(path)
    log.info(f"Screenshot: {path}")


def jsc(el):
    """JS click — lebih reliable untuk Angular."""
    driver.execute_script("arguments[0].click();", el)


def tunggu_loading():
    try:
        WebDriverWait(driver, 15).until(
            EC.invisibility_of_element_located(
                (By.XPATH, '//div[@id="assignmentDatatable_processing"]')
            )
        )
    except Exception:
        pass
    time.sleep(0.5)


def is_panel_terbuka():
    try:
        el = driver.find_element(By.XPATH, "//ngx-select[@name='region1Id']")
        return el.is_displayed()
    except Exception:
        return False


def buka_panel_filter():
    if is_panel_terbuka():
        return
    for _ in range(3):
        try:
            btn = WebDriverWait(driver, 10).until(EC.presence_of_element_located(
                (By.XPATH,
                 '//button[normalize-space(text())="Filter" and contains(@class,"pull-right")]'
                 '| //button[normalize-space(text())="Filter"]')
            ))
            jsc(btn)
            time.sleep(2)
            if is_panel_terbuka():
                log.info("Panel filter terbuka.")
                return
        except Exception as e:
            log.warning(f"buka_panel_filter error: {e}")
            time.sleep(1)
    log.error("Gagal membuka panel filter!")
    ss("gagal_buka_panel")


def tutup_panel_filter():
    if not is_panel_terbuka():
        return
    try:
        close_btn = driver.find_element(
            By.XPATH,
            '//button[contains(@class,"close") and ancestor::*[contains(@class,"filter")]]'
            '| //button[@aria-label="Close"]'
            '| //*[contains(@class,"filter")]//button[contains(@class,"close")]'
        )
        jsc(close_btn)
        log.info("Panel filter ditutup (X).")
        time.sleep(1)
        return
    except Exception:
        pass
    try:
        btn = driver.find_element(
            By.XPATH,
            '//button[normalize-space(text())="Filter" and contains(@class,"pull-right")]'
        )
        jsc(btn)
        log.info("Panel filter ditutup (toggle).")
        time.sleep(1)
    except Exception as e:
        log.warning(f"tutup_panel_filter error: {e}")


def pilih_option(name_attr, teks_option):
    """Pilih option dari ngx-select berdasarkan teks."""
    try:
        toggle = wait.until(EC.presence_of_element_located(
            (By.XPATH,
             f"//ngx-select[@name='{name_attr}']//div[contains(@class,'ngx-select__toggle')]")
        ))
        jsc(toggle)
        time.sleep(1.5)

        wait.until(EC.presence_of_element_located((By.XPATH, '//ngx-select-choices')))

        item = wait.until(EC.presence_of_element_located(
            (By.XPATH, f'//ngx-select-choices//a[normalize-space()="{teks_option}"]')
        ))
        driver.execute_script("arguments[0].scrollIntoView(true);", item)
        jsc(item)

        driver.find_element(By.TAG_NAME, "body").click()
        try:
            WebDriverWait(driver, 5).until(
                EC.invisibility_of_element_located((By.XPATH, '//ngx-select-choices'))
            )
        except Exception:
            pass
        time.sleep(0.5)
        log.info(f"  [{name_attr}] = '{teks_option}'")
        return True

    except Exception as e:
        log.error(f"  pilih_option [{name_attr}] '{teks_option}' error: {e}")
        ss(f"err_pilih_{name_attr}")
        return False


def get_all_options(name_attr):
    """Ambil semua teks option dari ngx-select."""
    try:
        toggle = wait.until(EC.presence_of_element_located(
            (By.XPATH,
             f"//ngx-select[@name='{name_attr}']//div[contains(@class,'ngx-select__toggle')]")
        ))
        jsc(toggle)
        time.sleep(1.5)

        wait.until(EC.presence_of_element_located((By.XPATH, '//ngx-select-choices')))
        items = wait.until(EC.presence_of_all_elements_located(
            (By.XPATH, '//ngx-select-choices//a')
        ))
        result = [it.text.strip() for it in items if it.text.strip()]

        driver.find_element(By.TAG_NAME, "body").click()
        try:
            WebDriverWait(driver, 5).until(
                EC.invisibility_of_element_located((By.XPATH, '//ngx-select-choices'))
            )
        except Exception:
            pass
        time.sleep(0.5)
        log.info(f"  [{name_attr}] {len(result)} options: {result[:5]}{'...' if len(result)>5 else ''}")
        return result

    except Exception as e:
        log.error(f"  get_all_options [{name_attr}] error: {e}")
        return []


def klik_filter_data():
    try:
        btn = wait.until(EC.presence_of_element_located(
            (By.XPATH, '//button[contains(.,"Filter Data")]')
        ))
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", btn)
        jsc(btn)
        log.info("Filter Data diapply.")
        time.sleep(2)
        tutup_panel_filter()
        tunggu_loading()
    except Exception as e:
        log.warning(f"klik_filter_data error: {e}")


def klik_reset():
    try:
        btn = wait.until(EC.presence_of_element_located(
            (By.XPATH, '//button[normalize-space(text())="Reset"]')
        ))
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", btn)
        jsc(btn)
        log.info("Reset OK.")
        time.sleep(1.5)
    except Exception as e:
        log.warning(f"klik_reset error: {e}")


def klik_submitted():
    try:
        btn = wait.until(EC.element_to_be_clickable(
            (By.XPATH, '//button[contains(text(),"SUBMITTED BY Pencacah")]')
        ))
        btn.click()
        time.sleep(2)
    except Exception as e:
        log.warning(f"klik_submitted error: {e}")


def set_show_100():
    try:
        sel = wait.until(EC.element_to_be_clickable((By.NAME, 'assignmentDatatable_length')))
        Select(sel).select_by_visible_text("100")
        tunggu_loading()
    except Exception as e:
        log.warning(f"set_show_100 error: {e}")


def ambil_data_semua_halaman(kec_nama, desa_nama):
    hasil  = []
    halaman = 1
    while True:
        tunggu_loading()
        try:
            rows = wait.until(EC.presence_of_all_elements_located(
                (By.XPATH, '//table[@id="assignmentDatatable"]/tbody/tr')
            ))
        except Exception:
            log.warning(f"  Tabel tidak muncul halaman {halaman}.")
            break

        if len(rows) == 1:
            try:
                rows[0].find_element(By.CLASS_NAME, "dataTables_empty")
                log.info(f"  Kosong: {kec_nama}/{desa_nama}")
                break
            except Exception:
                pass

        for row in rows:
            try:
                cols = row.find_elements(By.TAG_NAME, 'td')
                if len(cols) >= 8:
                    hasil.append({
                        "Kecamatan"            : kec_nama,
                        "Desa/Kelurahan"       : desa_nama,
                        "Kode Identitas"       : cols[1].text.strip(),
                        "Nama Kepala Keluarga" : cols[2].text.strip(),
                        "Nama Anggota Keluarga": cols[3].text.strip(),
                        "Alamat"               : cols[4].text.strip(),
                        "Keberadaan Keluarga"  : cols[5].text.strip(),
                        "User"                 : cols[7].text.strip(),
                    })
            except Exception as e:
                log.warning(f"  Row error: {e}")

        try:
            next_btn = driver.find_element(By.XPATH, '//a[@id="assignmentDatatable_next"]')
            if "disabled" in next_btn.get_attribute("class"):
                break
            jsc(next_btn)
            halaman += 1
            tunggu_loading()
        except Exception:
            break

    log.info(f"  {halaman} halaman → {len(hasil)} baris")
    return hasil


# ======================
# LOGIN
# ======================
try:
    driver.get("https://fasih-sm.bps.go.id/oauth_login.html")
    time.sleep(2)
    driver.find_element(By.XPATH, '//*[@id="login-in"]/a[2]').click()
    wait.until(EC.presence_of_element_located((By.ID, "username"))).send_keys(USERNAME)
    driver.find_element(By.ID, "password").send_keys(PASSWORD)
    driver.find_element(By.ID, "kc-login").click()
    wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
    log.info("Login sukses.")
    time.sleep(5)
except Exception as e:
    log.critical(f"GAGAL LOGIN: {e}")
    ss("login_error")
    driver.quit()
    exit(1)

driver.get(SURVEY_URL)
time.sleep(5)
ss("halaman_awal")

# ======================
# CEK CHECKPOINT — RESUME ATAU MULAI BARU
# ======================
cp = load_checkpoint()

if cp:
    jawab = input(
        f"\nDitemukan checkpoint terakhir:\n"
        f"  Kecamatan ke-{cp['kec_idx']+1}: {cp['kecamatan_list'][cp['kec_idx']]}\n"
        f"  Desa ke-{cp['desa_idx']+1}\n"
        f"  Diupdate: {cp['updated_at']}\n\n"
        f"Lanjut dari checkpoint? (y/n): "
    ).strip().lower()

    if jawab == 'y':
        kecamatan_list    = cp['kecamatan_list']
        desa_list_per_kec = cp['desa_list_per_kec']
        resume_kec_idx    = cp['kec_idx']
        resume_desa_idx   = cp['desa_idx']
        all_data          = load_existing_data()
        log.info(f"Resume dari kecamatan ke-{resume_kec_idx+1}, desa ke-{resume_desa_idx+1}. Data lama: {len(all_data)} baris.")
        MULAI_BARU = False
    else:
        log.info("Mulai dari awal (checkpoint diabaikan).")
        MULAI_BARU = True
else:
    MULAI_BARU = True

# ======================
# MULAI BARU — PILIH PROV+KAB, AMBIL LIST KECAMATAN
# ======================
if MULAI_BARU:
    all_data          = []
    desa_list_per_kec = {}
    resume_kec_idx    = 0
    resume_desa_idx   = 0

    buka_panel_filter()
    log.info("Pilih Provinsi...")
    pilih_option("region1Id", "[33] JAWA TENGAH")
    time.sleep(2)
    log.info("Pilih Kabupaten...")
    pilih_option("region2Id", "[24] KENDAL")
    time.sleep(2)

    log.info("Ambil list kecamatan...")
    kecamatan_list = get_all_options("region3Id")
    tutup_panel_filter()

    if not kecamatan_list:
        log.critical("List kecamatan kosong!")
        ss("error_kec_kosong")
        driver.quit()
        exit(1)

    log.info(f"Total {len(kecamatan_list)} kecamatan: {kecamatan_list}")

# ======================
# MAIN LOOP: KECAMATAN → DESA
# ======================
for kec_idx in range(resume_kec_idx, len(kecamatan_list)):
    kec_nama = kecamatan_list[kec_idx]
    log.info(f"\n{'='*50}")
    log.info(f"[{kec_idx+1}/{len(kecamatan_list)}] KECAMATAN: {kec_nama}")
    log.info(f"{'='*50}")

    # Ambil list desa (dari cache checkpoint atau fetch ulang)
    if kec_nama in desa_list_per_kec:
        desa_list = desa_list_per_kec[kec_nama]
        log.info(f"  Desa dari cache: {len(desa_list)} desa")
    else:
        try:
            buka_panel_filter()
            pilih_option("region1Id", "[33] JAWA TENGAH")
            time.sleep(1)
            pilih_option("region2Id", "[24] KENDAL")
            time.sleep(1)
            pilih_option("region3Id", kec_nama)
            time.sleep(1.5)
            desa_list = get_all_options("region4Id")
            tutup_panel_filter()
            desa_list_per_kec[kec_nama] = desa_list
        except Exception as e:
            log.error(f"  Gagal ambil desa {kec_nama}: {e}")
            ss(f"err_kec_{kec_nama[:10]}")
            tutup_panel_filter()
            continue

    if not desa_list:
        log.warning(f"  Tidak ada desa untuk {kec_nama}.")
        continue

    log.info(f"  {len(desa_list)} desa.")

    # Tentukan desa mulai dari mana
    start_desa = resume_desa_idx if kec_idx == resume_kec_idx else 0

    for desa_idx in range(start_desa, len(desa_list)):
        desa_nama = desa_list[desa_idx]
        log.info(f"\n  [{desa_idx+1}/{len(desa_list)}] DESA: {desa_nama}")

        try:
            # 1. Buka panel & isi filter
            buka_panel_filter()
            pilih_option("region1Id", "[33] JAWA TENGAH")
            time.sleep(1)
            pilih_option("region2Id", "[24] KENDAL")
            time.sleep(1)
            pilih_option("region3Id", kec_nama)
            time.sleep(1.5)
            pilih_option("region4Id", desa_nama)
            time.sleep(1)

            # 2. Apply filter
            klik_filter_data()
            tutup_panel_filter()

            # 3. Baca tabel
            # klik_submitted()
            set_show_100()
            data = ambil_data_semua_halaman(kec_nama, desa_nama)
            all_data.extend(data)
            log.info(f"    → {len(data)} baris | Total: {len(all_data)}")

            # 4. Simpan checkpoint & auto-save setelah tiap desa
            simpan_checkpoint(kec_idx, desa_idx + 1, kecamatan_list, desa_list_per_kec)
            auto_save(all_data)

            # 5. Reset filter
            driver.execute_script("window.scrollTo(0, 0);")
            buka_panel_filter()
            klik_reset()
            tutup_panel_filter()

        except Exception as e:
            log.error(f"  Error desa {desa_nama}: {e}\n{traceback.format_exc()}")
            ss(f"err_{kec_nama[:6]}_{desa_nama[:6]}")

            # Simpan checkpoint di posisi desa yang error supaya bisa resume
            simpan_checkpoint(kec_idx, desa_idx, kecamatan_list, desa_list_per_kec)
            auto_save(all_data)

            try:
                tutup_panel_filter()
                driver.execute_script("window.scrollTo(0, 0);")
                buka_panel_filter()
                klik_reset()
                tutup_panel_filter()
            except Exception:
                pass
            continue

    # Reset resume_desa_idx setelah kecamatan pertama selesai
    resume_desa_idx = 0

# ======================
# SIMPAN FINAL & BERSIHKAN
# ======================
log.info("\n" + "=" * 60)
if all_data:
    df = pd.DataFrame(all_data)
    df.to_excel(OUTPUT_FILE, index=False)
    log.info(f"SELESAI. {len(df)} baris → {OUTPUT_FILE}")

    # Hapus file temp & checkpoint
    hapus_checkpoint()
    if os.path.exists(TEMP_FILE):
        os.remove(TEMP_FILE)
        log.info(f"File temp dihapus: {TEMP_FILE}")
else:
    log.warning("Tidak ada data yang berhasil diambil.")

driver.quit()
log.info("Driver ditutup. Selesai.")