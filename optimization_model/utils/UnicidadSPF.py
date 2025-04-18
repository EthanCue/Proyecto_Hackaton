# ---------- UnicidadSPF.py ----------
import pulp as lp
from Suma_ponderada_funciones import (
    load_data, preprocess_data,
    c_prod, c_hold, c_exc,
    alpha, w_c, w_s, excel_file
)

TOL = 1e-6  # tolerancia numérica


def modelo_weighted(products, periods, D, SST, EEX, Cap,
                    alpha, w_c, w_s, c_prod, c_hold, c_exc):
    m = lp.LpProblem('Weighted_Sum', lp.LpMinimize)
    x = lp.LpVariable.dicts('x', (products, periods), lowBound=0)
    I = lp.LpVariable.dicts('I', (products, periods), lowBound=0)
    s = lp.LpVariable('shortfall', lowBound=0)

    cost = lp.lpSum(c_prod[p]*x[p][t] + c_hold[p]*I[p][t] +
                    c_exc[p]*EEX[(p, t)]
                    for p in products for t in periods)
    m += w_c * cost + w_s * s

    m += s >= alpha * lp.lpSum(D[(p, t)]
                               for p in products for t in periods) - \
           lp.lpSum(x[p][t] for p in products for t in periods)

    for p in products:
        for idx, t in enumerate(periods):
            if idx == 0:
                m += x[p][t] == D[(p, t)] + I[p][t]
            else:
                prev = periods[idx-1]
                m += I[p][prev] + x[p][t] == D[(p, t)] + I[p][t]
            m += I[p][t] >= SST[(p, t)]
    for t in periods:
        m += lp.lpSum(x[p][t] for p in products) <= Cap[t]

    m.solve(lp.PULP_CBC_CMD(msg=False))
    return m


def verifica_unicidad_weighted():
    df_sd, df_bc = load_data(excel_file)
    products, periods, D, SST, EEX, Cap = preprocess_data(df_sd, df_bc)

    m = modelo_weighted(products, periods, D, SST, EEX, Cap,
                        alpha, w_c, w_s, c_prod, c_hold, c_exc)

    alt_vars = [
        v.name for v in m.variables()
        if abs(v.dj) < TOL and abs(v.varValue) < TOL
    ]

    if alt_vars:
        print("ATENCIÓN: hay soluciones óptimas múltiples.")
        print("Variables no básicas con rc=0:")
        for name in alt_vars:
            print(f"  - {name}")
    else:
        print("SOLUCIÓN ÚNICA (según tolerancia).")


if __name__ == "__main__":
    verifica_unicidad_weighted()
