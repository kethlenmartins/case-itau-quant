#!/usr/bin/env python3
"""
Avaliador de uma solucao isolada do Case Quant.

Roda a solucao hora a hora sobre o cenario de simulacao e compara com o
baseline imovel. Para comparar varias solucoes ao mesmo tempo, use
avaliador/corrida.py.

Uso:
    python avaliador/avaliar.py minha_solucao
    python avaliador/avaliar.py minha_solucao --ate 2024-10-07 --verbose
"""

import argparse
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from motor import Baseline, Cenario, Participante, arquivo_cenario  # noqa: E402


def main():
    ap = argparse.ArgumentParser(description="Avalia uma solucao do Case Quant")
    ap.add_argument("pasta", help="pasta da solucao (deve conter main.py)")
    ap.add_argument("--dados", default=None,
                    help="pasta do cenario de simulacao (default: dados)")
    ap.add_argument("--ate", default=None, help="roda apenas ate esta data (YYYY-MM-DD)")
    ap.add_argument("--verbose", action="store_true", help="mostra cada hora com falha")
    ap.add_argument("--saida", default=None,
                    help="pasta onde gravar viagens realizadas e historico de status")
    args = ap.parse_args()

    arq = arquivo_cenario("intencoes", args.dados)
    if not os.path.isfile(arq):
        print("Arquivos de simulacao nao encontrados em %s" % os.path.dirname(arq))
        return 1

    if not os.path.isfile(os.path.join(args.pasta, "main.py")):
        print("main.py nao encontrado em %s" % args.pasta)
        return 1

    print("carregando cenario de %s/..." % (args.dados or "dados"))
    cenario = Cenario(args.dados, args.ate)
    print("  %s" % cenario.resumo())

    horas = cenario.horas
    if not horas:
        print("Nenhuma hora de decisao no recorte.")
        return 1

    nome = os.path.basename(os.path.abspath(args.pasta))
    sol = Participante(nome, os.path.abspath(args.pasta), cenario)
    base = Baseline(cenario)

    print("\npreparando solucao...")
    sol.preparar()

    print("avaliando %s sobre %d horas...\n" % (nome, len(horas)))
    t0 = time.time()

    for idx, ts in enumerate(horas, start=1):
        for p in (sol, base):
            p.sincronizar_status(ts)
            p.registrar_leitura(ts)

        movs = sol.chamar(ts)
        aplicadas = sol.aplicar_movimentacoes(movs, ts)

        f_sol = sol.avancar_hora(ts)
        base.avancar_hora(ts)

        if args.verbose and (f_sol > 0 or aplicadas > 0):
            print("  %s  movs=%d  falhas=%d  acum=%d" % (ts, aplicadas, f_sol, sol.score))
        elif not args.verbose and idx % 50 == 0:
            print("  %s  %d/%d  score=%d" % (ts, idx, len(horas), sol.score))

    decorrido = time.time() - t0
    sol.verificar()
    base.verificar()
    if args.saida:
        os.makedirs(args.saida, exist_ok=True)
        for p, rotulo in ((sol, nome), (base, "baseline")):
            for arq in p.gravar_saidas(args.saida, rotulo):
                print("gravado %s" % arq)
    salvas = base.score - sol.score
    melhora = (salvas / base.score * 100) if base.score else 0.0

    print()
    print("=" * 60)
    print("RESULTADO: %s" % nome)
    print("=" * 60)
    print("horas avaliadas ........ %6d" % len(horas))
    print("erros .................. %6d%s" % (
        sol.erros, ("  (ultimo: %s)" % sol.ultimo_erro) if sol.erros else ""))
    print("movimentacoes .......... %6d" % sol.movimentacoes)
    print("bicicletas movidas ..... %6d" % sol.bikes_movidas)
    print()
    print("falhas do baseline ..... %6d" % base.score)
    print("falhas da solucao ...... %6d" % sol.score)
    print("viagens salvas ......... %+6d" % salvas)
    print("melhora ................ %+6.1f%%" % melhora)
    print()
    print("tempo .................. %6.1fs  (%.0fms por chamada)" % (
        decorrido, sol.tempo_total / max(1, len(horas)) * 1000))
    print()
    if salvas > 0:
        print("A solucao MELHOROU o baseline.")
    elif salvas == 0:
        print("A solucao empatou com o baseline.")
    else:
        print("A solucao PIOROU o baseline.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
