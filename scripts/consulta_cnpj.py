import os
import time
import pandas as pd
import argparse
import requests
from dotenv import load_dotenv

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import WebDriverException, InvalidSessionIdException


# -------------------------------------------------
# Funções auxiliares
# -------------------------------------------------

def limpar_cnpj(cnpj):
    return ''.join([c for c in str(cnpj) if c.isdigit()])


def expandir_cnaes(lista, max_cnaes=80):
    cnaes = {}
    for i in range(max_cnaes):
        cnaes[f"cnae_{i+1}"] = lista[i] if i < len(lista) else ""
    return cnaes


def obter_dados_api(cnpj, api_mode, token=None, max_tentativas=10, tempo_base=10):
    """Consulta as APIs ReceitaWS ou CNPJ.ws com tratamento de erro 429"""
    headers = {"Authorization": f"Bearer {token}"} if token else {}

    if api_mode == "receitaws":
        url = f"https://www.receitaws.com.br/v1/cnpj/{cnpj}"
    else:
        url = f"https://publica.cnpj.ws/cnpj/{cnpj}"

    tempo_espera = tempo_base
    for tentativa in range(1, max_tentativas + 1):
        try:
            r = requests.get(url, headers=headers, timeout=25)
            if r.status_code == 200:
                return r.json()
            elif r.status_code == 429:
                print(f"⚠️ API {api_mode} retornou 429 (muitas requisições). Tentativa {tentativa}/{max_tentativas}. Aguardando {tempo_espera}s...")
                time.sleep(tempo_espera)
                tempo_espera *= 2
                continue
            else:
                print(f"⚠️ Erro {r.status_code} na API {api_mode} ({cnpj})")
                return None
        except Exception as e:
            print(f"⚠️ Falha na API {api_mode} (tentativa {tentativa}/{max_tentativas}): {e}")
            time.sleep(tempo_espera)
            tempo_espera *= 2

    print(f"❌ Falha definitiva após {max_tentativas} tentativas na API {api_mode} para {cnpj}")
    return None


def processar_dados_api(cnpj, dados):
    atividades_secundarias = []
    if "atividades_secundarias" in dados:
        atividades_secundarias = [a.get("code", "") for a in dados["atividades_secundarias"]]
    elif "estabelecimento" in dados and "atividades_secundarias" in dados["estabelecimento"]:
        atividades_secundarias = [a.get("id", "") for a in dados["estabelecimento"]["atividades_secundarias"]]

    registro = {
        "cnpj": cnpj,
        "razao_social": dados.get("nome") or dados.get("razao_social", ""),
        "fantasia": dados.get("fantasia", ""),
        "cidade": dados.get("municipio") or (dados.get("estabelecimento", {}).get("cidade", "")),
        "data_abertura": dados.get("abertura") or (dados.get("estabelecimento", {}).get("data_inicio_atividade", "")),
        "data_situacao": dados.get("data_situacao", ""),
        "cnae_principal": (
            dados.get("atividade_principal", [{}])[0].get("code", "")
            if "atividade_principal" in dados
            else dados.get("estabelecimento", {}).get("atividade_principal", {}).get("id", "")
        ),
        "is_mei": dados.get("situacao_especial", "") == "MEI",
        "data_enquadramento_mei": dados.get("data_situacao_especial", ""),
        "enquadramentos_anteriores": dados.get("motivo_situacao_cadastral", ""),
        "opcao_pelo_simples": dados.get("opcao_pelo_simples", ""),
        "data_exclusao_do_simples": dados.get("data_exclusao_do_simples", ""),
        "porte": dados.get("porte", ""),
        "regime_tributario": dados.get("natureza_juridica", "")
    }

    registro.update(expandir_cnaes(atividades_secundarias))
    return registro


def iniciar_chrome():
    """Abre o Chrome e retorna o driver."""
    try:
        chrome_options = Options()
        chrome_options.add_argument("--start-maximized")
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        return driver
    except Exception as e:
        print(f"❌ Erro ao iniciar o Chrome: {e}")
        return None


def mostrar_no_chrome(driver, cnpj):
    """Mostra o link da API visualmente no Chrome."""
    url = f"https://www.receitaws.com.br/v1/cnpj/{cnpj}"
    try:
        driver.get(url)
    except (InvalidSessionIdException, WebDriverException):
        raise InvalidSessionIdException("Sessão do Chrome perdida.")


