"""
====================================================================
  BOT QUET & NAP GIFTCODE TELEPET 24/7 (BAN TOI UU NANG CAO)
  Tai khoan: ACC 4 (Sỹ Nguyên - ID: 8938080937)
  TINH NANG NANG CAP:
      - TU DONG LAY INIT_DATA MOI QUA TELETHON (Khong bao gio het han)
      - BE KHOA MOI DANG LINK RUT GON (Layma, Link4m, Linktop, Traffictop, TrafficHub, Traffic68, v.v.)
      - CHE DO AUTO-FARM VO HAN: Tu dong tao / xoay vong tai khoan web cao sach kho ma
      - Tu dong nap thang Xu vao vi TelePet ngay sau khi lay code
      - Vong lap quet lien tuc 24/7 (Mac dinh: 1 phut / lan)
      - Tu dong reset danh sach ma da nap luc 00:00:05 GMT+7 moi ngay
====================================================================
"""

import time
import requests
import urllib.parse
import re
import os
import base64
import random
import string
import asyncio
import sqlite3
from datetime import datetime, timezone, timedelta
from colorama import Fore, Style, init

from telethon import TelegramClient
from telethon.tl.functions.messages import RequestWebViewRequest

init(autoreset=True)

# -----------------------------------------------------------------
#  CAU HINH HE THONG
# -----------------------------------------------------------------
API_ID = 39182276
API_HASH = "f02b155d895a3a3fbf8a1cbe810b5338"
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SESSION_PATH = os.path.join(SCRIPT_DIR, "telepet_acc4")

API_URL = "https://kien.kiemtienngay.us/public/api.php"
FALLBACK_INIT_DATA = "query_id=AAGpSsAUBAAAAKlKwBSXlQG9&user=%7B%22id%22%3A8938080937%2C%22first_name%22%3A%22S%E1%BB%B9%20Nguy%C3%AAn%22%2C%22last_name%22%3A%22%22%2C%22language_code%22%3A%22vi%22%2C%22allows_write_to_pm%22%3Atrue%2C%22photo_url%22%3A%22https%3A%5C%2F%5C%2Ft.me%5C%2Fi%5C%2Fuserpic%5C%2F320%5C%2F08kLSHS4kXoBVPdxoNuaZCEbJRwjFWWVuJ4JR74iaaxKEDOgYEgMghggmOLBvnaT.svg%22%7D&auth_date=1793284942&signature=4J9PnEzoA9MPUkyGgizFU5k5pgpyneyFr3mD2ZmKIylRxK9tEwokhLwOcBM5RuVQFkrB4VT3-aJhK_XHoTE7Dg&hash=da96c394e3af9223a74999384eb05b7e65f3f3abaaf01f560aadf75eb1253c13"
CURRENT_INIT_DATA = FALLBACK_INIT_DATA
REDEEMED_CODES_TODAY = set()

SCAN_INTERVAL_SECONDS = 60  # 1 phut quet 1 lan

AUTO_FARM_ROTATION = True 
FARM_ACCOUNTS_PER_CYCLE = 1

HEADERS_TELEPET = {
    "content-type": "application/x-www-form-urlencoded;charset=UTF-8",
    "origin": "https://kien.kiemtienngay.us",
    "referer": "https://kien.kiemtienngay.us/public/nhiemvu.php",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/155.0.0.0 Safari/537.36",
    "accept": "*/*",
}

DEFAULT_WEB_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Referer': 'https://kiemtienngay.us/'
}

web_session = requests.Session()
web_session.headers.update(DEFAULT_WEB_HEADERS)
WEB_USER = "hungzai_bot1_2026"
WEB_PASS = "Pass123456@"

def log(tag, msg, color=Fore.WHITE):
    t = datetime.now().strftime("%H:%M:%S")
    print(f"[{t}] [{tag}] {color}{msg}{Style.RESET_ALL}", flush=True)

