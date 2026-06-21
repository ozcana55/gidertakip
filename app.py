import streamlit as str_app
import os
from PIL import Image
from fis_okuyucu import fis_verilerini_ayıkla
import json
import pandas as pd
from datetime import datetime

# API Anahtarı Kontrolü
if "GEMINI_API_KEY" in str_app.secrets:
    str_app.sidebar.success("API Anahtarı başarıyla algılandı!")
else:
    str_app.sidebar.error("HATA: API Anahtarı bulunamadı! Lütfen Secrets panelini kontrol edin.")

str_app.set_page_config(page_title="Saha Gider Takip Sistemi", page_icon="📱", layout="centered")

str_app.title("📱 Saha Gider Takip Sistemi")
str_app.write("Hoş geldiniz! Lütfen harcamanıza ait fiş veya faturanın fotoğrafını yükleyin.")
str_app.markdown("---")

# Kullanıcı Bilgileri ve Kategoriler
satisci_adi = str_app.text_input("Satış Temsilcisi Adı Soyadı:", placeholder="Örn: Ahmet Yılmaz")

kategoriler = [
    "Yakıt Gideri", 
    "Kırtasiye", 
    "Yemek / Temsil Ağırlama", 
    "Hediye / İkram", 
    "Araç Gideri / Bakım", 
    "Konaklama",
    "Otopark / Otoban / Köprü",
    "Kargo / Posta",
    "Ofis / Genel Gider",
    "Diğer"
]
secilen_kategori = str_app.selectbox("Harcama Kategorisi Seçin:", kategoriler)

harcama_aciklamasi = str_app.text_input(
    "Harcama Açıklaması (Maksimum 90 Karakter):", 
    max_chars=90, 
    placeholder="Örn: Müşteri ziyareti otopark ücreti"
)

yuklenen_dosya = str_app.file_uploader("Fiş / Fatura Fotoğrafı Seçin", type=["jpg", "jpeg", "png"])