# -------------------------------------------------
# Função principal
# -------------------------------------------------

def main():
    load_dotenv()

    parser = argparse.ArgumentParser(description="Consulta CNPJ com APIs ReceitaWS + CNPJ.ws e visual no Chrome.")
    parser.add_argument("--input", required=True, help="Arquivo Excel de entrada (coluna 'cnpj')")
    parser.add_argument("--output", required=True, help="Arquivo Excel de saída")
    args = parser.parse_args()

    api_principal = "receitaws"
    api_fallback = "cnpjws"
    token = os.getenv("API_TOKEN", "")
    tempo_sucesso = 5
    tempo_erro = 10

    df = pd.read_excel(args.input)

    col_cnpj = None
    for c in df.columns:
        if str(c).strip().lower() in ["cnpj", "cnpjs"]:
            col_cnpj = c
            break
    if not col_cnpj:
        raise Exception("Planilha precisa ter uma coluna chamada 'cnpj'")

    resultados = []
    erros = []

    driver = iniciar_chrome()
    if not driver:
        print("⚠️ Não foi possível abrir o Chrome. Continuando sem visualização.")

    for idx, row in df.iterrows():
        cnpj = limpar_cnpj(row[col_cnpj])
        if not cnpj:
            continue

        print(f"🔍 Consultando {cnpj}...")

        # Tenta mostrar no Chrome
        if driver:
            try:
                mostrar_no_chrome(driver, cnpj)
            except InvalidSessionIdException:
                print("⚠️ Chrome reiniciando após desconexão...")
                driver = iniciar_chrome()
                if driver:
                    mostrar_no_chrome(driver, cnpj)

        # Consulta API principal com controle de 429
        dados = obter_dados_api(cnpj, api_principal, token, max_tentativas=10, tempo_base=10)

        # Fallback se falhar
        if not dados or ("status" in dados and dados["status"] == "ERROR"):
            print(f"⚠️ Erro na ReceitaWS, tentando fallback (CNPJ.ws)...")
            dados = obter_dados_api(cnpj, api_fallback, token, max_tentativas=10, tempo_base=10)

        # Se ainda falhou
        if not dados:
            print(f"❌ Falha nas duas APIs para {cnpj}")
            erros.append(cnpj)
            time.sleep(tempo_erro)
            continue

        try:
            registro = processar_dados_api(cnpj, dados)
            resultados.append(registro)

            # 🔥 Salvar progresso a cada 20 resultados bem-sucedidos
            if len(resultados) % 20 == 0:
                df_checkpoint = pd.DataFrame(resultados)
                df_checkpoint.to_excel("resultado_parcial.xlsx", index=False)
                print("💾 Arquivo parcial salvo: resultado_parcial.xlsx")

        except Exception as e:
            print(f"❌ Erro ao processar {cnpj}: {e}")
            erros.append(cnpj)

        time.sleep(tempo_sucesso)

    # Reprocessar erros
    if erros:
        print("\n🔁 Reprocessando CNPJs com erro...")
        for cnpj in erros:
            print(f"🔄 Tentando novamente: {cnpj}")
            if driver:
                try:
                    mostrar_no_chrome(driver, cnpj)
                except InvalidSessionIdException:
                    driver = iniciar_chrome()
                    if driver:
                        mostrar_no_chrome(driver, cnpj)

            dados = obter_dados_api(cnpj, api_principal, token, max_tentativas=10, tempo_base=10)
            if not dados:
                dados = obter_dados_api(cnpj, api_fallback, token, max_tentativas=10, tempo_base=10)

            if dados:
                registro = processar_dados_api(cnpj, dados)
                resultados.append(registro)
                print(f"✅ Sucesso na segunda tentativa: {cnpj}")
            else:
                print(f"❌ Falha definitiva para {cnpj}")

            time.sleep(tempo_erro)

    if driver:
        try:
            driver.quit()
        except Exception:
            pass

    # Salva resultado final
    if resultados:
        df_saida = pd.DataFrame(resultados)
        df_saida.to_excel(args.output, index=False)
        print(f"\n✅ Consulta concluída. Resultado salvo em: {args.output}")
    else:
        print("\n⚠️ Nenhum dado coletado. Nenhum arquivo gerado.")


if __name__ == "__main__":
    main()
