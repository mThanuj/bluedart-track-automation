import csv
import os
import re
import time
from datetime import datetime

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import NoSuchElementException, TimeoutException

from .captcha import solve_captcha, CAPTCHA_OCR_AVAILABLE

BLUEDART_URL = "https://www.bluedart.com/"
OUTPUT_DIR = "output"
RESULTS_CSV = os.path.join(OUTPUT_DIR, "results.csv")
SCREENSHOT_DIR = os.path.join(OUTPUT_DIR, "screenshots")


def open_tracking_page(driver):
    driver.get(BLUEDART_URL)
    try:
        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.ID, "trackingNoTrackDart"))
        )
    except TimeoutException:
        driver.get(BLUEDART_URL)
        time.sleep(5)
        try:
            WebDriverWait(driver, 30).until(
                EC.presence_of_element_located((By.ID, "trackingNoTrackDart"))
            )
        except TimeoutException:
            raise RuntimeError("Could not load BlueDart tracking page.")

    for sel in ["#onetrust-accept-btn-handler", ".cookie-accept", "#acceptCookies"]:
        try:
            btn = driver.find_element(By.CSS_SELECTOR, sel)
            if btn.is_displayed():
                btn.click()
                time.sleep(1)
                break
        except Exception:
            continue


def _ensure_form_visible(driver):
    try:
        el = driver.find_element(By.ID, "trackingNoTrackDart")
        if el.is_displayed():
            return
    except NoSuchElementException:
        pass

    for btn_id in ["upArrow", "testCall"]:
        try:
            el = driver.find_element(By.ID, btn_id)
            driver.execute_script("arguments[0].click();", el)
            time.sleep(1)
            return
        except NoSuchElementException:
            continue


def enter_waybill(driver, waybill):
    _ensure_form_visible(driver)
    textarea = WebDriverWait(driver, 15).until(
        EC.element_to_be_clickable((By.ID, "trackingNoTrackDart"))
    )
    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", textarea)
    time.sleep(0.3)

    try:
        textarea.clear()
    except Exception:
        driver.execute_script("arguments[0].value = '';", textarea)
    time.sleep(0.1)

    try:
        textarea.send_keys(waybill)
    except Exception:
        driver.execute_script("arguments[0].value = arguments[1];", textarea, waybill)
        driver.execute_script(
            "arguments[0].dispatchEvent(new Event('input', {bubbles: true}));", textarea
        )


def refresh_captcha(driver):
    for el_id in ["refreshCaptcha", "user_regCaptchaImg"]:
        try:
            driver.find_element(By.ID, el_id).click()
            time.sleep(1)
            return
        except NoSuchElementException:
            continue


def handle_captcha(driver, auto_solve=True):
    if auto_solve and CAPTCHA_OCR_AVAILABLE:
        for _ in range(3):
            text = solve_captcha(driver)
            if text:
                inp = driver.find_element(By.ID, "UserCaptchaCode")
                inp.clear()
                inp.send_keys(text)
                return text
            refresh_captcha(driver)
        print("  OCR failed. Enter captcha manually.")

    print("\n  CAPTCHA — MANUAL INPUT (r=refresh, q=quit)")
    while True:
        try:
            text = input("  >> CAPTCHA: ").strip()
        except (EOFError, KeyboardInterrupt):
            return None
        if text.lower() == "q":
            return None
        if text.lower() == "r":
            refresh_captcha(driver)
            continue
        if not text:
            continue
        inp = driver.find_element(By.ID, "UserCaptchaCode")
        inp.clear()
        inp.send_keys(text)
        return text


def submit_tracking(driver):
    try:
        btn = driver.find_element(By.ID, "goBtnTrackDart")
        driver.execute_script("arguments[0].scrollIntoView(true);", btn)
        driver.execute_script("arguments[0].click();", btn)
        return True
    except Exception:
        return False


def is_captcha_error(driver):
    try:
        body = driver.find_element(By.TAG_NAME, "body").text.lower()
        return any(
            p in body for p in ["invalid captcha", "incorrect captcha", "wrong captcha"]
        )
    except Exception:
        return False


