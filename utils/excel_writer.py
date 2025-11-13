import pandas as pd
def escrever_resultado(path, rows):
    df = pd.DataFrame(rows)
    df.to_excel(path, index=False)
