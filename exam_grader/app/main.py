from fastapi import FastAPI, Request, UploadFile, File, Form, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pathlib import Path
import json
import io
import re
from typing import List, Optional
from PIL import Image
import numpy as np

# Optional OCR - will be loaded lazily
ocr_reader = None

app = FastAPI(title="Exam Grader - SMA Boash Excellent", version="1.0")

# Paths
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
TEMPLATES_DIR = Path(__file__).resolve().parent / "templates"

app.mount("/static", StaticFiles(directory=Path(__file__).resolve().parent / "static"), name="static")
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

# Load answer keys
ANSWER_KEYS = {}
for kelas in ["X", "XI", "XII"]:
    key_file = DATA_DIR / f"kunci_kelas_{kelas}.json"
    if key_file.exists():
        with open(key_file, "r", encoding="utf-8") as f:
            ANSWER_KEYS[kelas] = json.load(f)


def get_ocr_reader():
    """Lazy load EasyOCR to avoid slow startup if not needed"""
    global ocr_reader
    if ocr_reader is None:
        try:
            import easyocr
            ocr_reader = easyocr.Reader(['id', 'en'], gpu=False)
        except Exception as e:
            print(f"OCR not available: {e}")
            ocr_reader = False
    return ocr_reader


def normalize_text(text: str) -> str:
    """Normalize text for comparison"""
    if not text:
        return ""
    text = text.lower().strip()
    text = re.sub(r'\s+', ' ', text)
    return text


def calculate_similarity(student_ans: str, correct_ans: str) -> float:
    """Simple similarity score between 0 and 1"""
    from fuzzywuzzy import fuzz
    if not student_ans or not correct_ans:
        return 0.0
    return fuzz.token_sort_ratio(normalize_text(student_ans), normalize_text(correct_ans)) / 100.0


def extract_text_from_image(image_bytes: bytes) -> str:
    """Extract text using EasyOCR"""
    reader = get_ocr_reader()
    if not reader:
        return "[OCR tidak tersedia di server ini]"
    
    try:
        image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        img_array = np.array(image)
        results = reader.readtext(img_array, detail=0, paragraph=True)
        return "\n".join(results)
    except Exception as e:
        return f"[Gagal membaca gambar: {str(e)}]"


def score_objective(student_answer: str, correct_answer: str, max_score: int) -> dict:
    """Score objective questions (PG, Matching, True/False)"""
    student_clean = normalize_text(student_answer)
    correct_clean = normalize_text(correct_answer)
    
    # Extract letter answers like "a", "b", "benar", etc.
    score = 0
    matched = False
    note = ""
    
    # Check for exact letter match (A/B/C/D/E)
    student_letter = re.search(r'\b([a-e])\b', student_clean)
    correct_letter = re.search(r'\b([a-e])\b', correct_clean)
    
    if student_letter and correct_letter:
        if student_letter.group(1) == correct_letter.group(1):
            score = max_score
            matched = True
            note = "Benar (huruf cocok)"
        else:
            note = f"Salah (siswa: {student_letter.group(1).upper()}, kunci: {correct_letter.group(1).upper()})"
    else:
        # Fuzzy match for True/False, Matching, short answers
        sim = calculate_similarity(student_answer, correct_answer)
        if sim >= 0.75:
            score = max_score
            matched = True
            note = f"Benar (kemiripan {sim:.0%})"
        elif sim >= 0.5:
            score = max_score // 2
            note = f"Sebagian (kemiripan {sim:.0%})"
        else:
            note = f"Kurang cocok (kemiripan {sim:.0%})"
    
    return {
        "score": score,
        "max_score": max_score,
        "matched": matched,
        "note": note,
        "similarity": calculate_similarity(student_answer, correct_answer)
    }


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {
        "request": request,
        "kelas_list": list(ANSWER_KEYS.keys())
    })


@app.get("/api/kunci/{kelas}")
async def get_kunci(kelas: str):
    if kelas not in ANSWER_KEYS:
        raise HTTPException(status_code=404, detail="Kelas tidak ditemukan")
    return ANSWER_KEYS[kelas]


@app.post("/api/ocr")
async def run_ocr(files: List[UploadFile] = File(...)):
    """Extract text from uploaded images"""
    all_text = []
    for file in files:
        content = await file.read()
        text = extract_text_from_image(content)
        all_text.append({
            "filename": file.filename,
            "text": text
        })
    return {"results": all_text}


@app.post("/api/grade")
async def grade_exam(
    kelas: str = Form(...),
    student_name: str = Form(""),
    answers_json: str = Form(...),  # JSON string of {no: student_answer}
):
    """Grade based on submitted answers"""
    if kelas not in ANSWER_KEYS:
        raise HTTPException(status_code=404, detail="Kelas tidak ditemukan")
    
    key_data = ANSWER_KEYS[kelas]
    try:
        student_answers = json.loads(answers_json)
    except:
        raise HTTPException(status_code=400, detail="Format jawaban tidak valid")
    
    results = []
    total_score = 0
    max_total = 0
    
    for soal in key_data["soal"]:
        no = soal["no"]
        max_score = soal["nilai"]
        max_total += max_score
        student_ans = student_answers.get(no, "")
        correct_ans = soal["jawaban"]
        
        # Different scoring for different types
        jenis = soal.get("jenis", "").lower()
        if any(x in jenis for x in ["pilihan", "menjodohkan", "benar"]):
            scoring = score_objective(student_ans, correct_ans, max_score)
        else:
            # Essay / short answer - more lenient + partial
            sim = calculate_similarity(student_ans, correct_ans)
            if sim >= 0.7:
                score = max_score
                note = f"Baik (kemiripan {sim:.0%})"
            elif sim >= 0.4:
                score = int(max_score * 0.6)
                note = f"Cukup (kemiripan {sim:.0%})"
            elif sim >= 0.2:
                score = int(max_score * 0.3)
                note = f"Kurang (kemiripan {sim:.0%})"
            else:
                score = 0
                note = "Tidak cocok / kosong"
            scoring = {
                "score": score,
                "max_score": max_score,
                "matched": sim >= 0.7,
                "note": note,
                "similarity": sim
            }
        
        total_score += scoring["score"]
        results.append({
            "no": no,
            "jenis": soal.get("jenis", ""),
            "soal_singkat": soal.get("soal", "")[:80] + ("..." if len(soal.get("soal", "")) > 80 else ""),
            "kunci": correct_ans,
            "jawaban_siswa": student_ans,
            "score": scoring["score"],
            "max_score": max_score,
            "note": scoring["note"],
            "similarity": round(scoring["similarity"] * 100, 1)
        })
    
    return {
        "student_name": student_name,
        "kelas": kelas,
        "total_score": total_score,
        "max_total": max_total,
        "percentage": round(total_score / max_total * 100, 1) if max_total > 0 else 0,
        "results": results
    }


@app.get("/health")
async def health():
    return {"status": "ok", "kelas_tersedia": list(ANSWER_KEYS.keys())}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
