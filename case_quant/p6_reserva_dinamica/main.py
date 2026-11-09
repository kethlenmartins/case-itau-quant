#!/usr/bin/env python3
"""P6: perda marginal com reservas derivadas de demanda prevista e incerteza."""
import datetime as dt
import importlib.util
import json
import math
import os
import sys

CAMINHO_P2 = os.path.join("..", "p2_perda_marginal", "main.py")
spec = importlib.util.spec_from_file_location("p2_base", CAMINHO_P2)
p2 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(p2)

MAX_MOV = 3
TOP_PONTAS = 5


def decidir(dados):
    try:
        with open(p2.ARQ_CACHE, encoding="utf-8") as arq:
            perfis = json.load(arq)["perfis"]
    except (OSError, ValueError, KeyError):
        return []
    momento = dt.datetime.fromisoformat(dados["timestamp"])
    hora, dow = momento.hour, momento.weekday()
    estado = {e["station_id"]: dict(e) for e in dados["estacoes"] if e["status"] == "active"}

    def previsao(e):
        return perfis.get(p2.chave(e["station_id"], hora, dow), (0.0, 0.0))

    def risco(e, bikes):
        retiradas, devolucoes = previsao(e)
        return p2.perda(bikes, e["capacity"], retiradas, devolucoes)

    def limites_dinamicos(e):
        """Intervalo de estoque seguro para a proxima hora.

        A raiz da demanda total e uma aproximacao de desvio padrao Poisson;
        portanto o buffer cresce com a incerteza prevista, sem quantidade fixa.
        """
        retiradas, devolucoes = previsao(e)
        margem = math.sqrt(retiradas + devolucoes)
        minimo = min(e["capacity"], int(math.ceil(retiradas + margem)))
        maximo = max(0, int(math.floor(e["capacity"] - devolucoes - margem)))
        return minimo, maximo

    movimentos = []
    for _ in range(MAX_MOV):
        melhor = None
        # Todas as quantidades candidatas respeitam limites baseados no perfil.
        maior_q = max((e["available_bikes"] for e in estado.values()), default=0)
        for qtd in range(1, maior_q + 1):
            origens = []
            destinos = []
            for e in estado.values():
                bikes = e["available_bikes"]
                minimo, maximo = limites_dinamicos(e)
                if bikes >= qtd and bikes - qtd >= minimo:
                    custo = risco(e, bikes - qtd) - risco(e, bikes)
                    origens.append((custo, e["station_id"]))
                if e["available_docks"] >= qtd and bikes + qtd <= maximo:
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
    print("P6 experimental; use --preparar e --passo.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
