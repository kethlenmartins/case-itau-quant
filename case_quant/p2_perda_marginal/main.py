#!/usr/bin/env python3
"""P2 experimental: perfis historicos e perda marginal, sem bibliotecas externas."""
import csv
import datetime as dt
import json
import os
import sys
from collections import defaultdict

PASTA_DADOS = os.path.join("..", "dados")
ARQ_CACHE = "perfil_cache.json"
MAX_MOV = 3


def chave(station_id, hora, dia_semana):
    return "%s|%d|%d" % (station_id, hora, dia_semana)


def preparar():
    """Cria medias por estacao, hora e dia da semana usando apenas viagens.csv."""
    viagens = os.path.join(PASTA_DADOS, "viagens.csv")
    retiradas = defaultdict(int)
    devolucoes = defaultdict(int)
    datas_por_dow = defaultdict(set)
    with open(viagens, encoding="utf-8", newline="") as arq:
        for linha in csv.DictReader(arq):
            inicio = dt.datetime.fromisoformat(linha["start_time"])
            fim = dt.datetime.fromisoformat(linha["end_time"])
            dow_i = inicio.weekday()
            dow_f = fim.weekday()
            datas_por_dow[dow_i].add(inicio.date().isoformat())
            datas_por_dow[dow_f].add(fim.date().isoformat())
            retiradas[chave(linha["start_station_id"], inicio.hour, dow_i)] += 1
            devolucoes[chave(linha["end_station_id"], fim.hour, dow_f)] += 1
    perfis = {}
    for k in set(retiradas) | set(devolucoes):
        dow = int(k.rsplit("|", 1)[1])
        n = max(1, len(datas_por_dow[dow]))
        perfis[k] = [retiradas[k] / n, devolucoes[k] / n]
    with open(ARQ_CACHE, "w", encoding="utf-8") as arq:
        json.dump({"perfis": perfis}, arq, separators=(",", ":"))
    return 0


def perda(bikes, capacidade, retiradas, devolucoes):
    return max(retiradas - bikes, 0.0) + max(devolucoes - (capacidade - bikes), 0.0)


def decidir(dados):
    try:
        with open(ARQ_CACHE, encoding="utf-8") as arq:
            perfis = json.load(arq)["perfis"]
    except (OSError, ValueError, KeyError):
        return []
    momento = dt.datetime.fromisoformat(dados["timestamp"])
    hora, dow = momento.hour, momento.weekday()
    estado = {e["station_id"]: dict(e) for e in dados["estacoes"] if e["status"] == "active"}

    def risco(e, bikes):
        r, a = perfis.get(chave(e["station_id"], hora, dow), (0.0, 0.0))
        return perda(bikes, e["capacity"], r, a)

    movimentos = []
    for _ in range(MAX_MOV):
        melhor = None
        for origem in estado.values():
            max_q = min(origem["available_bikes"], 10)
            if max_q <= 0:
                continue
            for destino in estado.values():
                if origem["station_id"] == destino["station_id"]:
                    continue
                limite = min(max_q, destino["available_docks"])
                if limite <= 0:
                    continue
                antes = risco(origem, origem["available_bikes"]) + risco(destino, destino["available_bikes"])
                for qtd in range(1, limite + 1):
                    depois = risco(origem, origem["available_bikes"] - qtd) + risco(destino, destino["available_bikes"] + qtd)
                    ganho = antes - depois
                    candidato = (ganho, qtd, origem["station_id"], destino["station_id"])
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
    print("P2 experimental; use --preparar e --passo.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
