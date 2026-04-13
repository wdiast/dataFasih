# Ambil Data Fasih

## Persiapan (Python dan Git)

Bagian ini untuk pengguna awam. Jika Python dan Git sudah terpasang, lanjut ke [Unduh Project](#unduh-project).

### 1) Install Python

Unduh dan instal Python 3 dari:
https://www.python.org/downloads/

Saat instalasi di Windows, centang opsi "Add Python to PATH", lalu lanjutkan sampai selesai.

### 2) Install Git

Unduh dan instal Git dari:
https://git-scm.com/downloads

### 3) Cek instalasi

Buka PowerShell atau CMD, lalu jalankan:

```bash
python --version
```

Contoh output yang benar:
`Python 3.11.6`

Lalu cek Git:

```bash
git --version
```

Contoh output yang benar:
`git version 2.44.0.windows.1`

Jika `python` tidak dikenali, tutup dan buka ulang terminal. Jika masih gagal, ulangi instalasi Python dan pastikan opsi "Add Python to PATH" dicentang.

## Unduh Project

Buka PowerShell atau CMD, lalu jalankan perintah berikut satu per satu:

```bash
git clone https://github.com/wdiast/dataFasih.git
```

Perintah di atas mengunduh project dari GitHub.

```bash
cd dataFasih
```

Perintah di atas masuk ke folder project (wajib sebelum menjalankan perintah lain).

## Instal Dependensi

Pastikan masih berada di folder project `dataFasih`, lalu jalankan:

```bash
python -m pip install -r requirements.txt
```

Perintah di atas menginstal semua library Python yang dibutuhkan.

```bash
python -m playwright install chromium
```

Perintah di atas mengunduh browser Chromium yang diperlukan Playwright. Cukup dijalankan sekali per environment.


## Cara Menjalankan - Script atau Terminal

## Login Akun SSO
Ada tanda 

 `#============
  #LOGIN
  #============`
Masukkan Username dan Password seperti yang ditunjukkan pada script


## Ubah Link Halaman Collect
 `#============
  #Halaman Collect
  #============`

  ganti sesuai dengan url pada halaman data yang ingin diam,

## Kredit

Semoga panduan ini membantu. Jika ada pertanyaan, hubungi tim IPDS BPS Kabupaten Bulungan.
