#!/usr/bin/env python3
"""P3: mesma perda de P2, com busca separável por origem, destino e quantidade."""
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


def decidir(dados):
    try:
        with open(p2.ARQ_CACHE, encoding="utf-8") as arq:
            perfis = json.load(arq)["perfis"]
    except (OSError, ValueError, KeyError):
        return []

    momento = dt.datetime.fromisoformat(dados["timestamp"])
    hora, dow = momento.hour, momento.weekday()
    estado = {e["station_id"]: dict(e) for e in dados["estacoes"] if e["status"] == "active"}

    def risco(e, bikes):
        retiradas, devolucoes = perfis.get(p2.chave(e["station_id"], hora, dow), (0.0, 0.0))
        return p2.perda(bikes, e["capacity"], retiradas, devolucoes)

    movimentos = []
    for _ in range(MAX_MOV):
        melhor = None
        # Para uma quantidade fixa, ganho = beneficio do destino - custo da origem.
        # Logo basta combinar o melhor par viavel, sem enumerar todos os pares.
        for qtd in range(1, MAX_Q + 1):
            origens = []
            destinos = []
            for e in estado.values():
                b = e["available_bikes"]
                if b >= qtd:
                    custo = risco(e, b - qtd) - risco(e, b)
                    origens.append((custo, e["station_id"]))
                if e["available_docks"] >= qtd:
                    beneficio = risco(e, b) - risco(e, b + qtd)
                    destinos.append((beneficio, e["station_id"]))
            if not origens or not destinos:
                continue
            # Mantem duas opcoes: a melhor pode apontar para a mesma estacao.
            origens.sort()
            destinos.sort(reverse=True)
            for custo, origem_id in origens[:2]:
                for beneficio, destino_id in destinos[:2]:
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
    print("P3 experimental; use --preparar e --passo.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
