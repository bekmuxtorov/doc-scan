from sentence_transformers import SentenceTransformer, util
import torch
import re

# MODEL_NAME = "intfloat/multilingual-e5-large"
MODEL_NAME = "intfloat/multilingual-e5-large" # Foydalanuvchi tanlovi

class ItemsNotFoundError(Exception):
    """Hujjatda bandlar topilmadi (re-pattern bo'yicha)."""
    pass

class SimilarityChecker:
    def __init__(self, model_name=MODEL_NAME):
        print(f"Loading model: {model_name}...")
        self.model = SentenceTransformer(model_name)
        print("Model loaded successfully.")

    def split_into_items(self, text: str) -> list[str]:
        """Matnni raqamlangan bandlarga (faqat '1. ' ko'rinishidagilar) ajratadi."""
        parts = re.split(r'(?<!\d)(\d+\.\s+)', text)
        items = []
        for i in range(1, len(parts), 2):
            item = parts[i] + parts[i+1]
            items.append(item.strip())
        return items

    def extract_number(self, item_text: str) -> str:
        """Band matnidan uning tartib raqamini ajratib oladi (masalan '10.' -> '10')."""
        match = re.match(r'(\d+)', item_text)
        return match.group(1) if match else None

    def compare_documents(self, s1: str, s2: str, threshold: float = 0.85):
        """Ikki hujjatni raqamlari bo'yicha qat'iy solishtiradi (Strict Number Match)."""
        items1 = self.split_into_items(s1)
        items2 = self.split_into_items(s2)

        if not items1 or not items2:
            raise ItemsNotFoundError("Hujjatda tahlil qilish uchun bandlar topilmadi. Iltimos, bandlar '1. ', '2. ' ko'rinishida ekanligiga ishonch hosil qiling.")

        # s1 dagi bandlarni raqamlari bo'yicha lug'atga o'tkazish
        # { '1': '1. matn...', '2': '2. matn...' }
        map1 = {}
        for it in items1:
            num = self.extract_number(it)
            if num:
                map1[num] = it

        print(f"\nHujjat 2 ({len(items2)} ta band) s1 dagi mos raqamli bandlar bilan solishtirilmoqda...")

        results = []
        for item2 in items2:
            num2 = self.extract_number(item2)
            
            # Agar s1 da xuddi shu raqamli band bo'lsa
            if num2 and num2 in map1:
                item1_match = map1[num2]
                
                # SBERT orqali solishtirish
                temp_embeddings = self.model.encode([f"query: {item1_match}", f"query: {item2}"], convert_to_tensor=True)
                score = util.cos_sim(temp_embeddings[0], temp_embeddings[1]).item()
                
                status = "MATCH" if score >= threshold else "PARTIAL" if score > 0.7 else "MISSING"
                
                results.append({
                    "s2_item": item2,
                    "s1_matched_item": item1_match,
                    "score": score,
                    "status": status
                })
            else:
                # Agar s1 da bunday raqam bo'lmasa, qidirib o'tirmaymiz
                results.append({
                    "s2_item": item2,
                    "s1_matched_item": "MOS RAQAMLI BAND TOPILMADI (S1 da yo'q)",
                    "score": 0,
                    "status": "MISSING"
                })

        return results

    def print_results(self, results):
        """Natijalarni chiroyli jadval ko'rinishida chiqaradi."""
        print("\n" + "="*80)
        print(f"{'Band (s2)':<30} | {'Mos raqamli (s1)':<30} | {'Foiz':<8} | {'Holat'}")
        print("-" * 80)
        
        for res in results:
            s2_short = (res['s2_item'][:27] + '...') if len(res['s2_item']) > 30 else res['s2_item']
            s1_short = (res['s1_matched_item'][:27] + '...') if len(res['s1_matched_item']) > 30 else res['s1_matched_item']
            
            print(f"{s2_short:<30} | {s1_short:<30} | {res['score']:.2%} | {res['status']}")
        print("="*80)

if __name__ == "__main__":
    checker = SimilarityChecker()
    
    s2: str = "1. Payvandlash qurilmasi uchun (Kabil) Проволка сварочная 32 а - 200  п/м 2. Avtogen shlangi шланг для автогена 32 а - 200  п/м 3. Avtogen uchun kislarod reduktur (БКО-50-12.5, ВАРИАНТ) Редуктор кислородный 32 а - 10  Дона 4. Propan reduktor (КЕДР БПО-5) Редуктор газа - 5  Шт 5. Payvandlash ishlarini amalga oshirishda qo’llaniladigan (shitok) СИБРТЕКҲ ойнаси 110 * 90 мм, 89118 Сварочный - 5  Шт 6. Avtogen garelka (ГЗУ-3-02 нак № 2/№ 3) Гоreлка 32 а - 7  Дона 7. 5 tonnali (Kalka) ГРОСSO Калитка - 7  Комплект 8. Temir kesish aparati (Balgarka) Реzak - 1  Дона 9. Asfalt kesish qurilmasi TOTAL TP1016-2 Реzak - 1  Дона 10. Bolg’a (отбойный молотог) NEX 30 мм Bosch GSH 16-30 Отбойные Молоток - 1  Дона"
    s1: str = "1. Payvandlash qurilmasi uchun (Kabil) Проволка сварочная 32 а - 200  п/м 2. Avtogen shlangi шланг для автогена 32 а - 200  п/м 3. Avtogen uchun kislarod reduktur (БКО-50-12.5, ВАРИАНТ) Редуктор кислородный 32 а - 10  Дона 4. Propan reduktor (КЕДР БПО-5) Редуктор газа - 5  Dona 5. Temir kesish aparati (Balgarka) Реzak - 1  Дона 10. Avtogen shlangi шланг для автогена 32 а - 200  п/м" 
    
    results = checker.compare_documents(s1, s2)
    if results:
        checker.print_results(results)
