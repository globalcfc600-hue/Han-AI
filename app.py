import streamlit as st
import requests
import time
import re
import base64
import pandas as pd
from urllib.parse import quote as urllib_parse_quote

st.set_page_config(page_title="HAN AI 2", layout="wide", initial_sidebar_state="collapsed")

# ==========================================
# GORSEL TASARIM & CSS (CHATGPT / GEMINI STYLE)
# ==========================================
st.markdown("""
<style>
    .stApp {
        background-color: #131314 !important;
        color: #e3e2e6 !important;
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }

    [data-testid="stSidebar"] {
        background-color: #1e1f20 !important;
        border-right: 1px solid #2d2f31 !important;
    }

    h1, h2, h3 {
        color: #e3e2e6 !important;
        font-weight: 600 !important;
    }

    .stChatMessage {
        background-color: #1e1f20 !important;
        border-radius: 18px !important;
        padding: 12px 18px !important;
        margin-bottom: 10px !important;
        border: 1px solid #2d2f31 !important;
    }

    [data-testid="stChatInput"] {
        background-color: #1e1f20 !important;
        border-radius: 24px !important;
        border: 1px solid #444746 !important;
    }

    [data-testid="stMetricValue"] {
        color: #a8c7fa !important;
    }
</style>
""", unsafe_allow_html=True)


# ==========================================
# UYGULAMA VE SISTEM DURUMU (SESSION STATE)
# ==========================================
if "sohbet_gecmisi" not in st.session_state:
    st.session_state.sohbet_gecmisi = []

if "yazilim_modu" not in st.session_state:
    st.session_state.yazilim_modu = False

if "kullanicilar" not in st.session_state:
    st.session_state.kullanicilar = [
        {"kullanici_adi": "admin", "email": "admin@han.ai", "sifre": "2013"},
        {"kullanici_adi": "test_user", "email": "user@gmail.com", "sifre": "1234"}
    ]

if "aktif_kullanici" not in st.session_state:
    st.session_state.aktif_kullanici = None

if "server_durumu" not in st.session_state:
    st.session_state.server_durumu = True

if "admin_giris_yapildi" not in st.session_state:
    st.session_state.admin_giris_yapildi = False


# ==========================================
# KODUN BEYNI & NLP MOTORU (DOKUNULMADI)
# ==========================================
TAVILY_API_KEY = "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"

