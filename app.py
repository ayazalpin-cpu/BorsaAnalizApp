import streamlit as str
import yfinance as yf
import pandas as pd
import google.generativeai as genai
import plotly.express as px

# --- 1. YAPAY ZEKA AYARLARI ---
GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

st.set_page_config(page_title="Buffett AI Pro", layout="wide", page_icon="🚀")

# --- SEKME (TAB) YAPISI ---
sekme1, sekme2 = st.tabs(["🔍 Tek Hisse Analizi", "🏆 NASDAQ Alım Gücü Tarayıcısı"])

# =====================================================================
# SEKME 1: MEVCUT TEK HİSSE ANALİZ SİSTEMİNİZ
# =====================================================================
with sekme1:
    st.title("🚀 Buffett AI Pro: Canlı Grafik ve Analiz Paneli")
    hisse_sembolu = st.text_input("Hisse Sembolü Girin:", value="AAPL", key="tek_hisse").upper()
    
    if st.button("Kapsamlı Analizi Başlat"):
        with st.spinner("Veriler getiriliyor..."):
            try:
                hisse = yf.Ticker(hisse_sembolu)
                info = hisse.info
                
                # Finansal Veriler
                ad = info.get('longName', hisse_sembolu)
                fiyat = info.get('currentPrice', 0)
                roe = info.get('returnOnEquity', 0) * 100
                brut_marj = info.get('grossMargins', 0) * 100
                fk = info.get('trailingPE', 0)
                
                st.subheader(f"📊 {ad} ({hisse_sembolu}) Finansal Sağlık")
                col1, col2, col3, col4 = st.columns(4)
                col1.metric("Anlık Fiyat", f"{fiyat} $")
                col2.metric("Özsermaye Karlılığı (ROE)", f"%{roe:.1f}")
                col3.metric("Brüt Kar Marjı", f"%{brut_marj:.1f}")
                col4.metric("F/K Oranı", f"{fk:.1f}" if fk else "N/A")
                
                # Grafik
                veriler = hisse.history(period="1y")
                fig = px.line(veriler, x=veriler.index, y="Close", title=f"{hisse_sembolu} Son 1 Yıl Trendi")
                st.plotly_chart(fig, use_container_width=True)
                
                # AI Yorumu
                st.subheader("🤖 Yapay Zeka Buffett Raporu")
                prompt = f"{ad} hissesinin ROE'si %{roe:.1f}, Brüt Marjı %{brut_marj:.1f} ve F/K'sı {fk}. Warren Buffett tarzında kısa bir yorum yap."
                cevap = model.generate_content(prompt)
                st.write(cevap.text)
                
            except Exception as e:
                st.error(f"Hata oluştu: {e}")

# =====================================================================
# SEKME 2: YENİ NASDAQ ALIM GÜCÜ TARAYICISI
# =====================================================================
with sekme2:
    st.title("🏆 NASDAQ Değer Odaklı Alım Gücü Tarayıcısı")
    st.write("Aşağıdaki buton NASDAQ'ın dev şirketlerini anlık olarak filtreler, puanlar ve en cazip olanları sıralar.")
    
    # Tarama havuzu (Geliştirilebilir popüler NASDAQ hisseleri listesi)
    NASDAQ_HAVUZU = ["AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "TSLA", "AVGO", "COST", "NFLX", "AMD", "PEP", "INTC", "QCOM", "TXN"]
    
    if st.button("NASDAQ Borsasını Tara ve Sırala"):
        tarama_sonuclari = []
        ilerleme_barı = st.progress(0)
        
        for index, sembol in enumerate(NASDAQ_HAVUZU):
            try:
                hisse = yf.Ticker(sembol)
                info = hisse.info
                
                roe = info.get('returnOnEquity', 0) * 100
                brut_marj = info.get('grossMargins', 0) * 100
                fk = info.get('trailingPE', 0)
                fiyat = info.get('currentPrice', 0)
                
                # Basit bir "Alım Gücü / Buffett Puanı" Algoritması:
                # Yüksek ROE ve Yüksek Brüt Marj istenir, Düşük F/K avantajdır.
                if fk and fk > 0:
                    alim_gucu_puani = (roe * 0.5) + (brut_marj * 0.5) - (fk * 0.1)
                else:
                    alim_gucu_puani = (roe * 0.5) + (brut_marj * 0.5) # F/K yoksa nötr kabul et
                
                tarama_sonuclari.append({
                    "Hisse": sembol,
                    "Şirket Adı": info.get('shortName', sembol),
                    "Fiyat ($)": fiyat,
                    "ROE (%)": round(roe, 1),
                    "Brüt Marj (%)": round(brut_marj, 1),
                    "F/K Oranı": round(fk, 1) if fk else "N/A",
                    "Alım Gücü Puanı": round(alim_gucu_puani, 1)
                })
            except:
                continue
            ilerleme_barı.progress((index + 1) / len(NASDAQ_HAVUZU))
            
        # Verileri DataFrame'e dönüştür ve puana göre sırala
        df = pd.DataFrame(tarama_sonuclari)
        df = df.sort_values(by="Alım Gücü Puanı", ascending=False).reset_index(drop=True)
        
        st.subheader("🥇 Algoritmik Sıralama Sonuçları")
        st.dataframe(df, use_container_width=True)
        
        # Şampiyon Şirketi AI'ye Analiz Ettirme
        if not df.empty:
            en_iyi_hisse = df.iloc[0]["Hisse"]
            en_iyi_ad = df.iloc[0]["Şirket Adı"]
            en_iyi_puan = df.iloc[0]["Alım Gücü Puanı"]
            
            st.success(f"🏆 Tarama Şampiyonu: **{en_iyi_ad} ({en_iyi_hisse})** - Puan: {en_iyi_puan}")
            
            with st.spinner(f"Yaypay Zeka, günün şampiyonu {en_iyi_hisse} için alım gücü raporu hazırlıyor..."):
                try:
                    prompt = f"NASDAQ taramasında ROE, Brüt Marj ve F/K dengesine göre en yüksek puanı {en_iyi_ad} ({en_iyi_hisse}) aldı. Bu şirketin neden lider çıktığını ve geleceğini yatırımcı gözüyle yorumla."
                    cevap = model.generate_content(prompt)
                    st.info(cevap.text)
                except Exception as ai_err:
                    st.error(f"AI Raporu oluşturulamadı: {ai_err}")
