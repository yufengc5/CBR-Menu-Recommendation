import time
import requests
import os
import io
import hashlib
from typing import Optional

from PIL import Image

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import StaleElementReferenceException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

BLOCKED_HOST_FRAGMENTS = [
    "google.com",
    "gstatic.com",
    "fonts.gstatic.com",
]

def handle_consent_form(wd):
    """Try to click the Google consent button (including Chinese 全部接受)."""
    try:
        time.sleep(1)

        # First: your exact element: <div class="QS5gu sy4vM">全部接受</div>
        try:
            btn = wd.find_element(
                By.XPATH,
                "//div[contains(@class,'QS5gu') and contains(@class,'sy4vM') and contains(., '全部接受')]"
            )
            wd.execute_script("arguments[0].click();", btn)
            print("✔ Consent clicked: 全部接受")
            time.sleep(1)
            return
        except Exception:
            pass

        # Fallback: scan other buttons/divs/spans for known consent keywords
        consent_keywords = [
            "Accept", "I agree", "Agree", "Accept all",
            "Aceptar", "Aceptar todo",
            "Tout accepter",
            "Alle akzeptieren",
            "Accetta tutto",
            "接受", "接受全部", "全部接受", "同意", "同意所有", "同意全部",
        ]

        elements = wd.find_elements(By.XPATH, "//button | //div | //span")
        for el in elements:
            txt = el.text.strip()
            if any(k in txt for k in consent_keywords):
                try:
                    wd.execute_script("arguments[0].click();", el)
                    print(f"✔ Consent clicked ({txt})")
                    time.sleep(1)
                    return
                except Exception:
                    continue

        print("ℹ No recognizable consent popup detected")

    except StaleElementReferenceException:
        # If the element disappears while we’re scanning, just ignore it
        print("ℹ Consent element went stale, ignoring.")
    except Exception as e:
        print("❌ Error handling consent:", e)

def get_webdriver():
    chrome_options = Options()
    # chrome_options.add_argument("--headless=new")  # uncomment if you want headless
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument(
        "user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 13_1) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115 Safari/537.36"
    )
    return webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)


def get_first_non_google_img_src(wd):
    imgs = wd.find_elements(By.TAG_NAME, "img")
    print(f"Found {len(imgs)} <img> elements")

    for img in imgs:
        src = img.get_attribute("src") or ""
        if not src:
            continue

        # Skip Google / gstatic / fonts
        if any(fragment in src for fragment in BLOCKED_HOST_FRAGMENTS):
            continue

        # This will accept things like:
        # - data:image/jpeg;base64,...
        # - https://some-site.com/image.jpg
        print("✅ Selected src:", src[:120], "...")
        return src

    print("⚠ No non-Google <img> found")
    return None

def fetch_one_image_url(query: str, wd):
    search_url = f"https://www.google.com/search?tbm=isch&q={query}"
    wd.get(search_url)

    handle_consent_form(wd)
    time.sleep(2)

    src = get_first_non_google_img_src(wd)
    return src


def persist_image(folder_path: str, file_name: str, url: str):
    try:
        image_content = requests.get(url, timeout=5).content
    except Exception as e:
        print(f"ERROR - Could not download {url} - {e}")
        return

    try:
        image_file = io.BytesIO(image_content)
        image = Image.open(image_file).convert("RGB")

        if not os.path.exists(folder_path):
            os.makedirs(folder_path)

        file_path = os.path.join(
            folder_path, f"{file_name}_{hashlib.sha1(image_content).hexdigest()[:10]}.jpg"
        )

        with open(file_path, "wb") as f:
            image.save(f, "JPEG", quality=85)

        print(f"SUCCESS - saved {url} - as {file_path}")

    except Exception as e:
        print(f"ERROR - Could not save {url} - {e}")


if __name__ == "__main__":
    wd = get_webdriver()

    try:
        queries = ["White Chocolate Thumbprint Cookies"]
        save_path = "downloaded_images"

        for query in queries:
            print(f"\n=== QUERY: {query} ===")
            image_url = fetch_one_image_url(query, wd=wd)

            if image_url:
                persist_image(save_path, query.replace(" ", "_"), image_url)
            else:
                print(f"⚠ No image found for query: {query}")

    finally:
        wd.quit()
