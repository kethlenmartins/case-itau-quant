#!/usr/bin/env python3
"""H3: P7 com suavizacao do perfil por zona (somente biblioteca padrao)."""
import csv
import datetime as dt
import importlib.util
import json
import os
import sys
from collections import defaultdict

spec = importlib.util.spec_from_file_location("p2_base", os.path.join("..", "p2_perda_marginal", "main.py"))
p2 = importlib.util.module_from_spec(spec); spec.loader.exec_module(p2)
CACHE = "perfil_zona_cache.json"
MAX_MOV, MAX_Q, TOP = 3, 10, 5
# Peso alto preserva o sinal local; a zona entra apenas como regularizacao.
PESO_ESTACAO = 0.80

def preparar():
    p2.preparar()
    with open(p2.ARQ_CACHE, encoding="utf-8") as f:
        perfis = json.load(f)["perfis"]
    zonas, por_zona = {}, defaultdict(list)
    with open(os.path.join("..", "dados", "estacoes.csv"), encoding="utf-8", newline="") as f:
        for linha in csv.DictReader(f):
            zonas[linha["station_id"]] = linha["zone"]
            por_zona[linha["zone"]].append(linha["station_id"])
    zona_perfis = {}
    for zona, ids in por_zona.items():
        for hora in range(24):
            for dow in range(7):
                retiradas = devolucoes = 0.0
                for sid in ids:
                    r, a = perfis.get(p2.chave(sid, hora, dow), (0.0, 0.0))
                    retiradas += r; devolucoes += a
                zona_perfis["%s|%d|%d" % (zona, hora, dow)] = [retiradas / len(ids), devolucoes / len(ids)]
    with open(CACHE, "w", encoding="utf-8") as f:
        json.dump({"perfis": perfis, "zonas": zonas, "zona_perfis": zona_perfis}, f, separators=(",", ":"))
    return 0

def decidir(dados):
    try:
        with open(CACHE, encoding="utf-8") as f: cache = json.load(f)
    except (OSError, ValueError, KeyError): return []
    perfis, zonas, zona_perfis = cache["perfis"], cache["zonas"], cache["zona_perfis"]
    agora = dt.datetime.fromisoformat(dados["timestamp"]); prox = agora + dt.timedelta(hours=1)
    estado = {e["station_id"]: dict(e) for e in dados["estacoes"] if e["status"] == "active"}
    def perfil(sid, instante):
        r, a = perfis.get(p2.chave(sid, instante.hour, instante.weekday()), (0.0, 0.0))
        z = zonas.get(sid)
        zr, za = zona_perfis.get("%s|%d|%d" % (z, instante.hour, instante.weekday()), (0.0, 0.0))
        r = PESO_ESTACAO * r + (1.0 - PESO_ESTACAO) * zr
        a = PESO_ESTACAO * a + (1.0 - PESO_ESTACAO) * za
        return (0.0 if instante.hour < 5 or instante.hour >= 22 else r), a
    def risco(e, bikes):
        total, b = 0.0, float(bikes)
        for instante in (agora, prox):
            r, a = perfil(e["station_id"], instante)
            total += p2.perda(b, e["capacity"], r, a)
            b = min(e["capacity"], max(0.0, b - r + a))
        return total
    movs = []
    for _ in range(MAX_MOV):
        melhor = None
        for q in range(1, MAX_Q + 1):
            origens, destinos = [], []
            for e in estado.values():
                b = e["available_bikes"]
                if b >= q: origens.append((risco(e, b-q) - risco(e, b), e["station_id"]))
                if e["available_docks"] >= q: destinos.append((risco(e, b) - risco(e, b+q), e["station_id"]))
            origens.sort(); destinos.sort(reverse=True)
            for custo, origem in origens[:TOP]:
                for ganho, destino in destinos[:TOP]:
                    if origem != destino:
                        candidato = (ganho-custo, q, origem, destino)
                        if melhor is None or candidato > melhor: melhor = candidato
        if melhor is None or melhor[0] <= 1e-9: break
        _, q, origem, destino = melhor; o, d = estado[origem], estado[destino]
        movs.append({"origem": origem, "destino": destino, "quantidade": q})
        o["available_bikes"] -= q; o["available_docks"] += q
        d["available_bikes"] += q; d["available_docks"] -= q
    return movs

def main():
    if "--preparar" in sys.argv: return preparar()
    if "--passo" in sys.argv:
        try: movs = decidir(json.load(sys.stdin))
        except Exception as erro: print(repr(erro), file=sys.stderr); movs = []
        print(json.dumps({"movimentacoes": movs})); return 0
    return 0
if __name__ == "__main__": raise SystemExit(main())
