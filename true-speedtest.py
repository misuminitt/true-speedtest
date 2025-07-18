import time
import base64
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

# =============== CONFIG ================
BASE_URL    = "http://192.168.1.1/"
LOGIN_URL   = "goform/webLogin"
STATS_PAGE  = "state/wireless_state.asp"
USERNAME    = "admin"
PASSWORD    = "admin"
DURATION    = 30  # durasi pengukuran dalam detik
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

def get_rx_tx(session):
    res = session.get(urljoin(BASE_URL, STATS_PAGE), headers=HEADERS, timeout=5)

    # Simpan halaman untuk debugging
    with open("debug_stats.html", "w", encoding="utf-8") as f:
        f.write(res.text)
    print("📄 Halaman stats disimpan sebagai debug_stats.html")

    soup = BeautifulSoup(res.text, "html.parser")
    rows = soup.find_all("tr")

    rx = tx = None
    for row in rows:
        cells = row.find_all("td")
        if len(cells) >= 2:
            label = cells[0].text.strip().lower()
            value = cells[1].text.strip().replace(",", "")
            if "received bytes count" in label:
                rx = int(value)
            elif "sent bytes count" in label:
                tx = int(value)

    if rx is None or tx is None:
        raise ValueError("Gagal menemukan RX/TX dari halaman.")

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
        rx1, tx1 = get_rx_tx(session)
        print(f"   RX awal: {rx1} byte")
        print(f"   TX awal: {tx1} byte")
        time.sleep(0.5)

        generate_dummy_traffic(DURATION)

        print("📶 Mengambil RX/TX akhir...")
        rx2, tx2 = get_rx_tx(session)
        print(f"   RX akhir: {rx2} byte")
        print(f"   TX akhir: {tx2} byte")

        dl_speed, ul_speed, delta_rx, delta_tx = calculate_speed(rx1, tx1, rx2, tx2, DURATION)

        print("\n📈 Kecepatan Internet (dalam {} detik):".format(DURATION))
        print(f"⬇️ Download : {dl_speed} Mbps ({delta_rx} byte data)")
        print(f"⬆️ Upload   : {ul_speed} Mbps ({delta_tx} byte data)")

if __name__ == "__main__":
    main()
