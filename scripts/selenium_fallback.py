# Selenium fallback (abre Chrome visível por padrão)
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import os
headless = os.getenv('CHROME_HEADLESS','false').lower() in ('1','true','yes')
options = Options()
if headless:
    options.add_argument('--headless=new')
# Important: do NOT set headless when CHROME_HEADLESS=false to open visible browser
driver = webdriver.Chrome(ChromeDriverManager().install(), options=options)
driver.get('https://www.google.com')
print('Selenium abriu o navegador. Título:', driver.title)
driver.quit()