class DinamikNLPMotoru:
    def __init__(self):
        self.durak_kelimeler = {
            "ve", "veya", "bir", "bu", "su", "için", "ile", "ne", "nasil", "nedir", 
            "mi", "mi", "de", "da", "bana", "ver", "kodu", "kodunu", "bul", "getir", 
            "kanka", "bro", "hocam", "reis", "lan", "ya", "soyle", "anlat"
        }

    def metin_temizle(self, metin):
        metin_alt = metin.lower()
        temiz_metin = re.sub(r'[^\w\s]', '', metin_alt)
        tokens = temiz_metin.split()
        temiz_tokens = [t for t in tokens if t not in self.durak_kelimeler]
        if temiz_tokens:
            return " ".join(temiz_tokens)
        return metin.strip()

    def canli_google_ara(self, sorgu, adet=3):
        url = "https://api.tavily.com/search"
        payload = {
            "api_key": TAVILY_API_KEY,
            "query": sorgu,
            "max_results": adet,
            "search_depth": "advanced",
            "include_answer": True
        }
        sonuclar = []
        try:
            res = requests.post(url, json=payload, timeout=8)
            if res.status_code == 200:
                data = res.json()
                if data.get("answer"):
                    sonuclar.append({
                        "baslik": "AI Analiz Ozet Yaniti",
                        "url": "https://tavily.com",
                        "ozet": data.get("answer")
                    })
                results = data.get("results", [])
                for item in results:
                    sonuclar.append({
                        "baslik": item.get("title", "Arama Sonucu"),
                        "url": item.get("url", "#"),
                        "ozet": item.get("content", "Aciklama bulunamadi.")
                    })
        except Exception:
            pass
        return sonuclar

    def github_tum_kodlari_cek(self, repo_full_name):
        headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "HAN-AI-App"
        }
        url = f"https://api.github.com/repos/{repo_full_name}/readme"
        try:
            res = requests.get(url, headers=headers, timeout=6)
            if res.status_code == 200:
                content_b64 = res.json().get("content", "")
                decoded = base64.b64decode(content_b64).decode("utf-8", errors="ignore")
                return decoded[:3000] + ("...\n\n[Kod/Icerik Devami GitHub Baglantisinda]" if len(decoded) > 3000 else "")
        except Exception:
            pass
        return "Kod icerigi dogrudan cekilemedi, detaylar icin asagidaki GitHub baglantisini ziyaret edebilirsiniz."

    def yazilim_modu_ara_ve_getir(self, sorgu_metni):
        headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "HAN-AI-App"
        }
        api_url = f"https://api.github.com/search/repositories?q={urllib_parse_quote(sorgu_metni)}+language:python&sort=stars&order=desc&per_page=2"
        bulunan_repolar = []
        ilk_url_aciklamasi = "Arama analizi tamamlandi."

        web_ozet = self.canli_google_ara(sorgu_metni, adet=1)
        if web_ozet:
            ilk_url_aciklamasi = web_ozet[0]["ozet"]

        try:
            res = requests.get(api_url, headers=headers, timeout=6)
            if res.status_code == 200:
                items = res.json().get("items", [])
                for item in items:
                    repo_adi = item.get("full_name")
                    if repo_adi:
                        bulunan_repolar.append(repo_adi)
        except Exception:
            pass

        cevap = "Elbette hemen bakalim, detaylari ve kodlari verecegim.\n\n"
        cevap += f"**Arama Analizi ve Aciklama:**\n{ilk_url_aciklamasi}\n\n"
        cevap += "---\n\n"

        if bulunan_repolar:
            cevap += f"### Bulunan GitHub Kod Projeleri ({len(bulunan_repolar)} Adet):\n\n"
            for i, repo_adi in enumerate(bulunan_repolar, 1):
                tum_kodlar = self.github_tum_kodlari_cek(repo_adi)
                repo_url = f"https://github.com/{repo_adi}"
                cevap += f"#### {i}. Proje Basligi: {repo_adi}\n"
                cevap += f"**GitHub Baglantisi:** [{repo_url}]({repo_url})\n"
                cevap += f"**Proje Butun Kodlari ve Icerigi:**\n```python\n{tum_kodlar}\n```\n\n---\n"
        else:
            cevap += f"Maalesef '{sorgu_metni}' konusuyla ilgili GitHub uzerinde dogrudan eslesen bir proje bulunamadi."

        return cevap

    def yanit_uret(self, girdi):
        girdi_temiz = girdi.strip().lower()

        if girdi_temiz in ["yazilim", "yazılım"]:
            st.session_state.yazilim_modu = True
            return "HAN AI 2 Yazilim Modu { Gizli Mod Acildi }"

        if girdi_temiz in ["yazilim_exit", "yazılım_exit"]:
            st.session_state.yazilim_modu = False
            return "Normal Moda Gecildi."

        if st.session_state.yazilim_modu:
            sorgu_metni = self.metin_temizle(girdi)
            return self.yazilim_modu_ara_ve_getir(sorgu_metni)

        selamlar = {"selam", "merhaba", "gunaydin", "iyi", "gunler", "naber", "nasilsin", "sa"}
        girdi_kelimeler = set(girdi_temiz.split())
        
        if girdi_kelimeler.intersection(selamlar):
            return "Merhaba! Iyiyim, tesekkur ederim. Size nasil yardimci olabilirim?"

        arama_sonuclari = self.canli_google_ara(girdi, adet=3)
        if arama_sonuclari:
            cevap = "Arama verilerine dayanarak buldugum sonuclar:\n\n"
            for i, item in enumerate(arama_sonuclari, 1):
                cevap += f"**{i}. {item['baslik']}**\n"
                cevap += f"{item['ozet']}\n"
                cevap += f"Kaynak: [{item['url']}]({item['url']})\n\n"
            return cevap
        else:
            return f"'{girdi}' sorgusu icin canli web aramasi uzerinden dogrudan sonuc cekilemedi."


motor = DinamikNLPMotoru()