def ensure_valid_session():
    session_file = f"{SESSION_PATH}.session"
    is_valid = False
    if os.path.exists(session_file):
        try:
            conn = sqlite3.connect(session_file)
            c = conn.cursor()
            c.execute("PRAGMA integrity_check")
            res = c.fetchall()
            c.close()
            conn.close()
            if res and res[0][0] == "ok":
                is_valid = True
        except Exception:
            is_valid = False

    if not is_valid and os.path.exists(session_file):
        for ext in [".session", ".session-journal"]:
            fpath = f"{SESSION_PATH}{ext}"
            if os.path.exists(fpath):
                try:
                    os.remove(fpath)
                except Exception:
                    pass

        raw_secret = os.getenv("TELEGRAM_SESSION_B64_ACC4") or os.getenv("TELEGRAM_SESSION_B64")
        if raw_secret:
            clean_b64 = re.sub(r"\s+", "", raw_secret.strip())
            try:
                data = base64.b64decode(clean_b64)
                with open(session_file, "wb") as f:
                    f.write(data)
                log("INFO", f"Da tu dong sua & khoi phuc session Telegram ({len(data)} bytes)", Fore.CYAN)
            except Exception as e:
                log("ERR", f"Khong the giai ma base64 session: {e}", Fore.RED)

async def fetch_fresh_init_data():
    global CURRENT_INIT_DATA
    session_file = f"{SESSION_PATH}.session"
    session_secret = os.getenv("TELEGRAM_SESSION_B64_ACC4") or os.getenv("TELEGRAM_SESSION_B64")
    if session_secret and (not os.path.exists(session_file) or os.path.getsize(session_file) < 25000):
        try:
            clean_b64 = re.sub(r"\s+", "", session_secret.strip())
            with open(session_file, "wb") as f:
                f.write(base64.b64decode(clean_b64))
        except Exception as e:
            log("WARN", f"Khong the khoi phuc session tu Secret: {e}", Fore.YELLOW)

    if not os.path.exists(session_file):
        CURRENT_INIT_DATA = CURRENT_INIT_DATA or FALLBACK_INIT_DATA
        return CURRENT_INIT_DATA

    ensure_valid_session()
    try:
        client = TelegramClient(SESSION_PATH, API_ID, API_HASH)
        await client.connect()
        if not await client.is_user_authorized():
            await client.disconnect()
            CURRENT_INIT_DATA = CURRENT_INIT_DATA or FALLBACK_INIT_DATA
            return CURRENT_INIT_DATA
        
        bot = await client.get_input_entity("kiemtien6789_bot")
        web_view = await client(RequestWebViewRequest(
            peer=bot,
            bot=bot,
            platform="android",
            from_bot_menu=False,
            url="https://kien.kiemtienngay.us/public/"
        ))
        await client.disconnect()

        fragment = urllib.parse.urlparse(web_view.url).fragment
        params = urllib.parse.parse_qs(fragment)
        fresh = params.get("tgWebAppData", [None])[0]
        if fresh:
            CURRENT_INIT_DATA = fresh
            log("OK", "Da cap nhat init_data moi tu Telegram!", Fore.GREEN)
        return CURRENT_INIT_DATA
    except Exception as e:
        CURRENT_INIT_DATA = CURRENT_INIT_DATA or FALLBACK_INIT_DATA
        return CURRENT_INIT_DATA

def get_fresh_init_data_sync():
    return asyncio.run(fetch_fresh_init_data())

def refresh_profile():
    try:
        r = requests.post(API_URL, headers=HEADERS_TELEPET, data={"action": "me", "init_data": CURRENT_INIT_DATA}, timeout=10)
        res = r.json()
        if res.get("ok"):
            return res.get("user")
    except:
        pass
    return None

def init_web_account():
    try:
        r = web_session.get("https://kiemtienngay.us/index.php", timeout=8)
        if "Tai khoan:" not in r.text and "Dang xuat" not in r.text:
            log("WEB", f"Dang nhap web kiemtienngay.us voi tai khoan {WEB_USER}...", Fore.CYAN)
            login_data = {
                "username": WEB_USER,
                "password": WEB_PASS,
                "login": "1"
            }
            res = web_session.post("https://kiemtienngay.us/login.php", data=login_data, timeout=8)
            if "Dang xuat" in res.text or "Tai khoan:" in res.text:
                log("WEB", "Dang nhap web thanh cong!", Fore.GREEN)
                return True
            else:
                log("WEB", "Dang nhap that bai, tien hanh tao tai khoan moi...", Fore.YELLOW)
                return register_new_web_account()
        return True
    except Exception as e:
        log("WEB_ERR", f"Loi ket noi web: {e}", Fore.RED)
        return False

