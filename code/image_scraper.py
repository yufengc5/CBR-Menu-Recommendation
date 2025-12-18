'''
This program tries to fetch the first image of a Google search for a specific query.

It is used to get the images for the dishes.
'''

import time
import os
import io
import re
import hashlib
import base64
from typing import Optional

import requests
from PIL import Image

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import StaleElementReferenceException

BLOCKED_HOST_FRAGMENTS = [
    "google.com",
    "gstatic.com",
    "fonts.gstatic.com",
]

# Where Flask can serve files from:
STATIC_IMG_DIR = os.path.join("static", "dish_images")


def slugify(s: str) -> str:
    return re.sub(r"[^a-zA-Z0-9_-]+", "_", s).strip("_").lower()


def handle_consent_form(wd):
    """Try to click the Google consent button."""
    try:
        time.sleep(1)

        # Exact element: <div class="QS5gu sy4vM">全部接受</div>
        try:
            btn = wd.find_element(
                By.XPATH,
                "//div[contains(@class,'QS5gu') and contains(@class,'sy4vM') and contains(., '全部接受')]"
            )
            wd.execute_script("arguments[0].click();", btn)
            time.sleep(1)
            return
        except Exception:
            pass

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
            txt = (el.text or "").strip()
            if any(k in txt for k in consent_keywords):
                try:
                    wd.execute_script("arguments[0].click();", el)
                    time.sleep(1)
                    return
                except Exception:
                    continue

    except StaleElementReferenceException:
        pass
    except Exception:
        pass


def get_webdriver():
    chrome_options = Options()
    chrome_options.add_argument("--headless=new")  # enable if you want headless
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument(
        "user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 13_1) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115 Safari/537.36"
    )
    return webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)


def get_first_non_google_img_src(wd) -> Optional[str]:
    imgs = wd.find_elements(By.TAG_NAME, "img")

    for img in imgs:
        src = img.get_attribute("src") or ""
        if not src:
            continue

        # Skip Google / gstatic / fonts
        if any(fragment in src for fragment in BLOCKED_HOST_FRAGMENTS):
            continue

        # Accept:
        # - data:image/jpeg;base64,...
        # - https://some-site.com/image.jpg
        return src

    return None


def fetch_one_image_src(query: str, wd) -> Optional[str]:
    search_url = f"https://www.google.com/search?tbm=isch&q={query}"
    wd.get(search_url)

    handle_consent_form(wd)
    time.sleep(2)

    return get_first_non_google_img_src(wd)


def persist_image(folder_path: str, dish_name: str, src: str) -> Optional[str]:
    """
    Save image to folder_path and return filename (not full path).
    Handles both:
      - http(s) URLs
      - data:image/...;base64,... URLs
    """
    try:
        if src.startswith("data:image"):
            # data:image/jpeg;base64,AAAA
            _, b64data = src.split(",", 1)
            image_bytes = base64.b64decode(b64data)
        else:
            image_bytes = requests.get(src, timeout=10).content

        img = Image.open(io.BytesIO(image_bytes)).convert("RGB")

        os.makedirs(folder_path, exist_ok=True)

        safe = slugify(dish_name)
        out_name = f"{safe}_{hashlib.sha1(image_bytes).hexdigest()[:10]}.jpg"
        out_path = os.path.join(folder_path, out_name)

        img.save(out_path, "JPEG", quality=85)
        return out_name

    except Exception as e:
        print(f"[image] ERROR saving image for '{dish_name}': {e}")
        return None


def get_cached_image_filename(dish_name: str, folder_path: str = STATIC_IMG_DIR) -> Optional[str]:
    """If already saved, return cached filename."""
    os.makedirs(folder_path, exist_ok=True)
    prefix = slugify(dish_name) + "_"
    for fn in os.listdir(folder_path):
        if fn.startswith(prefix) and fn.endswith(".jpg"):
            return fn
    return None


def get_or_fetch_dish_image(dish_name: str) -> Optional[str]:
    """
    Main function used by Flask.
    Returns a filename under static/dish_images/ or None.
    Caches results (if already downloaded, reuses).
    """
    cached = get_cached_image_filename(dish_name, STATIC_IMG_DIR)
    if cached:
        return cached

    wd = get_webdriver()
    try:
        src = fetch_one_image_src(dish_name, wd)
        if not src:
            return None
        return persist_image(STATIC_IMG_DIR, dish_name, src)
    finally:
        wd.quit()


# Optional: local test
if __name__ == "__main__":
    test = "White Chocolate Thumbprint Cookies"
    fn = get_or_fetch_dish_image(test)
    print("Saved:", fn)
