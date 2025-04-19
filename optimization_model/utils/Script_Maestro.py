"""
Script_Maestro.py
=================

Script unificado para comparar los modelos *lexicográfico* y *weighted‑sum*, 
trazar la frontera de Pareto **Coste vs Nivel de servicio**, y extraer la 
planificación óptima del modelo lexicográfico.

Estructura pedida
-----------------
1. **Importaciones** ↴
2. **Parámetros modificables** (con rangos sugeridos y explicación de su efecto)
3. Resto de utilidades, modelos y función `main()`
"""

# ---------------------------------------------------------------------------
# 1. IMPORTACIONES
# ---------------------------------------------------------------------------
import sys
from typing import List, Tuple

import matplotlib.pyplot as plt
import pandas as pd
import pulp as lp

from . import Bus_lex as lex
from . import Suma_ponderada_funciones as wsum

# Aseguramos que la salida soporte UTF‑8 para imprimir caracteres especiales
sys.stdout.reconfigure(encoding="utf-8", errors="replace")


# ---------------------------------------------------------------------------
# 2. PARÁMETROS MODIFICABLES 🛠️
# ---------------------------------------------------------------------------
# (Ajusta solo esta sección para experimentar con la frontera de Pareto)

ALPHA: float = 0.9  # 0.90 – 1.00  → ↑α = +coste, ↓α = –coste pero –servicio
WC:    float = 1.0   # Peso al coste (se suele dejar en 1.0)
WS_VALUES: List[float] = [0.1, 0.5, 1, 2, 5, 10, 20]  # 0.1 – 20  → ↑w_s = +servicio 

# Tolerancia numérica para detectar variables libres y degeneración
TOL: float = 1e-6


# ---------------------------------------------------------------------------
# 3. RESTO DEL CÓDIGO
# ---------------------------------------------------------------------------

# 3.1  Utilidades genéricas ------------------------------------------------

def lock_opt(model: lp.LpProblem, expr: lp.LpAffineExpression, z_star: float, delta: float = 1e-7) -> None:
    """Fija el valor óptimo añadiendo *expr == z★* mediante dos desigualdades."""
    model += expr <= z_star + delta
    model += expr >= z_star - delta


def free_vars(model: lp.LpProblem) -> List[lp.LpVariable]:
    """Variables no básicas con *reduced cost* ≈ 0 y valor 0."""
    return [v for v in model.variables() if abs(v.dj) < TOL and abs(v.varValue) < TOL]


def extreme_points(model: lp.LpProblem, free_list: List[lp.LpVariable]) -> List[dict]:
    """Calcula vértices de la cara óptima optimizando cada var libre ±."""
    base_obj, base_sense = model.objective, model.sense
    pts = []
    for v in free_list:
        for sense, coef in [(lp.LpMaximize, 1), (lp.LpMinimize, -1)]:
            model.sense, model.objective = sense, coef * v
            model.solve(lp.PULP_CBC_CMD(msg=False))
            if model.status == lp.LpStatusOptimal:
                pts.append({x.name: x.varValue for x in model.variables()})
    model.objective, model.sense = base_obj, base_sense  # restaurar
    return pts


def scatter_face(points: List[dict], vx: str, vy: str, title: str) -> None:
    """Grafica la proyección (vx, vy) de los puntos extremos obtenidos."""
    df = pd.DataFrame([{"vx": p.get(vx, 0), "vy": p.get(vy, 0)} for p in points])
    if df.empty or (df["vx"].nunique() <= 1 and df["vy"].nunique() <= 1):
        print(f"⚠️  Cara óptima {title} degenerada (no se grafica).")
        return
    plt.figure()
    plt.scatter(df["vx"], df["vy"])
    plt.xlabel(vx)
    plt.ylabel(vy)
    plt.title(title)
    plt.grid(True)
    plt.show()


# 3.2  Modelo lexicográfico ------------------------------------------------

