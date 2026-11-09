#!/usr/bin/env python3
"""H4: P7 ajustado pela condicao meteorologica observada no instante."""
import csv
import datetime as dt
import importlib.util
import json
import os
import sys
from collections import defaultdict

spec = importlib.util.spec_from_file_location("p2_base", os.path.join("..", "p2_perda_marginal", "main.py"))
p2 = importlib.util.module_from_spec(spec); spec.loader.exec_module(p2)
CACHE = "perfil_clima_cache.json"
MAX_MOV, MAX_Q, TOP = 3, 10, 5

def hora_chave(instante):
    return instante.replace(minute=0, second=0, microsecond=0).isoformat(sep=" ")

def preparar():
    p2.preparar()
    with open(p2.ARQ_CACHE, encoding="utf-8") as f: perfis = json.load(f)["perfis"]
    condicao = {}
    with open(os.path.join("..", "dados", "clima.csv"), encoding="utf-8", newline="") as f:
        for linha in csv.DictReader(f): condicao[linha["timestamp"]] = linha["weather_condition"]
    # Total de viagens por hora, condicionado ao clima e comparado ao mesmo hora/dia.
    contagem = defaultdict(lambda: [0, 0]); horas = defaultdict(set)
    for chave_ts, c in condicao.items():
        t = dt.datetime.fromisoformat(chave_ts); base = "%d|%d" % (t.hour, t.weekday())
        horas[base].add(chave_ts); horas[c + "|" + base].add(chave_ts)
    with open(os.path.join("..", "dados", "viagens.csv"), encoding="utf-8", newline="") as f:
        for linha in csv.DictReader(f):
            for indice, campo in enumerate(("start_time", "end_time")):
                t = dt.datetime.fromisoformat(linha[campo]); ts = hora_chave(t); c = condicao.get(ts)
                if c is not None: contagem[c + "|%d|%d" % (t.hour, t.weekday())][indice] += 1
                contagem["_base|%d|%d" % (t.hour, t.weekday())][indice] += 1
    fatores = {}
    for k, valores in contagem.items():
        if not k.startswith("_base|"): continue
        _, hora, dow = k.split("|"); n_base = len(horas.get(hora + "|" + dow, ()))
        for c in set(x.split("|", 1)[0] for x in condicao.values()):
            ck = c + "|" + hora + "|" + dow; n_cond = len(horas.get(ck, ()))
            if n_cond and n_base:
                atual = contagem[ck]; fatores[ck] = [
                    (atual[0] / n_cond) / (valores[0] / n_base) if valores[0] else 1.0,
                    (atual[1] / n_cond) / (valores[1] / n_base) if valores[1] else 1.0,
                ]
    with open(CACHE, "w", encoding="utf-8") as f: json.dump({"perfis": perfis, "fatores": fatores}, f, separators=(",", ":"))
    return 0

def decidir(dados):
    try:
        with open(CACHE, encoding="utf-8") as f: cache = json.load(f)
    except (OSError, ValueError, KeyError): return []
    agora = dt.datetime.fromisoformat(dados["timestamp"]); prox = agora + dt.timedelta(hours=1)
    perfis, fatores = cache["perfis"], cache["fatores"]
    estado = {e["station_id"]: dict(e) for e in dados["estacoes"] if e["status"] == "active"}
    def perfil(sid, instante, clima):
        r, a = perfis.get(p2.chave(sid, instante.hour, instante.weekday()), (0.0, 0.0))
        c = clima.get("weather_condition")
        fr, fa = fatores.get("%s|%d|%d" % (c, instante.hour, instante.weekday()), (1.0, 1.0))
        return (0.0 if instante.hour < 5 or instante.hour >= 22 else r * fr), a * fa
    def risco(e, bikes):
        total, b = 0.0, float(bikes)
        # O clima futuro nao esta disponivel no payload: somente a hora corrente e ajustada.
        for instante, clima in ((agora, dados.get("clima", {})), (prox, {})):
            r, a = perfil(e["station_id"], instante, clima)
            total += p2.perda(b, e["capacity"], r, a)
            b = min(e["capacity"], max(0.0, b-r+a))
        return total
    movs = []
    for _ in range(MAX_MOV):
        melhor = None
        for q in range(1, MAX_Q + 1):
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
