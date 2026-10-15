# Exam Grader (Streamlit Version)

Aplikasi pengoreksi ujian Informatika SMA Boash Excellent (Kelas X, XI, XII).

## Cara Deploy di Streamlit Community Cloud (Gratis)

### Langkah 1: Siapkan GitHub
1. Buat repository baru di GitHub (contoh nama: `exam-grader`)
2. Upload semua file berikut ke repository:
   - `app.py`
   - `requirements.txt`
   - `kunci_kelas_X.json`
   - `kunci_kelas_XI.json`
   - `kunci_kelas_XII.json`
   - `README.md`

### Langkah 2: Deploy
1. Buka https://share.streamlit.io
2. Login dengan akun GitHub
3. Klik **New app**
4. Isi:
   - Repository: pilih repository yang tadi dibuat
   - Branch: `main`
   - Main file path: `app.py`
5. Klik **Deploy**

Tunggu 1–3 menit sampai muncul link aplikasi.

### Cara Pakai
1. Buka link aplikasi di HP atau komputer
2. Pilih kelas di sidebar
3. Isi nama siswa
4. Isi jawaban siswa satu per satu
5. Klik **Hitung Nilai Otomatis**
6. Lihat hasilnya
