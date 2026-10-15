import streamlit as st
import json
from pathlib import Path
from fuzzywuzzy import fuzz
import re

# Page config
st.set_page_config(
    page_title="Exam Grader - SMA Boash Excellent",
    page_icon="📝",
    layout="centered",
    initial_sidebar_state="expanded"
)

# Load answer keys
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

def similarity(a: str, b: str) -> float:
    if not a or not b:
        return 0.0
    return fuzz.token_sort_ratio(normalize(a), normalize(b)) / 100.0

def score_answer(student: str, correct: str, max_score: int, jenis: str) -> dict:
    jenis = jenis.lower()
    student_clean = normalize(student)
    correct_clean = normalize(correct)

    # Objective questions (PG, Matching, Benar/Salah)
    if any(x in jenis for x in ["pilihan", "menjodohkan", "benar"]):
        # Try letter match first
        s_letter = re.search(r'\b([a-e])\b', student_clean)
        c_letter = re.search(r'\b([a-e])\b', correct_clean)
        if s_letter and c_letter:
            if s_letter.group(1) == c_letter.group(1):
                return {"score": max_score, "note": "✅ Benar", "sim": 1.0}
            else:
                return {"score": 0, "note": f"❌ Salah (siswa: {s_letter.group(1).upper()})", "sim": 0.0}

        # True/False style
        if "benar" in student_clean or student_clean in ["b", "benar", "true", "√", "v"]:
            if "benar" in correct_clean or "√" in correct_clean:
                return {"score": max_score, "note": "✅ Benar", "sim": 1.0}
        if "salah" in student_clean or student_clean in ["s", "salah", "false", "x"]:
            if "salah" in correct_clean or "x" in correct_clean:
                return {"score": max_score, "note": "✅ Benar", "sim": 1.0}

        sim = similarity(student, correct)
        if sim >= 0.75:
            return {"score": max_score, "note": f"✅ Benar (kemiripan {sim:.0%})", "sim": sim}
        elif sim >= 0.45:
            return {"score": max_score // 2, "note": f"⚠️ Sebagian ({sim:.0%})", "sim": sim}
        else:
            return {"score": 0, "note": f"❌ Tidak cocok ({sim:.0%})", "sim": sim}

    # Short answer / Essay - more lenient
    sim = similarity(student, correct)
    if sim >= 0.70:
        return {"score": max_score, "note": f"✅ Baik ({sim:.0%})", "sim": sim}
    elif sim >= 0.40:
        return {"score": int(max_score * 0.6), "note": f"⚠️ Cukup ({sim:.0%})", "sim": sim}
    elif sim >= 0.20:
        return {"score": int(max_score * 0.3), "note": f"⚠️ Kurang ({sim:.0%})", "sim": sim}
    else:
        return {"score": 0, "note": "❌ Kosong / tidak cocok", "sim": sim}


# ====================== UI ======================

st.title("📝 Exam Grader")
st.caption("SMA Boash Excellent • Informatics • Semester Ganjil 2026/2027")

# Sidebar
with st.sidebar:
    st.header("Pengaturan")
    kelas = st.selectbox("Pilih Kelas", options=["", "X", "XI", "XII"], format_func=lambda x: f"Kelas {x}" if x else "-- Pilih Kelas --")
    nama_siswa = st.text_input("Nama Siswa", placeholder="Contoh: Budi Santoso")
    st.divider()
    st.markdown("**Petunjuk:**")
    st.markdown("""
    1. Pilih kelas
    2. Isi nama siswa
    3. Isi jawaban siswa pada setiap soal
    4. Klik tombol **Hitung Nilai**
    """)
    st.info("Sistem ini semi-otomatis. Guru tetap bisa menyesuaikan nilai akhir.")

if not kelas:
    st.warning("Silakan pilih kelas di sidebar sebelah kiri.")
    st.stop()

key_data = ANSWER_KEYS.get(kelas)
if not key_data:
    st.error("Kunci jawaban untuk kelas ini tidak ditemukan.")
    st.stop()

st.subheader(f"Kelas {kelas} — {nama_siswa if nama_siswa else '(Nama belum diisi)'}")
st.write(f"Total soal: **{len(key_data['soal'])}** | Skor maksimal: **{key_data.get('total_skor', 100)}**")

# Input answers
st.markdown("---")
st.subheader("Isi Jawaban Siswa")

student_answers = {}
for soal in key_data["soal"]:
    no = soal["no"]
    jenis = soal.get("jenis", "")
    max_nilai = soal.get("nilai", 0)
    pertanyaan = soal.get("soal", "")[:120] + ("..." if len(soal.get("soal", "")) > 120 else "")

    with st.expander(f"**No. {no}** — {jenis} ({max_nilai} poin)", expanded=False):
        st.caption(pertanyaan)
        ans = st.text_input(
            f"Jawaban siswa untuk no. {no}",
            key=f"ans_{no}",
            placeholder="Ketik jawaban siswa di sini...",
            label_visibility="collapsed"
        )
        student_answers[no] = ans

# Grade button
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
            "kunci": correct[:100] + ("..." if len(correct) > 100 else "")
        })

    # Show summary
    percentage = round(total_score / max_total * 100, 1) if max_total > 0 else 0

    st.success(f"**Hasil Akhir: {total_score} / {max_total}** ({percentage}%)")
    st.progress(percentage / 100)

    # Detailed results
    st.subheader("Detail per Soal")
    for r in results:
        if r["score"] == r["max"]:
            color = "green"
        elif r["score"] > 0:
            color = "orange"
        else:
            color = "red"

        with st.container():
            cols = st.columns([1, 3, 1])
            cols[0].markdown(f"**No. {r['no']}**")
            cols[1].markdown(f"{r['note']}")
            cols[2].markdown(f"**{r['score']}/{r['max']}**")
            st.caption(f"Siswa: {r['siswa'][:80]}")
            st.caption(f"Kunci: {r['kunci']}")
            st.divider()

# Footer
st.markdown("---")
st.caption("Exam Grader • SMA Boash Excellent • Dibuat untuk memudahkan koreksi ujian Informatika")
