import sys
import os
sys.path.append(os.path.dirname(__file__))  # permitir imports locales

import pandas as pd
import Bus_lex as lex
import Simplex_Goal_programming as goal
import Simplex_Restriccion_Funcional as func
import Suma_ponderada_funciones as sumw

# ================================
# Parámetros de usuario (ajustables)
# ================================
# Cobertura mínima (alpha): 0.90–0.99
alpha = 0.95
# Peso de costo (w_c): normalmente 1.0
w_c = 1.0
# Peso de shortfall (w_s): 5.0–20.0
w_s = 10.0
# Factor para definir cost_target en goal y funcional: 1.05–1.15
cost_factor = 1.05

# ================================
# Carga y preprocesamiento de datos
# ================================
excel_file = lex.excel_file
# 1) Carga de datos
df_sd, df_bc = lex.load_data(excel_file)
# 2) Preprocesamiento de parámetros
products, periods, D, SST, EEX, Cap = lex.preprocess_data(df_sd, df_bc)
# 3) Demanda total para métricas de servicio
total_demand = sum(D.values())

# ================================
# Definición de funciones de ejecución
# ================================
def run_lex():
    f1_star, shortfall, prod_plan = lex.build_lex_model(
        products, periods, D, SST, EEX, Cap,
        alpha, lex.c_prod, lex.c_hold, lex.c_exc
    )
    total_prod = sum(prod_plan.values())
    return {
        'model_name': 'lexicográfico',
        'total_cost': f1_star,
        'service_level': total_prod / total_demand,
        'shortfall_units': shortfall,
        'backorder_units': 0.0
    }


def run_goal(f1_star):
    goal.alpha = alpha
    goal.cost_target = f1_star * cost_factor
    dev_cov, dev_cost = goal.build_goal_model(
        products, periods, D, SST, EEX, Cap
    )
    shortfall = dev_cov[1]
    total_cost = goal.cost_target - dev_cost[0] + dev_cost[1]
    service_level = (alpha * total_demand - shortfall) / total_demand
    return {
        'model_name': 'goal-programming',
        'total_cost': total_cost,
        'service_level': service_level,
        'shortfall_units': shortfall,
        'backorder_units': 0.0
    }


def run_functional(f1_star):
    # Implementación funcional reutiliza goal_model por ahora
    func.alpha = alpha
    func.cost_target = f1_star * cost_factor
    dev_cov, dev_cost = func.build_goal_model(
        products, periods, D, SST, EEX, Cap
    )
    shortfall = dev_cov[1]
    total_cost = func.cost_target - dev_cost[0] + dev_cost[1]
    service_level = (alpha * total_demand - shortfall) / total_demand
    return {
        'model_name': 'funcional',
        'total_cost': total_cost,
        'service_level': service_level,
        'shortfall_units': shortfall,
        'backorder_units': 0.0
    }


def run_weighted():
    obj_val, shortfall, prod_plan = sumw.build_weighted_model(
        products, periods, D, SST, EEX, Cap,
        alpha, w_c, w_s,
        sumw.c_prod, sumw.c_hold, sumw.c_exc
    )
    total_prod = sum(prod_plan.values())
    return {
        'model_name': 'weighted-sum',
        'total_cost': obj_val,
        'service_level': total_prod / total_demand,
        'shortfall_units': shortfall,
        'backorder_units': 0.0
    }


def run_all_models():
    # Ejecuta todos los modelos y devuelve DataFrame con métricas homogéneas
    results = []
    # 1) Lexicográfico
    m_lex = run_lex()
    results.append(m_lex)
    f1_star = m_lex['total_cost']
    # 2) Goal Programming
    results.append(run_goal(f1_star))
    # 3) Funcional
    results.append(run_functional(f1_star))
    # 4) Weighted Sum
    results.append(run_weighted())
    return pd.DataFrame(results)


if __name__ == '__main__':
    df_compare = run_all_models()
    print(df_compare)
