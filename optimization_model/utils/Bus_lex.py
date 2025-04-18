# ----------------------------------------
# 1. Importaciones de librerías
# ----------------------------------------
import pandas as pd
import pulp as lp

# ----------------------------------------
# 2. Parámetros definidos por el usuario
# ----------------------------------------
# alpha: Cobertura mínima deseada (e.g., 0.95 para 95%).
alpha = 0.6 

# c_prod: Costos de producción por SKU ($/unidad).
c_prod = {'21A': 5.0, '22B': 4.5, '23C': 6.0}

# c_hold: Costos de mantenimiento de inventario por SKU ($/unidad).
c_hold = {'21A': 0.2, '22B': 0.15, '23C': 0.25}

# c_exc: Costos por exceso de inventario sobre stock de seguridad ($/unidad).
c_exc = {'21A': 1.0, '22B': 1.0, '23C': 1.0}

# excel_file: Ruta al archivo de datos de entrada (Supply_Demand y Boundary Conditions).
excel_file = 'Hackaton DB Final.xlsx'

def load_data(file_path):
    """
    Carga los datos de Supply_Demand y Boundary Conditions desde un archivo Excel.
    Parámetros:
        file_path (str): Ruta al archivo .xlsx con la base de datos.
    Devuelve:
        df_sd (DataFrame): Hoja Supply_Demand.
        df_bc (DataFrame): Hoja Boundary Conditions.
    """
    df_sd = pd.read_excel(file_path, sheet_name='Supply_Demand', skiprows=2)
    df_bc = pd.read_excel(file_path, sheet_name='Boundary Conditions', skiprows=1)
    return df_sd, df_bc

def preprocess_data(df_sd, df_bc):
    """
    Extrae productos, periodos y diccionarios de parámetros:
      - D: Demanda efectiva por SKU y periodo.
      - SST: Stock de seguridad objetivo por SKU y periodo.
      - EEX: Exceso de inventario sobre SST por SKU y periodo.
      - Cap: Capacidad productiva por periodo.
    Parámetros:
        df_sd (DataFrame): Datos de Supply_Demand.
        df_bc (DataFrame): Datos de Boundary Conditions.
    Devuelve:
        products, periods, D, SST, EEX, Cap
    """
    # Extraer lista de productos únicos
    products = df_sd['Product ID'].unique().tolist()

    # Extraer lista de periodos (columnas con formato 'MM-DD-YY')
    periods = [col for col in df_sd.columns if col.count('-') == 2]

    # Construir diccionarios de parámetros
    D   = {(row['Product ID'], t): row[t]
           for _, row in df_sd.iterrows()
           if row['Attribute'] == 'EffectiveDemand'
           for t in periods}
    SST = {(row['Product ID'], t): row[t]
           for _, row in df_sd.iterrows()
           if row['Attribute'] == 'Safety Stock Target'
           for t in periods}
    EEX = {(row['Product ID'], t): row[t]
           for _, row in df_sd.iterrows()
           if row['Attribute'] == 'Inventory Balance in excess of SST'
           for t in periods}

    # Calcular capacidad productiva por periodo (fallback si no está en df_bc)
    Cap = {}
    for t in periods:
        if t in df_bc.columns:
            # Sumar las capacidades disponibles para todas las columnas
            Cap[t] = df_bc.loc[df_bc['Attribute']=='Available Capacity', t].sum()
        else:
            # Fallback: Demanda + SST si falta la columna
            Cap[t] = sum(D[(p,t)] + SST[(p,t)] for p in products)

    return products, periods, D, SST, EEX, Cap

