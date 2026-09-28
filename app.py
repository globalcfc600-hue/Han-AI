import streamlit as st
import requests
import time
import re
import base64

st.set_page_config(page_title="HAN AI", layout="centered")

if "github_hafizasi" not in st.session_state:
    st.session_state.github_hafizasi = []

if "ogrenilen_kavramlar" not in st.session_state:
    st.session_state.ogrenilen_kavramlar = {}

if "sohbet_gecmisi" not in st.session_state:
    st.session_state.sohbet_gecmisi = []

if "son_tarama_zamani" not in st.session_state:
    st.session_state.son_tarama_zamani = 0

if "yazilim_modu" not in st.session_state:
    st.session_state.yazilim_modu = False


class DinamikNLPMotoru:
    def __init__(self):
        self.durak_kelimeler = {"ve", "veya", "bir", "bu", "şu", "için", "ile", "ne", "nasıl", "nedir", "mi", "mı", "de", "da", "bana", "ver", "kodu", "kodunu", "bul", "getir"}
        self.spam_kelimeler = {"test", "asdf", "qwerty", "1234", "null", "undefined", "foo", "bar"}

    def metin_temizle(self, metin):
        metin = metin.lower()
        metin = re.sub(r'[^\w\s]', '', metin)
        tokens = metin.split()
        return [t for t in tokens if t not in self.durak_kelimeler]

    def spam_mi(self, metin):
        metin_alt = metin.lower()
        if len(metin_alt.strip()) < 3 or any(s in metin_alt for s in self.spam_kelimeler):
            return True
        return False

    def veri_egit(self, repo_listesi):
        for repo in repo_listesi:
            ad = repo.get("ad", "").lower()
            aciklama = repo.get("aciklama", "").lower()
            if self.spam_mi(aciklama) or self.spam_mi(ad):
                continue
            kelimeler = self.metin_temizle(aciklama)
            for k in kelimeler:
                if len(k) > 2 and not k.isdigit():
                    if k not in st.session_state.ogrenilen_kavramlar:
                        st.session_state.ogrenilen_kavramlar[k] = []
                    if repo not in st.session_state.ogrenilen_kavramlar[k]:
                        st.session_state.ogrenilen_kavramlar[k].append(repo)

    def github_kod_icerigi_cek(self, repo_full_name):
        headers = {"Accept": "application/vnd.github.v3+json"}
        url = f"https://api.github.com/repos/{repo_full_name}/readme"
        try:
            res = requests.get(url, headers=headers, timeout=5)
            if res.status_code == 200:
                content_b64 = res.json().get("content", "")
                decoded = base64.b64decode(content_b64).decode("utf-8", errors="ignore")
                return decoded[:1500] + "\n\n...[Kodun Devamı GitHub Adresinde]..." if len(decoded) > 1500 else decoded
        except Exception:
            pass
        return "Kod içeriği çekilemedi, bağlantıdan inceleyebilirsiniz."

    def github_kod_ara_coklu(self, sorgu_kelimesi, adet=2):
        url = f"https://api.github.com/search/repositories?q={sorgu_kelimesi}&sort=updated&order=desc&per_page={adet}"
        headers = {"Accept": "application/vnd.github.v3+json"}
        sonuclar = []
        try:
            res = requests.get(url, headers=headers, timeout=10)
            if res.status_code == 200:
                items = res.json().get("items", [])
                for item in items[:adet]:
                    repo_adi = item.get("full_name")
                    kod_icerik = self.github_kod_icerigi_cek(repo_adi)
                    sonuclar.append({
                        "ad": repo_adi,
                        "aciklama": item.get("description") or "Açıklama yok.",
                        "url": item.get("html_url"),
                        "kod": kod_icerik
                    })
        except Exception:
            pass
        return sonuclar

    def yanit_uret(self, girdi):
        girdi_temiz = girdi.strip().lower()

        if girdi_temiz in ["yazılım", "yazilim"]:
            st.session_state.yazilim_modu = True
            return "HAN AI Yazılım Modu { Gizli Mod Açıldı }"

        if girdi_temiz in ["normal", "çıkış", "cikis", "kapat"]:
            st.session_state.yazilim_modu = False
            return "Normal Moda Geçildi."

        if st.session_state.yazilim_modu:
            kelimeler = self.metin_temizle(girdi)
            sorgu_metni = "+".join(kelimeler) if kelimeler else girdi_temiz
            sonuclar = self.github_kod_ara_coklu(sorgu_metni, adet=2)

            if sonuclar:
                cevap = f"### GitHub'dan Bulunan Kod Örnekleri ({len(sonuclar)} Adet):\n\n"
                for i, item in enumerate(sonuclar, 1):
                    cevap += f"#### Örnek {i}: {item['ad']}\n"
                    cevap += f"**Açıklama:** {item['aciklama']}\n"
                    cevap += f"**Kod / İçerik:**\n```python\n{item['kod']}\n```\n"
                    cevap += f"**URL:** [{item['url']}]({item['url']})\n\n---\n"
                return cevap
            else:
                return f"GitHub üzerinde '{sorgu_metni}' aramasıyla ilgili doğrudan bir kod örneği bulunamadı."

        kelimeler = self.metin_temizle(girdi)
        selamlar = {"selam", "merhaba", "gunaydin", "iyi", "gunler", "naber", "nasilsin", "sa"}
        
        if set(kelimeler).intersection(selamlar):
            return "Merhaba! İyiyim, teşekkür ederim. Size nasıl yardımcı olabilirim?"

        if not st.session_state.github_hafizasi:
            gecen = int(time.time() - st.session_state.son_tarama_zamani)
            kalan = max(1, 10 - gecen)
            return f"Mantık Motoru Yükleniyor Lütfen Bekle _ {kalan}s"

        eslesen = []
        for k in kelimeler:
            if k in st.session_state.ogrenilen_kavramlar:
                eslesen.extend(st.session_state.ogrenilen_kavramlar[k])

        if eslesen:
            en_yakin = eslesen[-1]
            return f"Öğrendiğim kadarıyla ilgili proje: **{en_yakin['ad']}**\n\nAçıklama: {en_yakin['aciklama']}\nAdres: {en_yakin['url']}"
        else:
            son_veri = st.session_state.github_hafizasi[-1]
            return f"Aradığınız kavrama tam ulaşamadım ama son öğrendiğim proje: **{son_veri['ad']}** - {son_veri['aciklama']}"