def run_lexicographic(alpha: float, excel_file: str) -> Tuple[float, float, pd.DataFrame]:
    """
    Resuelve la Fase 2 del modelo lexicográfico.
    Devuelve:
      - coste mínimo (fase 1)
      - nivel de servicio
      - DataFrame con la planificación óptima: columnas ['Product','Period','Production']
    """
    # Cargar y preprocesar
    df_sd, df_bc = lex.load_data(excel_file)
    P, T, D, SST, EEX, Cap = lex.preprocess_data(df_sd, df_bc)

    # --- Fase 1: coste mínimo f★ ---
    f_star, _, _ = lex.build_lex_model(P, T, D, SST, EEX, Cap, alpha, lex.c_prod, lex.c_hold, lex.c_exc)

    # --- Fase 2: minimiza shortfall manteniendo coste f★ ---
    m = lp.LpProblem("lex_phase2", lp.LpMinimize)
    x = lp.LpVariable.dicts("x", (P, T), lowBound=0)
    I = lp.LpVariable.dicts("I", (P, T), lowBound=0)
    s = lp.LpVariable("shortfall", lowBound=0)

    cost_expr = lp.lpSum(lex.c_prod[p]*x[p][t] + lex.c_hold[p]*I[p][t] + lex.c_exc[p]*EEX[(p, t)]
                         for p in P for t in T)
    m += s
    m += cost_expr <= f_star

    total_demand = sum(D[(p, t)] for p in P for t in T)
    m += lp.lpSum(x[p][t] for p in P for t in T) + s >= alpha * total_demand

    # Inventario encadenado, SST y capacidad
    for p in P:
        for k, t in enumerate(T):
            if k == 0:
                m += x[p][t] == D[(p, t)] + I[p][t]
            else:
                prev = T[k-1]
                m += I[p][prev] + x[p][t] == D[(p, t)] + I[p][t]
            m += I[p][t] >= SST[(p, t)]
    for t in T:
        m += lp.lpSum(x[p][t] for p in P) <= Cap[t]

    m.solve(lp.PULP_CBC_CMD(msg=False))

    # --- Extraer resultados ---
    # Nivel de servicio
    total_production = sum(x[p][t].value() for p in P for t in T)
    service_level = total_production / total_demand

    # Planificación a DataFrame
    plan = [
        {"Product": p, "Period": t, "Production": x[p][t].value()}
        for p in P for t in T if x[p][t].value() > TOL
    ]
    plan_df = pd.DataFrame(plan)

    return f_star, service_level, plan_df


# 3.3  Modelo weighted‑sum --------------------------------------------------

def run_weighted(ws: float, excel_file: str, wc: float = WC, alpha: float = ALPHA) -> Tuple[float, float]:
    """Ejecuta weighted‑sum y devuelve (coste_total, service_level)."""
    df_sd, df_bc = wsum.load_data(excel_file)
    P, T, D, SST, EEX, Cap = wsum.preprocess_data(df_sd, df_bc)

    m = lp.LpProblem("weighted_sum", lp.LpMinimize)
    x = lp.LpVariable.dicts("x", (P, T), lowBound=0)
    I = lp.LpVariable.dicts("I", (P, T), lowBound=0)
    s = lp.LpVariable("shortfall", lowBound=0)

    cost_expr = lp.lpSum(wsum.c_prod[p]*x[p][t] + wsum.c_hold[p]*I[p][t] + wsum.c_exc[p]*EEX[(p, t)]
                         for p in P for t in T)
    m += wc * cost_expr + ws * s

    total_demand = sum(D[(p, t)] for p in P for t in T)
    m += s >= alpha * total_demand - lp.lpSum(x[p][t] for p in P for t in T)

    for p in P:
        for k, t in enumerate(T):
            if k == 0:
                m += x[p][t] == D[(p, t)] + I[p][t]
            else:
                prev = T[k-1]
                m += I[p][prev] + x[p][t] == D[(p, t)] + I[p][t]
            m += I[p][t] >= SST[(p, t)]
    for t in T:
        m += lp.lpSum(x[p][t] for p in P) <= Cap[t]

    m.solve(lp.PULP_CBC_CMD(msg=False))

    total_cost = lp.value(cost_expr)
    total_production = sum(x[p][t].value() for p in P for t in T)
    service_level = total_production / total_demand
    return total_cost, service_level


