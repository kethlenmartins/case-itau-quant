#!/usr/bin/env python3
"""
Solucao inicial: ponto de partida para o case.

Cumpre o contrato do avaliador (ver descricao/CASE.md, Parte 2), mas nunca
movimenta nada. O score dela e igual ao do baseline. A estrategia fica por
sua conta, na funcao decidir().

Modos:
    python main.py              Parte 1: analise e interface (a implementar)
    python main.py --preparar   chamado uma vez antes da simulacao (5 min)
    python main.py --passo      uma hora de outubro: JSON no stdin -> JSON no stdout (30 s)

O avaliador roda o programa com esta pasta como diretorio de trabalho. Os
dados ficam em ../dados/.
"""

import json
import os
import sys
from collections import defaultdict

PASTA_DADOS = os.path.join("..", "dados")
MAX_MOV = 3


def log(*args):
    """Mensagens de diagnostico vao para o stderr: o stdout e so do JSON."""
    print(*args, file=sys.stderr)


def series_por_estacao(historico):
    """Agrupa a lista unica do historico em {station_id: [leituras em ordem de tempo]}."""
    series = defaultdict(list)
    for leitura in historico:
        series[leitura["station_id"]].append(leitura)
    return series


def decidir(dados):
    """
    Recebe a entrada de uma hora e devolve ate 3 movimentacoes, cada uma no
    formato {"origem": "ST001", "destino": "ST015", "quantidade": 5}.

    Esta versao nunca movimenta nada.
    """
    estacoes = {e["station_id"]: e for e in dados["estacoes"]}
    series = series_por_estacao(dados["historico"])
    log("%s: %d estacoes, %d series" % (dados["timestamp"], len(estacoes), len(series)))
    return []


def limpar(movimentacoes):
    """Garante o formato do contrato: no maximo 3 itens e quantidade inteira positiva."""
    saida = []
    for m in movimentacoes[:MAX_MOV]:
        qtd = int(m["quantidade"])
        if qtd > 0 and m["origem"] != m["destino"]:
            saida.append({"origem": m["origem"], "destino": m["destino"], "quantidade": qtd})
    return saida


def preparar():
    """
    Pre-processamento opcional (perfis, modelos, cache). Leia os dados de
    PASTA_DADOS e grave o resultado nesta pasta, para o --passo so carregar.
    O --passo deve funcionar mesmo que o cache nao exista.
    """
    return 0


def passo():
    dados = json.load(sys.stdin)
    try:
        movimentacoes = limpar(decidir(dados))
    except Exception as erro:  # uma falha na estrategia nao deve derrubar a hora
        log("erro em decidir: %r" % erro)
        movimentacoes = []
    print(json.dumps({"movimentacoes": movimentacoes}))
    return 0


def main():
    if "--preparar" in sys.argv:
        return preparar()
    if "--passo" in sys.argv:
        return passo()
    print("Parte 1: implemente aqui a analise e a interface.")
    print("Parte 2: python main.py --passo < entrada_exemplo.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
