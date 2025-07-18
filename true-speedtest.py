import time
import base64
import requests
import threading
from bs4 import BeautifulSoup
from urllib.parse import urljoin

# =============== CONFIG ================
BASE_URL    = "http://192.168.1.1/"
LOGIN_URL   = "goform/webLogin"
STATS_PAGE  = "state/wireless_state.asp"
USERNAME    = "admin"
PASSWORD    = "admin"
DURATION    = 30  # durasi pengukuran dalam detik
# MAC Address perangkat kamu (yang sedang konek WiFi)
DEVICE_MAC  = "cc:06:77:38:d9:18"
# =======================================

HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Referer": urljoin(BASE_URL, "login.html"),
    "X-Requested-With": "XMLHttpRequest"
}

def login_to_router(session):
    print("🔐 Login ke router...")
    encoded_username = base64.b64encode(USERNAME.encode()).decode()
    encoded_password = base64.b64encode(PASSWORD.encode()).decode()
    login_data = {
        "username": encoded_username,
        "password": encoded_password
    }
    res = session.post(urljoin(BASE_URL, LOGIN_URL), data=login_data, headers=HEADERS)
    return "menu.html" in res.text or "logout.asp" in res.text or session.cookies.get_dict()

def fetch_stats_page(session):
    url = BASE_URL + "/cgi-bin/status_cgi"
    response = session.get(url)
    response.encoding = 'utf-8'
    html = response.text
    with open("debug_stats.html", "w", encoding="utf-8") as f:
        f.write(html)
    return html

def get_rx_tx(html):
    soup = BeautifulSoup(html, 'html.parser')

    rx_tag = soup.find(id="stream_rbc")  # Received Bytes Count
    tx_tag = soup.find(id="stream_sbc")  # Sent Bytes Count

    if rx_tag is None or tx_tag is None:
        raise ValueError("❌ Gagal menemukan RX/TX di HTML. Struktur halaman mungkin berubah.")

    rx = int(rx_tag.text.strip())
    tx = int(tx_tag.text.strip())

    return rx, tx

def generate_dummy_traffic(duration):
    try:
        print(f"▶️ Mengunduh file dummy selama {duration} detik...")
        dummy_url = f"http://speed.cloudflare.com/__down?bytes=500000000&t={int(time.time())}"
        with requests.get(dummy_url, stream=True, timeout=duration) as r:
            start_time = time.time()
            for _ in r.iter_content(chunk_size=1024 * 1024):
                if time.time() - start_time > duration:
                    break
    except Exception as e:
        print(f"⚠️ Gagal generate trafik: {e}")

def calculate_speed(start_rx, start_tx, end_rx, end_tx, duration):
    if end_tx < start_tx or end_rx < start_rx:
        print("⚠️ Peringatan: RX/TX akhir lebih kecil dari awal. Mungkin counter di-reset oleh router.")

    delta_rx = max(0, end_rx - start_rx)
    delta_tx = max(0, end_tx - start_tx)

    download_speed = delta_rx / duration / 125000  # byte → Mbps
    upload_speed   = delta_tx / duration / 125000
    return round(download_speed, 2), round(upload_speed, 2), delta_rx, delta_tx

def main():
    with requests.Session() as session:
        if not login_to_router(session):
            print("❌ Gagal login ke router.")
            return

        print("📶 Mengambil RX/TX awal...")
        html1 = fetch_stats_page(session)
        rx1, tx1 = get_rx_tx(html1)
        print(f"   RX awal: {rx1} byte")
        print(f"   TX awal: {tx1} byte")
        time.sleep(0.5)

        generate_dummy_traffic(DURATION)

        print("📶 Mengambil RX/TX akhir...")
        html2 = fetch_stats_page(session)
        rx2, tx2 = get_rx_tx(html2)
        print(f"   RX akhir: {rx2} byte")
        print(f"   TX akhir: {tx2} byte")

        dl_speed, ul_speed, delta_rx, delta_tx = calculate_speed(rx1, tx1, rx2, tx2, DURATION)

        print("\n📈 Kecepatan Internet (dalam {} detik):".format(DURATION))
        print(f"⬇️ Download : {dl_speed} Mbps ({delta_rx} byte data)")
        print(f"⬆️ Upload   : {ul_speed} Mbps ({delta_tx} byte data)")
        
if __name__ == "__main__":
    main()
