# ----------------------------------------
# 1. Importaciones de librerías
# ----------------------------------------
import re
import pandas as pd
from pyomo.environ import (
    ConcreteModel, Set, Param, Var,
    NonNegativeReals, Constraint, Objective,
    SolverFactory, minimize
)

# ----------------------------------------
# 2. Parámetros definidos por el usuario
# ----------------------------------------
# alpha: Cobertura mínima deseada (e.g., 0.98 para 98%)
alpha = 0.98  # valor de ejemplo

# cost_target: Meta de costo total para programación por metas
cost_target = 1e8  # valor de ejemplo

# Pesos para desviaciones en la función objetivo
w_cov = 1.0  # peso para desviación de cobertura
w_cost = 1.0  # peso para desviación de costo

# Costos unitarios por SKU ($/unidad)
c_prod = {'21A': 5.0, '22B': 4.5, '23C': 6.0}
c_hold = {'21A': 0.2, '22B': 0.15, '23C': 0.25}

# Ruta al archivo de datos de entrada (Supply_Demand)
excel_file = 'Hackaton DB Final.xlsx'

# ----------------------------------------
# 3. Funciones
# ----------------------------------------

def load_data(file_path):
    """
    Carga la hoja 'Supply_Demand' desde un archivo Excel.
    Parámetros:
        file_path (str): Ruta al archivo .xlsx.
    Devuelve:
        df (DataFrame): Datos de Supply_Demand.
    """
    return pd.read_excel(file_path, sheet_name='Supply_Demand', skiprows=2)


def preprocess_data(df):
    """
    Extrae productos, periodos y diccionarios de parámetros:
      - D: Demanda efectiva por SKU y periodo.
      - SST: Stock de seguridad objetivo.
      - EEX: Exceso de inventario sobre SST.
      - Cap: Capacidad productiva por periodo (fallback: D+SST).
    """
    # Productos únicos y columnas de fecha
    products = df['Product ID'].unique().tolist()
    period_cols = [c for c in df.columns if re.match(r"\d{2}-\d{2}-\d{2}$", c)]

    # Convertir periodos a datetime para uniformidad
    periods = [pd.to_datetime(c, format='%m-%d-%y') for c in period_cols]

    # Diccionarios de parámetros
    D = {(r['Product ID'], pd.to_datetime(c, format='%m-%d-%y')): r[c]
         for _, r in df.iterrows() if r['Attribute'] == 'EffectiveDemand' for c in period_cols}
    SST = {(r['Product ID'], pd.to_datetime(c, format='%m-%d-%y')): r[c]
           for _, r in df.iterrows() if r['Attribute'] == 'Safety Stock Target' for c in period_cols}
    EEX = {(r['Product ID'], pd.to_datetime(c, format='%m-%d-%y')): r[c]
           for _, r in df.iterrows() if r['Attribute'] == 'Inventory Balance in excess of SST' for c in period_cols}

    # Capacidad productiva (fallback: demanda + SST)
    Cap = {t: sum(D[(p, t)] + SST[(p, t)] for p in products) for t in periods}

    return products, periods, D, SST, EEX, Cap


def build_goal_model(products, periods, D, SST, EEX, Cap):
    """
    Construye y resuelve el modelo de Goal Programming:
      - Variables de decisión de producción e inventario.
      - Variables de desviación para cobertura y costo.
      - Metas definidas por alpha y cost_target.
    Devuelve las desviaciones de cobertura y costo.
    """
    model = ConcreteModel()

    # Conjuntos y parámetros
    model.P = Set(initialize=products)
    model.T = Set(initialize=periods)
    model.D = Param(model.P, model.T, initialize=D, mutable=True)
    model.SST = Param(model.P, model.T, initialize=SST, mutable=True)
    model.EEX = Param(model.P, model.T, initialize=EEX, mutable=True)
    model.Cap = Param(model.T, initialize=Cap, mutable=True)

    # Variables de decisión
    model.x = Var(model.P, model.T, within=NonNegativeReals)
    model.I = Var(model.P, model.T, within=NonNegativeReals)
    model.dev_cov_neg = Var(within=NonNegativeReals)
    model.dev_cov_pos = Var(within=NonNegativeReals)
    model.dev_cost_neg = Var(within=NonNegativeReals)
    model.dev_cost_pos = Var(within=NonNegativeReals)

    # Restricción de inventario encadenado
    def inv_balance(m, p, t):
        ts = sorted(m.T)
        idx = ts.index(t)
        if idx == 0:
            return m.x[p, t] == m.D[p, t] + m.I[p, t]
        prev = ts[idx - 1]
        return m.I[p, prev] + m.x[p, t] == m.D[p, t] + m.I[p, t]
    model.InvBalance = Constraint(model.P, model.T, rule=inv_balance)

    # Stock de seguridad
    model.SafetyStock = Constraint(
        model.P, model.T,
        rule=lambda m, p, t: m.I[p, t] >= m.SST[p, t]
    )

    # Meta de cobertura
    def goal_cov(m):
        total_prod = sum(m.x[p, t] for p in m.P for t in m.T)
        total_demand = sum(m.D[p, t] for p in m.P for t in m.T)
        return total_prod + m.dev_cov_neg - m.dev_cov_pos == alpha * total_demand
    model.GoalCov = Constraint(rule=goal_cov)

    # Meta de costo
    def goal_cost(m):
        total_cost = sum(c_prod[p] * m.x[p, t] + c_hold[p] * m.I[p, t]
                         for p in m.P for t in m.T)
        return total_cost + m.dev_cost_neg - m.dev_cost_pos == cost_target
    model.GoalCost = Constraint(rule=goal_cost)

    # Capacidad productiva
    model.Capacity = Constraint(
        model.T,
        rule=lambda m, t: sum(m.x[p, t] for p in m.P) <= m.Cap[t]
    )

    # Objetivo: minimizar desviaciones ponderadas
    model.obj = Objective(
        expr=w_cov * (model.dev_cov_neg + model.dev_cov_pos)
             + w_cost * (model.dev_cost_neg + model.dev_cost_pos),
        sense=minimize
    )

    # Resolver el modelo
    solver = SolverFactory('glpk')
    result = solver.solve(model, tee=True)

    desv_cov = (model.dev_cov_neg(), model.dev_cov_pos())
    desv_cost = (model.dev_cost_neg(), model.dev_cost_pos())
    return desv_cov, desv_cost


def print_goal_results(desv_cov, desv_cost):
    """
    Imprime las desviaciones de cobertura y costo.
    """
    print(f"Desviación cobertura (-/+): {desv_cov[0]:.2f} / {desv_cov[1]:.2f}")
    print(f"Desviación costo (-/+): {desv_cost[0]:.2f} / {desv_cost[1]:.2f}")


def main():
    """
    Flujo principal:
      1) Cargar y preprocesar datos
      2) Construir y resolver modelo Goal Programming
      3) Mostrar resultados
    """
    df = load_data(excel_file)
    products, periods, D, SST, EEX, Cap = preprocess_data(df)
    desv_cov, desv_cost = build_goal_model(products, periods, D, SST, EEX, Cap)
    print_goal_results(desv_cov, desv_cost)

if __name__ == '__main__':
    main()
