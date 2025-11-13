"""
consulta_cnpj.py — versão completa (2025)
Executa a consulta automática de CNPJs lendo planilha Excel e salvando resultado estruturado.
API principal: ReceitaWS (https://www.receitaws.com.br)
API secundária: CNPJ.ws
Fallback: Selenium (abre Chrome visível, se permitido)
"""

import os
import time
import json
import argparse
import pandas as pd
import requests
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from rich.console import Console

console = Console()
load_dotenv()

# Variáveis de ambiente do .env
TEMPO_SUCESSO = int(os.getenv("TEMPO_SUCESSO", "5"))
TEMPO_ERRO = int(os.getenv("TEMPO_ERRO", "1"))
CHROME_HEADLESS = os.getenv("CHROME_HEADLESS", "false").lower() in ("1", "true", "yes")
API_MODE = os.getenv("API_MODE", "receitaws").lower()
API_FALLBACK = os.getenv("API_FALLBACK", "cnpjws").lower()
API_TOKEN = os.getenv("API_TOKEN", "").strip()

# Funções auxiliares ----------------------------------------------------------

def limpar_cnpj(cnpj):
    """Remove caracteres não numéricos do CNPJ"""
    return "".join(filter(str.isdigit, str(cnpj)))[:14]

def consultar_receitaws(cnpj):
    """Consulta na API da ReceitaWS"""
    url = f"https://www.receitaws.com.br/v1/cnpj/{cnpj}"
    r = requests.get(url, timeout=40)
    if r.status_code == 200:
        data = r.json()
        if data.get("status") == "ERROR":
            raise Exception(data.get("message"))
        return data
    else:
        raise Exception(f"Erro ReceitaWS: {r.status_code}")

def consultar_cnpjws(cnpj):
    """Consulta na API CNPJ.ws (precisa de token)"""
    if not API_TOKEN:
        raise Exception("Token da API CNPJ.ws não informado (.env)")
    url = f"https://api.cnpj.ws/cnpj/{cnpj}"
    headers = {"Authorization": f"Bearer {API_TOKEN}"}
    r = requests.get(url, headers=headers, timeout=40)
    if r.status_code == 200:
        return r.json()
    else:
        raise Exception(f"Erro CNPJ.ws: {r.status_code}")

def consultar_selenium(cnpj):
    """Fallback via Selenium — abre Chrome visível e busca dados básicos"""
    options = Options()
    if CHROME_HEADLESS:
        options.add_argument("--headless=new")
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)

    try:
        url = f"https://cnpj.biz/{cnpj}"
        driver.get(url)
        time.sleep(4)
        html = driver.page_source
        razao = ""
        if "Razão Social" in html:
            start = html.find("Razão Social")
            snippet = html[start:start+200]
            razao = snippet.split("<")[0].replace("Razão Social", "").strip()
        return {"cnpj": cnpj, "razao_social": razao or "Desconhecida (via Selenium)"}
    finally:
        driver.quit()

def consultar_cnpj(cnpj):
    """Consulta principal com fallback automático"""
    cnpj = limpar_cnpj(cnpj)
    if len(cnpj) != 14:
        raise ValueError("CNPJ inválido")

    for metodo in [API_MODE, API_FALLBACK, "selenium"]:
        try:
            console.print(f"[bold blue]→ Consultando {cnpj} via {metodo}...[/bold blue]")
            if metodo == "receitaws":
                data = consultar_receitaws(cnpj)
                return normalizar_receitaws(data)
            elif metodo == "cnpjws":
                data = consultar_cnpjws(cnpj)
                return normalizar_cnpjws(data)
            elif metodo == "selenium":
                return consultar_selenium(cnpj)
        except Exception as e:
            console.print(f"[yellow]⚠ Erro em {metodo}: {e}[/yellow]")
            time.sleep(TEMPO_ERRO)
    return {"cnpj": cnpj, "erro": "Não foi possível consultar"}

def normalizar_receitaws(data):
    """Transforma resposta da ReceitaWS em formato padronizado"""
    return {
        "cnpj": data.get("cnpj"),
        "razao_social": data.get("nome"),
        "nome_fantasia": data.get("fantasia"),
        "situacao": data.get("situacao"),
        "abertura": data.get("abertura"),
        "atividade_principal": ", ".join([a.get("text", "") for a in data.get("atividade_principal", [])]),
        "atividades_secundarias": "; ".join([a.get("text", "") for a in data.get("atividades_secundarias", [])]),
        "uf": data.get("uf"),
        "municipio": data.get("municipio"),
        "logradouro": data.get("logradouro"),
        "numero": data.get("numero"),
        "bairro": data.get("bairro"),
        "cep": data.get("cep"),
        "email": data.get("email"),
        "telefone": data.get("telefone"),
        "capital_social": data.get("capital_social"),
    }

def normalizar_cnpjws(data):
    """Transforma resposta da CNPJ.ws em formato padronizado"""
    return {
        "cnpj": data.get("estabelecimento", {}).get("cnpj"),
        "razao_social": data.get("razao_social"),
        "nome_fantasia": data.get("nome_fantasia"),
        "situacao": data.get("estabelecimento", {}).get("situacao_cadastral"),
        "abertura": data.get("data_inicio_atividade"),
        "atividade_principal": data.get("estabelecimento", {}).get("atividade_principal", {}).get("descricao"),
        "atividades_secundarias": "; ".join(
            [a.get("descricao") for a in data.get("estabelecimento", {}).get("atividades_secundarias", [])]
        ),
        "uf": data.get("estabelecimento", {}).get("estado", {}).get("sigla"),
        "municipio": data.get("estabelecimento", {}).get("cidade", {}).get("nome"),
        "logradouro": data.get("estabelecimento", {}).get("logradouro"),
        "numero": data.get("estabelecimento", {}).get("numero"),
        "bairro": data.get("estabelecimento", {}).get("bairro"),
        "cep": data.get("estabelecimento", {}).get("cep"),
        "email": data.get("estabelecimento", {}).get("email"),
        "telefone": data.get("estabelecimento", {}).get("telefone1"),
        "capital_social": data.get("capital_social"),
    }

# ------------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Consulta múltiplos CNPJs e gera planilha")
    parser.add_argument("--input", required=True, help="Caminho do arquivo Excel de entrada")
    parser.add_argument("--output", required=True, help="Caminho do arquivo de saída (Excel)")
    args = parser.parse_args()

    console.print(f"[bold green]Lendo arquivo de entrada: {args.input}[/bold green]")
    df = pd.read_excel(args.input)
    if "cnpj" not in df.columns:
        raise Exception("Planilha precisa ter uma coluna chamada 'cnpj'")

    resultados = []
    for cnpj in df["cnpj"]:
        try:
            info = consultar_cnpj(cnpj)
            resultados.append(info)
            console.print(f"[green]✓ Sucesso:[/green] {cnpj}")
            time.sleep(TEMPO_SUCESSO)
        except Exception as e:
            console.print(f"[red]✗ Erro com {cnpj}: {e}[/red]")
            resultados.append({"cnpj": cnpj, "erro": str(e)})
            time.sleep(TEMPO_ERRO)

    # Salvar resultado em planilha
    out_df = pd.DataFrame(resultados)
    out_df.to_excel(args.output, index=False)
    console.print(f"\n[bold cyan]✅ Resultado salvo em:[/bold cyan] {args.output}")

if __name__ == "__main__":
    main()