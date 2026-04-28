import os
import shutil
import uuid
from typing import List, Dict, Any

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# O'zimizning modullarni import qilamiz
from get_text_from_word import WordExtractor
from option import SimilarityChecker, ItemsNotFoundError
from fastapi.responses import JSONResponse

app = FastAPI(title="AI-word-scan API", version="1.0.0")

# CORS sozlamalari
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Modelni pre-load qilamiz (bir marta xotiraga yuklanadi)
checker = SimilarityChecker()

@app.exception_handler(ItemsNotFoundError)
async def items_not_found_handler(request, exc):
    return JSONResponse(
        status_code=400,
        content={
            "status_code": 400,
            "error": str(exc),
            "results": []
        }
    )

class AnalysisResponse(BaseModel):
    status_code: int
    error: str
    results: List[Dict[str, Any]]

@app.post("/analyze", response_model=AnalysisResponse)
async def analyze_document(
    file: UploadFile = File(...),
    s2: str = Form(...)
):
    """
    Word fayl va s2 matnni solishtiradi.
    """
    temp_file_path = f"temp_{uuid.uuid4()}_{file.filename}"
    
    try:
        # 1. Faylni vaqtincha saqlash
        with open(temp_file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # 2. s1 matnini Word'dan olish
        extractor = WordExtractor(temp_file_path)
        s1_raw = extractor.get_purchase_purpose()
        
        if s1_raw == "Ma'lumot topilmadi":
            return AnalysisResponse(
                status_code=404,
                error="Word hujjatida 'Xaridlar maqsadi' topilmadi.",
                results=[]
            )

        # 3. Solishtirish (SimilarityChecker orqali)
        # s1: Word matni, s2: User yuborgan matn
        raw_results = checker.compare_documents(s2,s1_raw)
        
        if not raw_results:
            return AnalysisResponse(
                status_code=500,
                error="Solishtirish jarayonida xatolik yuz berdi.",
                results=[]
            )

        # 4. Natijalarni foydalanuvchi so'ragan formatga o'tkazish
        formatted_results = []
        for i, res in enumerate(raw_results, 1):
            formatted_results.append({
                "row": i,
                "s1": res["s1_matched_item"], # Word dagi mos keluvchi band
                "s2": res["s2_item"],         # User yuborgan band
                "concurrence": f"{res['score'] * 100:.2f}" # Foiz ko'rinishida string
            })

        return AnalysisResponse(
            status_code=200,
            error="",
            results=formatted_results
        )

    except Exception as e:
        return AnalysisResponse(
            status_code=500,
            error=str(e),
            results=[]
        )
    finally:
        # Vaqtinchalik faylni o'chirish
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
