import io
import re

from PIL import Image, ImageFilter, ImageEnhance

try:
    import pytesseract
    import platform

    if platform.system() == "Windows":
        tess = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
        import os

        if os.path.isfile(tess):
            pytesseract.pytesseract.tesseract_cmd = tess
    CAPTCHA_OCR_AVAILABLE = True
except ImportError:
    CAPTCHA_OCR_AVAILABLE = False

from selenium.webdriver.common.by import By


def remove_horizontal_lines(img):
    w, h = img.size
    pixels = img.load()
    line_rows = set()

    for y in range(h):
        dark_count = 0
        current_run = 0
        max_run = 0
        for x in range(w):
            if pixels[x, y] < 128:
                dark_count += 1
                current_run += 1
                max_run = max(max_run, current_run)
            else:
                current_run = 0
        if max_run > w * 0.5 and dark_count > w * 0.6:
            line_rows.add(y)

    for y in line_rows:
        for x in range(w):
            is_thin = True
            for dy in range(-3, 4):
                ny = y + dy
                if 0 <= ny < h and ny not in line_rows:
                    if pixels[x, ny] < 128:
                        is_thin = False
                        break
            if is_thin:
                for dy in range(-1, 2):
                    ny = y + dy
                    if 0 <= ny < h:
                        pixels[x, ny] = 255

    return img


def solve_captcha(driver, captcha_img_id="user_regCaptchaImg"):
    if not CAPTCHA_OCR_AVAILABLE:
        return None

    try:
        from PIL import ImageOps

        captcha_img = driver.find_element(By.ID, captcha_img_id)
        img_data = captcha_img.screenshot_as_png
        if not img_data:
            return None

        best_text = None

        for approach in ["remove_lines", "clean", "raw"]:
            try:
                img = Image.open(io.BytesIO(img_data))
                img = img.convert("L")
                w, h = img.size
                img = img.resize((w * 4, h * 4), Image.LANCZOS)

                if approach == "remove_lines":
                    img = img.point(lambda x: 0 if x < 160 else 255)
                    img = remove_horizontal_lines(img)
                    img = img.filter(ImageFilter.MedianFilter(3))
                elif approach == "clean":
                    enhancer = ImageEnhance.Contrast(img)
                    img = enhancer.enhance(2.0)
                    img = img.point(lambda x: 0 if x < 150 else 255)
                    img = img.filter(ImageFilter.MedianFilter(3))
                elif approach == "raw":
                    enhancer = ImageEnhance.Contrast(img)
                    img = enhancer.enhance(1.5)

                for psm in ["--psm 7", "--psm 8", "--psm 13"]:
                    config = f"{psm} --oem 3 " "-c tessedit_char_whitelist=0123456789"
                    text = pytesseract.image_to_string(img, config=config).strip()
                    text = re.sub(r"\D", "", text)

                    if len(text) == 4:
                        return text
                    elif len(text) > 4 and best_text is None:
                        best_text = text[:4]
            except Exception:
                continue

        return best_text
    except Exception:
        return None
