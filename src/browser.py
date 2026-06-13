import os
import json
import subprocess
import zipfile
import urllib.request

from selenium import webdriver
from selenium.webdriver.chrome.service import Service

CHROMEDRIVER_DIR = os.path.join(os.path.expanduser("~"), ".bluedart_chromedriver")
CHROMEDRIVER_EXE = os.path.join(CHROMEDRIVER_DIR, "chromedriver.exe")


def find_browser_path():
    paths = [
        r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe",
        r"C:\Program Files (x86)\BraveSoftware\Brave-Browser\Application\brave.exe",
        os.path.expanduser(
            r"~\AppData\Local\BraveSoftware\Brave-Browser\Application\brave.exe"
        ),
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        os.path.expanduser(r"~\AppData\Local\Google\Chrome\Application\chrome.exe"),
        r"C:\Program Files\Chromium\Application\chrome.exe",
        os.path.expanduser(r"~\AppData\Local\Chromium\Application\chrome.exe"),
    ]
    for p in paths:
        if os.path.isfile(p):
            return p
    return None


def get_browser_version(browser_path):
    try:
        r = subprocess.run(
            [
                "powershell",
                "-Command",
                f"(Get-Item '{browser_path}').VersionInfo.ProductVersion",
            ],
            capture_output=True,
            text=True,
            timeout=10,
        )
        return r.stdout.strip().split(".")[0]
    except Exception:
        return None


def download_chromedriver(version):
    os.makedirs(CHROMEDRIVER_DIR, exist_ok=True)

    if os.path.isfile(CHROMEDRIVER_EXE):
        try:
            r = subprocess.run(
                [CHROMEDRIVER_EXE, "--version"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if r.stdout and f"ChromeDriver {version}." in r.stdout:
                return CHROMEDRIVER_EXE
        except Exception:
            pass

    try:
        req = urllib.request.Request(
            "https://googlechromelabs.github.io/chrome-for-testing/known-good-versions-with-downloads.json",
            headers={"User-Agent": "Mozilla/5.0"},
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read())

        driver_url = None
        for entry in reversed(data.get("versions", [])):
            if entry.get("version", "").startswith(f"{version}."):
                for d in entry.get("downloads", {}).get("chromedriver", []):
                    if d.get("platform") == "win64":
                        driver_url = d.get("url")
                        break
                if driver_url:
                    break

        if not driver_url:
            return None

        zip_path = os.path.join(CHROMEDRIVER_DIR, "chromedriver.zip")
        urllib.request.urlretrieve(driver_url, zip_path)

        with zipfile.ZipFile(zip_path, "r") as z:
            for name in z.namelist():
                if name.endswith("chromedriver.exe"):
                    with z.open(name) as src, open(CHROMEDRIVER_EXE, "wb") as dst:
                        dst.write(src.read())
                    break

        os.remove(zip_path)
        return CHROMEDRIVER_EXE
    except Exception:
        return None


def create_driver(headless=False):
    options = webdriver.ChromeOptions()
    options.add_argument("--start-maximized")
    options.add_argument("--disable-notifications")
    options.add_argument("--disable-popup-blocking")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument(
        "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)
    options.page_load_strategy = "eager"

    if headless:
        options.add_argument("--headless=new")
        options.add_argument("--disable-gpu")

    browser_path = find_browser_path()
    driver = None

    if browser_path:
        options.binary_location = browser_path
        is_brave = "brave" in os.path.basename(browser_path).lower()
        if is_brave:
            version = get_browser_version(browser_path)
            if version:
                driver_path = download_chromedriver(version)
                if driver_path and os.path.isfile(driver_path):
                    try:
                        driver = webdriver.Chrome(
                            service=Service(executable_path=driver_path),
                            options=options,
                        )
                    except Exception:
                        pass

    if driver is None:
        try:
            driver = webdriver.Chrome(options=options)
        except Exception:
            try:
                from webdriver_manager.chrome import ChromeDriverManager

                driver = webdriver.Chrome(
                    service=Service(ChromeDriverManager().install()), options=options
                )
            except Exception as e3:
                raise RuntimeError(f"Could not start browser: {e3}")

    try:
        driver.execute_cdp_cmd(
            "Page.addScriptToEvaluateOnNewDocument",
            {
                "source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined});"
            },
        )
    except Exception:
        pass

    return driver
