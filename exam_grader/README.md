# Exam Grader - SMA Boash Excellent

Aplikasi web untuk mengoreksi lembar ujian Informatika (Kelas X, XI, XII) secara semi-otomatis.

## Fitur
- Pilih kelas (X / XI / XII)
- Upload foto lembar jawaban (bisa dari kamera HP)
- OCR (pembacaan teks dari foto)
- Input / edit jawaban siswa
- Perhitungan skor otomatis berdasarkan kunci jawaban
- Tampilan hasil detail per soal
- Mobile-friendly

## Cara Menjalankan di Komputer Lokal

```bash
# 1. Masuk ke folder project
cd exam_grader

# 2. Buat virtual environment
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate

# 3. Install library
pip install -r requirements.txt

# 4. Jalankan
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Buka browser: http://localhost:8000

## Cara Deploy Online (Gratis) di Render.com

1. Buat akun di [https://render.com](https://render.com) (bisa pakai Google/GitHub)
2. Klik **New +** → **Web Service**
3. Hubungkan repository GitHub Anda (atau upload manual)
4. Isi pengaturan:
   - **Name**: exam-grader
   - **Runtime**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
5. Klik **Create Web Service**
6. Tunggu beberapa menit sampai status **Live**
7. Link aplikasi akan muncul (contoh: `https://exam-grader-xxxx.onrender.com`)

Setelah itu Anda bisa membuka link tersebut dari HP.

## Catatan Penting
- OCR membutuhkan resource cukup besar. Di plan gratis Render kadang lambat saat pertama kali.
- Untuk akurasi terbaik: foto harus jelas, terang, dan tidak miring.
- Sistem ini bersifat **semi-otomatis**. Guru tetap disarankan memeriksa ulang hasil, terutama soal isian dan essay.
- Kunci jawaban tersimpan di folder `data/`.

## Struktur Folder
```
exam_grader/
├── app/
│   ├── main.py
│   ├── templates/
│   │   └── index.html
│   └── static/
├── data/
│   ├── kunci_kelas_X.json
│   ├── kunci_kelas_XI.json
│   ├── kunci_kelas_XII.json
│   └── kunci_semua_kelas.json
├── requirements.txt
└── README.md
```
