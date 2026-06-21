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
        # İsim kontrolünü butonun hemen içinde yapıyoruz ki Streamlit atlama yapmasın
        if not satisci_adi.strip():
            str_app.error("Lütfen işlem yapmadan önce adınızı ve soyadınızı girin!")
        else:
            gecici_yol = "gecici_gorsel.jpeg"
            gorsel.save(gecici_yol)
            
            with str_app.spinner("Yapay zeka analiz ediyor, lütfen bekleyin..."):
                try:
                    analiz_sonucu_metin = fis_verilerini_ayıkla(gecici_yol)
                    
                    # Markdown temizliği (Eğer yapay zeka ```json ... ``` formatında döndüyse temizle)
                    temiz_metin = analiz_sonucu_metin.strip()
                    if temiz_metin.startswith("```"):
                        temiz_metin = temiz_metin.split("```")[1]
                        if temiz_metin.startswith("json"):
                            temiz_metin = temiz_metin[4:]
                    
                    analiz_sonucu = json.loads(temiz_metin)
                    
                    # --- ESNEK VERİ YAKALAMA ALGORİTMASI ---
                    sirket_adi = analiz_sonucu.get('Şiriket Adı') or analiz_sonucu.get('Şirket Adı') or analiz_sonucu.get('Şirket adı') or analiz_sonucu.get('sirket_adi') or 'Bulunamadı'
                    tarih = analiz_sonucu.get('Tarih') or analiz_sonucu.get('tarih') or analiz_sonucu.get('Fiş Tarihi') or analiz_sonucu.get('fiş tarihi') or 'Bulunamadı'
                    toplam_tutar = analiz_sonucu.get('Toplam Tutar') or analiz_sonucu.get('Toplam tutar') or analiz_sonucu.get('toplam_tutar') or 'Bulunamadı'
                    
                    kdv_orani = analiz_sonucu.get('KDV Oranı') or analiz_sonucu.get('KDV oranı') or analiz_sonucu.get('kdv_orani') or 'Bulunamadı'
                    if isinstance(kdv_orani, list) and len(kdv_orani) > 0:
                        kdv_orani = kdv_orani[0]
                    
                    kdv_tutari = analiz_sonucu.get('KDV Tutarı') or analiz_sonucu.get('KDV tutarı') or analiz_sonucu.get('kdv_tutari') or 'Bulunamadı'
                    gercek_numara = analiz_sonucu.get('Fiş Numarası') or analiz_sonucu.get('Fiş numarası') or analiz_sonucu.get('Belge No') or analiz_sonucu.get('fis_numarasi') or 'Bulunamadı'
                    # ----------------------------------------
                    
                    # --- EXCEL KAYIT MANTIĞI ---
                    excel_dosya_adi = "saha_giderleri.xlsx"
                    sisteme_kayit_tarihi = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    
                    yeni_veri = {
                        "Sisteme Kayıt Tarihi": [sisteme_kayit_tarihi],
                        "Satış Temsilcisi": [satisci_adi],
                        "Kategori": [secilen_kategori],
                        "Açıklama": [harcama_aciklamasi if harcama_aciklamasi else "Belirtilmedi"],
                        "Şirket Adı": [sirket_adi],
                        "Fiş Tarihi": [tarih],
                        "Toplam Tutar (TL)": [toplam_tutar],
                        "KDV Oranı": [kdv_orani],
                        "KDV Tutarı (TL)": [kdv_tutari],
                        "Belge No": [gercek_numara]
                    }
                    
                    df_yeni = pd.DataFrame(yeni_veri)
                    
                    if os.path.exists(excel_dosya_adi):
                        df_eski = pd.read_excel(excel_dosya_adi)
                        df_son = pd.concat([df_eski, df_yeni], ignore_index=True)
                    else:
                        df_son = df_yeni
                    
                    df_son.to_excel(excel_dosya_adi, index=False)
                    # ----------------------------
                    
                    str_app.success("İşlem başarıyla okundu ve Excel dosyasına satır olarak kaydedildi! 📊✅")
                    
                    # Ekran Çıktısı (Kullanıcı Görebilsin Diye)
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
                    
                    # Güncel Excel tablosunu canlı önizleme olarak basalım
                    str_app.markdown("### 📋 Güncel Gider Tablosu (Excel Verisi)")
                    str_app.dataframe(df_son)
                    
                except Exception as e:
                    str_app.error(f"Veri çözümlenirken bir hata oluştu: {e}")
                    if 'analiz_sonucu_metin' in locals():
                        str_app.info("Yapay Zekadan Gelen Ham Metin:")
                        str_app.code(analiz_sonucu_metin)
                finally:
                    if os.path.exists(gecici_yol):
                        os.remove(gecici_yol)
