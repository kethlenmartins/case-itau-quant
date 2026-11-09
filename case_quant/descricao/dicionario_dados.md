# Dicionário de Dados

Este documento descreve todos os arquivos de dados fornecidos para o desafio. Leia com atenção antes de iniciar.

---

## Visão Geral do Sistema

O sistema de bicicletas compartilhadas funciona da seguinte forma:

1. **Estações** são pontos físicos espalhados pela cidade onde ficam as bicicletas.
2. **Usuários** retiram bicicletas de uma estação e devolvem em outra (ou na mesma).
3. Cada estação tem uma **capacidade fixa** de vagas (docks) onde as bicicletas ficam estacionadas.
4. Uma vaga pode estar ocupada (com bicicleta) ou livre (disponível para devolução).
5. A **equipe de operações** redistribui bicicletas entre estações usando veículos, para evitar que estações fiquem vazias ou lotadas.

**Importante:** Os dados de viagens (`viagens.csv`) registram apenas as viagens dos **usuários**. As redistribuições feitas pela equipe de operações **não estão registradas** nos dados.

---

## estacoes.csv

Cadastro das 80 estações de bicicletas compartilhadas na cidade de São Paulo.

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `station_id` | string | Identificador único da estação. Formato: "ST001", "ST002", etc. |
| `name` | string | Nome da estação, geralmente baseado no bairro ou ponto de referência próximo. |
| `address` | string | Endereço aproximado da estação. |
| `neighborhood` | string | Bairro onde a estação está localizada. |
| `zone` | string | Zona da cidade: Centro, Zona Sul, Zona Oeste, Zona Norte ou Zona Leste. |
| `latitude` | float | Coordenada geográfica (latitude). |
| `longitude` | float | Coordenada geográfica (longitude). |
| `capacity` | int | **Número total de vagas (docks)** da estação. Varia de 12 a 30 dependendo do tipo. |
| `installation_date` | date | Data em que a estação foi instalada e começou a operar. |
| `station_type` | string | Tipo da estação (ver explicação abaixo). |

### Tipos de Estação (`station_type`)

| Tipo | Capacidade | Características |
|------|-----------|-----------------|
| `standard` | 15–24 vagas | Estação padrão em áreas residenciais e comerciais. ~60% da rede. |
| `premium` | 20–30 vagas | Alta capacidade, em pontos de grande movimento (metrô, shoppings, centros empresariais). ~25% da rede. |
| `express` | 12–18 vagas | Compacta, em locais com restrição de espaço. ~15% da rede. |

---

## historico_status.csv

Série temporal do estado de cada estação, registrado automaticamente pelo sistema **a cada 15 minutos**.

Este é o arquivo mais volumoso (~707 mil registros) e representa a "fotografia" da rede ao longo do tempo.

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `timestamp` | datetime | Data e hora do registro. Formato: "2024-07-01 08:15:00". |
| `station_id` | string | Identificador da estação. |
| `available_bikes` | int | **Número de bicicletas disponíveis para retirada** naquele momento. |
| `available_docks` | int | **Número de vagas livres para devolução** naquele momento. |
| `status` | string | Status operacional da estação (ver abaixo). |

### Status da Estação

| Status | Significado |
|--------|-------------|
| `active` | Estação funcionando normalmente. |
| `inactive` | Estação temporariamente fora de operação (ex: problema elétrico, vandalismo). |
| `maintenance` | Estação em manutenção programada. |

### Relação entre bikes, docks e capacidade

Em todas as leituras: `available_bikes + available_docks = capacity`

---

## viagens.csv

Histórico de **viagens realizadas pelos usuários** do sistema. Cada registro representa uma pessoa que retirou uma bicicleta de uma estação e devolveu em outra (ou na mesma).

**Atenção:** Este arquivo **NÃO inclui** as redistribuições feitas pela equipe de operações.

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `trip_id` | string | Identificador único da viagem. Formato: "TR0000001". |
| `start_time` | datetime | Data e hora em que o usuário **retirou** a bicicleta. |
| `end_time` | datetime | Data e hora em que o usuário **devolveu** a bicicleta. |
| `start_station_id` | string | Estação onde a viagem **começou** (bicicleta foi retirada). |
| `end_station_id` | string | Estação onde a viagem **terminou** (bicicleta foi devolvida). |
| `duration_minutes` | float | Duração da viagem em minutos. |
| `user_type` | string | `subscriber` (plano mensal/anual, ~75%) ou `casual` (avulso, ~25%). |

### Como as viagens afetam as estações

Cada viagem:
- **Remove 1 bicicleta** da estação de origem (`start_station_id`)
- **Adiciona 1 bicicleta** na estação de destino (`end_station_id`)

Se muitas viagens saem de uma estação e poucas chegam, ela tende a **esvaziar**. O inverso causa **lotação**.

---

## calendario.csv

