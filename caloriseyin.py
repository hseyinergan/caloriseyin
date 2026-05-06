import streamlit as st
import google.generativeai as genai
import pandas as pd
from PIL import Image
from datetime import datetime
import os
import json
import time
# --- SAYFA AYARLARI VE GİZLEME KODU (EN ÜSTTE OLMALI) ---
st.set_page_config(page_title="Caloriseyin", page_icon="logo.png", layout="centered")

gizleme_kodu = """
<style>
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}

</style>
"""
st.markdown(gizleme_kodu, unsafe_allow_html=True)
# --- 🔒 GÜVENLİK VE ŞİFRE EKRANI ---
if "sifre_dogru" not in st.session_state:
    st.session_state.sifre_dogru = False

if not st.session_state.sifre_dogru:
    
    st.markdown("<h1 style='text-align: center; color: #ff4b4b;'>Caloriseyin 🍎</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center;'>Kanka, sisteme girmek için şifreyi yaz.</p>", unsafe_allow_html=True)
    
    sifre = st.text_input("Parola", type="password")
    if st.button("Kilidi Aç", use_container_width=True):
        if sifre == "19": 
            st.session_state.sifre_dogru = True
            st.rerun()
        else:
            st.error("Yanlış şifre kanka!")
    st.stop() 

# --- AYARLAR (BULUT İÇİN GİZLİ API KEY) ---
try:
    API_KEY = st.secrets["API_KEY"]
except:
    st.error("API Anahtarı bulunamadı! Lütfen Streamlit ayarlarından 'Secrets' kısmını doldur.")
    st.stop()

