Feature: Consulta CNPJ
  Scenario: Consultar um CNPJ de teste
    Given que eu tenho a planilha de teste
    When eu executo a automação
    Then devo obter um arquivo resultado.xlsx com os dados normalizados
