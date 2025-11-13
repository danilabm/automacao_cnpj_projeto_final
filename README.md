# Automacao CNPJ - Pacote Final (Windows + Chrome visível)

Versão: final entregue

## Objetivo
Ler CNPJs de planilha (XLSX/CSV), consultar ReceitaWS (principal) com fallback CNPJ.ws e Selenium (Chrome visível) como último recurso; gerar `resultado.xlsx`.

## Conteúdo do pacote
- .env (configurações)
- requirements.txt
- setup.py
- install.ps1
- scripts/
- utils/
- features/
- dados/teste.xlsx
- README.md (este arquivo)
- docs/passo_a_passo.docx (arquivo em Word com o passo a passo detalhado)

## Observação importante sobre Chrome
Por sua solicitação, o Chrome será aberto **em modo visível** durante a execução do Selenium. No .env, `CHROME_HEADLESS=false`.

## Como usar (resumo)
1. Extrair ZIP em uma pasta local.
2. Abrir PowerShell como Administrador para instalar Chocolatey (se necessário).
3. Executar `.\install.ps1` (opcional) ou abrir PowerShell no diretório do projeto e executar `python setup.py`.
4. Ativar venv: `.\.venv\Scripts\Activate.ps1`
5. Rodar a automação: `python scripts/consulta_cnpj.py --input dados/teste.xlsx --output resultado.xlsx`

Para o passo a passo completo, abra `docs/passo_a_passo.docx`.
