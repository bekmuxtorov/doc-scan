import logging
import re
from pathlib import Path
from typing import Optional, List, Union

from docx import Document
from docx.table import Table

# Logging sozlamalari
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class WordExtractionError(Exception):
    """Word hujjatidan ma'lumot olishda yuzaga keladigan maxsus xatolik."""
    pass

class WordExtractor:
    """Word hujjatlari bilan ishlash uchun professional klass."""

    def __init__(self, file_path: Union[str, Path]):
        self.file_path = Path(file_path)
        if not self.file_path.exists():
            raise FileNotFoundError(f"Fayl topilmadi: {self.file_path}")
        
    def _extract_from_table(self, doc: Document, keywords: List[str]) -> Optional[str]:
        """Jadvallardan kalit so'zlar bo'yicha ma'lumot qidiradi."""
        for table in doc.tables:
            for row in table.rows:
                # Jadvalda kamida 2 ta ustun bo'lishi kerak
                if len(row.cells) < 2:
                    continue
                
                key_cell = row.cells[0].text.strip()
                
                # Regex orqali aniqroq qidirish (case-insensitive)
                for keyword in keywords:
                    if re.search(keyword, key_cell, re.IGNORECASE):
                        value = row.cells[1].text.strip()
                        if value:
                            logger.info(f"Ma'lumot topildi (Kalit: '{key_cell}')")
                            return value
        return None

    def _extract_from_paragraphs(self, doc: Document, keywords: List[str]) -> Optional[str]:
        """Paragraflardan ma'lumot qidiradi (agar jadvalda bo'lmasa)."""
        # Bu yerda murakkabroq mantiq qo'shish mumkin
        # Masalan, kalit so'zdan keyingi kelgan paragrafni olish
        for i, para in enumerate(doc.paragraphs):
            text = para.text.strip()
            for keyword in keywords:
                if re.search(keyword, text, re.IGNORECASE):
                    # Kalit so'z o'sha qatorda bo'lsa, lekin qiymat yo'q bo'lsa keyingi qatordan qidirish
                    if len(text) < len(keyword) + 5 and i + 1 < len(doc.paragraphs):
                        return doc.paragraphs[i+1].text.strip()
                    return text
        return None

    def get_purchase_purpose(self) -> str:
        """'Xaridlar maqsadi' bo'limini qaytaradi."""
        try:
            doc = Document(self.file_path)
            
            # Qidiriladigan patternlar
            keywords = [
                r"Xaridlar\s+maqsadi",
                r"Xarid\s+maqsadi",
                r"^2\.$" # Faqat "2." deb boshlanadigan qatorlar
            ]

            # 1. Avval jadvallardan qidiramiz
            value = self._extract_from_table(doc, keywords)
            
            # 2. Agar topilmasa, paragraflardan qidiramiz
            if not value:
                value = self._extract_from_paragraphs(doc, keywords)
            
            if value:
                return value
            
            logger.warning(f"'{self.file_path}' hujjatida 'Xaridlar maqsadi' topilmadi.")
            return "Ma'lumot topilmadi"

        except Exception as e:
            logger.error(f"Xatolik yuz berdi: {str(e)}")
            raise WordExtractionError(f"Hujjatni o'qishda xatolik: {e}")

# INTERFACE: Foydalanish uchun qulay funksiya
def get_text_from_word(file_path: str) -> str:
    """Senior yondashuv: Sodda interfeys, murakkab mantiq."""
    try:
        extractor = WordExtractor(file_path)
        return extractor.get_purchase_purpose()
    except Exception as e:
        return f"Xato: {str(e)}"

if __name__ == "__main__":
    # Test qilish
    TARGET_FILE = "test.docx"
    
    # Namuna (agar fayl mavjud bo'lsa)
    if Path(TARGET_FILE).exists():
        text = get_text_from_word(TARGET_FILE)
        print("\nOlingan matn:")
        print("-" * 30)
        print(text)
    else:
        print(f"Eslatma: '{TARGET_FILE}' fayli topilmadi. Uni loyiha papkasiga joylashtiring.")