Informações de calendário. **Cobre julho a novembro de 2024**, estendendo-se além do período dos dados históricos.

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `date` | date | Data no formato "2024-07-01". |
| `day_of_week` | int | Dia da semana: 0=Segunda, ..., 6=Domingo. |
| `day_name` | string | Nome do dia da semana em português. |
| `is_weekend` | bool | `True` se for sábado ou domingo. |
| `is_holiday` | bool | `True` se for feriado (nacional, estadual ou municipal). |
| `holiday_name` | string | Nome do feriado, se aplicável. |
| `school_vacation` | bool | `True` se for período de férias escolares (julho). |
| `special_event` | string | Evento especial na cidade que pode afetar a demanda. Vazio na maioria dos dias. **Quando há mais de um evento no mesmo dia, os nomes vêm unidos por `" + "`.** |

### Por que isso importa?

Feriados e eventos deslocam a demanda, e antecipá-los é parte da priorização.

Em tempo de execução, o dia corrente chega pronto no campo `calendario` da entrada de cada chamada `--passo`, incluindo `special_event`. **Ler de lá é mais confiável que cruzar este arquivo por data** — o campo da entrada é sempre a informação oficial do dia que está sendo operado.

---

## clima.csv

Condições climáticas históricas para São Paulo, registradas **a cada hora** (período Jul–Set/2024).

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `timestamp` | datetime | Data e hora do registro. |
| `temperature_c` | float | Temperatura do ar em graus Celsius. |
| `feels_like_c` | float | Sensação térmica em graus Celsius. |
| `humidity_pct` | float | Umidade relativa do ar em percentual (0–100). |
| `precipitation_mm` | float | Precipitação acumulada na última hora, em milímetros. |
| `wind_speed_kmh` | float | Velocidade do vento em km/h. |
| `weather_condition` | string | `clear`, `cloudy`, `rain` ou `storm`. |
| `uv_index` | int | Índice de radiação ultravioleta (0–11+). |

**Impacto do clima na demanda:**
- `rain`: reduz drasticamente o uso (cerca de 60% menos viagens)
- `storm`: reduz ainda mais (cerca de 80% menos viagens)
- Temperaturas muito baixas (<15°C) ou muito altas (>32°C) também reduzem o uso
- Temperatura agradável (20–28°C) com céu limpo aumenta o uso em torno de 6%

---

## snapshot_atual.csv

"Fotografia" do estado da rede no momento da extração dos dados: **30 de setembro de 2024, às 14:30**.

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `station_id` | string | Identificador da estação. |
| `name` | string | Nome da estação. |
| `neighborhood` | string | Bairro. |
| `zone` | string | Zona da cidade. |
| `capacity` | int | Capacidade total de vagas. |
| `available_bikes` | int | Bicicletas disponíveis agora. |
| `available_docks` | int | Vagas livres agora. |
| `status` | string | Status operacional atual. |
| `last_update` | datetime | Momento desta leitura (2024-09-30 14:30:00 para todos). |
| `bikes_pct` | float | Percentual de ocupação: `(available_bikes / capacity) * 100`. |

### Interpretação do `bikes_pct`

| Faixa | Situação | Risco |
|-------|----------|-------|
| 0–10% | Quase vazia | **Alto risco de escassez** |
| 10–30% | Baixa ocupação | Risco moderado de escassez |
| 30–70% | Ocupação saudável | Situação ideal |
| 70–90% | Alta ocupação | Risco moderado de lotação |
| 90–100% | Quase cheia | **Alto risco de lotação** |

---

## Período dos Dados

| Arquivo | Período | Granularidade |
|---------|---------|---------------|
| `estacoes.csv` | Cadastro atual | — |
| `historico_status.csv` | 01/jul/2024 a 30/set/2024 | A cada 15 minutos |
| `viagens.csv` | 01/jul/2024 a 30/set/2024 | Por viagem |
| `calendario.csv` | 01/jul/2024 a **30/nov/2024** | Diário |
| `clima.csv` | 01/jul/2024 a 30/set/2024 | Horário |
| `snapshot_atual.csv` | 30/set/2024 14:30 | Instantâneo |

---

## Arquivos de Simulação

Estes arquivos cobrem outubro/2024 e alimentam a operação simulada hora a hora (`--passo`). Use-os para desenvolver e testar a sua solução localmente.

| Arquivo | Formato | Período | Registros |
|---------|---------|---------|-----------|
| `intencoes_simulacao.csv` | idêntico a `viagens.csv` (ids com prefixo `SIM`) | 01/out a 31/out | ~57k |
| `estado_inicial_simulacao.csv` | `station_id`, `available_bikes` | 01/out 00:00 | 80 |
| `status_simulacao.csv` | `timestamp`, `station_id`, `status` | 01/out a 31/out, de hora em hora | 59.520 |
| `clima_simulacao.csv` | idêntico a `clima.csv` | 01/out a 31/out | 744 |
| `calendario_simulacao.csv` | idêntico a `calendario.csv` | 01/out a 31/out | 31 |

### O que é uma intenção

Cada linha de `intencoes_simulacao.csv` é uma pessoa que **tentou** retirar uma bicicleta: a estação de origem, o destino pretendido e o horário. O arquivo não diz se a viagem aconteceu; isso depende do estoque, que por sua vez depende das suas movimentações. `end_station_id` é o destino pretendido, sem redirecionamento, e `end_time` é o fim previsto.

