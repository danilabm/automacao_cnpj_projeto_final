# utilitário para chamadas às APIs (esqueleto)
import os, requests
def consultar_receitaws(cnpj):
    url = f'https://www.receitaws.com.br/v1/cnpj/{cnpj}'
    r = requests.get(url, timeout=30)
    if r.status_code==200:
        return r.json()
    r.raise_for_status()