def build_lex_model(products, periods, D, SST, EEX, Cap, alpha, c_prod, c_hold, c_exc):
    """
    Construye y resuelve un modelo lexicográfico con dos fases:
      1) Minimizar costos.
      2) Minimizar shortfall de cobertura, dados los costos óptimos de la fase 1.
    Parámetros:
        products (list): Lista de SKUs.
        periods (list): Lista de periodos históricos.
        D, SST, EEX, Cap (dicts): Parámetros del problema.
        alpha (float): Cobertura mínima deseada.
        c_prod, c_hold, c_exc (dicts): Costos unitarios.
    Devuelve:
        f1_star (float): Costo óptimo de la fase 1.
        shortfall (float): Shortfall de cobertura encontrado.
        production_plan (dict): Plan de producción lexicográfico.
    """
    # Fase 1: minimización de costos
    m1 = lp.LpProblem('CostMin', lp.LpMinimize)
    x1 = lp.LpVariable.dicts('x', (products, periods), lowBound=0, cat='Integer')
    I1 = lp.LpVariable.dicts('I', (products, periods), lowBound=0, cat='Integer')

    # Función objetivo: costos de producción + inventario + excedentes
    m1 += lp.lpSum(c_prod[p]*x1[p][t] + c_hold[p]*I1[p][t] + c_exc[p]*EEX[(p,t)]
                   for p in products for t in periods)

    # Restricciones de balance de inventario
    for p in products:
        for idx, t in enumerate(periods):
            if idx == 0:
                m1 += x1[p][t] == D[(p,t)] + I1[p][t]
            else:
                prev = periods[idx-1]
                m1 += I1[p][prev] + x1[p][t] == D[(p,t)] + I1[p][t]

    # Restricciones de stock de seguridad
    for p in products:
        for t in periods:
            m1 += I1[p][t] >= SST[(p,t)]

    # Restricciones de capacidad
    for t in periods:
        m1 += lp.lpSum(x1[p][t] for p in products) <= Cap[t]

    # Resolver fase 1
    m1.solve(lp.PULP_CBC_CMD(msg=False))
    f1_star = lp.value(m1.objective)

    # Fase 2: minimización de shortfall de cobertura
    m2 = lp.LpProblem('Lexico', lp.LpMinimize)
    x2 = lp.LpVariable.dicts('x2', (products, periods), lowBound=0, cat='Integer')
    I2 = lp.LpVariable.dicts('I2', (products, periods), lowBound=0, cat='Integer')
    s   = lp.LpVariable('shortfall', lowBound=0)

    # Cota de costo igual a costo óptimo de fase 1
    m2 += lp.lpSum(c_prod[p]*x2[p][t] + c_hold[p]*I2[p][t] + c_exc[p]*EEX[(p,t)]
                   for p in products for t in periods) <= f1_star

    # Objetivo secundario: minimizar shortfall
    m2 += s

    # Restricción de cobertura mínima con slack
    m2 += lp.lpSum(x2[p][t] for p in products for t in periods) + s \
          >= alpha * lp.lpSum(D[(p,t)] for p in products for t in periods)

    # Repetir restricciones de balance, stock y capacidad de fase 1
    for p in products:
        for idx, t in enumerate(periods):
            if idx == 0:
                m2 += x2[p][t] == D[(p,t)] + I2[p][t]
            else:
                prev = periods[idx-1]
                m2 += I2[p][prev] + x2[p][t] == D[(p,t)] + I2[p][t]

    for p in products:
        for t in periods:
            m2 += I2[p][t] >= SST[(p,t)]

    for t in periods:
        m2 += lp.lpSum(x2[p][t] for p in products) <= Cap[t]

    # Resolver fase 2
    m2.solve(lp.PULP_CBC_CMD(msg=False))

    # Capturar resultados
    shortfall = s.value()
    production_plan = {(p,t): x2[p][t].value()
                       for p in products for t in periods if x2[p][t].value() > 1e-6}

    return f1_star, shortfall, production_plan

def print_results(f1_star, shortfall, production_plan):
    """
    Imprime en consola el costo óptimo, el shortfall y el plan de producción.
    """
    print(f"Costo óptimo (Fase 1): {f1_star:.2f}")
    print(f"Shortfall de cobertura: {shortfall:.2f}\n")
    print("Plan de producción (lexicográfico):")
    for (p,t), qty in production_plan.items():
        print(f"  - {p} en {t}: {qty:.1f} unidades")

def main():
    """
    Flujo principal de ejecución:
      1) Cargar datos
      2) Preprocesar
      3) Construir y resolver modelo lexicográfico
      4) Mostrar resultados
    """
    # 1) Carga de datos
    df_sd, df_bc = load_data(excel_file)

    # 2) Preprocesamiento y extracción de parámetros
    products, periods, D, SST, EEX, Cap = preprocess_data(df_sd, df_bc)

    # 3) Construcción y resolución del modelo
    f1_star, shortfall, production_plan = build_lex_model(
        products, periods, D, SST, EEX, Cap,
        alpha, c_prod, c_hold, c_exc
    )

    # 4) Resultados finales
    print_results(f1_star, shortfall, production_plan)

if __name__ == '__main__':
    main()
