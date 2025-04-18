# ----------------------------------------
# 1. Importaciones de librerías
# ----------------------------------------
import pandas as pd
import pulp as lp

# ----------------------------------------
# 2. Parámetros definidos por el usuario
# ----------------------------------------
# alpha: Cobertura mínima deseada (ej: 0.95 para 95%)
alpha = 0.95

# w_c: Peso para el término de costo en la función objetivo
w_c = 1.0
# w_s: Peso para el shortfall de cobertura en la función objetivo
w_s = 10.0

# Costos unitarios por SKU ($/unidad)
c_prod = {'21A': 5.0, '22B': 4.5, '23C': 6.0}
c_hold = {'21A': 0.2, '22B': 0.15, '23C': 0.25}
c_exc = {'21A': 1.0, '22B': 1.0, '23C': 1.0}

# Ruta al archivo de datos de entrada (Supply_Demand y Boundary Conditions)
excel_file = 'Hackaton DB Final.xlsx'

# ----------------------------------------
# 3. Funciones
# ----------------------------------------

def load_data(file_path):
    """
    Carga las hojas 'Supply_Demand' y 'Boundary Conditions' desde un archivo Excel.
    Parámetros:
        file_path (str): Ruta al archivo .xlsx.
    Devuelve:
        df_sd (DataFrame): Supply_Demand.
        df_bc (DataFrame): Boundary Conditions.
    """
    df_sd = pd.read_excel(file_path, sheet_name='Supply_Demand', skiprows=2)
    df_bc = pd.read_excel(file_path, sheet_name='Boundary Conditions', skiprows=1)
    return df_sd, df_bc


def preprocess_data(df_sd, df_bc):
    """
    Extrae productos, periodos y diccionarios de parámetros:
      - D: Demanda efectiva.
      - SST: Stock de seguridad.
      - EEX: Exceso de inventario sobre SST.
      - Cap: Capacidad productiva.
    """
    products = df_sd['Product ID'].unique().tolist()
    periods = [c for c in df_sd.columns if c.count('-') == 2]

    D = {(r['Product ID'], t): r[t]
         for _, r in df_sd.iterrows() if r['Attribute']=='EffectiveDemand' for t in periods}
    SST = {(r['Product ID'], t): r[t]
           for _, r in df_sd.iterrows() if r['Attribute']=='Safety Stock Target' for t in periods}
    EEX = {(r['Product ID'], t): r[t]
           for _, r in df_sd.iterrows() if r['Attribute']=='Inventory Balance in excess of SST' for t in periods}

    Cap = {}
    for t in periods:
        if t in df_bc.columns:
            Cap[t] = df_bc.loc[df_bc['Attribute']=='Available Capacity', t].sum()
        else:
            Cap[t] = sum(D[(p,t)] + SST[(p,t)] for p in products)

    return products, periods, D, SST, EEX, Cap


def build_weighted_model(products, periods, D, SST, EEX, Cap, alpha, w_c, w_s, c_prod, c_hold, c_exc):
    """
    Construye y resuelve el modelo de suma ponderada:
    Objetivo: w_c * costo_total + w_s * shortfall.
    Devuelve:
        objective_value (float), shortfall (float), production_plan (dict)
    """
    model = lp.LpProblem('Weighted_Sum', lp.LpMinimize)

    # Variables de decisión
    x = lp.LpVariable.dicts('x', (products, periods), lowBound=0, cat='Integer')
    I = lp.LpVariable.dicts('I', (products, periods), lowBound=0, cat='Integer')
    s = lp.LpVariable('shortfall', lowBound=0)

    # Término de costo total
    cost_term = lp.lpSum(c_prod[p]*x[p][t] + c_hold[p]*I[p][t] + c_exc[p]*EEX[(p,t)]
                         for p in products for t in periods)

    # Función objetivo
    model += w_c * cost_term + w_s * s

    # Restricción de shortfall
    model += s >= alpha * lp.lpSum(D[(p,t)] for p in products for t in periods) - \
              lp.lpSum(x[p][t] for p in products for t in periods)

    # Balance de inventario
    for p in products:
        for i, t in enumerate(periods):
            if i == 0:
                model += x[p][t] == D[(p,t)] + I[p][t]
            else:
                prev = periods[i-1]
                model += I[p][prev] + x[p][t] == D[(p,t)] + I[p][t]

    # Stock de seguridad
    for p in products:
        for t in periods:
            model += I[p][t] >= SST[(p,t)]

    # Capacidad productiva
    for t in periods:
        model += lp.lpSum(x[p][t] for p in products) <= Cap[t]

    # Resolver
    model.solve(lp.PULP_CBC_CMD(msg=False))

    obj_val = lp.value(model.objective)
    shortfall_val = s.value()
    production_plan = {(p,t): x[p][t].value() for p in products for t in periods if x[p][t].value() > 1e-6}

    return obj_val, shortfall_val, production_plan


def print_weighted_results(obj_val, shortfall, production_plan):
    """
    Imprime el valor de la función objetivo, shortfall y plan de producción.
    """
    print(f"Valor objetivo: {obj_val:.2f}")
    print(f"Shortfall de cobertura: {shortfall:.2f}\n")
    print("Plan de producción:")
    for (p,t), qty in production_plan.items():
        print(f"  - {p} en {t}: {qty:.1f} unidades")


def main():
    """
    Flujo principal:
      1) Cargar datos
      2) Preprocesar
      3) Construir y resolver modelo ponderado
      4) Mostrar resultados
    """
    df_sd, df_bc = load_data(excel_file)
    products, periods, D, SST, EEX, Cap = preprocess_data(df_sd, df_bc)
    obj_val, shortfall, prod_plan = build_weighted_model(
        products, periods, D, SST, EEX, Cap,
        alpha, w_c, w_s, c_prod, c_hold, c_exc
    )
    print_weighted_results(obj_val, shortfall, prod_plan)

if __name__ == '__main__':
    main()
