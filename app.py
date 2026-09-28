import streamlit as st
import requests
import time
import re
import base64
import urllib.parse

st.set_page_config(page_title="HAN AI 2", layout="centered")

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
        metin = metin.lower()
        metin = re.sub(r'[^\w\s]', '', metin)
        tokens = metin.split()
        temiz = [t for t in tokens if t not in self.durak_kelimeler]
        return temiz if temiz else tokens

    def saf_web_ara(self, sorgu, adet=3):
        """Kütüphane gerektirmeyen, doğrudan HTTP isteği ve Regex ile çalışan web arama motoru"""
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        url = "https://html.duckduckgo.com/html/"
        sonuclar = []

        try:
            res = requests.post(url, data={"q": sorgu}, headers=headers, timeout=6)
            if res.status_code == 200:
                raw_matches = re.findall(
                    r'<a class="result__url" href="([^"]+)">(.*?)</a>.*?<a class="result__snippet[^"]*">(.*?)</a>',
                    res.text,
                    re.DOTALL
                )

                for raw_link, raw_title, raw_snippet in raw_matches[:adet]:
                    clean_title = re.sub(r'<[^>]+>', '', raw_title).strip()
                    clean_snippet = re.sub(r'<[^>]+>', '', raw_snippet).strip()

                    actual_url = raw_link
                    if "uddg=" in raw_link:
                        match = re.search(r'uddg=([^&]+)', raw_link)
                        if match:
                            actual_url = urllib.parse.unquote(match.group(1))

                    if clean_title:
                        sonuclar.append({
                            "baslik": clean_title,
                            "url": actual_url,
                            "ozet": clean_snippet if clean_snippet else "Açıklama bulunamadı."
                        })
        except Exception:
            pass

        return sonuclar

    def github_tum_kodlari_cek(self, repo_full_name):
        """GitHub API üzerinden reponun README/Kod içeriğini çeker"""
        headers = {"Accept": "application/vnd.github.v3+json"}
        url = f"https://api.github.com/repos/{repo_full_name}/readme"
        try:
            res = requests.get(url, headers=headers, timeout=5)
            if res.status_code == 200:
                content_b64 = res.json().get("content", "")
                decoded = base64.b64decode(content_b64).decode("utf-8", errors="ignore")
                return decoded
        except Exception:
            pass
        return "Kod içeriği çekilemedi, bağlantı üzerinden inceleyebilirsiniz."

    def yazilim_modu_ara_ve_getir(self, sorgu_metni):
        """Web Arama Analizi + GitHub API projelerini ve kodlarını sunar"""
        headers = {"Accept": "application/vnd.github.v3+json"}
        api_url = f"https://api.github.com/search/repositories?q={sorgu_metni}&sort=stars&order=desc&per_page=2"
        
        bulunan_repolar = []
        ilk_url_aciklamasi = "Arama analizi tamamlandı."

        # Web araması ile özet analizi alma
        web_ozet = self.saf_web_ara(sorgu_metni, adet=1)
        if web_ozet:
            ilk_url_aciklamasi = web_ozet[0]["ozet"]

        # GitHub API ile repoları bulma
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
            cevap += f"Maalesef '{sorgu_metni}' konusuyla ilgili uygun bir GitHub reposu bulunamadı."

        return cevap

    def yanit_uret(self, girdi):
        girdi_temiz = girdi.strip().lower()

        # Mod Giriş
        if girdi_temiz in ["yazılım", "yazilim"]:
            st.session_state.yazilim_modu = True
            return "HAN AI 2 Yazılım Modu { Gizli Mod Açıldı }"

        # Mod Çıkış (İstediğin şekilde)
        if girdi_temiz in ["yazılım_exit", "yazilim_exit"]:
            st.session_state.yazilim_modu = False
            return "Normal Moda Geçildi."

        # YAZILIM MODU
        if st.session_state.yazilim_modu:
            temiz_kelimeler = self.metin_temizle(girdi)
            sorgu_metni = " ".join(temiz_kelimeler)
            return self.yazilim_modu_ara_ve_getir(sorgu_metni)

        # NORMAL SOHBET MODU
        kelimeler = self.metin_temizle(girdi)
        selamlar = {"selam", "merhaba", "gunaydin", "iyi", "gunler", "naber", "nasilsin", "sa"}
        
        if set(kelimeler).intersection(selamlar):
            return "Merhaba! İyiyim, teşekkür ederim. Size nasıl yardımcı olabilirim?"

        arama_sonuclari = self.saf_web_ara(girdi, adet=3)
        
        if arama_sonuclari:
            cevap = "Arama verilerine dayanarak bulduğum sonuçlar:\n\n"
            for i, item in enumerate(arama_sonuclari, 1):
                cevap += f"**{i}. {item['baslik']}**\n"
                cevap += f"{item['ozet']}\n"
                cevap += f"Kaynak: [{item['url']}]({item['url']})\n\n"
            return cevap
        else:
            return f"'{girdi}' sorgusu için canlı web araması üzerinden doğrudan sonuç çekilemedi."


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