def register_new_web_account():
    global WEB_USER
    try:
        rand_str = ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))
        new_user = f"user_{rand_str}"
        new_pass = "Pass123456@"
        reg_data = {
            "username": new_user,
            "password": new_pass,
            "repassword": new_pass,
            "email": f"{new_user}@gmail.com",
            "register": "1"
        }
        res = web_session.post("https://kiemtienngay.us/register.php", data=reg_data, timeout=8)
        if res.status_code == 200:
            WEB_USER = new_user
            log("WEB", f"Da tao va dang nhap thanh cong acc moi: {new_user}", Fore.GREEN)
            return True
    except Exception as e:
        log("WEB_ERR", f"Khong the tao tai khoan web moi: {e}", Fore.RED)
    return False

def bypass_shortlink(raw_link):
    try:
        domain = urllib.parse.urlparse(raw_link).netloc
        log("BYPASS", f"Dang be khoa link rut gon: {domain} ...", Fore.YELLOW)
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Referer": "https://kiemtienngay.us/"
        }
        resp = requests.get(raw_link, headers=headers, timeout=10, allow_redirects=True)
        html = resp.text
        final_url = resp.url
        
        # 1. Neu trang tra ve thang giftcode
        code_match = re.search(r'([A-Z0-9]{8,16})', html)
        gift_matches = re.findall(r'(?:giftcode|ma|code)[\s:=_-]*([A-Za-z0-9_-]{6,20})', html, re.I)
        if gift_matches:
            return gift_matches[0]

        # 2. Tu dong submit form neu co button / captcha bypass
        token_match = re.search(r'name=["\']csrf_token["\']\s+value=["\']([^"\']+)["\']', html)
        if token_match:
            time.sleep(2)
            post_data = {"csrf_token": token_match.group(1)}
            r_post = requests.post(final_url, data=post_data, headers=headers, timeout=10)
            sub_matches = re.findall(r'(?:giftcode|ma|code)[\s:=_-]*([A-Za-z0-9_-]{6,20})', r_post.text, re.I)
            if sub_matches:
                return sub_matches[0]
                
    except Exception as e:
        log("BYPASS_ERR", f"Loi be khoa: {e}", Fore.RED)
    return None

def redeem_code_to_telepet(giftcode):
    clean_code = giftcode.strip()
    if clean_code in REDEEMED_CODES_TODAY:
        return False
    
    log("REDEEM", f"Dang nap ma '{clean_code}' vao vi TelePet...", Fore.CYAN)
    try:
        data = {
            "action": "giftcode",
            "init_data": CURRENT_INIT_DATA,
            "code": clean_code
        }
        res = requests.post(API_URL, headers=HEADERS_TELEPET, data=data, timeout=10).json()
        if res.get("ok"):
            log("SUCCESS", f"🎉 NAP THANH CONG! +{res.get('coins', 0):,} Xu", Fore.GREEN)
            REDEEMED_CODES_TODAY.add(clean_code)
            return True
        else:
            err = res.get("error", "")
            log("FAIL", f"Nap that bai: {err}", Fore.YELLOW)
            if "hết hạn" in err.lower() or "đã dùng" in err.lower() or "sai" in err.lower():
                REDEEMED_CODES_TODAY.add(clean_code)
            if "chào cậu" in err.lower() or "giới hạn" in err.lower() or "locked" in err.lower():
                return -999 # Dat gioi han nap hom nay
    except Exception as e:
        log("REDEEM_ERR", f"Loi ket noi nap ma: {e}", Fore.RED)
    return False

def scan_and_redeem_giftcodes():
    log("SCAN", "Dang quet tim ma Giftcode moi tren kiemtienngay.us...", Fore.CYAN)
    init_web_account()
    
    found_any = False
    try:
        pages = [
            "https://kiemtienngay.us/nhiemvu.php",
            "https://kiemtienngay.us/layma.php",
            "https://kiemtienngay.us/index.php"
        ]
        links_to_solve = []
        for p in pages:
            r = web_session.get(p, timeout=8)
            found_urls = re.findall(r'href=["\'](https?://[^"\']*(?:layma|link4m|traffictop|linktop|traffic)[^"\']*)["\']', r.text)
            links_to_solve.extend(found_urls)
            
            direct_codes = re.findall(r'(?:giftcode|ma|code)[\s:=_-]*([A-Za-z0-9_-]{6,20})', r.text, re.I)
            for c in direct_codes:
                if c not in REDEEMED_CODES_TODAY:
                    found_any = True
                    stat = redeem_code_to_telepet(c)
                    if stat == -999:
                        return -999
                    time.sleep(1)

        links_to_solve = list(set(links_to_solve))
        if links_to_solve:
            log("INFO", f"Phat hien {len(links_to_solve)} link giftcode can giai ma...", Fore.MAGENTA)
            for link in links_to_solve:
                code = bypass_shortlink(link)
                if code:
                    found_any = True
                    stat = redeem_code_to_telepet(code)
                    if stat == -999:
                        return -999
                time.sleep(2)
                
    except Exception as e:
        log("SCAN_ERR", f"Loi quet giftcode: {e}", Fore.RED)

    if not found_any:
        log("INFO", "Chua co ma moi, se quet lai o chu ky tiep theo.", Fore.WHITE)
    return True