Na simulação, as retiradas só começam entre **05:00 e 21:59**. O histórico de Jul–Set (`viagens.csv`) tem viagens noturnas; em outubro o sistema não aceita retiradas entre 22:00 e 05:00 (devoluções de viagens iniciadas antes podem cair depois das 22:00).

### Como o avaliador usa esses arquivos

| Arquivo | Papel na simulação |
|---------|--------------------|
| `estacoes.csv` | `capacity`; `latitude`/`longitude` para redirecionar devoluções; `name`/`zone` repassados à solução |
| `estado_inicial_simulacao.csv` | Estoque de cada estação em 01/out 00:00 |
| `status_simulacao.csv` | `status` operacional de cada hora, 24h por dia (paradas e manutenções são exógenas, iguais para todas as soluções) |
| `intencoes_simulacao.csv` | A demanda: cada intenção é seguida em ordem cronológica (retirada no `start_time`, devolução no `end_time`) |
| `clima_simulacao.csv` | Preenche o campo `clima` da entrada de cada chamada |
| `calendario_simulacao.csv` | Preenche o campo `calendario` da entrada de cada chamada |

O estoque de bicicletas evolui a partir do estado inicial, das suas movimentações e da demanda. Ou seja, suas decisões têm consequência acumulada. O `status` de uma hora vale para a hora inteira: para retiradas, devoluções e para validar as movimentações feitas às `hh:00`.

### O campo `historico` de cada chamada

Cada chamada `--passo` recebe, em `historico`, as últimas 8 leituras de 15 minutos (2h) de cada estação, com `timestamp`, `station_id`, `available_bikes` e `available_docks`. É uma lista única, ordenada por `timestamp` e depois por `station_id`.

- A leitura mais recente é a de `hh:00`, gravada **antes** das movimentações daquela hora. Na chamada das 08:00, as leituras vão de 06:15 a 08:00.
- As leituras continuam à noite. Na chamada das 05:00, cobrem 03:15 a 05:00. Na primeira chamada (01/out 05:00), todas repetem o `estado_inicial_simulacao.csv`, porque não há viagens antes das 05:00.
- As leituras vêm da rede simulada da **sua** solução e refletem as suas movimentações anteriores. Não são linhas de `historico_status.csv`.

**Regras por viagem.** Na retirada, se a origem não está `active` ou não tem bicicleta, é uma `falha_retirada` e a viagem termina. Na devolução, se o destino não está `active` ou não tem vaga, é uma `falha_devolucao` e a bicicleta vai para a estação `active` mais próxima (distância em linha reta) com vaga naquele instante; se não houver nenhuma, ela sai do sistema. Cada intenção gera no máximo uma falha.

### Saídas do baseline

Dois arquivos de `dados/` são **saídas do avaliador** rodando uma solução que nunca movimenta nada (o baseline) em outubro. Mostram o que acontece sem intervenção.

| Arquivo | Formato | Registros |
|---------|---------|-----------|
| `viagens_realizadas_baseline.csv` | colunas de `intencoes_simulacao.csv` + `end_station_real` + `resultado` | ~57k (uma por intenção) |
| `historico_status_baseline.csv` | idêntico a `historico_status.csv` | ~240k |

- `resultado`: `realizada`, `falha_retirada` ou `falha_devolucao`.
- `end_station_real`: igual a `end_station_id` em `realizada`; a estação do redirecionamento em `falha_devolucao`; vazio em `falha_retirada` ou quando a bicicleta sai do sistema.
- `historico_status_baseline.csv` tem uma leitura a cada 15 minutos, de 01/out 00:00 até 01/nov 04:45. A cauda depois de 31/out vem das devoluções pendentes que o avaliador ainda processa depois da última hora de decisão.

Com `--saida <pasta>`, o avaliador grava esses mesmos dois arquivos para a sua solução (`viagens_realizadas_<nome>.csv` e `historico_status_<nome>.csv`) e mais `movimentacoes_<nome>.csv` (`timestamp` da decisão, `origem`, `destino`, `quantidade` efetivamente movida, uma linha por movimentação aplicada). Movimentações ignoradas, ou recortadas para zero, não aparecem nesse arquivo.

---

## Resumo: O que cada arquivo responde?

| Pergunta | Arquivo(s) |
|----------|------------|
| Onde ficam as estações? | `estacoes.csv` |
| Qual a capacidade de cada estação? | `estacoes.csv` |
| Como estava a rede em um momento específico? | `historico_status.csv` |
| Quantas bicicletas há agora em cada estação? | `snapshot_atual.csv` |
| De onde as pessoas saem e para onde vão? | `viagens.csv` |
| Quais horários têm mais demanda? | `viagens.csv` |
| Estava chovendo em determinado momento? | `clima.csv` |
| Era feriado ou evento especial naquele dia? | `calendario.csv` |
| O que vai acontecer em outubro? | `calendario.csv` (feriados/eventos) |
| Quantas pessoas vão tentar viajar em outubro? | `intencoes_simulacao.csv` |
| O que acontece em outubro se ninguém mexer nas bicicletas? | `viagens_realizadas_baseline.csv`, `historico_status_baseline.csv` |
