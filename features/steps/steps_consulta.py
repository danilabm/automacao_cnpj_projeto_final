from behave import given, when, then
import os
@given('que eu tenho a planilha de teste')
def step_impl(context):
    assert os.path.exists('dados/teste.xlsx')
@when('eu executo a automação')
def step_impl(context):
    os.system('python scripts/consulta_cnpj.py --input dados/teste.xlsx --output resultado.xlsx')
@then('devo obter um arquivo resultado.xlsx com os dados normalizados')
def step_impl(context):
    assert os.path.exists('resultado.xlsx')