def wait_for_results(driver, timeout=5):
    try:
        WebDriverWait(driver, timeout).until(
            lambda d: len(d.find_elements(By.TAG_NAME, "table")) > 0
        )
        time.sleep(0.3)
        return True
    except TimeoutException:
        return False


def _click_status_scan_tab(driver):
    try:
        for link in driver.find_elements(By.TAG_NAME, "a"):
            if "status and scan" in link.text.strip().lower():
                driver.execute_script("arguments[0].click();", link)
                time.sleep(1)
                return True
    except Exception:
        pass

    for sel in ["a[data-toggle='tab'][href*='scan']", ".nav-tabs a", ".nav-link"]:
        try:
            for tab in driver.find_elements(By.CSS_SELECTOR, sel):
                if "scan" in tab.text.strip().lower():
                    driver.execute_script("arguments[0].click();", tab)
                    time.sleep(1)
                    return True
        except Exception:
            continue
    return False


def extract_results(driver):
    _click_status_scan_tab(driver)
    results = []

    for sel in [
        ".tab-pane.active table",
        ".table-bordered",
        "table.table",
        ".portlet-body table",
    ]:
        for table in driver.find_elements(By.CSS_SELECTOR, sel):
            for row in table.find_elements(By.TAG_NAME, "tr"):
                ths = row.find_elements(By.TAG_NAME, "th")
                cells = row.find_elements(By.TAG_NAME, "td")
                if ths:
                    h = [t.text.strip() for t in ths if t.text.strip()]
                    if h:
                        results.append({"type": "header", "columns": h})
                elif cells:
                    d = [c.text.strip() for c in cells]
                    if any(d):
                        results.append({"type": "row", "data": d})
            if results:
                return results

    for table in driver.find_elements(By.TAG_NAME, "table"):
        for row in table.find_elements(By.TAG_NAME, "tr"):
            ths = row.find_elements(By.TAG_NAME, "th")
            cells = row.find_elements(By.TAG_NAME, "td")
            if ths:
                h = [t.text.strip() for t in ths if t.text.strip()]
                if h:
                    results.append({"type": "header", "columns": h})
            elif cells:
                d = [c.text.strip() for c in cells]
                if any(d):
                    results.append({"type": "row", "data": d})
    if results:
        return results

    for sel in [".portlet-boundary_track_resultportlet_WAR_Track_Dartportlet_"]:
        try:
            portlet = driver.find_element(By.CSS_SELECTOR, sel)
            for line in portlet.text.strip().split("\n"):
                line = line.strip()
                if line:
                    results.append({"type": "text", "data": line})
            if results:
                return results
        except NoSuchElementException:
            continue

    try:
        for line in driver.find_element(By.TAG_NAME, "body").text.split("\n")[:80]:
            line = line.strip()
            if line:
                results.append({"type": "page_text", "data": line})
    except Exception:
        pass

    return results


def format_table(waybill, results):
    lines = [f"\n  TRACKING RESULTS FOR: {waybill}\n"]
    headers = []
    rows = []

    for item in results:
        if item["type"] == "header":
            headers = item["columns"]
        elif item["type"] == "row":
            rows.append(item["data"])

    if not rows:
        return "\n".join(lines) + "  No results found.\n"

    if not headers:
        headers = [f"Col {i+1}" for i in range(max(len(r) for r in rows))]

    nc = len(headers)
    cw = [len(h) for h in headers]
    for row in rows:
        for i, cell in enumerate(row[:nc]):
            if i < len(cw):
                cw[i] = max(cw[i], len(str(cell)))
    cw = [w + 2 for w in cw]

    sep = "+" + "+".join("-" * w for w in cw) + "+"
    fmt = "|" + "|".join(f" {{:<{w}}} " for w in cw) + "|"

    lines.append("  " + sep)
    lines.append("  " + fmt.format(*headers))
    lines.append("  " + sep)
    for row in rows:
        padded = [str(row[i]) if i < len(row) else "" for i in range(nc)]
        lines.append("  " + fmt.format(*padded))
    lines.append("  " + sep + "\n")
    return "\n".join(lines)


