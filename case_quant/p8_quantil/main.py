#!/usr/bin/env python3
"""P8: P7 com perfis de demanda por quantil empirico, sem dependencias externas."""
import csv
import datetime as dt
import importlib.util
import json
import math
import os
import sys
from collections import defaultdict

CAMINHO_P2 = os.path.join("..", "p2_perda_marginal", "main.py")
spec = importlib.util.spec_from_file_location("p2_base", CAMINHO_P2)
p2 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(p2)

PASTA_DADOS = os.path.join("..", "dados")
ARQ_CACHE = "perfil_quantil_cache.json"
QUANTIL = float(os.environ.get("QUANTIL", "0.70"))
MAX_MOV = 3
MAX_Q = 10
TOP_PONTAS = 5


def q_empirico(valores, q):
    valores = sorted(valores)
    return valores[max(0, math.ceil(q * len(valores)) - 1)]


def preparar():
    """Constroi quantis incluindo zeros para cada estacao, hora e dia da semana."""
    estacoes = []
    with open(os.path.join(PASTA_DADOS, "estacoes.csv"), encoding="utf-8", newline="") as arq:
        for linha in csv.DictReader(arq):
            estacoes.append(linha["station_id"])
    retiradas = defaultdict(int)
    devolucoes = defaultdict(int)
    datas = set()
    with open(os.path.join(PASTA_DADOS, "viagens.csv"), encoding="utf-8", newline="") as arq:
        for linha in csv.DictReader(arq):
            inicio = dt.datetime.fromisoformat(linha["start_time"])
            fim = dt.datetime.fromisoformat(linha["end_time"])
            datas.add(inicio.date())
            chave_r = (linha["start_station_id"], inicio.hour, inicio.weekday(), inicio.date())
            chave_a = (linha["end_station_id"], fim.hour, fim.weekday(), fim.date())
            retiradas[chave_r] += 1
            devolucoes[chave_a] += 1
    datas_por_dow = defaultdict(list)
    for data in sorted(datas):
        datas_por_dow[data.weekday()].append(data)
    perfis = {}
    for station_id in estacoes:
        for hora in range(24):
            for dow in range(7):
                dias = datas_por_dow[dow]
                r = [retiradas[(station_id, hora, dow, data)] for data in dias]
                a = [devolucoes[(station_id, hora, dow, data)] for data in dias]
                perfis[p2.chave(station_id, hora, dow)] = [q_empirico(r, QUANTIL), q_empirico(a, QUANTIL)]
    with open(ARQ_CACHE, "w", encoding="utf-8") as arq:
        json.dump({"quantil": QUANTIL, "perfis": perfis}, arq, separators=(",", ":"))
    return 0


def decidir(dados):
    try:
        with open(ARQ_CACHE, encoding="utf-8") as arq:
            perfis = json.load(arq)["perfis"]
    except (OSError, ValueError, KeyError):
        return []
    momento = dt.datetime.fromisoformat(dados["timestamp"])
    proximo = momento + dt.timedelta(hours=1)
    estado = {e["station_id"]: dict(e) for e in dados["estacoes"] if e["status"] == "active"}

    def perfil(station_id, instante):
        r, a = perfis.get(p2.chave(station_id, instante.hour, instante.weekday()), (0.0, 0.0))
        return (0.0 if instante.hour < 5 or instante.hour >= 22 else r), a

    def risco(e, bikes):
        r0, a0 = perfil(e["station_id"], momento)
        atual = p2.perda(bikes, e["capacity"], r0, a0)
        bikes_1 = min(e["capacity"], max(0.0, bikes - r0 + a0))
        r1, a1 = perfil(e["station_id"], proximo)
        return atual + p2.perda(bikes_1, e["capacity"], r1, a1)

    movimentos = []
    for _ in range(MAX_MOV):
        melhor = None
        for qtd in range(1, MAX_Q + 1):
            origens, destinos = [], []
            for e in estado.values():
                bikes = e["available_bikes"]
                if bikes >= qtd:
                    origens.append((risco(e, bikes - qtd) - risco(e, bikes), e["station_id"]))
                if e["available_docks"] >= qtd:
                    destinos.append((risco(e, bikes) - risco(e, bikes + qtd), e["station_id"]))
            origens.sort()
            destinos.sort(reverse=True)
            for custo, origem_id in origens[:TOP_PONTAS]:
                for beneficio, destino_id in destinos[:TOP_PONTAS]:
                    if origem_id != destino_id:
                        candidato = (beneficio - custo, qtd, origem_id, destino_id)
                        if melhor is None or candidato > melhor:
                            melhor = candidato
        if melhor is None or melhor[0] <= 1e-9:
            break
        _, qtd, origem_id, destino_id = melhor
        origem, destino = estado[origem_id], estado[destino_id]
        movimentos.append({"origem": origem_id, "destino": destino_id, "quantidade": qtd})
        origem["available_bikes"] -= qtd
        origem["available_docks"] += qtd
        destino["available_bikes"] += qtd
        destino["available_docks"] -= qtd
    return movimentos


def main():
    if "--preparar" in sys.argv:
        return preparar()
    if "--passo" in sys.argv:
        dados = json.load(sys.stdin)
        try:
            movs = decidir(dados)
        except Exception as erro:
            print(repr(erro), file=sys.stderr)
            movs = []
        print(json.dumps({"movimentacoes": movs}))
        return 0
    print("P8 experimental; use --preparar e --passo.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