genai.configure(api_key=API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

DB_FILE = "veritabani_caloriseyin.csv"
PROFIL_FILE = "profil_caloriseyin.json"
KILO_FILE = "kilo_caloriseyin.csv"
SU_FILE = "su_caloriseyin.csv"

st.markdown("""
<style>
    div[role="radiogroup"] > label > div:first-child { display: none !important; }
    div[role="radiogroup"] > label { padding: 10px; border-radius: 10px; cursor: pointer; transition: 0.3s; }
    div[role="radiogroup"] > label:hover { background-color: rgba(255,255,255,0.1); }
    .h-loader {
        font-size: 60px; font-weight: 900; color: #ff4b4b; text-align: center; font-family: 'Arial', sans-serif;
        animation: pulse 1s infinite alternate, spin 3s linear infinite; display: inline-block; margin: 20px auto;
    }
    @keyframes pulse { 0% { transform: scale(0.8); opacity: 0.5; } 100% { transform: scale(1.2); opacity: 1; } }
</style>
""", unsafe_allow_html=True)

def yuvarlak_bar(yuzde, renk, baslik, deger, hedef):
    yuzde = min(yuzde, 100)
    html = f"""
    <div style="display: flex; flex-direction: column; align-items: center; justify-content: center;">
        <div style="width: 100px; height: 100px; border-radius: 50%; background: conic-gradient({renk} {yuzde}%, #333 {yuzde}%); display: flex; align-items: center; justify-content: center; margin-bottom: 10px;">
            <div style="width: 80px; height: 80px; background-color: #0e1117; border-radius: 50%; display: flex; align-items: center; justify-content: center; flex-direction: column;">
                <span style="font-size: 18px; font-weight: bold; color: white;">%{int(yuzde)}</span>
            </div>
        </div>
        <p style="margin:0; font-weight:bold; color: white;">{baslik}</p>
        <p style="margin:0; font-size: 12px; color: gray;">{int(deger)} / {int(hedef)}g</p>
    </div>
    """
    return html

def yapay_zeka_yukleniyor(mesaj="H"):
    yazi = st.empty()
    yazi.markdown(f'<div style="text-align:center;"><div class="h-loader">{mesaj}</div><br><span style="color:gray;">Caloriseyin Hesaplarken Bekle Kanka...</span></div>', unsafe_allow_html=True)
    return yazi

def profil_var_mi(): return os.path.isfile(PROFIL_FILE)
def profil_kaydet(veriler):
    with open(PROFIL_FILE, "w") as f: json.dump(veriler, f)

def veriyi_kaydet(tur, isim, kalori, protein, karb, yag):
    tarih = datetime.now().strftime("%Y-%m-%d %H:%M")
    yeni_satir = pd.DataFrame([[tarih, tur, isim, int(kalori), int(protein), int(karb), int(yag)]], columns=["Tarih", "Tur", "Isim", "Kalori", "Protein", "Karb", "Yag"])
    if not os.path.isfile(DB_FILE): yeni_satir.to_csv(DB_FILE, index=False)
    else: yeni_satir.to_csv(DB_FILE, mode='a', header=False, index=False)

def kilo_kaydet(kilo):
    tarih = datetime.now().strftime("%Y-%m-%d")
    yeni_satir = pd.DataFrame([[tarih, float(kilo)]], columns=["Tarih", "Kilo"])
    if not os.path.isfile(KILO_FILE): yeni_satir.to_csv(KILO_FILE, index=False)
    else:
        df = pd.read_csv(KILO_FILE)
        df = df[df["Tarih"] != tarih]
        df = pd.concat([df, yeni_satir], ignore_index=True)
        df.to_csv(KILO_FILE, index=False)

def su_kaydet(ml):
    tarih = datetime.now().strftime("%Y-%m-%d")
    yeni_satir = pd.DataFrame([[tarih, ml]], columns=["Tarih", "Miktar_ml"])
    if not os.path.isfile(SU_FILE): yeni_satir.to_csv(SU_FILE, index=False)
    else: yeni_satir.to_csv(SU_FILE, mode='a', header=False, index=False)

def tema_degistir(tema):
    os.makedirs(".streamlit", exist_ok=True)
    with open(".streamlit/config.toml", "w") as f:
        if tema == "Karanlık": f.write('[theme]\nbase="dark"')
        else: f.write('[theme]\nbase="light"')

# --- 1. AŞAMA: İLK KURULUM ---
if not profil_var_mi():
    st.set_page_config(page_title="Caloriseyin Kurulum", page_icon="🚀", layout="centered")
    st.title("🚀 Caloriseyin'e Hoş Geldin!")
    st.write("Sana özel planı hazırlayabilmem için formu doldur kanka.")
    with st.form("onboarding"):
        yas = st.number_input("Yaşın", min_value=15, max_value=80, value=21)
        boy = st.number_input("Boyun (cm)", min_value=150, max_value=220, value=180)
        kilo = st.number_input("Kilon (kg)", min_value=40.0, max_value=180.0, value=75.0)
        cinsiyet = st.selectbox("Cinsiyet", ["Erkek", "Kadın"])
        hedef = st.selectbox("Amacın Ne?", ["Kilo Almak (Bulking)", "Kilo Vermek (Deficit)", "Kilomu Korumak"])
        spor = st.selectbox("Haftada Kaç Gün Spor Yapıyorsun?", ["Hiç (Hareketsiz)", "1-3 Gün (Hafif)", "3-5 Gün (Orta)", "6-7 Gün (Ağır)"])
        if st.form_submit_button("Sistemi Başlat"):
            carpan = 1.2 if spor == "Hiç (Hareketsiz)" else 1.375 if spor == "1-3 Gün (Hafif)" else 1.55 if spor == "3-5 Gün (Orta)" else 1.725
            profil_kaydet({"yas": yas, "boy": boy, "kilo": kilo, "cinsiyet": cinsiyet, "hedef": hedef, "carpan": carpan})
            kilo_kaydet(kilo)
            st.success("Profil oluşturuldu! Yönlendiriliyorsun...")
            time.sleep(2)
            st.rerun()
    st.stop()

# --- 2. AŞAMA: ANA UYGULAMA ---
st.set_page_config(page_title="Caloriseyin", page_icon="📱", layout="wide")

if "mesajlar" not in st.session_state: st.session_state.mesajlar = [{"role": "ai", "content": "Sistem hazır! Bugün ne yedik, ne bastık?"}]
with open(PROFIL_FILE, "r") as f: profil = json.load(f)

guncel_kilo = float(pd.read_csv(KILO_FILE).iloc[-1]["Kilo"]) if os.path.isfile(KILO_FILE) else profil["kilo"]
bmr = (10 * guncel_kilo) + (6.25 * profil["boy"]) - (5 * profil["yas"]) + (5 if profil["cinsiyet"] == "Erkek" else -161)
gunluk_ihtiyac = bmr * profil["carpan"]

if profil["hedef"] == "Kilo Almak (Bulking)": hedef_kalori, hedef_protein, hedef_yag = gunluk_ihtiyac + 500, guncel_kilo * 2.2, guncel_kilo * 1.0
elif profil["hedef"] == "Kilo Vermek (Deficit)": hedef_kalori, hedef_protein, hedef_yag = gunluk_ihtiyac - 500, guncel_kilo * 2.0, guncel_kilo * 0.8
else: hedef_kalori, hedef_protein, hedef_yag = gunluk_ihtiyac, guncel_kilo * 1.8, guncel_kilo * 1.0

hedef_karb = (hedef_kalori - ((hedef_protein * 4) + (hedef_yag * 9))) / 4

bugun = datetime.now().strftime("%Y-%m-%d")
alinan_kalori, alinan_protein, alinan_karb, alinan_yag, yakilan_kalori = 0, 0, 0, 0, 0

if os.path.isfile(DB_FILE):
    df = pd.read_csv(DB_FILE)
    df["SadeceTarih"] = df["Tarih"].apply(lambda x: x.split(" ")[0])
    bugunku_df = df[df["SadeceTarih"] == bugun]
    yemekler = bugunku_df[bugunku_df["Tur"] == "Yemek"]
    alinan_kalori, alinan_protein, alinan_karb, alinan_yag = yemekler["Kalori"].sum(), yemekler["Protein"].sum(), yemekler["Karb"].sum(), yemekler["Yag"].sum()
    yakilan_kalori = bugunku_df[bugunku_df["Tur"] == "Egzersiz"]["Kalori"].sum()

st.sidebar.title("📱 Caloriseyin Menü")
sayfa = st.sidebar.radio("", ["🏠 Ana Sayfa", "💧 Su Takibi", "⚖️ Kilo Takibi", "📋 Tüm Tablolar", "⚙️ Ayarlar"])

if sayfa == "🏠 Ana Sayfa":
    st.markdown("### 🎯 Günlük Makro Hedeflerin")
    c1, c2, c3, c4 = st.columns(4)
    with c1: st.markdown(yuvarlak_bar((alinan_kalori / (hedef_kalori + yakilan_kalori)) * 100 if (hedef_kalori + yakilan_kalori) > 0 else 0, "#ff4b4b", "Kalori", alinan_kalori, hedef_kalori+yakilan_kalori), unsafe_allow_html=True)
    with c2: st.markdown(yuvarlak_bar((alinan_karb / hedef_karb) * 100 if hedef_karb > 0 else 0, "#4b8bff", "Karb", alinan_karb, hedef_karb), unsafe_allow_html=True)
    with c3: st.markdown(yuvarlak_bar((alinan_protein / hedef_protein) * 100 if hedef_protein > 0 else 0, "#4bff6e", "Protein", alinan_protein, hedef_protein), unsafe_allow_html=True)
    with c4: st.markdown(yuvarlak_bar((alinan_yag / hedef_yag) * 100 if hedef_yag > 0 else 0, "#ffa84b", "Yağ", alinan_yag, hedef_yag), unsafe_allow_html=True)
    st.divider()

    for msg in st.session_state.mesajlar:
        if msg["role"] == "ai": st.chat_message("ai", avatar="🤖").write(msg["content"])
        else: st.chat_message("user", avatar="👤").write(msg["content"])

    # --- KAMERA ÇÖZÜMÜ BURADA ---
    with st.expander("📸 Fotoğraf Ekle / Çek"):
        girdi_tipi = st.selectbox("Nasıl yükleyeceksin?", ["Seçim Yap...", "Kamerayı Aç", "Galeriden Seç"])
        img_file = None
        
        if girdi_tipi == "Kamerayı Aç":
            img_file = st.camera_input("Tabağını Çek")
        elif girdi_tipi == "Galeriden Seç":
            img_file = st.file_uploader("Fotoğraf Seç", type=["jpg", "jpeg", "png"])

        if img_file:
            loader = yapay_zeka_yukleniyor("H")
            try:
                prompt = "Fotoğraftaki yemeği analiz et. SADECE şu formatta ver: TÜR | İSİM | KALORİ | PROTEİN | KARBONHİDRAT | YAĞ"
                response = model.generate_content([prompt, Image.open(img_file)])
                loader.empty()
                if "|" in response.text:
                    veri = [v.strip() for v in response.text.split("|")]
                    veriyi_kaydet(veri[0], veri[1], veri[2], veri[3], veri[4], veri[5])
                    st.session_state.mesajlar.append({"role": "user", "content": f"📸 [Fotoğraf] {veri[1]}"})
                    st.session_state.mesajlar.append({"role": "ai", "content": f"Sisteme eklendi: {veri[1]} (+{veri[2]} kcal, +{veri[4]}g Karb)"})
                    st.rerun()
            except:
                loader.empty()
                st.error("Bir aksilik çıktı kanka, fotoğrafı tekrar at.")

    kullanici_mesaji = st.chat_input("Yemeğini veya sporunu yaz...")
    if kullanici_mesaji:
        st.session_state.mesajlar.append({"role": "user", "content": kullanici_mesaji})
        loader = yapay_zeka_yukleniyor("H")
        try:
            prompt = f"Kullanıcı: '{kullanici_mesaji}'. Kilo: {guncel_kilo}kg, Amacı: {profil['hedef']}. Yemekse makrolarını, egzersizse yakılan kaloriyi bul. SADECE format: TÜR | İSİM | KALORİ | PROTEİN | KARBONHİDRAT | YAĞ"
            response = model.generate_content(prompt)
            loader.empty()
            if "|" in response.text:
                veri = [v.strip() for v in response.text.split("|")]
                veriyi_kaydet(veri[0], veri[1], int(''.join(filter(str.isdigit, veri[2]))), int(''.join(filter(str.isdigit, veri[3]))), int(''.join(filter(str.isdigit, veri[4]))), int(''.join(filter(str.isdigit, veri[5]))))
                st.session_state.mesajlar.append({"role": "ai", "content": f"{veri[1]} başarıyla işlendi! ({veri[2]} kcal)"})
                st.rerun()
                    except Exception as e:
                        st.error(f"Kanka arka planda şu hata koptu: {e}")

elif sayfa == "💧 Su Takibi":
    st.title("💧 Günlük Su Tüketimi")
    hedef_su_ml, bardak_hacmi = int(guncel_kilo * 35), 200
    hedef_bardak = int(hedef_su_ml / bardak_hacmi)
    icilen_su_ml = pd.read_csv(SU_FILE)[pd.read_csv(SU_FILE)["Tarih"] == bugun]["Miktar_ml"].sum() if os.path.isfile(SU_FILE) and not pd.read_csv(SU_FILE)[pd.read_csv(SU_FILE)["Tarih"] == bugun].empty else 0
    icilen_bardak = int(icilen_su_ml / bardak_hacmi)
    st.markdown(f"### 🎯 Günlük Hedefin: **{hedef_su_ml / 1000:.1f} Litre** ({hedef_bardak} Bardak)")
    st.markdown(f"<h1 style='text-align: center; font-size: 50px;'>{'🥛' * icilen_bardak}{'🫗' * max(0, hedef_bardak - icilen_bardak)}</h1>", unsafe_allow_html=True)
    st.markdown(f"<p style='text-align: center;'>Bugün içilen: {icilen_bardak} bardak ({icilen_su_ml} ml)</p>", unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        if st.button("➕ 1 Bardak (200ml)", use_container_width=True): su_kaydet(200); st.rerun()
    with col2:
        if st.button("🚰 1 Şişe (500ml)", use_container_width=True): su_kaydet(500); st.rerun()

elif sayfa == "⚖️ Kilo Takibi":
    st.title("⚖️ Kilo Gelişimi")
    yeni_kilo = st.number_input("Bugün Tartıldın Mı? Yeni Kilonu Gir:", min_value=40.0, max_value=180.0, value=guncel_kilo, step=0.1)
    if st.button("Güncelle ve Tabloya Ekle"): kilo_kaydet(yeni_kilo); st.success("Kilon güncellendi!"); st.rerun()
    if os.path.isfile(KILO_FILE): st.line_chart(pd.read_csv(KILO_FILE).set_index("Tarih"))

elif sayfa == "📋 Tüm Tablolar":
    st.title("📋 Geçmiş Kayıtların")
    if os.path.isfile(DB_FILE): st.dataframe(pd.read_csv(DB_FILE).sort_values(by="Tarih", ascending=False), use_container_width=True)
    else: st.info("Henüz bir kayıt yok.")

elif sayfa == "⚙️ Ayarlar":
    st.title("⚙️ Sistem Ayarları")
    tema_secimi = st.radio("Tema Seç:", ["Aydınlık", "Karanlık"], horizontal=True)
    if st.button("Temayı Uygula"): tema_degistir(tema_secimi); st.success("Tema uygulandı! Sayfayı yenile (F5).")
    st.divider()
    if st.button("Sistemi Sıfırla (Onboarding'e Dön)"): os.remove(PROFIL_FILE); st.rerun()
