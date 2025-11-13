# Script principal (simplificado)
import os, time, argparse
from dotenv import load_dotenv
load_dotenv()
TEMPO_SUCESSO = int(os.getenv('TEMPO_SUCESSO','5'))
TEMPO_ERRO = int(os.getenv('TEMPO_ERRO','1'))
CHROME_HEADLESS = os.getenv('CHROME_HEADLESS','false').lower() in ('1','true','yes')
def consultar(cnpj):
    # placeholder: implement API calls to receitaws and cnpj.ws and fallback to selenium
    return {'cnpj': cnpj, 'razao_social': 'Empresa Exemplo'}
def main():
    p = argparse.ArgumentParser()
    p.add_argument('--input', required=True)
    p.add_argument('--output', required=True)
    args = p.parse_args()
    # read input (left as exercise)
    cnpjs = ['00000000000191']
    results = []
    for c in cnpjs:
        try:
            data = consultar(c)
            time.sleep(TEMPO_SUCESSO)
        except Exception:
            time.sleep(TEMPO_ERRO)
            data = {'cnpj':c}
        results.append(data)
    # write a simple xlsx
    import pandas as pd
    df = pd.DataFrame(results)
    df.to_excel(args.output, index=False)
    print('Resultado salvo em', args.output)
if __name__=='__main__':
    main()
