import os, sys
import pandas as pd
import matplotlib.pyplot as plt

# y tus .py (Bus_lex.py, Simplex_*.py, Suma_*.py)
os.chdir(r"C:\Users\JL504802\Desktop\TalentLand\Implementaciones de ejemplo")
sys.path.append(os.getcwd())

import Bus_lex as lex
import Simplex_Goal_programming as goal
import Simplex_Restriccion_Funcional as func
import Suma_ponderada_funciones as sumw

# Parámetros
alpha       = 0.9       # 0.90–0.99
w_c         = 1.0        # peso coste
w_s         = 15.0       # 5.0–20.0
cost_factor = 1.15       # 1.00–1.15

# Carga y preprocesamiento
df_sd, df_bc = lex.load_data(lex.excel_file)
prods, periods, D, SST, EEX, Cap = lex.preprocess_data(df_sd, df_bc)
total_demand = sum(D.values())

# Funciones de corrida
def run_lex():
    f_star, short, plan = lex.build_lex_model(prods,periods,D,SST,EEX,Cap, alpha, lex.c_prod, lex.c_hold, lex.c_exc)
    svc = sum(plan.values())/total_demand
    return ("lexicográfico", f_star, svc)

def run_goal(f_star):
    goal.alpha = alpha
    goal.cost_target = f_star * cost_factor
    dev_cov, dev_cost = goal.build_goal_model(prods,periods,D,SST,EEX,Cap)
    short = dev_cov[1]
    svc   = (alpha*total_demand - short)/total_demand
    cost  = goal.cost_target - dev_cost[0] + dev_cost[1]
    return ("goal-programming", cost, svc)

def run_func(f_star):
    func.alpha = alpha
    func.cost_target = f_star * cost_factor
    dev_cov, dev_cost = func.build_goal_model(prods,periods,D,SST,EEX,Cap)
    short = dev_cov[1]
    svc   = (alpha*total_demand - short)/total_demand
    cost  = func.cost_target - dev_cost[0] + dev_cost[1]
    return ("funcional", cost, svc)

def run_weighted():
    obj, short, plan = sumw.build_weighted_model(prods,periods,D,SST,EEX,Cap, alpha, w_c, w_s, sumw.c_prod, sumw.c_hold, sumw.c_exc)
    svc = sum(plan.values())/total_demand
    return ("weighted-sum", obj, svc)

# Ejecutar y montar DataFrame
rows = []
lex_name, f_star, _ = run_lex()
rows.append(run_lex())
rows.append(run_goal(f_star))
rows.append(run_func(f_star))
rows.append(run_weighted())
df = pd.DataFrame(rows, columns=["Modelo","Coste","Servicio"])

# Graficar
plt.figure()
plt.scatter(df["Servicio"], df["Coste"])
for _, r in df.iterrows():
    plt.annotate(r["Modelo"], (r["Servicio"], r["Coste"]))
plt.xlabel("Nivel de servicio")
plt.ylabel("Coste total")
plt.title("Coste vs. Nivel de servicio")
plt.tight_layout()
plt.show()
