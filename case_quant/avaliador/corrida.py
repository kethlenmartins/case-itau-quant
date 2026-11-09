#!/usr/bin/env python3
"""
Corrida de solucoes do Case Quant.

Roda varias solucoes em paralelo sobre o mesmo cenario de simulacao, hora a
hora, e mostra um placar ao vivo no terminal.

Uso:
    python avaliador/corrida.py minhas_solucoes
    python avaliador/corrida.py minhas_solucoes --ate 2024-10-07
    python avaliador/corrida.py minhas_solucoes --sem-animacao

A "distancia percorrida" de cada solucao e o numero de viagens que ela
salvou em relacao ao baseline imovel. Quem salvou mais, lidera.
"""

import argparse
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from motor import (Baseline, Cenario, Participante, arquivo_cenario,  # noqa: E402
                   descobrir_solucoes)

LARGURA_PISTA = 34
CORES = ["\033[96m", "\033[92m", "\033[93m", "\033[95m", "\033[91m",
         "\033[94m", "\033[36m", "\033[32m"]
RESET = "\033[0m"
NEGRITO = "\033[1m"
CINZA = "\033[90m"

MEDALHAS = ["1o", "2o", "3o"]


def preparar_terminal():
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass


def suporta_unicode():
    enc = (getattr(sys.stdout, "encoding", "") or "").lower()
    return "utf" in enc


# ----------------------------------------------------------------------------
# Renderizacao
# ----------------------------------------------------------------------------

class Placar:
    def __init__(self, participantes, baseline, cenario, usar_cor=True, animar=True):
        self.participantes = participantes
        self.baseline = baseline
        self.cenario = cenario
        self.usar_cor = usar_cor and sys.stdout.isatty()
        self.animar = animar and sys.stdout.isatty()
        self.linhas_anteriores = 0
        self.ultimo_desenho = 0.0
        self.posicoes_anteriores = {}

        if suporta_unicode():
            self.cheio, self.vazio = "█", "░"
            self.seta_cima, self.seta_baixo = "▲", "▼"
        else:
            self.cheio, self.vazio = "#", "-"
            self.seta_cima, self.seta_baixo = "^", "v"

    def cor(self, i):
        return CORES[i % len(CORES)] if self.usar_cor else ""

    def fim(self):
        return RESET if self.usar_cor else ""

    def forte(self):
        return NEGRITO if self.usar_cor else ""

    def fraco(self):
        return CINZA if self.usar_cor else ""

    def ordenar(self):
        """Ordena por viagens salvas (desc), empate pelo menor score."""
        def chave(p):
            salvas = self.baseline.score - p.score
            return (-salvas, p.score, p.nome)
        return sorted(self.participantes, key=chave)

    def montar(self, ts_hora, idx_hora, total_horas, encerrado=False):
        cen = self.cenario
        linhas = []
        W = 78

        titulo = "CORRIDA DE SOLUCOES" if not encerrado else "RESULTADO FINAL"
        linhas.append("%s%s%s  %s" % (
            self.forte(), titulo, self.fim(),
            self.fraco() + ("cenario: %s" % cen.dados) + self.fim()))
        linhas.append("=" * W)

        clima = cen.clima.get(ts_hora, {})
        cal = cen.calendario.get(ts_hora[:10], {})
        cond = clima.get("weather_condition", "-")
        temp = clima.get("temperature_c", 0.0)
        mm = clima.get("precipitation_mm", 0.0)
        evento = cal.get("special_event", "") or "-"
        if len(evento) > 46:
            evento = evento[:43] + "..."

        pct = (idx_hora / total_horas * 100) if total_horas else 100.0
        linhas.append(" relogio  %s   hora %d/%d  [%4.1f%%]" % (
            ts_hora, idx_hora, total_horas, pct))
        linhas.append(" clima    %-7s %5.1fC  %4.1fmm      %s" % (cond, temp, mm,
                      ("CHUVA" if cond in ("rain", "storm") else "")))
        linhas.append(" evento   %s" % evento)
        linhas.append("")

        base = self.baseline.score
        ordenados = self.ordenar()
        melhor_salvas = max((base - p.score) for p in ordenados) if ordenados else 0
        escala = max(melhor_salvas, 1)

        linhas.append(" %-3s %-14s %-*s %8s %7s %6s" % (
            "pos", "solucao", LARGURA_PISTA, "viagens salvas vs baseline",
            "salvas", "falhas", "movs"))
        linhas.append(" " + "-" * (W - 2))

        for pos, p in enumerate(ordenados, start=1):
            salvas = base - p.score
            frac = max(0.0, min(1.0, salvas / escala)) if escala else 0.0
            n = int(round(frac * LARGURA_PISTA))
            pista = self.cheio * n + self.vazio * (LARGURA_PISTA - n)

            anterior = self.posicoes_anteriores.get(p.nome)
            if anterior is None or anterior == pos:
                delta = "  "
            elif pos < anterior:
                delta = self.seta_cima + " "
            else:
                delta = self.seta_baixo + " "

            rotulo = MEDALHAS[pos - 1] if pos <= 3 else "%do" % pos
            marca = "!" if p.erros else " "

            linhas.append(" %s%-3s%s %-14s %s%s%s %+8d %7d %6d %s" % (
                self.forte() if pos == 1 else "", rotulo, self.fim(),
                p.nome[:14],
                self.cor(self.participantes.index(p)), pista, self.fim(),
                salvas, p.score, p.movimentacoes, delta + marca))

        linhas.append("")
        linhas.append(" %sbaseline imovel: %d viagens nao atendidas%s" % (
            self.fraco(), base, self.fim()))

        com_erro = [p for p in ordenados if p.erros]
        if com_erro:
            linhas.append("")
            for p in com_erro:
                linhas.append(" %s! %s: %d erro(s) - %s%s" % (
                    self.fraco(), p.nome, p.erros, (p.ultimo_erro or "")[:44], self.fim()))

        self.posicoes_anteriores = {p.nome: i for i, p in enumerate(ordenados, start=1)}
        return linhas

    def desenhar(self, ts_hora, idx_hora, total_horas, forcar=False, encerrado=False):
        agora = time.time()
        if not forcar and self.animar and agora - self.ultimo_desenho < 0.08:
            return
        self.ultimo_desenho = agora

        linhas = self.montar(ts_hora, idx_hora, total_horas, encerrado)

        if self.animar:
            if self.linhas_anteriores:
                sys.stdout.write("\033[%dA" % self.linhas_anteriores)
            for ln in linhas:
                sys.stdout.write("\033[2K" + ln + "\n")
            # limpa sobras de um placar anterior mais alto
            for _ in range(max(0, self.linhas_anteriores - len(linhas))):
                sys.stdout.write("\033[2K\n")
            self.linhas_anteriores = max(len(linhas), self.linhas_anteriores)
            sys.stdout.flush()
        else:
            print("\n".join(linhas))
            print()


