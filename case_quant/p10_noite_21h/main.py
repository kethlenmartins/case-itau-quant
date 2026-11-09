#!/usr/bin/env python3
"""H2: P7 com horizonte estendido entre 21h e 05h."""
import datetime as dt
import importlib.util
import json
import os
import sys

spec = importlib.util.spec_from_file_location("p2_base", os.path.join("..", "p2_perda_marginal", "main.py"))
p2 = importlib.util.module_from_spec(spec); spec.loader.exec_module(p2)
MAX_MOV, MAX_Q, TOP = 3, 10, 5

def decidir(dados):
    try:
        with open(p2.ARQ_CACHE, encoding="utf-8") as f: perfis = json.load(f)["perfis"]
    except (OSError, ValueError, KeyError): return []
    agora = dt.datetime.fromisoformat(dados["timestamp"])
    estado = {e["station_id"]: dict(e) for e in dados["estacoes"] if e["status"] == "active"}
    passos = 8 if agora.hour == 21 else 2
    def perfil(sid, instante):
        r, a = perfis.get(p2.chave(sid, instante.hour, instante.weekday()), (0.0, 0.0))
        return (0.0 if instante.hour < 5 or instante.hour >= 22 else r), a
    def risco(e, bikes):
        total, instante, b = 0.0, agora, float(bikes)
        for _ in range(passos):
            r, a = perfil(e["station_id"], instante)
            total += p2.perda(b, e["capacity"], r, a)
            b = min(e["capacity"], max(0.0, b - r + a))
            instante += dt.timedelta(hours=1)
        return total
    movs=[]
    for _ in range(MAX_MOV):
        melhor=None
        for q in range(1, MAX_Q+1):
            osrc=[]; odst=[]
            for e in estado.values():
                b=e["available_bikes"]
                if b>=q: osrc.append((risco(e,b-q)-risco(e,b),e["station_id"]))
                if e["available_docks"]>=q: odst.append((risco(e,b)-risco(e,b+q),e["station_id"]))
            osrc.sort(); odst.sort(reverse=True)
            for custo,o in osrc[:TOP]:
                for beneficio,d in odst[:TOP]:
                    if o!=d:
                        cand=(beneficio-custo,q,o,d)
                        if melhor is None or cand>melhor: melhor=cand
        if melhor is None or melhor[0]<=1e-9: break
        _,q,o,d=melhor; origem,destino=estado[o],estado[d]
        movs.append({"origem":o,"destino":d,"quantidade":q})
        origem["available_bikes"]-=q; origem["available_docks"]+=q
        destino["available_bikes"]+=q; destino["available_docks"]-=q
    return movs

def main():
    if "--preparar" in sys.argv: return p2.preparar()
    if "--passo" in sys.argv:
        try: movs=decidir(json.load(sys.stdin))
        except Exception as e: print(repr(e),file=sys.stderr); movs=[]
        print(json.dumps({"movimentacoes":movs})); return 0
    return 0
if __name__ == "__main__": raise SystemExit(main())
