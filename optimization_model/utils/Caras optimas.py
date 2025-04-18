# ============================================================================
#  caras_optimas_fix.py         <--  python caras_optimas_fix.py
#  (todo ASCII; DELTA = 1e-4)
# ============================================================================
import pulp as lp
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import sys, warnings

# salida UTF‑8 (Windows)
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import Bus_lex as lex
import Suma_ponderada_funciones as wsum

TOL        = 1e-6     # tolerancia |dj|
DELTA      = 1e-4     # holgura en el óptimo  (coste <= z*+DELTA)
N_SAMPLES  = 60       # cuántas soluciones aleatorias

# ─────────────────────────────────────────────────────────────
# utilidades
# ─────────────────────────────────────────────────────────────
def lock_opt(model, expr, z_star):
    model += expr <= z_star + DELTA

def free_vars(model):
    return [v for v in model.variables()
            if abs(v.dj) < TOL and abs(v.varValue) < TOL]

def random_point(model, free_list):
    coeffs = {v: np.random.randn() for v in free_list}
    old_obj, old_sense = model.objective, model.sense
    model.sense, model.objective = lp.LpMaximize, lp.lpSum(coeffs[v]*v for v in free_list)
    model.solve(lp.PULP_CBC_CMD(msg=False))
    sol = {v.name: v.varValue for v in model.variables()}
    model.objective, model.sense = old_obj, old_sense
    return sol

def sample_face(model, free_list):
    pts, seen = [], set()
    for _ in range(N_SAMPLES):
        p = random_point(model, free_list)
        key = tuple(round(p[v.name], 6) for v in free_list[:2])
        if key not in seen:
            pts.append(p); seen.add(key)
    return pts

def plot_points(points, v1, v2, title):
    df = pd.DataFrame({v1: [p.get(v1,0) for p in points],
                       v2: [p.get(v2,0) for p in points]})
    if df[v1].nunique() <= 1 and df[v2].nunique() <= 1:
        print(f"⚠  {title}: la cara sigue siendo puntual; nada que mostrar.")
        return
    plt.figure(figsize=(6,5))
    plt.scatter(df[v1], df[v2])
    plt.title(title); plt.xlabel(v1); plt.ylabel(v2); plt.grid(True)
    plt.show()

# ─────────────────────────────────────────────────────────────
# modelos
# ─────────────────────────────────────────────────────────────
def build_lex_phase2():
    df_sd, df_bc = lex.load_data(lex.excel_file)
    P,T,D,SST,EEX,Cap = lex.preprocess_data(df_sd, df_bc)
    z1,*_ = lex.build_lex_model(P,T,D,SST,EEX,Cap,
                                lex.alpha, lex.c_prod, lex.c_hold, lex.c_exc)

    m = lp.LpProblem("lex_fase2", lp.LpMinimize)
    x = lp.LpVariable.dicts("x", (P,T), 0)
    I = lp.LpVariable.dicts("I", (P,T), 0)
    s = lp.LpVariable("short", 0)

    cost = lp.lpSum(lex.c_prod[p]*x[p][t] + lex.c_hold[p]*I[p][t] +
                    lex.c_exc[p]*EEX[(p,t)] for p in P for t in T)
    m += s
    lock_opt(m, cost, z1)

    dem = lp.lpSum(D[(p,t)] for p in P for t in T)
    m += lp.lpSum(x[p][t] for p in P for t in T) + s >= lex.alpha*dem

    for p in P:
        for k,t in enumerate(T):
            if k==0: m += x[p][t] == D[(p,t)] + I[p][t]
            else:    m += I[p][T[k-1]] + x[p][t] == D[(p,t)] + I[p][t]
            m += I[p][t] >= SST[(p,t)]
    for t in T:
        m += lp.lpSum(x[p][t] for p in P) <= Cap[t]

    m.solve(lp.PULP_CBC_CMD(msg=False))
    return m

# ─── parche rápido dentro de build_weighted() ────────────────────────────
def build_weighted():
    df_sd, df_bc = wsum.load_data(wsum.excel_file)
    P,T,D,SST,EEX,Cap = wsum.preprocess_data(df_sd, df_bc)

    m = lp.LpProblem("weighted", lp.LpMinimize)
    x = lp.LpVariable.dicts("x", (P,T), 0)
    I = lp.LpVariable.dicts("I", (P,T), 0)
    s = lp.LpVariable("short", 0)

    cost = lp.lpSum(wsum.c_prod[p]*x[p][t] + wsum.c_hold[p]*I[p][t] +
                    wsum.c_exc[p]*EEX[(p,t)] for p in P for t in T)
    obj_expr = wsum.w_c*cost + wsum.w_s*s
    m += obj_expr                            # objetivo

    dem = lp.lpSum(D[(p,t)] for p in P for t in T)
    m += s >= wsum.alpha*dem - lp.lpSum(x[p][t] for p in P for t in T)

    for p in P:
        for k,t in enumerate(T):
            if k==0: m += x[p][t] == D[(p,t)] + I[p][t]
            else:    m += I[p][T[k-1]] + x[p][t] == D[(p,t)] + I[p][t]
            m += I[p][t] >= SST[(p,t)]
    for t in T:
        m += lp.lpSum(x[p][t] for p in P) <= Cap[t]

    # 1ª resolución: obtenemos z*
    m.solve(lp.PULP_CBC_CMD(msg=False))
    z_star = lp.value(obj_expr)

    # fijamos el óptimo y resolvemos de nuevo para obtener duales
    m += obj_expr <= z_star + DELTA
    m += obj_expr >= z_star - DELTA
    m.solve(lp.PULP_CBC_CMD(msg=False))

    return m
# ────────────────────────────────────────────────────────────────────────


# ─────────────────────────────────────────────────────────────
def analyse(name, builder):
    print(f"\n— {name} —")
    m = builder()
    libres = free_vars(m)
    if not libres:
        print("✅  solución única.")
        return
    print("⚠  variables libres:", [v.name for v in libres])

    pts = sample_face(m, libres)
    if len(libres) >= 2:
        plot_points(pts, libres[0].name, libres[1].name, f"Cara óptima – {name}")
    else:
        print("(solo 1 variable libre; no hay plano 2‑D para pintar)")

# ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    warnings.filterwarnings("ignore", category=UserWarning)
    analyse("Lexicográfico", build_lex_phase2)
    analyse("Suma ponderada", build_weighted)
