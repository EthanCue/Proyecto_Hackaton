# ---------- UnicidadLex.py ----------
import pulp as lp
from Bus_lex import (
    load_data, preprocess_data,
    c_prod, c_hold, c_exc, alpha,
    build_lex_model, excel_file
)

TOL = 1e-6  # tolerancia numérica


def modelo_fase2(products, periods, D, SST, EEX, Cap,
                 alpha, c_prod, c_hold, c_exc, f1_star):
    m2 = lp.LpProblem('Lexico_Fase2', lp.LpMinimize)
    x2 = lp.LpVariable.dicts('x', (products, periods), lowBound=0)
    I2 = lp.LpVariable.dicts('I', (products, periods), lowBound=0)
    s  = lp.LpVariable('shortfall', lowBound=0)

    # coste ≤ f1_star
    m2 += lp.lpSum(
        c_prod[p]*x2[p][t] + c_hold[p]*I2[p][t] + c_exc[p]*EEX[(p, t)]
        for p in products for t in periods
    ) <= f1_star

    m2 += s  # objetivo

    # cobertura mínima
    m2 += lp.lpSum(x2[p][t] for p in products for t in periods) + s >= \
          alpha * lp.lpSum(D[(p, t)] for p in products for t in periods)

    # balance inventario, SST, capacidad
    for p in products:
        for idx, t in enumerate(periods):
            if idx == 0:
                m2 += x2[p][t] == D[(p, t)] + I2[p][t]
            else:
                prev = periods[idx-1]
                m2 += I2[p][prev] + x2[p][t] == D[(p, t)] + I2[p][t]
            m2 += I2[p][t] >= SST[(p, t)]
    for t in periods:
        m2 += lp.lpSum(x2[p][t] for p in products) <= Cap[t]

    m2.solve(lp.PULP_CBC_CMD(msg=False))
    return m2


def verifica_unicidad_lex():
    df_sd, df_bc = load_data(excel_file)
    products, periods, D, SST, EEX, Cap = preprocess_data(df_sd, df_bc)

    f1_star, *_ = build_lex_model(
        products, periods, D, SST, EEX, Cap,
        alpha, c_prod, c_hold, c_exc
    )

    m2 = modelo_fase2(products, periods, D, SST, EEX, Cap,
                      alpha, c_prod, c_hold, c_exc, f1_star)

    alt_vars = [
        v.name for v in m2.variables()
        if abs(v.dj) < TOL and abs(v.varValue) < TOL
    ]

    if alt_vars:
        print("ATENCIÓN: existen soluciones óptimas alternativas.")
        print("Variables no básicas con coste reducido = 0:")
        for name in alt_vars:
            print(f"  - {name}")
    else:
        print("SOLUCIÓN ÚNICA dentro de la tolerancia numérica.")


if __name__ == "__main__":
    verifica_unicidad_lex()
