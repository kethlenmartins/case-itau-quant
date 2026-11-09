#!/usr/bin/env python3
"""P4: beam search conjunto sobre a mesma perda marginal de P3."""
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
LARGURA_BEAM = int(os.environ.get("BEAM_WIDTH", "2"))
TOP_CANDIDATOS = int(os.environ.get("TOP_CANDIDATOS", "5"))
TOP_PONTAS = 5


def copiar_estado(estado):
    return {station_id: dict(e) for station_id, e in estado.items()}


def decidir(dados):
    try:
        with open(p2.ARQ_CACHE, encoding="utf-8") as arq:
            perfis = json.load(arq)["perfis"]
    except (OSError, ValueError, KeyError):
        return []

    momento = dt.datetime.fromisoformat(dados["timestamp"])
    hora, dow = momento.hour, momento.weekday()
    inicial = {e["station_id"]: dict(e) for e in dados["estacoes"] if e["status"] == "active"}

    def risco(e, bikes):
        retiradas, devolucoes = perfis.get(p2.chave(e["station_id"], hora, dow), (0.0, 0.0))
        return p2.perda(bikes, e["capacity"], retiradas, devolucoes)

    def candidatos(estado):
        """Retorna somente os melhores movimentos de ganho positivo deste estado."""
        todos = []
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
            origens.sort()
            destinos.sort(reverse=True)
            for custo, origem_id in origens[:TOP_PONTAS]:
                for beneficio, destino_id in destinos[:TOP_PONTAS]:
                    if origem_id != destino_id and beneficio - custo > 1e-9:
                        todos.append((beneficio - custo, origem_id, destino_id, qtd))
        todos.sort(reverse=True)
        return todos[:TOP_CANDIDATOS]

    # Cada item: (ganho acumulado, estado apos a sequencia, movimentacoes).
    beam = [(0.0, inicial, [])]
    melhor_final = beam[0]
    for _ in range(MAX_MOV):
        expansoes = []
        for ganho_total, estado, movimentos in beam:
            for ganho, origem_id, destino_id, qtd in candidatos(estado):
                proximo = copiar_estado(estado)
                origem, destino = proximo[origem_id], proximo[destino_id]
                origem["available_bikes"] -= qtd
                origem["available_docks"] += qtd
                destino["available_bikes"] += qtd
                destino["available_docks"] -= qtd
                mov = {"origem": origem_id, "destino": destino_id, "quantidade": qtd}
                expansoes.append((ganho_total + ganho, proximo, movimentos + [mov]))
        if not expansoes:
            break
        expansoes.sort(key=lambda item: (item[0], len(item[2])), reverse=True)
        beam = expansoes[:LARGURA_BEAM]
        if beam[0][0] > melhor_final[0]:
            melhor_final = beam[0]
    return melhor_final[2]


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
    print("P4 experimental; use --preparar e --passo.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
