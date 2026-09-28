import streamlit as st
import requests
import time
import re
import base64

st.set_page_config(page_title="HAN AI 2", layout="centered")

# TAVILY API KEY
TAVILY_API_KEY = "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"

if "sohbet_gecmisi" not in st.session_state:
    st.session_state.sohbet_gecmisi = []

if "yazilim_modu" not in st.session_state:
    st.session_state.yazilim_modu = False


class DinamikNLPMotoru:
    def __init__(self):
        self.durak_kelimeler = {
            "ve", "veya", "bir", "bu", "şu", "için", "ile", "ne", "nasıl", "nedir", 
            "mi", "mı", "de", "da", "bana", "ver", "kodu", "kodunu", "bul", "getir", 
            "kanka", "bro", "hocam", "reis", "lan", "ya", "söyle", "anlat"
        }

    def metin_temizle(self, metin):
        metin_alt = metin.lower()
        temiz_metin = re.sub(r'[^\w\s]', '', metin_alt)
        tokens = temiz_metin.split()
        temiz_tokens = [t for t in tokens if t not in self.durak_kelimeler]
        
        # Eğer temizleme sonrası hiçbir şey kalmadıysa orijinal metni geri döndür
        if temiz_tokens:
            return " ".join(temiz_tokens)
        return metin.strip()

    def canlı_google_ara(self, sorgu, adet=3):
        """Render IP engeline takılmayan Tavily AI Arama Motoru"""
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
                
                # Eğer Tavily yapay zeka özeti/yanıtı ürettiyse önce onu ekle
                if data.get("answer"):
                    sonuclar.append({
                        "baslik": "AI Analiz Özet Yanıtı",
                        "url": "https://tavily.com",
                        "ozet": data.get("answer")
                    })

                results = data.get("results", [])
                for item in results:
                    sonuclar.append({
                        "baslik": item.get("title", "Arama Sonucu"),
                        "url": item.get("url", "#"),
                        "ozet": item.get("content", "Açıklama bulunamadı.")
                    })
        except Exception:
            pass

        return sonuclar

    def github_tum_kodlari_cek(self, repo_full_name):
        """GitHub API üzerinden reponun README/Kod içeriğini çeker"""
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
                # Çok uzun README dosyalarını kesip ilk 3000 karakterini sunalım
                return decoded[:3000] + ("...\n\n[Kod/İçerik Devamı GitHub Bağlantısında]" if len(decoded) > 3000 else "")
        except Exception:
            pass
        return "Kod içeriği doğrudan çekilemedi, detaylar için aşağıdaki GitHub bağlantısını ziyaret edebilirsiniz."

    def yazilim_modu_ara_ve_getir(self, sorgu_metni):
        """Web Arama Analizi + GitHub API projelerini ve kodlarını sunar"""
        headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "HAN-AI-App"
        }
        
        # GitHub Arama Sorgusunu Hazırla
        api_url = f"https://api.github.com/search/repositories?q={urllib_parse_quote(sorgu_metni)}+language:python&sort=stars&order=desc&per_page=2"
        
        bulunan_repolar = []
        ilk_url_aciklamasi = "Arama analizi tamamlandı."

        # Tavily API ile canlı web araması ve detaylı özet analizi
        web_ozet = self.canlı_google_ara(sorgu_metni, adet=1)
        if web_ozet:
            ilk_url_aciklamasi = web_ozet[0]["ozet"]

        # GitHub API ile projeleri bulma
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

        cevap = "Elbete Hemen Bakalım Size Detayları Ve Kodları Vericeğim\n\n"
        cevap += f"**Arama Analizi & Açıklama:**\n{ilk_url_aciklamasi}\n\n"
        cevap += "---\n\n"

        if bulunan_repolar:
            cevap += f"### Bulunan GitHub Kod Projeleri ({len(bulunan_repolar)} Adet):\n\n"
            for i, repo_adi in enumerate(bulunan_repolar, 1):
                tum_kodlar = self.github_tum_kodlari_cek(repo_adi)
                repo_url = f"https://github.com/{repo_adi}"
                
                cevap += f"#### {i}. Proje Başlığı: {repo_adi}\n"
                cevap += f"**GitHub Bağlantısı:** [{repo_url}]({repo_url})\n"
                cevap += f"**Proje Bütün Kodları & İçeriği:**\n```python\n{tum_kodlar}\n```\n\n---\n"
        else:
            cevap += f"Maalesef '{sorgu_metni}' konusuyla ilgili GitHub üzerinde doğrudan eşleşen bir proje bulunamadı."

        return cevap

    def yanit_uret(self, girdi):
        girdi_temiz = girdi.strip().lower()

        # Mod Giriş
        if girdi_temiz in ["yazılım", "yazilim"]:
            st.session_state.yazilim_modu = True
            return "HAN AI 2 Yazılım Modu { Gizli Mod Açıldı }"

        # Mod Çıkış
        if girdi_temiz in ["yazılım_exit", "yazilim_exit"]:
            st.session_state.yazilim_modu = False
            return "Normal Moda Geçildi."

        # YAZILIM MODU
        if st.session_state.yazilim_modu:
            sorgu_metni = self.metin_temizle(girdi)
            return self.yazilim_modu_ara_ve_getir(sorgu_metni)

        # NORMAL SOHBET MODU
        selamlar = {"selam", "merhaba", "gunaydin", "iyi", "gunler", "naber", "nasilsin", "sa"}
        girdi_kelimeler = set(girdi_temiz.split())
        
        if girdi_kelimeler.intersection(selamlar):
            return "Merhaba! İyiyim, teşekkür ederim. Size nasıl yardımcı olabilirim?"

        arama_sonuclari = self.canlı_google_ara(girdi, adet=3)
        
        if arama_sonuclari:
            cevap = "Arama verilerine dayanarak bulduğum sonuçlar:\n\n"
            for i, item in enumerate(arama_sonuclari, 1):
                cevap += f"**{i}. {item['baslik']}**\n"
                cevap += f"{item['ozet']}\n"
                cevap += f"Kaynak: [{item['url']}]({item['url']})\n\n"
            return cevap
        else:
            return f"'{girdi}' sorgusu için canlı web araması üzerinden doğrudan sonuç çekilemedi."


# URL Encode için yardımcı import eklemesi
from urllib.parse import quote as urllib_parse_quote

motor = DinamikNLPMotoru()

st.title("HAN AI 2")

mod_etiketi = " [Yazılım Modu]" if st.session_state.yazilim_modu else ""
st.caption(f"Yerli Ve Milli NLP Tabanlı Yapay Zeka Sistem Altyapısı Ücretsiz | Yazılım HAN AI Tarafından{mod_etiketi}")

st.divider()

sohbet_alani = st.container(height=420)

with sohbet_alani:
    for mesaj in st.session_state.sohbet_gecmisi:
        with st.chat_message(mesaj["rol"]):
            st.write(mesaj["icerik"])

if kullanici_input := st.chat_input("HAN AI POWER OF TECHNOLOGY"):
    st.session_state.sohbet_gecmisi.append({"rol": "user", "icerik": kullanici_input})
    
    with st.spinner("Anlamaya Çalışıyorum..."):
        time.sleep(0.5)
        bot_cevabi = motor.yanit_uret(kullanici_input)
        
    st.session_state.sohbet_gecmisi.append({"rol": "assistant", "icerik": bot_cevabi})
    st.rerun()