motor = DinamikNLPMotoru()


def github_veri_cek():
    su_an = time.time()
    if st.session_state.son_tarama_zamani == 0:
        st.session_state.son_tarama_zamani = su_an

    if len(st.session_state.github_hafizasi) == 0 or (su_an - st.session_state.son_tarama_zamani >= 10):
        st.session_state.son_tarama_zamani = su_an
        url = "https://api.github.com/search/repositories?q=topic:ai+topic:chat+topic:python&sort=updated&order=desc&per_page=5"
        headers = {"Accept": "application/vnd.github.v3+json"}
        try:
            res = requests.get(url, headers=headers, timeout=5)
            if res.status_code == 200:
                items = res.json().get("items", [])
                yeni_repolar = []
                for item in items:
                    repo = {
                        "ad": item.get("full_name"),
                        "aciklama": item.get("description") or "Açıklama yok",
                        "url": item.get("html_url")
                    }
                    yeni_repolar.append(repo)
                    st.session_state.github_hafizasi.append(repo)
                motor.veri_egit(yeni_repolar)
        except Exception:
            pass


github_veri_cek()

st.title("HAN AI")

gecen_sure = int(time.time() - st.session_state.son_tarama_zamani)
if len(st.session_state.github_hafizasi) == 0:
    kalan_sure = max(1, 10 - gecen_sure)
    st.caption(f"Mantık Motoru Yükleniyor Lütfen Bekle _ {kalan_sure}s")
else:
    mod_etiketi = " [Yazılım Modu]" if st.session_state.yazilim_modu else ""
    st.caption(f"Sistem Hazır{mod_etiketi}")

st.divider()

sohbet_alani = st.container(height=420)

with sohbet_alani:
    for mesaj in st.session_state.sohbet_gecmisi:
        with st.chat_message(mesaj["rol"]):
            st.write(mesaj["icerik"])

if kullanici_input := st.chat_input("Bir şeyler yazın... (Örn: merhaba, yazılım)"):
    st.session_state.sohbet_gecmisi.append({"rol": "user", "icerik": kullanici_input})
    
    with st.spinner("Anlamaya Çalışıyorum..."):
        time.sleep(0.6)
        bot_cevabi = motor.yanit_uret(kullanici_input)
        
    st.session_state.sohbet_gecmisi.append({"rol": "assistant", "icerik": bot_cevabi})
    st.rerun()