if yuklenen_dosya is not None:
    gorsel = Image.open(yuklenen_dosya)
    str_app.image(gorsel, caption="Yüklenen Görsel", use_container_width=True)
    
    if str_app.button("Fişi İşle ve Gönder 🚀"):
        # Boş isim kontrolü
        if not satisci_adi.strip():
            str_app.error("Lütfen işlem yapmadan önce adınızı ve soyadınızı girin!")
        else:
            gecici_yol = "gecici_gorsel.jpeg"
            gorsel.save(gecici_yol)
            
            with str_app.spinner("Yapay zeka analiz ediyor ve Excel'e kaydediyor..."):
                try:
                    # 1. Yapay zekadan analiz sonucunu alıyoruz
                    analiz_sonucu_metin = fis_verilerini_ayıkla(gecici_yol)
                    
                    # Markdown temizliği (Eğer ```json ... ``` formatında geldiyse ayıklıyoruz)
                    temiz_metin = analiz_sonucu_metin.strip()
                    if temiz_metin.startswith("```"):
                        temiz_metin = temiz_metin.split("```")[1]
                        if temiz_metin.startswith("json"):
                            temiz_metin = temiz_metin[4:]
                    
                    analiz_sonucu = json.loads(temiz_metin)
                    
                    # --- ESNEK VERİ YAKALAMA (Prompt Anahtarlarına Göre) ---
                    sirket_adi = analiz_sonucu.get('1. Şirket Adı') or analiz_sonucu.get('Şirket Adı') or analiz_sonucu.get('Şirket adı') or 'Bulunamadı'
                    tarih = analiz_sonucu.get('2. Tarih') or analiz_sonucu.get('Tarih') or analiz_sonucu.get('tarih') or 'Bulunamadı'
                    toplam_tutar = analiz_sonucu.get('3. Toplam Tutar') or analiz_sonucu.get('Toplam Tutar') or 'Bulunamadı'
                    
                    kdv_orani = analiz_sonucu.get('4. KDV Oranı') or analiz_sonucu.get('KDV Oranı') or 'Bulunamadı'
                    if isinstance(kdv_orani, list) and len(kdv_orani) > 0:
                        kdv_orani = kdv_orani[0]
                    
                    kdv_tutari = analiz_sonucu.get('5. KDV Tutarı') or analiz_sonucu.get('KDV Tutarı') or 'Bulunamadı'
                    gercek_numara = analiz_sonucu.get('6. Fiş Numarası') or analiz_sonucu.get('Fiş Numarası') or analiz_sonucu.get('Belge No') or 'Bulunamadı'
                    # -----------------------------------------------------
                    
                    # --- EXCEL KAYIT MANTIĞI ---
                    excel_dosya_adi = "saha_giderleri.xlsx"
                    sisteme_kayit_tarihi = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    
                    # Sizin Excel dosyanızdaki sütun isimleriyle birebir eşleşen yeni satır yapısı
                    yeni_veri = {
                        "Sisteme Kayıt Tarihi": [sisteme_kayit_tarihi],
                        "Satış Temsilcisi": [satisci_adi],
                        "Kategori": [secilen_kategori],
                        "Açıklama": [harcama_aciklamasi if harcama_aciklamasi else "Belirtilmedi"],
                        "Şirket Adı": [sirket_adi],
                        "Fiş Tarihi": [tarih],
                        "Toplam Tutar": [toplam_tutar],
                        "KDV Oranı": [kdv_orani],
                        "KDV Tutarı": [kdv_tutari],
                        "Belge No": [gercek_numara]
                    }
                    
                    df_yeni = pd.DataFrame(yeni_veri)
                    
                    if os.path.exists(excel_dosya_adi):
                        df_eski = pd.read_excel(excel_dosya_adi)
                        # Tablonun altına yeni kaydı ekliyoruz
                        df_son = pd.concat([df_eski, df_yeni], ignore_index=True)
                    else:
                        df_son = df_yeni
                    
                    # Değişiklikleri tam hedeflediğiniz Excel dosyasına kaydediyoruz
                    df_son.to_excel(excel_dosya_adi, index=False)
                    # ----------------------------
                    
                    str_app.success("İşlem başarıyla okundu ve Excel dosyasına kaydedildi! 📊✅")
                    
                    # Arayüz Bilgi Ekranı
                    str_app.subheader("📊 Ayıklanan Muhasebe Bilgileri")
                    str_app.write(f"**Yükleyen Satışçı:** {satisci_adi}")
                    str_app.write(f"**Harcama Kategorisi:** {secilen_kategori}")
                    str_app.write(f"**Harcama Açıklaması:** {harcama_aciklamasi if harcama_aciklamasi else 'Belirtilmedi'}")
                    str_app.markdown("---")
                    
                    str_app.write(f"**Şirket Adı:** {sirket_adi}")
                    str_app.write(f"**Fiş Tarihi:** {tarih}")
                    str_app.write(f"**Toplam Tutar:** {toplam_tutar} TL")
                    str_app.write(f"**KDV Oranı:** {kdv_orani}")
                    str_app.write(f"**KDV Tutarı:** {kdv_tutari} TL")
                    str_app.write(f"**Belge No:** {gercek_numara}")
                    
                    # Excel tablosunun güncel halini canlı önizleme olarak Streamlit'e basalım
                    str_app.markdown("### 📋 Güncel Gider Tablosu (saha_giderleri.xlsx)")
                    str_app.dataframe(df_son)
                    
                except Exception as e:
                    str_app.error(f"Veri çözümlenirken veya Excel'e yazılırken bir hata oluştu: {e}")
                    if 'analiz_sonucu_metin' in locals():
                        str_app.info("Yapay Zekadan Gelen Ham Çıktı:")
                        str_app.code(analiz_sonucu_metin)
                finally:
                    if os.path.exists(gecici_yol):
                        os.remove(gecici_yol)

elif yuklenen_dosya is not None and satisci_adi == "":
    str_app.warning("Lütfen işlem yapmadan önce adınızı ve soyadınızı girin.")
