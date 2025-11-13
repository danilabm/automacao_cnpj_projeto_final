from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import os

# Lê configuração do .env (se existir)
headless = os.getenv('CHROME_HEADLESS', 'false').lower() in ('1', 'true', 'yes')

options = Options()
if headless:
    options.add_argument('--headless=new')

# Cria o service corretamente
service = Service(ChromeDriverManager().install())

# Inicializa o Chrome visível
driver = webdriver.Chrome(service=service, options=options)

driver.get('https://www.google.com')
print('✅ Selenium abriu o navegador. Título:', driver.title)

driver.quit()