# 3.4  Plot de la frontera de Pareto ----------------------------------------

def plot_pareto(pareto_df: pd.DataFrame) -> None:
    plt.figure()
    plt.scatter(pareto_df["service"], pareto_df["cost"], label="Weighted‑sum")
    row_lex = pareto_df[pareto_df["model"] == "lex"]
    plt.scatter(row_lex["service"], row_lex["cost"], marker="x", s=100, label="Lexicográfico")
    plt.xlabel("Service Level")
    plt.ylabel("Coste total")
    plt.title("Frontera de Pareto – Coste vs Service Level")
    plt.legend()
    plt.grid(True)
    plt.show()


# 3.5  Función main() --------------------------------------------------------

def main(input_excel) -> None:
    # --- Lexicográfico ---
    print(f">>> Ejecutando lexicográfico con α={ALPHA:.2f} …")
    cost_lex, srv_lex, plan_df = run_lexicographic(ALPHA, input_excel)
    print(f"   Coste           : {cost_lex:,.2f}")
    print(f"   Service level   : {srv_lex:.4f}\n")

    # Imprimir planificación y guardar Excel
    print(">>> Planificación óptima (lexicográfico):")
    print(plan_df.to_string(index=False))
    plan_df.to_excel("Plan_de_Produccion_Lexico.xlsx", index=False)
    print("Plan guardado en Plan_de_Produccion_Lexico.xlsx\n")

    # --- Weighted‑sum para distintos pesos ---
    print(">>> Explorando weighted‑sum en distintos w_s …")
    results = []
    for ws in WS_VALUES:
        cost, srv = run_weighted(ws, input_excel)
        print(f"   w_s={ws:<5}: coste={cost:,.2f}  service={srv:.4f}")
        results.append({"model": "ws", "w_s": ws, "cost": cost, "service": srv})

    # Añadimos el punto lexicográfico para graficar
    results.append({"model": "lex", "w_s": None, "cost": cost_lex, "service": srv_lex})
    df_pareto = pd.DataFrame(results)
    df_pareto.to_csv("pareto_results.csv", index=False)
    print("\nResultados guardados en pareto_results.csv\n")

    # --- Dibujo de Pareto ---
    plot_pareto(df_pareto)


# ---------------------------------------------------------------------------
if __name__ == "__main__":
    main()

def optimize_from_excel(input_excel) -> dict:
    """Ejecuta la optimización a partir de un archivo Excel y devuelve los resultados clave como diccionario."""
    cost_lex, srv_lex, plan_df = run_lexicographic(ALPHA, input_excel)

    results = []
    for ws in WS_VALUES:
        cost, srv = run_weighted(ws, input_excel)
        results.append({"model": "ws", "w_s": ws, "cost": cost, "service": srv})

    results.append({"model": "lex", "w_s": None, "cost": cost_lex, "service": srv_lex})

    cost_lex, srv_lex, plan_df = run_lexicographic(ALPHA, input_excel)
    print(f"   Coste           : {cost_lex:,.2f}")
    print(f"   Service level   : {srv_lex:.4f}\n")

    # Imprimir planificación y guardar Excel
    print(">>> Planificación óptima (lexicográfico):")
    print(plan_df.to_string(index=False))
    plan_df.to_excel("Plan_de_Produccion_Lexico.xlsx", index=False)
    
    # Regresar el DataFrame actualizado
    return plan_df