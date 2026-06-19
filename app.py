import streamlit as st
import yfinance as yf
import pandas as pd
import google.generativeai as genai
import plotly.express as px

# --- 1. YAPAY ZEKA VE SAYFA AYARLARI ---
GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
genai.configure(api_key=GEMINI_API_KEY)

st.set_page_config(page_title="Buffett AI Pro", layout="wide", page_icon="🚀")

# --- SMART PEER MAPPING (Akıllı Rakip Eşleştirme) ---
RAKIP_HARITASI = {
    "AAPL": ["MSFT", "GOOGL", "META"],
    "KO": ["PEP", "MNST", "KDP"],
    "NVDA": ["AMD", "INTC", "AVGO"],
    "PEP": ["KO", "MNST", "KDP"],
    "MSFT": ["AAPL", "GOOGL", "AMZN"],
    "GOOGL": ["MSFT", "META", "AMZN"],
    "TSLA": ["BYDDF", "F", "GM"]
}

# --- HELPER FONKSİYONLAR ---
def dcf_degerleme_hesapla(info):
    try:
        serbest_nakit_akisi = info.get("freeCashflow")
        hise_sayisi = info.get("sharesOutstanding")
        toplam_nakit = info.get("totalCash", 0)
        toplam_borc = info.get("totalDebt", 0)
        
        if not serbest_nakit_akisi or not hise_sayisi or serbest_nakit_akisi <= 0:
            return None, None
        
        buyume_orani = 0.10
        iskonto_orani = 0.09
        kalici_buyume = 0.02
        
        toplam_indirgenmis_deger = 0
        guncel_nakit = serbest_nakit_akisi
        for yil in range(1, 6):
            guncel_nakit = guncel_nakit * (1 + buyume_orani)
            indirgenmis_nakit = guncel_nakit / ((1 + iskonto_orani) ** yil)
            toplam_indirgenmis_deger += indirgenmis_nakit
            
        terminal_deger = (guncel_nakit * (1 + kalici_buyume)) / (iskonto_orani - kalici_buyume)
        indirgenmis_terminal_deger = terminal_deger / ((1 + iskonto_orani) ** 5)
        
        toplam_sirket_degeri = toplam_indirgenmis_deger + indirgenmis_terminal_deger
        ozsermaye_degeri = toplam_sirket_degeri + toplam_nakit - toplam_borc
        icsel_deger = ozsermaye_degeri / hise_sayisi
        guncel_fiyat = info.get("currentPrice", 1)
        guvenlik_marji = ((icsel_deger - guncel_fiyat) / icsel_deger) * 100
        
        return round(icsel_deger, 2), round(guvenlik_marji, 2)
    except:
        return None, None

def yapay_zeka_buffett_analizi(sirket_adi, sektor, is_tanimi):
    prompt = f"""
    Sen Warren Buffett tarzında düşünen kıdemli bir değer yatırımı analistisin.
    Şirket Adı: {sirket_adi} | Sektör: {sektor}
    İş Tanımı: {is_tanimi}
    Lütfen bu şirketi Ekonomik Hendek, Anlaşılabilirlik ve Genel Buffett Kararı açısından 3 kısa başlıkla analiz et. Türkçe olsun.
    """
    try:
        # 1. BÖLGE: Model tanımı güncel 'gemini-2.0-flash' olarak değiştirildi
        model = genai.GenerativeModel('gemini-2.0-flash')
        response = model.generate_content(prompt)
        if response and hasattr(response, 'text') and response.text:
            return response.text.strip()
        return None
    except Exception as e:
        return f"AI Raporu Hatası: {e}"

def rakip_verilerini_topla(ana_ticker, rakipler):
    veriler = []
    tum_hisseler = [ana_ticker] + rakipler
    for t in tum_hisseler:
        try:
            h = yf.Ticker(t)
            inf = h.info
            veriler.append({
                "Hisse": t,
                "Şirket Adı": inf.get("shortName", t),
                "ROE (%)": round(inf.get("returnOnEquity", 0) * 100, 1) if inf.get("returnOnEquity") else "Veri Yok",
                "Brüt Marj (%)": round(inf.get("grossMargins", 0) * 100, 1) if inf.get("grossMargins") else "Veri Yok",
                "F/K Oranı": round(inf.get("trailingPE", 0), 1) if inf.get("trailingPE") else "Veri Yok",
                "Fiyat ($)": inf.get("currentPrice", "Veri Yok")
            })
        except:
            continue
    return pd.DataFrame(veriler)