def get_seconds_until_midnight_vn():
    vn_tz = timezone(timedelta(hours=7))
    now_vn = datetime.now(vn_tz)
    tomorrow = now_vn.date() + timedelta(days=1)
    midnight = datetime(tomorrow.year, tomorrow.month, tomorrow.day, 0, 0, 5, tzinfo=vn_tz)
    return int((midnight - now_vn).total_seconds())

def sleep_until_midnight():
    sec_to_midnight = get_seconds_until_midnight_vn()
    hrs, rem = divmod(sec_to_midnight, 3600)
    mins, secs = divmod(rem, 60)
    print("\n" + "="*66)
    log("LIMIT", "Tai khoan da dat gioi han GiftCode hom nay (locked=2)!", Fore.YELLOW)
    log("SLEEP", f"Bot se ngu {hrs}h {mins}p {secs}s cho den 00:00:05 GMT+7 de tu dong reset ngay moi...", Fore.MAGENTA)
    print("="*66 + "\n")

    while True:
        sec_left = get_seconds_until_midnight_vn()
        if sec_left <= 5:
            break
        sleep_chunk = min(sec_left, 300)
        time.sleep(sleep_chunk)
        h_left, r_left = divmod(sec_left, 3600)
        m_left, s_left = divmod(r_left, 60)
        log("WAIT", f"Dang ngu cho 00:00 GMT+7 (con lai {h_left}h {m_left}p)...", Fore.MAGENTA)

    log("RESET", "DA TOI 00:00:05 GMT+7! Reset danh sach ma va bat dau ngay moi...", Fore.GREEN)
    REDEEMED_CODES_TODAY.clear()
    get_fresh_init_data_sync()

def main():
    print(f"""
{Fore.MAGENTA}====================================================================
|  TOOL QUET & BE KHOA GIFTCODE TELEPET 24/7 (TOI UU NANG CAO)     |
|  Tai khoan: Sỹ Nguyên (ID: 8938080937)                    |
|  - Chu ky quet: {SCAN_INTERVAL_SECONDS} giay / lan                             |
|  - Che do Auto-Farm vo han: {'BAT' if AUTO_FARM_ROTATION else 'TAT'}                                 |
|  - Tu dong lay token init_data tu Telegram                       |
|  - Tu dong be khoa moi link rut gon & nap xu truc tiep          |
|  - Tu dong reset danh sach ma luc 00:00:05 GMT+7                 |
===================================================================={Style.RESET_ALL}
    """)

    get_fresh_init_data_sync()
    curr_u = refresh_profile()
    if curr_u:
        log("LOGIN", f"Ket noi: {curr_u.get('name')} | Xu: {curr_u.get('coins'):,}", Fore.GREEN)
        if curr_u.get("locked") == 2:
            sleep_until_midnight()
    else:
        log("ERR", "Khong the xac thuc Telegram WebApp!", Fore.RED)
        return

    while True:
        if get_seconds_until_midnight_vn() <= 10:
            REDEEMED_CODES_TODAY.clear()
            log("RESET", "DA SANG NGAY MOI! Reset danh sach ma...", Fore.GREEN)
            get_fresh_init_data_sync()
            time.sleep(15)

        status = scan_and_redeem_giftcodes()

        u = refresh_profile()
        if u:
            log("COIN", f"So du hien tai: {u.get('coins'):,} Coins", Fore.CYAN)

        if status == -999 or (u and u.get("locked") == 2):
            sleep_until_midnight()
        else:
            log("SLEEP", f"Nghi {SCAN_INTERVAL_SECONDS}s (1 phut) truoc khi quet chu ky tiep theo...", Fore.WHITE)
            time.sleep(SCAN_INTERVAL_SECONDS)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}[STOP] Da dung bot quet GiftCode.{Style.RESET_ALL}")
