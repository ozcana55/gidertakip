import os
from google import genai
from google.genai import types
from PIL import Image
import streamlit as str_app

# 1. API Anahtarınızı Tanımlayın
# Not: API anahtarınızı güvenliğiniz için ortam değişkeni (Environment Variable) 
# olarak 'GEMINI_API_KEY' adıyla kaydetmeniz önerilir.
# 1. API Anahtarınızı Güvenli Kasadan Tanımlayın
os.environ["GEMINI_API_KEY"] = str_app.secrets["GEMINI_API_KEY"]

def fis_verilerini_ayıkla(gorsel_yolu: str):
    """
    Verilen fiş/fatura fotoğrafını analiz eder ve muhasebe bilgilerini çeker.
    """
    # Google GenAI istemcisini başlatıyoruz
    client = genai.Client()
    
    # Görseli yüklüyoruz
    try:
        gorsel = Image.open(gorsel_yolu)
    except FileNotFoundError:
        return {"hata": f"Dosya bulunamadı: {gorsel_yolu}"}
    
    # Yapay zekaya ne yapması gerektiğini anlatan net bir talimat (Prompt) yazıyoruz
    talimat = (
        "Sana bir fiş veya fatura fotoğrafı veriyorum. Lütfen bu görseli dikkatlice incele "
        "ve şu bilgileri ayıkla:\n"
        "1. Şirket Adı (Fişi kesen işletme)\n"
        "2. Tarih (GG.AA.YYYY formatında)\n"
        "3. Toplam Tutar (Sadece sayısal değer, örn: 250.50)\n"
        "4. KDV Oranı (Varsa %20, %10 gibi oranlar)\n"
        "5. KDV Tutarı (Fişteki toplam KDV miktarı, sadece sayısal değer)\n"
        "6. Fiş Numarası\n\n"
        "Çıktıyı sadece ve sadece temiz bir JSON formatında ver. Başka hiçbir açıklama yazma."
    )
    
    print("Görsel analiz ediliyor, lütfen bekleyin...")
    
    # gemini-2.5-flash modelini çağırıyoruz (Hem hızlı hem de görsel okumada çok başarılı)
    response = client.models.generate_content(
        model='gemini-2.5-flash',
        contents=[gorsel, talimat],
        # Çıktının kesinlikle JSON formatında gelmesini zorunlu kılıyoruz
        config=types.GenerateContentConfig(
            response_mime_type="application/json"
        )
    )
    
    return response.text

# --- KODU TEST ETME ---
if __name__ == "__main__":
    # Test etmek için bilgisayarındaki bir fiş fotoğrafının yolunu buraya yaz
    test_gorseli = "test_fisi.jpeg" 
    
    # Eğer test görseli yoksa kodun hata vermemesi için küçük bir kontrol
    if os.path.exists(test_gorseli):
        analiz_sonucu = fis_verilerini_ayıkla(test_gorseli)
        print("\n--- YAPAY ZEKA ÇIKTISI (JSON) ---")
        print(analiz_sonucu)
    else:
        print(f"\nLütfen proje klasörüne '{test_gorseli}' adında bir örnek fotoğraf koyun veya kodu düzenleyin.")