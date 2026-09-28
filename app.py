import streamlit as st
import requests
import time
import re
import base64
from duckduckgo_search import DDGS
from bs4 import BeautifulSoup

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

    def github_tum_kodlari_cek(self, repo_full_name):
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
        ilk_url_aciklamasi = "Arama üzerinden açıklama alınamadı."
        bulunan_repolar = []

        try:
            with DDGS() as ddgs:
                # 1. Aşama: Genel arama yapıp ilk sonucun özet açıklamalarını alma
                genel_sonuclar = list(ddgs.text(sorgu_metni, max_results=1))
                if genel_sonuclar:
                    ilk_url_aciklamasi = genel_sonuclar[0].get("body", "Açıklama bulunamadı.")

                # 2. Aşama: GitHub reponu tespit etme (2 adet)
                github_sonuclar = list(ddgs.text(f"site:github.com {sorgu_metni} python", max_results=5))
                for res in github_sonuclar:
                    url = res.get("href", "")
                    match = re.search(r'github\.com/([^/]+/[^/]+)', url)
                    if match:
                        repo_adi = match.group(1).rstrip('/')
                        if repo_adi not in bulunan_repolar and not repo_adi.endswith('.git'):
                            bulunan_repolar.append(repo_adi)
                    if len(bulunan_repolar) >= 2:
                        break
        except Exception:
            pass

        # Yedek mekanizma: Eğer 2 repo bulunamadıysa GitHub API ile tamamla
        if len(bulunan_repolar) < 2:
            api_url = f"https://api.github.com/search/repositories?q={sorgu_metni}&sort=updated&order=desc&per_page=2"
            try:
                res = requests.get(api_url, headers={"Accept": "application/vnd.github.v3+json"}, timeout=5)
                if res.status_code == 200:
                    items = res.json().get("items", [])
                    for item in items:
                        repo_adi = item.get("full_name")
                        if repo_adi not in bulunan_repolar:
                            bulunan_repolar.append(repo_adi)
                        if len(bulunan_repolar) >= 2:
                            break
            except Exception:
                pass

        # 3. Aşama: İstenen formattaki yanıtı oluşturma
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

    def normal_google_ara(self, sorgu, adet=2):
        sonuclar = []
        try:
            with DDGS() as ddgs:
                ddg_sonuclar = list(ddgs.text(sorgu, max_results=adet))
                for item in ddg_sonuclar:
                    sonuclar.append({
                        "baslik": item.get("title", ""),
                        "url": item.get("href", ""),
                        "ozet": item.get("body", "")
                    })
        except Exception:
            pass
        return sonuclar

    def yanit_uret(self, girdi):
        girdi_temiz = girdi.strip().lower()

        # Yazılım Moduna Giriş
        if girdi_temiz in ["yazılım", "yazilim"]:
            st.session_state.yazilim_modu = True
            return "HAN AI 2 Yazılım Modu { Gizli Mod Açıldı }"

        # Yazılım Modundan Çıkış
        if girdi_temiz in ["yazılım_exit", "yazilim_exit"]:
            st.session_state.yazilim_modu = False
            return "Normal Moda Geçildi."

        # YAZILIM MODU İŞLEYİŞİ
        if st.session_state.yazilim_modu:
            temiz_kelimeler = self.metin_temizle(girdi)
            sorgu_metni = " ".join(temiz_kelimeler)
            return self.yazilim_modu_ara_ve_getir(sorgu_metni)

        # NORMAL SOHBET MODU İŞLEYİŞİ
        kelimeler = self.metin_temizle(girdi)
        selamlar = {"selam", "merhaba", "gunaydin", "iyi", "gunler", "naber", "nasilsin", "sa"}
        
        if set(kelimeler).intersection(selamlar):
            return "Merhaba! İyiyim, teşekkür ederim. Size nasıl yardımcı olabilirim?"

        google_sonuclari = self.normal_google_ara(girdi, adet=2)
        
        if google_sonuclari:
            cevap = "Arama verilerine dayanarak bulduğum sonuçlar:\n\n"
            for i, item in enumerate(google_sonuclari, 1):
                cevap += f"**{i}. {item['baslik']}**\n"
                cevap += f"{item['ozet']}\n"
                cevap += f"Kaynak: [{item['url']}]({item['url']})\n\n"
            return cevap
        else:
            return f"Arama üzerinde '{girdi}' sorgusu için doğrudan bir yanıt çekilemedi."


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
