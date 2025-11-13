import os, subprocess, sys
print('Setup iniciado: criando .venv e instalando dependências...')
if not os.path.exists('.venv'):
    subprocess.run([sys.executable, '-m', 'venv', '.venv'], check=True)
# activate and install - best run from PowerShell
print('Para instalar dependências, ative .venv e execute: pip install -r requirements.txt')
print('Após instalar, rode: python scripts/consulta_cnpj.py --input dados/teste.xlsx --output resultado.xlsx')
