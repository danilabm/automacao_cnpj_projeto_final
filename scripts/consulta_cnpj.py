import pandas as pd
import requests
import time
import argparse
import os
from dotenv import load_dotenv

# ---------------------------------------
# Funções utilitárias
# ---------------------------------------

def limpar_cnpj(cnpj):
    return ''.join([c for c in str(cnpj) if c.isdigit()])

def expandir_cnaes(dados, max_cnaes=80):
    """
    Expande o campo de atividades secundárias em até 80 colunas (cnae_1..cnae_80)
    """
    secundarias = dados.get("atividades_secundarias", [])
    cnaes = {}
    for i in range(max_cnaes):
        if i < len(secundarias):
            cnaes[f"cnae_{i+1}"] = secundarias[i].get("code", "")
        else:
            cnaes[f"cnae_{i+1}"] = ""
    return cnaes

def obter_dados_cnpj(cnpj, api_mode="receitaws", token=None):
    base_urls = {
        "receitaws": f"https://www.receitaws.com.br/v1/cnpj/{cnpj}",
        "cnpjws": f"https://publica.cnpj.ws/cnpj/{cnpj}",
    }

    url = base_urls.get(api_mode, base_urls["receitaws"])
    headers = {"Authorization": f"Bearer {token}"} if token else {}

    try:
        r = requests.get(url, headers=headers, timeout=20)
        if r.status_code == 200:
            return r.json()
        else:
            print(f"⚠️ Erro {r.status_code} ao consultar {cnpj}")
            return None
    except Exception as e:
        print(f"⚠️ Falha na requisição do CNPJ {cnpj}: {e}")
        return None

# ---------------------------------------
# Função principal
# ---------------------------------------

def main():
    load_dotenv()

    parser = argparse.ArgumentParser(description="Consulta CNPJ em massa e gera planilha detalhada.")
    parser.add_argument("--input", required=True, help="Arquivo Excel de entrada com coluna 'cnpj'")
    parser.add_argument("--output", required=True, help="Arquivo Excel de saída")
    args = parser.parse_args()

    tempo_sucesso = int(os.getenv("TEMPO_SUCESSO", 5))
    tempo_erro = int(os.getenv("TEMPO_ERRO", 1))
    api_mode = os.getenv("API_MODE", "receitaws")
    token = os.getenv("API_TOKEN", "")

    df = pd.read_excel(args.input)

    # Aceita variações no nome da coluna
    col_cnpj = None
    for c in df.columns:
        if str(c).strip().lower() in ["cnpj", "cnpjs"]:
            col_cnpj = c
            break

    if not col_cnpj:
        raise Exception("Planilha precisa ter uma coluna chamada 'cnpj'")

    resultados = []

    for idx, row in df.iterrows():
        cnpj = limpar_cnpj(row[col_cnpj])
        if not cnpj:
            continue

        print(f"🔍 Consultando {cnpj}...")
        dados = obter_dados_cnpj(cnpj, api_mode, token)
        if not dados:
            time.sleep(tempo_erro)
            continue

        registro = {
            "cnpj": cnpj,
            "razao_social": dados.get("nome") or dados.get("razao_social", ""),
            "fantasia": dados.get("fantasia", ""),
            "cidade": (dados.get("municipio") or dados.get("cidade", "")),
            "data_abertura": dados.get("abertura", ""),
            "data_situacao": dados.get("data_situacao", ""),
            "cnae_principal": (dados.get("atividade_principal", [{}])[0].get("code", "")),
            "is_mei": dados.get("situacao_especial", "") == "MEI",
            "data_enquadramento_mei": dados.get("data_situacao_especial", ""),
            "enquadramentos_anteriores": dados.get("motivo_situacao_cadastral", ""),
            "opcao_pelo_simples": dados.get("opcao_pelo_simples", ""),
            "data_exclusao_do_simples": dados.get("data_exclusao_do_simples", ""),
            "porte": dados.get("porte", ""),
            "regime_tributario": dados.get("natureza_juridica", "")
        }

        # Adiciona CNAEs secundários (até 80)
        registro.update(expandir_cnaes(dados))

        resultados.append(registro)
        time.sleep(tempo_sucesso)

    if not resultados:
        print("⚠️ Nenhum dado foi coletado. Verifique os CNPJs.")
        return

    df_saida = pd.DataFrame(resultados)
    df_saida.to_excel(args.output, index=False)
    print(f"✅ Consulta concluída. Resultados salvos em: {args.output}")

# ---------------------------------------
# Execução direta
# ---------------------------------------

if __name__ == "__main__":
    main()