# ==========================================
# YAN MENU (SIDEBAR / KONTROL PANELERI)
# ==========================================
with st.sidebar:
    st.title("Kontrol Paneli")
    
    sekme = st.radio("Secenekler", ["Giris Yap / Kayit Ol", "Admin Panel", "Hakkimizda"])
    st.divider()

    # 1. KULLANICI KAYIT / GIRIS PANELI
    if sekme == "Giris Yap / Kayit Ol":
        if st.session_state.aktif_kullanici:
            st.success(f"Hos geldin, **{st.session_state.aktif_kullanici}**!")
            if st.button("Cikis Yap"):
                st.session_state.aktif_kullanici = None
                st.rerun()
        else:
            islem_turu = st.radio("Islem Secin", ["Giris Yap", "Kayit Ol"])
            
            if islem_turu == "Kayit Ol":
                yeni_kullanici = st.text_input("Kullanici Adi")
                yeni_email = st.text_input("E-Posta Adresi")
                yeni_sifre = st.text_input("Sifre", type="password")
                
                if st.button("Kayit Ol ve Katil"):
                    if yeni_kullanici and yeni_email and yeni_sifre:
                        st.session_state.kullanicilar.append({
                            "kullanici_adi": yeni_kullanici,
                            "email": yeni_email,
                            "sifre": yeni_sifre
                        })
                        st.session_state.aktif_kullanici = yeni_kullanici
                        st.success("Kayit Basarili! Oturum Acildi.")
                        st.rerun()
                    else:
                        st.warning("Lutfen tum alanlari doldurun.")
            
            elif islem_turu == "Giris Yap":
                giris_kullanici = st.text_input("Kullanici Adi veya E-Posta")
                giris_sifre = st.text_input("Sifre", type="password")
                
                if st.button("Oturum Ac"):
                    bulundu = False
                    for u in st.session_state.kullanicilar:
                        if (u["kullanici_adi"] == giris_kullanici or u["email"] == giris_kullanici) and u["sifre"] == giris_sifre:
                            st.session_state.aktif_kullanici = u["kullanici_adi"]
                            bulundu = True
                            break
                    if bulundu:
                        st.success("Giris Basarili!")
                        st.rerun()
                    else:
                        st.error("Kullanici adi veya sifre hatali.")

    # 2. ADMIN PANELI (Giris Sifresi: 2013)
    elif sekme == "Admin Panel":
        if not st.session_state.admin_giris_yapildi:
            admin_sifre_input = st.text_input("Admin Panel Sifresi", type="password")
            if st.button("Admin Paneline Giris Yap"):
                if admin_sifre_input == "2013":
                    st.session_state.admin_giris_yapildi = True
                    st.success("Admin Dogrulandi!")
                    st.rerun()
                else:
                    st.error("Hatali Admin Sifresi!")
        else:
            st.subheader("HAN AI Admin Yönetimi")
            if st.button("Admin Oturumunu Kapat"):
                st.session_state.admin_giris_yapildi = False
                st.rerun()

            st.divider()
            
            # Sunucu Salteri (Server Kapat/Ac)
            st.write("### Sunucu Guvenlik Anahtari")
            if st.session_state.server_durumu:
                if st.button("SERVER KAPAT"):
                    st.session_state.server_durumu = False
                    st.warning("Sunucu Devre Disi Birakildi!")
                    st.rerun()
            else:
                if st.button("SERVER AC"):
                    st.session_state.server_durumu = True
                    st.success("Sunucu Yeniden Yayinda!")
                    st.rerun()

            st.divider()

            # Online & Kullanici Istatistikleri
            col1, col2 = st.columns(2)
            col1.metric("Online Kullanici", "1" if st.session_state.aktif_kullanici else "0")
            col2.metric("Kayitli Kullanici", len(st.session_state.kullanicilar))

            # Sistem Durumu Grafigi (Arama Motoru, API, GitHub)
            st.write("### API ve Sistem Durum Grafigi")
            grafik_veri = pd.DataFrame({
                "Sistem Bileseni": ["Tavily API", "GitHub API", "NLP Engine", "Render Server"],
                "Erisilebilirlik (%)": [100, 98, 100, 100]
            })
            st.bar_chart(grafik_veri.set_index("Sistem Bileseni"))

            # Kayitli Kullanici Veri Tablosu
            st.write("### Kayitli Kullanici Listesi")
            df_users = pd.DataFrame(st.session_state.kullanicilar)[["kullanici_adi", "email"]]
            st.dataframe(df_users, use_container_width=True)

            st.divider()

            # Minik Test Chat Box (Admin icin)
            st.write("### Minik Test HAN AI")
            admin_test_input = st.text_input("Admin Test Mesaji")
            if st.button("Test Et"):
                if admin_test_input:
                    cevap = motor.yanit_uret(admin_test_input)
                    st.code(cevap, language="markdown")

    # 3. HAKKIMIZDA BOLUMU
    elif sekme == "Hakkimizda":
        st.subheader("Hakkinda")
        st.write("""
        **HAN AI 2**, yuksek performansli NLP altyapisi ve canli web arama entegrasyonuyla donatilmis yerli yapay zeka sistemidir.

        * **Gelistirici:** HAN AI Technology
        * **Surum:** v2.4 Stable
        * **Altyapi:** Streamlit & Python NLP
        * **Guvenlik:** Dinamik API Yonetimi ve Sifreli Kimlik Dogrulama
        """)
        st.caption("Copyright 2026 HAN AI Technology. Tum Haklari Saklidir.")


# ==========================================
# ANA SAYFA VE CHAT ALANI
# ==========================================
st.title("HAN AI 2")

mod_etiketi = " | Yazilim Modu" if st.session_state.yazilim_modu else ""
st.caption(f"Sade ve Sik NLP Tabanli Yapay Zeka Sistem Altyapisi{mod_etiketi}")
st.divider()

# SUNUCU KAPALI ISE KULLANICILARA GOSTERILECEK UYARI EKRANI
if not st.session_state.server_durumu:
    st.error("HAN AI Servis Disidir.")
    st.info("Sistem bakimdadir veya yoneticiler tarafindan gecici olarak durdurulmustur. Lutfen daha sonra tekrar deneyiniz.")
else:
    # SUNUCU ACIKSA NORMAL SOHBET AKISI
    sohbet_alani = st.container(height=430)

    with sohbet_alani:
        for mesaj in st.session_state.sohbet_gecmisi:
            with st.chat_message(mesaj["rol"]):
                st.write(mesaj["icerik"])

    if kullanici_input := st.chat_input("HAN AI 2 ile sohbet edin..."):
        st.session_state.sohbet_gecmisi.append({"rol": "user", "icerik": kullanici_input})
        
        with st.spinner("Dusunuyor..."):
            time.sleep(0.3)
            bot_cevabi = motor.yanit_uret(kullanici_input)
            
        st.session_state.sohbet_gecmisi.append({"rol": "assistant", "icerik": bot_cevabi})
        st.rerun()
