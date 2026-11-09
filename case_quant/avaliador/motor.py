#!/usr/bin/env python3
"""
Motor de avaliacao do Case Quant.

Roda o loop de simulacao hora a hora, aciona cada solucao via
`python main.py --passo` (JSON no stdin, JSON no stdout) e mantem o
estado da rede de cada participante de forma independente.

Pontos importantes do modelo:

  - O estoque de bicicletas de cada participante evolui SOZINHO: estado
    inicial + movimentacoes da propria solucao + intencoes de viagem.

  - O status operacional (active/inactive/maintenance) vem de
    status_simulacao.csv, por hora cheia: paradas de estacao sao exogenas
    e iguais para todos.

  - Cada intencao vira dois eventos em ordem cronologica (empate: retirada
    antes de devolucao, depois a ordem do arquivo):
      retirada no start_time: falha se a origem nao esta active ou esta
        vazia (falha_retirada, sem devolucao);
      devolucao no end_time: falha se o destino nao esta active ou esta
        cheio (falha_devolucao); a bicicleta vai para a estacao active com
        vaga mais proxima ou, se nao houver nenhuma, sai do sistema.

  - Leituras do estoque a cada 15 minutos, 24h por dia; a leitura hh:00 e
    feita antes das movimentacoes daquela hora.

  - Score = intencoes nao atendidas (cada pessoa gera no maximo uma falha).
    Menor e melhor.
"""

import csv
import heapq
import json
import math
import os
import subprocess
import sys
from datetime import datetime, timedelta

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIR_DADOS = os.path.join(RAIZ, "dados")


def resolver_dir(dados=None):
    """
    Pasta de onde o cenario e lido. Por padrao, dados/.
    Um caminho explicito (relativo a raiz do projeto ou absoluto) permite
    rodar o mesmo avaliador sobre outro conjunto de simulacao.
    """
    if not dados:
        return DIR_DADOS
    if os.path.isabs(dados):
        return dados
    return os.path.join(RAIZ, dados)


def arquivo_cenario(base, dados=None):
    """Caminho de um arquivo de simulacao (ex: intencoes)."""
    return os.path.join(resolver_dir(dados), "%s_simulacao.csv" % base)


HORA_INICIO_OP = 5  # equipe opera das 05:00
HORA_FIM_OP = 22  # ... a ultima chamada e as 21:00
MAX_MOV_HORA = 3  # restricao do enunciado
COLUNAS_INTENCOES = ["trip_id", "start_time", "end_time", "start_station_id",
                     "end_station_id", "duration_minutes", "user_type"]
JANELA_HISTORICO = 8  # leituras de 15 min enviadas como contexto (2h)
TIMEOUT_PASSO = 30  # segundos por chamada --passo
TIMEOUT_PREPARAR = 300  # segundos para o passo opcional --preparar


# ----------------------------------------------------------------------------
# Carregamento
# ----------------------------------------------------------------------------