# --- 3. STREAMLIT ARAYÜZÜ ---
st.title("🚀 Buffett AI Pro: Finansal Analiz & Tarama Dünyası")

# Sayfayı iki sekmeye ayırıyoruz
sekme1, sekme2 = st.tabs(["🔍 Tek Hisse Analizi & Rakipler", "🏆 NASDAQ Alım Gücü Tarayıcısı"])

# --- SEKME 1: TEK HİSSE DETAYLI ANALİZ ---
with sekme1:
    st.markdown("Bu panel finansal filtreleme, interaktif teknik grafikler ve sektörel rakip kıyaslamasını anlık olarak yapar.")
    ticker = st.text_input("Hisse Sembolü Girin:", value="AAPL", key="tek_hisse_input").strip().upper()

    if st.button("Kapsamlı Analizi Başlat", key="btn_tek_hisse"):
        with st.spinner("Finansal tablolar inceleniyor, rakipler taranıyor ve AI raporu hazırlanıyor..."):
            try:
                hisse = yf.Ticker(ticker)
                info = hisse.info
                
                if not info or "currentPrice" not in info:
                    st.error("Hisse bulunamadı. Lütfen sembolü kontrol edin.")
                else:
                    sirket_adi = info.get("longName", ticker)
                    sektor = info.get("sector", "Bilinmiyor")
                    guncel_fiyat = info.get("currentPrice", 0)
                    roe_yuzde = (info.get("returnOnEquity", 0) * 100) if info.get("returnOnEquity") else 0
                    marj_yuzde = (info.get("grossMargins", 0) * 100) if info.get("grossMargins") else 0
                    fk = info.get("trailingPE", "Veri Yok")
                    
                    st.header(f"📊 {sirket_adi} ({ticker}) Finansal Sağlık")
                    c1, c2, c3, c4 = st.columns(4)
                    c1.metric("Anlık Fiyat", f"{guncel_fiyat} $")
                    c2.metric("Özsermaye Karlılığı (ROE)", f"%{roe_yuzde:.1f}", delta="Hedef >= %15" if roe_yuzde >= 15 else "Zayıf")
                    c3.metric("Brüt Kar Marjı", f"%{marj_yuzde:.1f}", delta="Hedef >= %40" if marj_yuzde >= 40 else "Zayıf")
                    c4.metric("F/K Oranı", f"{fk:.1f}" if type(fk) in [float, int] else fk)
                    
                    st.divider()
                    
                    st.subheader("📈 1 Yıllık İnteraktif Fiyat Hareketi")
                    gecmis_veri = hisse.history(period="1y")
                    if not gecmis_veri.empty:
                        fig = px.line(gecmis_veri, x=gecmis_veri.index, y="Close", 
                                      labels={"x": "Tarih", "Close": "Kapanış Fiyatı ($)"},
                                      title=f"{ticker} Son 1 Yıl Trendi")
                        fig.update_traces(line_color="#1f77b4", line_width=2)
                        st.plotly_chart(fig, use_container_width=True)
                    
                    st.divider()
                    
                    st.subheader("⚔️ Sektörel Rakip Kıyaslama Tablosu")
                    rakipler = RAKIP_HARITASI.get(ticker, ["MSFT", "GOOGL", "AMZN"])
                    rakip_df = rakip_verilerini_topla(ticker, rakipler)
                    st.dataframe(rakip_df, use_container_width=True, hide_index=True)
                    
                    st.divider()
                    
                    col_sol, col_sag = st.columns(2)
                    
                    with col_sol:
                        st.subheader("🪙 İçsel Değer (DCF Modeli)")
                        icsel_deger, guvenlik_marji = dcf_degerleme_hesapla(info)
                        if icsel_deger is not None:
                            st.write(f"**Şirketin Olması Gereken Gerçek Ederi:** {icsel_deger} $")
                            if guvenlik_marji > 0:
                                st.success(f"🎉 Güvenlik Marjı: %{guvenlik_marji} UCUZ!")
                            else:
                                st.error(f"⚠️ Güvenlik Marjı: %{guvenlik_marji} PAHALI!")
                        else:
                            st.info("Nakit akışları yetersiz olduğundan veya eksik veriden dolayı DCF hesaplanamadı.")
                            
                    with col_sag:
                        st.subheader("🤖 Yapay Zeka Buffett Raporu")
                        ai_raporu = yapay_zeka_buffett_analizi(sirket_adi, sektor, info.get("longBusinessSummary", ""))
                        if ai_raporu:
                            st.info(ai_raporu)
                        else:
                            st.warning("⚠️ Yapay zeka analizi şu an üretilemedi. Kota sınırını veya model ismini kontrol edin.")
                            
            except Exception as e:
                st.error(f"Veriler okunurken teknik bir sorun oluştu: {e}")

