import pandas as pd

def optimize_data(df):
    # Calcular la suma de la columna 'columna1'
    costo_total = df["columna1"].sum()

    # Crear una nueva fila con el resultado de la suma
    nueva_fila = pd.DataFrame({"columna1": [costo_total]})
    
    # Agregar la nueva fila al DataFrame original
    df = pd.concat([df, nueva_fila], ignore_index=True)
    
    # Guardar el DataFrame actualizado en un archivo Excel
    df.to_excel("resultado_optimizacion.xlsx", index=False)
    
    # Regresar el DataFrame actualizado
    return df
