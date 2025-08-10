from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import time

REPORT_LOG = "report_log.txt"
ADMIN_URL = "http://localhost/login.php"

def admin_login(driver):
    driver.get(ADMIN_URL)
    driver.find_element("name", "username").send_keys("admin")
    driver.find_element("name", "password").send_keys("admin1234")
    driver.find_element("tag name", "form").submit()
    time.sleep(1)

opts = Options()
opts.add_argument("--headless")
driver = webdriver.Chrome(options=opts)

admin_login(driver)

with open(REPORT_LOG) as f:
    urls = [u.strip() for u in f if u.strip()]

for url in urls:
    print(f"[BOT] Visiting: {url}")
    driver.get(url)
    time.sleep(3) 
driver.quit()