def take_screenshot(driver, waybill):
    try:
        os.makedirs(SCREENSHOT_DIR, exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        path = os.path.join(SCREENSHOT_DIR, f"result_{waybill}_{ts}.png")
        driver.save_screenshot(path)
        return path
    except Exception:
        return ""


def save_csv(waybill, status, details, url, screenshot):
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    exists = os.path.isfile(RESULTS_CSV)
    with open(RESULTS_CSV, "a", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        if not exists:
            w.writerow(
                ["Timestamp", "Waybill", "Status", "Details", "URL", "Screenshot"]
            )
        w.writerow(
            [
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                waybill,
                status,
                details,
                url,
                screenshot,
            ]
        )


def process_waybill(driver, waybill, auto_solve=True, index=None, total=None):
    waybill = waybill.strip()
    if not waybill:
        return None

    prefix = f"  [{index}/{total}] " if index and total else "  "
    print(f"\n{'─' * 55}")
    print(f"{prefix}Tracking: {waybill}")
    print(f"{'─' * 55}")

    enter_waybill(driver, waybill)
    time.sleep(0.3)

    for retry in range(3):
        if retry > 0:
            print(f"  Retry {retry}/2...")
            enter_waybill(driver, waybill)
            time.sleep(0.3)

        captcha = handle_captcha(driver, auto_solve)
        if captcha is None:
            return None

        if not submit_tracking(driver):
            continue

        time.sleep(1)

        if is_captcha_error(driver):
            print("  Wrong captcha. Retrying...")
            refresh_captcha(driver)
            continue

        wait_for_results(driver)
        break
    else:
        print("  Failed after 3 attempts.")
        save_csv(waybill, "Failed", "", driver.current_url, "")
        return None

    results = extract_results(driver)
    has_data = any(item.get("type") == "row" for item in results)
    print(format_table(waybill, results))

    if has_data:
        try:
            from .visualizer import generate_visuals

            generate_visuals(results, waybill)
        except Exception as e:
            print(f"  Visualization error: {e}")

        screenshot = take_screenshot(driver, waybill)
    else:
        screenshot = ""

    detail_parts = []
    for item in results:
        if item.get("type") == "row":
            detail_parts.append(" | ".join(item.get("data", [])))
        elif item.get("type") in ("text", "page_text"):
            detail_parts.append(item.get("data", ""))
    details_str = " ;; ".join(detail_parts)[:2000]

    save_csv(
        waybill,
        "Completed" if has_data else "No Data",
        details_str,
        driver.current_url,
        screenshot,
    )
    return results


def process_waybills(driver, waybills, auto_solve=True):
    total = len(waybills)
    for i, wb in enumerate(waybills, 1):
        result = process_waybill(
            driver, wb, auto_solve=auto_solve, index=i, total=total
        )
        if result is None and i < total:
            print("\n  Stopped.")
            break
        if i < total:
            time.sleep(1)


def interactive_mode(driver, auto_solve=True):
    print("\n  BLUEDART TRACKER — INTERACTIVE MODE")
    print("  Enter waybills one at a time. Type 'q' to quit.\n")
    count = 0
    while True:
        try:
            wb = input("  >> Waybill: ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if wb.lower() in ("q", "quit", "exit"):
            break
        if not wb:
            continue
        count += 1
        process_waybill(driver, wb, auto_solve=auto_solve, index=count, total="N")
        time.sleep(1)


def batch_from_file(driver, filepath, auto_solve=True):
    if not os.path.isfile(filepath):
        print(f"  File not found: {filepath}")
        return
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
    waybills = [w.strip() for w in re.split(r"[,\s]+", content.strip()) if w.strip()]
    if not waybills:
        print(f"  No waybills in {filepath}")
        return
    print(f"  Loaded {len(waybills)} waybill(s) from {filepath}")
    process_waybills(driver, waybills, auto_solve=auto_solve)
