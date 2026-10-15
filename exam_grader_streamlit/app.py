import streamlit as st
import json
from pathlib import Path
import re
from PIL import Image

st.set_page_config(
    page_title="Exam Grader - SMA Boash Excellent",
    page_icon="📝",
    layout="wide",
    initial_sidebar_state="expanded"
)

@st.cache_data
def load_keys():
    keys = {}
    base = Path(__file__).parent
    for kelas in ["X", "XI", "XII"]:
        path = base / f"kunci_kelas_{kelas}.json"
        if path.exists():
            with open(path, "r", encoding="utf-8") as f:
                keys[kelas] = json.load(f)
    return keys

ANSWER_KEYS = load_keys()

def normalize(text: str) -> str:
    if not text:
        return ""
    text = str(text).lower().strip()
    text = re.sub(r'\s+', ' ', text)
    return text

def simple_similarity(a: str, b: str) -> float:
    a = normalize(a)
    b = normalize(b)
    if not a or not b:
        return 0.0
    if a == b:
        return 1.0
    if a in b or b in a:
        return 0.8
    words_a = set(a.split())
    words_b = set(b.split())
    if not words_a or not words_b:
        return 0.0
    common = words_a.intersection(words_b)
    return len(common) / max(len(words_a), len(words_b))

def score_answer(student: str, correct: str, max_score: int, jenis: str) -> dict:
    jenis = jenis.lower()
    student_clean = normalize(student)
    correct_clean = normalize(correct)

    if any(x in jenis for x in ["pilihan", "menjodohkan", "benar"]):
        s_letter = re.search(r'\b([a-e])\b', student_clean)
        c_letter = re.search(r'\b([a-e])\b', correct_clean)
        if s_letter and c_letter:
            if s_letter.group(1) == c_letter.group(1):
                return {"score": max_score, "note": "✅ Benar", "sim": 1.0}
            else:
                return {"score": 0, "note": f"❌ Salah (siswa: {s_letter.group(1).upper()})", "sim": 0.0}

        if any(x in student_clean for x in ["benar", "true", "√", "v"]):
            if any(x in correct_clean for x in ["benar", "√"]):
                return {"score": max_score, "note": "✅ Benar", "sim": 1.0}
        if any(x in student_clean for x in ["salah", "false", "x"]):
            if any(x in correct_clean for x in ["salah", "x"]):
                return {"score": max_score, "note": "✅ Benar", "sim": 1.0}

        sim = simple_similarity(student, correct)
        if sim >= 0.75:
            return {"score": max_score, "note": f"✅ Benar ({sim:.0%})", "sim": sim}
        elif sim >= 0.4:
            return {"score": max_score // 2, "note": f"⚠️ Sebagian ({sim:.0%})", "sim": sim}
        else:
            return {"score": 0, "note": "❌ Tidak cocok", "sim": sim}

    sim = simple_similarity(student, correct)
    if sim >= 0.65:
        return {"score": max_score, "note": f"✅ Baik ({sim:.0%})", "sim": sim}
    elif sim >= 0.35:
        return {"score": int(max_score * 0.6), "note": f"⚠️ Cukup ({sim:.0%})", "sim": sim}
    elif sim >= 0.15:
        return {"score": int(max_score * 0.3), "note": f"⚠️ Kurang ({sim:.0%})", "sim": sim}
    else:
        return {"score": 0, "note": "❌ Kosong / tidak cocok", "sim": sim}


# ====================== UI ======================
st.title("📝 Exam Grader")
st.caption("SMA Boash Excellent • Informatics • 2026/2027")

with st.sidebar:
    st.header("Pengaturan")
    kelas = st.selectbox("Pilih Kelas", options=["", "X", "XI", "XII"],
                         format_func=lambda x: f"Kelas {x}" if x else "-- Pilih Kelas --")
    nama_siswa = st.text_input("Nama Siswa", placeholder="Contoh: Budi Santoso")
    st.divider()
    st.markdown("""
    **Cara Pakai:**
    1. Pilih kelas & isi nama siswa
    2. Upload foto lembar jawaban
    3. Lihat foto sambil isi jawaban
    4. Klik **Hitung Nilai**
    """)
    st.info("Tips: Foto yang jelas dan terang akan memudahkan Anda membaca jawaban siswa.")

if not kelas:
    st.warning("Silakan pilih kelas di sidebar.")
    st.stop()

key_data = ANSWER_KEYS.get(kelas)
if not key_data:
    st.error("Kunci jawaban tidak ditemukan.")
    st.stop()

st.subheader(f"Kelas {kelas} — {nama_siswa if nama_siswa else '(Nama belum diisi)'}")
st.write(f"Total soal: **{len(key_data['soal'])}** | Skor maksimal: **100**")

# ========== UPLOAD FOTO ==========
st.markdown("---")
st.subheader("📷 Upload Foto Lembar Jawaban")

uploaded_files = st.file_uploader(
    "Pilih foto kertas ujian siswa (bisa lebih dari 1)",
    type=["jpg", "jpeg", "png", "webp"],
    accept_multiple_files=True
)

if uploaded_files:
    st.success(f"{len(uploaded_files)} foto berhasil diunggah")
    cols = st.columns(min(3, len(uploaded_files)))
    for idx, file in enumerate(uploaded_files):
        with cols[idx % 3]:
            image = Image.open(file)
            st.image(image, caption=file.name, use_container_width=True)
else:
    st.info("Belum ada foto. Silakan upload foto lembar jawaban siswa.")

# ========== FORM JAWABAN ==========
st.markdown("---")
st.subheader("✏️ Isi Jawaban Siswa")
st.caption("Lihat foto di atas sambil mengisi jawaban di bawah ini. Lebih cepat daripada memegang kertas fisik.")

student_answers = {}
for soal in key_data["soal"]:
    no = soal["no"]
    jenis = soal.get("jenis", "")
    max_nilai = soal.get("nilai", 0)
    pertanyaan = soal.get("soal", "")[:100]
    if len(soal.get("soal", "")) > 100:
        pertanyaan += "..."

    with st.expander(f"**No. {no}** — {jenis} ({max_nilai} poin)", expanded=False):
        st.caption(pertanyaan)
        ans = st.text_input(
            f"Jawaban {no}",
            key=f"ans_{no}",
            placeholder="Ketik/salin jawaban siswa...",
            label_visibility="collapsed"
        )
        student_answers[no] = ans

# ========== HITUNG NILAI ==========
st.markdown("---")
if st.button("Hitung Nilai Otomatis", type="primary", use_container_width=True):
    results = []
    total_score = 0
    max_total = 0

    for soal in key_data["soal"]:
        no = soal["no"]
        max_score = soal.get("nilai", 0)
        max_total += max_score
        student = student_answers.get(no, "")
        correct = soal.get("jawaban", "")
        jenis = soal.get("jenis", "")

        scoring = score_answer(student, correct, max_score, jenis)
        total_score += scoring["score"]

        results.append({
            "no": no,
            "jenis": jenis,
            "max": max_score,
            "score": scoring["score"],
            "note": scoring["note"],
            "siswa": student if student else "(kosong)",
            "kunci": correct[:90] + ("..." if len(correct) > 90 else "")
        })

    percentage = round(total_score / max_total * 100, 1) if max_total > 0 else 0

    st.success(f"**Hasil Akhir: {total_score} / {max_total}**  ({percentage}%)")
    st.progress(min(percentage / 100, 1.0))

    if nama_siswa:
        st.write(f"**Siswa:** {nama_siswa} | **Kelas:** {kelas}")

    st.subheader("Detail per Soal")
    for r in results:
        cols = st.columns([1, 4, 1])
        cols[0].markdown(f"**No. {r['no']}**")
        cols[1].markdown(r["note"])
        cols[2].markdown(f"**{r['score']}/{r['max']}**")
        st.caption(f"Siswa: {r['siswa'][:70]}")
        st.caption(f"Kunci : {r['kunci']}")
        st.divider()

st.markdown("---")
st.caption("Exam Grader • SMA Boash Excellent • Semi-otomatis")