def carregar_estacoes(dados=None):
    """estacoes.csv da pasta do cenario; se nao existir la, o de dados/."""
    caminho = os.path.join(resolver_dir(dados), "estacoes.csv")
    if not os.path.isfile(caminho):
        caminho = os.path.join(DIR_DADOS, "estacoes.csv")
    estacoes = {}
    with open(caminho, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            estacoes[row["station_id"]] = {
                "station_id": row["station_id"],
                "name": row["name"],
                "zone": row["zone"],
                "capacity": int(row["capacity"]),
                "latitude": float(row["latitude"]),
                "longitude": float(row["longitude"]),
            }
    return estacoes


def carregar_estado_inicial(dados=None):
    """{sid: bikes} em 01/out 00:00."""
    with open(arquivo_cenario("estado_inicial", dados), encoding="utf-8") as f:
        return {row["station_id"]: int(row["available_bikes"]) for row in csv.DictReader(f)}


def carregar_status_horario(dados=None):
    """
    Retorna:
      status_por_hora: {(sid, ts_hora): status}
      horas: lista ordenada de timestamps de hora cheia
    """
    status_por_hora = {}
    with open(arquivo_cenario("status", dados), encoding="utf-8") as f:
        for row in csv.DictReader(f):
            status_por_hora[(row["station_id"], row["timestamp"])] = row["status"]
    return status_por_hora, sorted({ts for _, ts in status_por_hora})


def carregar_intencoes(dados=None, ate=None):
    """Intencoes de viagem (strings do CSV), com start_time ate o fim de `ate`."""
    with open(arquivo_cenario("intencoes", dados), encoding="utf-8") as f:
        intencoes = [r for r in csv.DictReader(f) if not ate or r["start_time"][:10] <= ate]
    intencoes.sort(key=lambda r: (r["start_time"], r["trip_id"]))
    return intencoes


def haversine(a, b):
    """Distancia em km entre duas estacoes (dicts com latitude/longitude)."""
    la1, lo1, la2, lo2 = map(
        math.radians, (a["latitude"], a["longitude"], b["latitude"], b["longitude"])
    )
    h = math.sin((la2 - la1) / 2) ** 2 + math.cos(la1) * math.cos(la2) * math.sin((lo2 - lo1) / 2) ** 2
    return 2 * 6371.0 * math.asin(math.sqrt(h))


def carregar_clima(dados=None):
    caminho = arquivo_cenario("clima", dados)
    clima = {}
    with open(caminho, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            clima[row["timestamp"]] = {
                "temperature_c": float(row["temperature_c"]),
                "feels_like_c": float(row["feels_like_c"]),
                "humidity_pct": float(row["humidity_pct"]),
                "precipitation_mm": float(row["precipitation_mm"]),
                "wind_speed_kmh": float(row["wind_speed_kmh"]),
                "weather_condition": row["weather_condition"],
                "uv_index": int(row["uv_index"]),
            }
    return clima


def carregar_calendario(dados=None):
    caminho = arquivo_cenario("calendario", dados)
    if not os.path.isfile(caminho):
        caminho = os.path.join(DIR_DADOS, "calendario.csv")
    cal = {}
    with open(caminho, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            cal[row["date"]] = {
                "date": row["date"],
                "day_of_week": int(row["day_of_week"]),
                "day_name": row["day_name"],
                "is_weekend": row["is_weekend"] == "True",
                "is_holiday": row["is_holiday"] == "True",
                "holiday_name": row["holiday_name"],
                "special_event": row["special_event"],
            }
    return cal


class Cenario:
    """Dados de um conjunto de simulacao, compartilhados por todos os participantes."""

    def __init__(self, dados=None, ate=None):
        self.dados = dados or "dados"
        self.estacoes = carregar_estacoes(dados)
        self.ids = sorted(self.estacoes)
        self.estado_inicial = carregar_estado_inicial(dados)
        self.status_por_hora, todas_horas = carregar_status_horario(dados)
        for sid in self.ids:
            assert 0 <= self.estado_inicial[sid] <= self.estacoes[sid]["capacity"], \
                "estado inicial fora da capacidade: " + sid
        self.intencoes = carregar_intencoes(dados, ate)
        self.clima = carregar_clima(dados)
        self.calendario = carregar_calendario(dados)

        # Apenas as horas operacionais entram no loop de decisao
        self.horas = [
            h for h in todas_horas
            if HORA_INICIO_OP <= int(h[11:13]) < HORA_FIM_OP and (not ate or h[:10] <= ate)
        ]

        # Demais estacoes por distancia crescente (redirecionamento de devolucoes)
        self.vizinhos = {
            s: sorted((o for o in self.ids if o != s),
                      key=lambda o: (haversine(self.estacoes[s], self.estacoes[o]), o))
            for s in self.ids
        }

    def status_em(self, sid, ts):
        """Status da hora cheia de ts; active se ausente."""
        return self.status_por_hora.get((sid, ts[:13] + ":00:00"), "active")

    def resumo(self):
        d0 = self.horas[0][:10] if self.horas else "?"
        d1 = self.horas[-1][:10] if self.horas else "?"
        return "%s a %s  |  %d horas de decisao  |  %d estacoes" % (
            d0,
            d1,
            len(self.horas),
            len(self.ids),
        )


# ----------------------------------------------------------------------------
# Participante
# ----------------------------------------------------------------------------


class Participante:
    """Uma solucao competindo, com seu proprio estado da rede."""

    def __init__(self, nome, pasta, cenario):
        self.nome = nome
        self.pasta = pasta
        self.main_py = os.path.join(pasta, "main.py")
        self.cenario = cenario

        self.bikes = dict(cenario.estado_inicial)
        self.status = {sid: "active" for sid in cenario.ids}
        self.janela = {sid: [] for sid in cenario.ids}
        self.leituras = []  # (ts, sid, bikes, docks, status)

        # Fila de eventos: ponteiro sobre as intencoes + heap de devolucoes
        self.proxima = 0
        self.devolucoes = []  # (end_time, 1, ordem, destino)
        self.resultados = [None] * len(cenario.intencoes)  # (end_station_real, resultado)
        self.perdidas = 0

        # Nenhum evento acontece antes da primeira hora de decisao (retiradas
        # so a partir das 05:00): leituras de 00:00 ate a ultima antes dela
        if cenario.horas:
            q = datetime.strptime(cenario.horas[0][:10], "%Y-%m-%d")
            while q.strftime("%Y-%m-%d %H:%M:%S") < cenario.horas[0]:
                self.registrar_leitura(q.strftime("%Y-%m-%d %H:%M:%S"))
                q += timedelta(minutes=15)

        self.score = 0
        self.movimentacoes = 0
        self.bikes_movidas = 0
        self.movimentacoes_aplicadas = []  # (ts_hora, origem, destino, quantidade)
        self.erros = 0
        self.ultimo_erro = None
        self.tempo_total = 0.0
        self.historico_score = []

    def valido(self):
        return os.path.isfile(self.main_py)

    # -- protocolo ----------------------------------------------------------

    def preparar(self):
        """Chama o passo opcional --preparar (construcao de cache/modelo)."""
        try:
            r = subprocess.run(
                [sys.executable, "main.py", "--preparar"],
                capture_output=True,
                text=True,
                timeout=TIMEOUT_PREPARAR,
                cwd=self.pasta,
            )
            return r.returncode == 0
        except Exception:
            return False

    def montar_entrada(self, ts_hora):
        cen = self.cenario
        data = ts_hora[:10]

        estacoes = []
        for sid in cen.ids:
            info = cen.estacoes[sid]
            bk = self.bikes[sid]
            estacoes.append(
                {
                    "station_id": sid,
                    "name": info["name"],
                    "zone": info["zone"],
                    "capacity": info["capacity"],
                    "available_bikes": bk,
                    "available_docks": info["capacity"] - bk,
                    "status": self.status[sid],
                }
            )

        historico = []
        for sid in cen.ids:
            for ts, bk, dk in self.janela[sid]:
                historico.append(
                    {
                        "timestamp": ts,
                        "station_id": sid,
                        "available_bikes": bk,
                        "available_docks": dk,
                    }
                )
        historico.sort(key=lambda x: (x["timestamp"], x["station_id"]))

        return {
            "timestamp": ts_hora,
            "estacoes": estacoes,
            "historico": historico,
            "clima": cen.clima.get(ts_hora, {}),
            "calendario": cen.calendario.get(data, {}),
        }

    def chamar(self, ts_hora):
        """Aciona a solucao. Retorna lista de movimentacoes (ja truncada)."""
        import time

        entrada = self.montar_entrada(ts_hora)
        t0 = time.time()
        try:
            r = subprocess.run(
                [sys.executable, "main.py", "--passo"],
                input=json.dumps(entrada),
                capture_output=True,
                text=True,
                timeout=TIMEOUT_PASSO,
                cwd=self.pasta,
            )
            self.tempo_total += time.time() - t0

            if r.returncode != 0:
                self.erros += 1
                self.ultimo_erro = "exit %d: %s" % (
                    r.returncode,
                    r.stderr.strip()[:120],
                )
                return []

            saida = json.loads(r.stdout.strip() or "{}")
            movs = saida.get("movimentacoes", [])
            if not isinstance(movs, list):
                self.erros += 1
                self.ultimo_erro = "campo 'movimentacoes' nao e lista"
                return []
            return movs[:MAX_MOV_HORA]

        except subprocess.TimeoutExpired:
            self.tempo_total += time.time() - t0
            self.erros += 1
            self.ultimo_erro = "timeout (%ds)" % TIMEOUT_PASSO
            return []
        except json.JSONDecodeError as e:
            self.tempo_total += time.time() - t0
            self.erros += 1
            self.ultimo_erro = "JSON invalido: %s" % str(e)[:80]
            return []
        except Exception as e:
            self.tempo_total += time.time() - t0
            self.erros += 1
            self.ultimo_erro = str(e)[:120]
            return []

    # -- evolucao do estado -------------------------------------------------

    def sincronizar_status(self, ts_hora):
        """Status operacional e exogeno: vem do cenario, igual para todos."""
        for sid in self.cenario.ids:
            st = self.cenario.status_por_hora.get((sid, ts_hora))
            if st:
                self.status[sid] = st

    def registrar_leitura(self, ts):
        """Leitura do estoque no instante ts. Idempotente para o mesmo ts."""
        if self.leituras and self.leituras[-1][0] == ts:
            return
        for sid in self.cenario.ids:
            cap = self.cenario.estacoes[sid]["capacity"]
            bk = self.bikes[sid]
            self.leituras.append((ts, sid, bk, cap - bk, self.cenario.status_em(sid, ts)))
            j = self.janela[sid]
            j.append((ts, bk, cap - bk))
            if len(j) > JANELA_HISTORICO:
                j.pop(0)

    def aplicar_movimentacoes(self, movs, ts_hora=None):
        """Aplica movimentacoes validas. Invalidas sao silenciosamente ignoradas.

        ts_hora e o instante da decisao, so para o registro gravado em --saida."""
        cen = self.cenario
        aplicadas = 0
        for mov in movs:
            if not isinstance(mov, dict):
                continue
            origem = mov.get("origem")
            destino = mov.get("destino")
            try:
                qtd = int(mov.get("quantidade", 0))
            except (TypeError, ValueError):
                continue

            if origem not in self.bikes or destino not in self.bikes:
                continue
            if origem == destino or qtd <= 0:
                continue
            if self.status[origem] != "active" or self.status[destino] != "active":
                continue

            cap_dest = cen.estacoes[destino]["capacity"]
            real = min(qtd, self.bikes[origem], cap_dest - self.bikes[destino])
            if real > 0:
                self.bikes[origem] -= real
                self.bikes[destino] += real
                aplicadas += 1
                self.bikes_movidas += real
                self.movimentacoes_aplicadas.append((ts_hora, origem, destino, real))

        self.movimentacoes += aplicadas
        return aplicadas

    def processar_eventos(self, limite=None):
        """Processa os eventos com instante < limite (todos, se limite e None)."""
        cen = self.cenario
        falhas = 0
        while True:
            ret = None
            if self.proxima < len(cen.intencoes):
                ret = (cen.intencoes[self.proxima]["start_time"], 0, self.proxima)
            dev = self.devolucoes[0] if self.devolucoes else None
            evento = min((e for e in (ret, dev) if e), default=None)
            if evento is None or (limite and evento[0] >= limite):
                return falhas

            ts = evento[0]
            if evento[1] == 0:
                v = cen.intencoes[self.proxima]
                self.proxima += 1
                origem = v["start_station_id"]
                if cen.status_em(origem, ts) != "active" or self.bikes[origem] == 0:
                    self.resultados[evento[2]] = ("", "falha_retirada")
                    falhas += 1
                else:
                    self.bikes[origem] -= 1
                    heapq.heappush(self.devolucoes,
                                   (v["end_time"], 1, evento[2], v["end_station_id"]))
                continue

            heapq.heappop(self.devolucoes)
            ordem, destino = evento[2], evento[3]
            if self.tem_vaga(destino, ts):
                self.bikes[destino] += 1
                self.resultados[ordem] = (destino, "realizada")
                continue
            falhas += 1
            alt = next((s for s in cen.vizinhos[destino] if self.tem_vaga(s, ts)), None)
            if alt is None:
                self.perdidas += 1
                self.resultados[ordem] = ("", "falha_devolucao")
            else:
                self.bikes[alt] += 1
                self.resultados[ordem] = (alt, "falha_devolucao")

    def tem_vaga(self, sid, ts):
        return (self.cenario.status_em(sid, ts) == "active"
                and self.bikes[sid] < self.cenario.estacoes[sid]["capacity"])

    def avancar_hora(self, ts_hora):
        """
        Processa os eventos de [ts_hora, proxima hora de decisao), gravando as
        leituras de 15 min internas. Depois da ultima hora do cenario,
        processa tambem todos os eventos restantes.
        """
        ini = datetime.strptime(ts_hora, "%Y-%m-%d %H:%M:%S")
        if ini.hour + 1 < HORA_FIM_OP:
            fim = ini + timedelta(hours=1)
        else:
            fim = (ini + timedelta(days=1)).replace(hour=HORA_INICIO_OP)

        falhas = 0
        q = ini + timedelta(minutes=15)
        while q < fim:
            ts_q = q.strftime("%Y-%m-%d %H:%M:%S")
            falhas += self.processar_eventos(ts_q)
            self.registrar_leitura(ts_q)
            q += timedelta(minutes=15)
        ultima = ts_hora == self.cenario.horas[-1]
        falhas += self.processar_eventos(None if ultima else fim.strftime("%Y-%m-%d %H:%M:%S"))

        self.score += falhas
        self.historico_score.append(self.score)
        return falhas

    def gravar_saidas(self, pasta, rotulo):
        """Grava viagens_realizadas_, historico_status_ e movimentacoes_<rotulo>.csv."""
        via = os.path.join(pasta, "viagens_realizadas_%s.csv" % rotulo)
        hist = os.path.join(pasta, "historico_status_%s.csv" % rotulo)
        movs = os.path.join(pasta, "movimentacoes_%s.csv" % rotulo)
        with open(via, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f, lineterminator="\n")
            w.writerow(COLUNAS_INTENCOES + ["end_station_real", "resultado"])
            for it, (fim, res) in zip(self.cenario.intencoes, self.resultados):
                w.writerow([it[c] for c in COLUNAS_INTENCOES] + [fim, res])
        with open(hist, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f, lineterminator="\n")
            w.writerow(["timestamp", "station_id", "available_bikes", "available_docks", "status"])
            w.writerows(sorted(self.leituras, key=lambda l: (l[0], l[1])))
        with open(movs, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f, lineterminator="\n")
            w.writerow(["timestamp", "origem", "destino", "quantidade"])
            w.writerows(self.movimentacoes_aplicadas)
        return via, hist, movs

    def verificar(self):
        """Checagens de conservacao e coerencia, ao fim da execucao."""
        cen = self.cenario
        em_transito = len(self.devolucoes)
        assert sum(self.bikes.values()) + em_transito + self.perdidas == sum(
            cen.estado_inicial.values()), "bicicletas nao conservadas"
        for sid in cen.ids:
            assert 0 <= self.bikes[sid] <= cen.estacoes[sid]["capacity"], sid
        assert len(self.resultados) == len(cen.intencoes)
        assert None not in self.resultados, "intencao sem resultado"
        assert self.score == sum(1 for _, r in self.resultados if r != "realizada")


class Baseline(Participante):
    """Referencia: nunca movimenta nada. Nao executa subprocesso."""

    def __init__(self, cenario):
        super().__init__("(baseline imovel)", "", cenario)

    def valido(self):
        return True

    def preparar(self):
        return True

    def chamar(self, ts_hora):
        return []


# ----------------------------------------------------------------------------
# Descoberta de solucoes
# ----------------------------------------------------------------------------


def descobrir_solucoes(caminho):
    """
    Se caminho contem main.py, retorna [caminho].
    Senao, retorna as subpastas que contem main.py, em ordem alfabetica.
    """
    caminho = os.path.abspath(caminho)
    if os.path.isfile(os.path.join(caminho, "main.py")):
        return [caminho]
    achados = []
    for nome in sorted(os.listdir(caminho)):
        sub = os.path.join(caminho, nome)
        if os.path.isdir(sub) and os.path.isfile(os.path.join(sub, "main.py")):
            achados.append(sub)
    return achados
