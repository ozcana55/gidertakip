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
        if not satisci_adi.strip():
            str_app.error("Lütfen işlem yapmadan önce adınızı ve soyadınızı girin!")
        else:
            gecici_yol = "gecici_gorsel.jpeg"
            gorsel.save(gecici_yol)
            
            with str_app.spinner("Yapay zeka analiz ediyor ve gerçek Excel dosyasına yazıyor..."):
                try:
                    analiz_sonucu_metin = fis_verilerini_ayıkla(gecici_yol)
                    
                    temiz_metin = analiz_sonucu_metin.strip()
                    if temiz_metin.startswith("```"):
                        temiz_metin = temiz_metin.split("```")[1]
                        if temiz_metin.startswith("json"):
                            temiz_metin = temiz_metin[4:]
                    
                    analiz_sonucu = json.loads(temiz_metin)
                    
                    if "hata" in analiz_sonucu:
                        str_app.error(analiz_sonucu["hata"])
                    else:
                        # Verileri Ayıklama
                        sirket_adi = analiz_sonucu.get('1. Şirket Adı') or analiz_sonucu.get('Şirket Adı') or analiz_sonucu.get('Şirket adı') or 'Bulunamadı'
                        tarih = analiz_sonucu.get('2. Tarih') or analiz_sonucu.get('Tarih') or analiz_sonucu.get('tarih') or 'Bulunamadı'
                        toplam_tutar = analiz_sonucu.get('3. Toplam Tutar') or analiz_sonucu.get('Toplam Tutar') or 'Bulunamadı'
                        
                        kdv_orani = analiz_sonucu.get('4. KDV Oranı') or analiz_sonucu.get('KDV Oranı') or 'Bulunamadı'
                        if isinstance(kdv_orani, list) and len(kdv_orani) > 0:
                            kdv_orani = kdv_orani[0]
                        
                        kdv_tutari = analiz_sonucu.get('5. KDV Tutarı') or analiz_sonucu.get('KDV Tutarı') or 'Bulunamadı'
                        gercek_numara = analiz_sonucu.get('6. Fiş Numarası') or analiz_sonucu.get('Fiş Numarası') or analiz_sonucu.get('Belge No') or 'Bulunamadı'
                        
                        # --- DOĞRUDAN EXCEL DOSYASINA YAZMA MANTIĞI ---
                        excel_dosya_adi = "saha_giderleri.xlsx"
                        sisteme_kayit_tarihi = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        
                        yeni_satir = {
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
                        
                        df_yeni = pd.DataFrame(yeni_satir)
                        
                        # Klasördeki gerçek saha_giderleri.xlsx dosyasını kontrol et ve üzerine ekle
                        if os.path.exists(excel_dosya_adi):
                            try:
                                df_eski = pd.read_excel(excel_dosya_adi)
                                df_son = pd.concat([df_eski, df_yeni], ignore_index=True)
                            except Exception:
                                # Eğer Excel dosyası boş veya bozuksa doğrudan yenisini temel al
                                df_son = df_yeni
                        else:
                            df_son = df_yeni
                        
                        # VERİYİ GERÇEK DOSYAYA KAYDEDİYORUZ (Açık olan Excel sayfasına yazılır)
                        df_son.to_excel(excel_dosya_adi, index=False)
                        
                        str_app.success("İşlem başarıyla tamamlandı! Veriler 'saha_giderleri.xlsx' dosyasına kalıcı olarak kaydedildi. 📊✅")
                        
                        # Önizleme ekranı
                        str_app.subheader("📊 Son Eklenen Fiş Bilgileri")
                        str_app.write(f"**Şirket Adı:** {sirket_adi}")
                        str_app.write(f"**Fiş Tarihi:** {tarih}")
                        str_app.write(f"**Toplam Tutar:** {toplam_tutar} TL")
                        str_app.write(f"**Belge No:** {gercek_numara}")
                        
                        str_app.markdown("### 📋 Güncel Gider Tablosu Önizlemesi")
                        str_app.dataframe(df_son)
                        
                except Exception as e:
                    str_app.error(f"Excel dosyasına yazılırken teknik bir hata oluştu: {e}")
                finally:
                    if os.path.exists(gecici_yol):
                        os.remove(gecici_yol)
