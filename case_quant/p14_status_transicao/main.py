#!/usr/bin/env python3
"""H6: P13 com P(active em t+1 | active em t), e nao frequencia marginal."""
import csv
import datetime as dt
import importlib.util
import json
import os
import sys
from collections import defaultdict

spec = importlib.util.spec_from_file_location("p2_base", os.path.join("..", "p2_perda_marginal", "main.py"))
p2 = importlib.util.module_from_spec(spec); spec.loader.exec_module(p2)
CACHE = "perfil_transicao_status_cache.json"
MAX_MOV, MAX_Q, TOP = 3, 10, 5

def preparar():
    p2.preparar()
    with open(p2.ARQ_CACHE, encoding="utf-8") as f: perfis = json.load(f)["perfis"]
    estados = {}
    with open(os.path.join("..", "dados", "historico_status.csv"), encoding="utf-8", newline="") as f:
        for linha in csv.DictReader(f): estados[(linha["station_id"], linha["timestamp"])] = linha["status"]
    base, continua = defaultdict(int), defaultdict(int)
    for (sid, ts), status in estados.items():
        if status != "active": continue
        t = dt.datetime.fromisoformat(ts); prox = (t + dt.timedelta(hours=1)).isoformat(sep=" ")
        futuro = estados.get((sid, prox))
        if futuro is None: continue
        k = p2.chave(sid, t.hour, t.weekday())
        base[k] += 1
        if futuro == "active": continua[k] += 1
    transicao = {k: continua[k] / n for k, n in base.items() if n}
    with open(CACHE, "w", encoding="utf-8") as f: json.dump({"perfis": perfis, "transicao": transicao}, f, separators=(",", ":"))
    return 0

def decidir(dados):
    try:
        with open(CACHE, encoding="utf-8") as f: cache = json.load(f)
    except (OSError, ValueError, KeyError): return []
    perfis, transicao = cache["perfis"], cache["transicao"]
    agora = dt.datetime.fromisoformat(dados["timestamp"]); prox = agora + dt.timedelta(hours=1)
    estado = {e["station_id"]: dict(e) for e in dados["estacoes"] if e["status"] == "active"}
    def perfil(sid, instante):
        r, a = perfis.get(p2.chave(sid, instante.hour, instante.weekday()), (0.0, 0.0))
        return (0.0 if instante.hour < 5 or instante.hour >= 22 else r), a
    def risco(e, bikes):
        r0, a0 = perfil(e["station_id"], agora)
        atual = p2.perda(bikes, e["capacity"], r0, a0)
        b1 = min(e["capacity"], max(0.0, bikes-r0+a0))
        r1, a1 = perfil(e["station_id"], prox)
        prob = transicao.get(p2.chave(e["station_id"], agora.hour, agora.weekday()), 1.0)
        return atual + prob * p2.perda(b1, e["capacity"], r1, a1)
    movs = []
    for _ in range(MAX_MOV):
        melhor = None
        for q in range(1, MAX_Q+1):
            origens, destinos = [], []
            for e in estado.values():
                b = e["available_bikes"]
                if b >= q: origens.append((risco(e,b-q)-risco(e,b), e["station_id"]))
                if e["available_docks"] >= q: destinos.append((risco(e,b)-risco(e,b+q), e["station_id"]))
            origens.sort(); destinos.sort(reverse=True)
            for custo, origem in origens[:TOP]:
                for ganho, destino in destinos[:TOP]:
                    if origem != destino:
                        cand = (ganho-custo, q, origem, destino)
                        if melhor is None or cand > melhor: melhor = cand
        if melhor is None or melhor[0] <= 1e-9: break
        _, q, origem, destino = melhor; o, d = estado[origem], estado[destino]
        movs.append({"origem": origem, "destino": destino, "quantidade": q})
        o["available_bikes"] -= q; o["available_docks"] += q; d["available_bikes"] += q; d["available_docks"] -= q
    return movs

def main():
    if "--preparar" in sys.argv: return preparar()
    if "--passo" in sys.argv:
        try: movs = decidir(json.load(sys.stdin))
        except Exception as erro: print(repr(erro), file=sys.stderr); movs = []
        print(json.dumps({"movimentacoes": movs})); return 0
    return 0
if __name__ == "__main__": raise SystemExit(main())
