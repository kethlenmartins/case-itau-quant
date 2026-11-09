#!/usr/bin/env python3
"""P7: mesma busca de P3, com perda determinística em duas horas."""
import datetime as dt
import importlib.util
import json
import os
import sys

CAMINHO_P2 = os.path.join("..", "p2_perda_marginal", "main.py")
spec = importlib.util.spec_from_file_location("p2_base", CAMINHO_P2)
p2 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(p2)

MAX_MOV = 3
MAX_Q = 10
TOP_PONTAS = 5


def decidir(dados):
    try:
        with open(p2.ARQ_CACHE, encoding="utf-8") as arq:
            perfis = json.load(arq)["perfis"]
    except (OSError, ValueError, KeyError):
        return []
    momento = dt.datetime.fromisoformat(dados["timestamp"])
    proximo_momento = momento + dt.timedelta(hours=1)
    estado = {e["station_id"]: dict(e) for e in dados["estacoes"] if e["status"] == "active"}

    def perfil(station_id, instante):
        retiradas, devolucoes = perfis.get(p2.chave(station_id, instante.hour, instante.weekday()), (0.0, 0.0))
        # O simulador nao aceita retiradas noturnas; devolucoes pendentes permanecem possiveis.
        if instante.hour < 5 or instante.hour >= 22:
            retiradas = 0.0
        return retiradas, devolucoes

    def risco(e, bikes):
        r0, a0 = perfil(e["station_id"], momento)
        perda_atual = p2.perda(bikes, e["capacity"], r0, a0)
        # Aproximacao de estoque no inicio da hora seguinte; a politica sera reotimizada la.
        bikes_1 = min(e["capacity"], max(0.0, bikes - r0 + a0))
        r1, a1 = perfil(e["station_id"], proximo_momento)
        perda_proxima = p2.perda(bikes_1, e["capacity"], r1, a1)
        return perda_atual + perda_proxima

    movimentos = []
    for _ in range(MAX_MOV):
        melhor = None
        for qtd in range(1, MAX_Q + 1):
            origens = []
            destinos = []
            for e in estado.values():
                bikes = e["available_bikes"]
                if bikes >= qtd:
                    custo = risco(e, bikes - qtd) - risco(e, bikes)
                    origens.append((custo, e["station_id"]))
                if e["available_docks"] >= qtd:
                    beneficio = risco(e, bikes) - risco(e, bikes + qtd)
                    destinos.append((beneficio, e["station_id"]))
            if not origens or not destinos:
                continue
            origens.sort()
            destinos.sort(reverse=True)
            for custo, origem_id in origens[:TOP_PONTAS]:
                for beneficio, destino_id in destinos[:TOP_PONTAS]:
                    if origem_id == destino_id:
                        continue
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
        return p2.preparar()
    if "--passo" in sys.argv:
        dados = json.load(sys.stdin)
        try:
            movs = decidir(dados)
        except Exception as erro:
            print(repr(erro), file=sys.stderr)
            movs = []
        print(json.dumps({"movimentacoes": movs}))
        return 0
    print("P7 experimental; use --preparar e --passo.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
