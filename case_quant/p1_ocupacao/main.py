#!/usr/bin/env python3
"""P1 experimental: rebalanceamento por faixas de ocupacao."""
import json
import sys

MAX_MOV = 3


def decidir(dados):
    # Copia mutavel porque as transferencias sao sequenciais no avaliador.
    estado = {e["station_id"]: dict(e) for e in dados["estacoes"] if e["status"] == "active"}
    movimentos = []
    for _ in range(MAX_MOV):
        fontes = [e for e in estado.values() if e["available_bikes"] / e["capacity"] >= 0.80]
        destinos = [e for e in estado.values() if e["available_bikes"] / e["capacity"] <= 0.20]
        if not fontes or not destinos:
            break
        origem = max(fontes, key=lambda e: (e["available_bikes"] / e["capacity"], e["available_bikes"]))
        destino = min(destinos, key=lambda e: (e["available_bikes"] / e["capacity"], e["available_bikes"]))
        if origem["station_id"] == destino["station_id"]:
            break
        # Preserva ao menos 60% na origem e busca 40% no destino.
        pode_ceder = origem["available_bikes"] - int(0.60 * origem["capacity"])
        precisa = int(0.40 * destino["capacity"] + 0.999) - destino["available_bikes"]
        qtd = min(pode_ceder, precisa, destino["available_docks"])
        if qtd <= 0:
            break
        movimentos.append({"origem": origem["station_id"], "destino": destino["station_id"], "quantidade": qtd})
        origem["available_bikes"] -= qtd
        origem["available_docks"] += qtd
        destino["available_bikes"] += qtd
        destino["available_docks"] -= qtd
    return movimentos


def main():
    if "--preparar" in sys.argv:
        return 0
    if "--passo" in sys.argv:
        dados = json.load(sys.stdin)
        try:
            movs = decidir(dados)
        except Exception as erro:
            print(repr(erro), file=sys.stderr)
            movs = []
        print(json.dumps({"movimentacoes": movs}))
        return 0
    print("P1 experimental; use --passo.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