# ----------------------------------------------------------------------------
# Loop da corrida
# ----------------------------------------------------------------------------

def correr(pasta, dados=None, ate=None, animar=True, usar_cor=True, workers=None):
    print("carregando cenario de %s/..." % (dados or "dados"))
    cenario = Cenario(dados, ate)
    print("  %s" % cenario.resumo())

    caminhos = descobrir_solucoes(pasta)
    if not caminhos:
        print("Nenhuma solucao encontrada em %s (esperado main.py)" % pasta)
        return 1

    participantes = []
    for c in caminhos:
        p = Participante(os.path.basename(c), c, cenario)
        if p.valido():
            participantes.append(p)
    if not participantes:
        print("Nenhuma solucao valida encontrada.")
        return 1

    print("  %d solucoes: %s" % (len(participantes),
                                 ", ".join(p.nome for p in participantes)))

    horas = cenario.horas
    if ate:
        print("  recorte: ate %s (%d horas)" % (ate, len(horas)))
    if not horas:
        print("Nenhuma hora de decisao no recorte.")
        return 1

    baseline = Baseline(cenario)

    print("\npreparando solucoes (passo opcional --preparar)...")
    n_workers = workers or min(len(participantes), 8)
    with ThreadPoolExecutor(max_workers=n_workers) as ex:
        list(ex.map(lambda p: p.preparar(), participantes))
    print("  ok\n")

    placar = Placar(participantes, baseline, cenario, usar_cor=usar_cor, animar=animar)
    todos = participantes + [baseline]
    t_inicio = time.time()

    with ThreadPoolExecutor(max_workers=n_workers) as ex:
        for idx, ts_hora in enumerate(horas, start=1):
            for p in todos:
                p.sincronizar_status(ts_hora)
                p.registrar_leitura(ts_hora)

            # Todas as solucoes decidem em paralelo, sobre o mesmo instante
            futuros = {p: ex.submit(p.chamar, ts_hora) for p in participantes}
            for p, fut in futuros.items():
                p.aplicar_movimentacoes(fut.result(), ts_hora)

            for p in todos:
                p.avancar_hora(ts_hora)

            placar.desenhar(ts_hora, idx, len(horas))

    placar.desenhar(horas[-1], len(horas), len(horas), forcar=True, encerrado=True)

    decorrido = time.time() - t_inicio
    for p in todos:
        p.verificar()
    print()
    print("tempo de corrida: %.1fs  (%d chamadas a solucoes)" % (
        decorrido, len(horas) * len(participantes)))

    print()
    print("detalhe por solucao:")
    print("  %-16s %8s %8s %8s %7s %8s %9s" % (
        "solucao", "falhas", "salvas", "melhora", "movs", "bikes", "tempo"))
    print("  " + "-" * 70)
    base = baseline.score
    for p in placar.ordenar():
        salvas = base - p.score
        melhora = (salvas / base * 100) if base else 0.0
        print("  %-16s %8d %8d %7.1f%% %7d %8d %8.1fs" % (
            p.nome[:16], p.score, salvas, melhora,
            p.movimentacoes, p.bikes_movidas, p.tempo_total))
    print("  %-16s %8d %8s %8s %7s %8s %9s" % (
        "baseline", base, "-", "-", "0", "0", "-"))

    return 0


def main():
    preparar_terminal()
    ap = argparse.ArgumentParser(description="Corrida de solucoes do Case Quant")
    ap.add_argument("pasta", help="pasta com as solucoes (ou uma solucao)")
    ap.add_argument("--dados", default=None,
                    help="pasta do cenario de simulacao (default: dados)")
    ap.add_argument("--ate", default=None,
                    help="roda apenas ate esta data (YYYY-MM-DD), para testes rapidos")
    ap.add_argument("--sem-animacao", action="store_true",
                    help="imprime placares sequenciais em vez de redesenhar")
    ap.add_argument("--sem-cores", action="store_true")
    ap.add_argument("--workers", type=int, default=None)
    args = ap.parse_args()

    arq = arquivo_cenario("intencoes", args.dados)
    if not os.path.isfile(arq):
        print("Arquivos de simulacao nao encontrados em %s" % os.path.dirname(arq))
        return 1

    return correr(args.pasta, dados=args.dados, ate=args.ate,
                  animar=not args.sem_animacao,
                  usar_cor=not args.sem_cores,
                  workers=args.workers)


if __name__ == "__main__":
    raise SystemExit(main())