# --- SEKME 2: TÜM NASDAQ BORSASI ALIM GÜCÜ TARAYICISI ---
with sekme2:
    st.header("🏆 NASDAQ Değer Odaklı Alım Gücü Tarayıcısı")
    st.write("Aşağıdaki sistem NASDAQ borsasındaki lider dev şirketleri anlık rasyolarına göre filtreler ve en yüksek alım gücü puanına göre sıralar.")
    
    if st.button("NASDAQ Borsasını Tara ve Sırala", key="btn_nasdaq_tarayici"):
        NASDAQ_HAVUZU = ["AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "TSLA", "AVGO", "COST", "NFLX", "AMD", "PEP", "INTC", "QCOM", "TXN"]
        
        tarama_sonuclari = []
        ilerleme_cubugu = st.progress(0)
        
        for index, sembol in enumerate(NASDAQ_HAVUZU):
            try:
                hisse = yf.Ticker(sembol)
                info = hisse.info
                
                roe = info.get('returnOnEquity', 0) * 100
                brut_marj = info.get('grossMargins', 0) * 100
                fk = info.get('trailingPE', 0)
                fiyat = info.get('currentPrice', 0)
                
                if fk and fk > 0:
                    alim_gucu_puani = (roe * 0.5) + (brut_marj * 0.5) - (fk * 0.1)
                else:
                    alim_gucu_puani = (roe * 0.5) + (brut_marj * 0.5)
                
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
            ilerleme_cubugu.progress((index + 1) / len(NASDAQ_HAVUZU))
            
        df = pd.DataFrame(tarama_sonuclari)
        if not df.empty:
            df = df.sort_values(by="Alım Gücü Puanı", ascending=False).reset_index(drop=True)
            
            st.subheader("🥇 Algoritmik Alım Gücü Sıralama Sonuçları")
            st.dataframe(df, use_container_width=True, hide_index=True)
            
            # Şampiyonu AI'ye yorumlatma
            en_iyi_hisse = df.iloc[0]["Hisse"]
            en_iyi_ad = df.iloc[0]["Şirket Adı"]
            en_iyi_puan = df.iloc[0]["Alım Gücü Puanı"]
            
            st.success(f"🏆 Tarama Şampiyonu: **{en_iyi_ad} ({en_iyi_hisse})** - Puan: {en_iyi_puan}")
            
            with st.spinner(f"Yapay Zeka, günün şampiyonu {en_iyi_hisse} için özel analiz hazırlıyor..."):
                # Rapor oluşturma işlemini bir butona bağlıyoruz
if st.button(f"🤖 {en_iyi_hisse} İçin Yapay Zeka Buffett Raporu Oluştur"):
    with st.spinner(f"Yapay Zeka, günün şampiyonu {en_iyi_hisse} için özel analiz hazırlıyor..."):
        try:
            prompt_top = f"NASDAQ taramasında ROE, Brüt Marj ve F/K dengesine göre en yüksek puanı {en_iyi_ad} ({en_iyi_hisse}) aldı. Bu şirketin finansallarını yorumla..."
            model = genai.GenerativeModel('gemini-2.0-flash')
            cevap = model.generate_content(prompt_top)
            st.info(cevap.text)
        except Exception as ai_err:
            st.error(f"AI Raporu oluşturulamadı: {ai_err}")
                try:
                    prompt_top = f"NASDAQ taramasında ROE, Brüt Marj ve F/K dengesine göre en yüksek puanı {en_iyi_ad} ({en_iyi_hisse}) aldı. Bu şirketin neden lider çıktığını ve geleceğini yatırımcı gözüyle yorumla."
                    # 2. BÖLGE: Model tanımı güncel 'gemini-2.0-flash' olarak değiştirildi
                    model = genai.GenerativeModel('gemini-2.0-flash')
                    cevap = model.generate_content(prompt_top)
                    st.info(cevap.text)
                except Exception as ai_err:
                    st.error(f"AI Raporu oluşturulamadı: {ai_err}")
        else:
            st.error("Borsa verileri çekilemedi. Lütfen bağlantınızı kontrol edin.")
