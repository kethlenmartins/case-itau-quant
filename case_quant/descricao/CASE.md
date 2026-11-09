# Case: Sistema de Bicicletas Compartilhadas — São Paulo

## Contexto

Você foi contratado como cientista de dados por uma empresa que opera um sistema de bicicletas compartilhadas em São Paulo. O sistema possui 80 estações distribuídas em 5 zonas da cidade (Centro, Zona Sul, Zona Oeste, Zona Norte e Zona Leste).

O principal desafio operacional é garantir que as estações não fiquem **vazias** (sem bicicletas para retirada) nem **lotadas** (sem vagas para devolução). Quando isso ocorre, o usuário desiste da viagem ou precisa devolver a bicicleta em outra estação — a empresa perde receita e reputação.

A equipe de operações tem veículos para redistribuir bicicletas, mas consegue fazer **no máximo 3 movimentações por hora** (cada uma leva bicicletas de uma estação para outra). Essa restrição é o coração do problema: não basta saber onde está ruim, é preciso escolher quais 3 movimentações valem mais nesta hora.

---

## O que você entrega

Você entrega **dois arquivos**, que juntos cobrem **três partes** do trabalho:

| Parte | O que é | Quem produz | Onde está descrita |
|---|---|---|---|
| **1. Interface** | Uma aplicação web local que responde às 5 perguntas sobre o estado atual da rede, para um operador usar | O modelo de linguagem, a partir do seu `.md` | *Parte 1* |
| **2. Simulação** | O modo `--passo`, que decide as movimentações de cada hora de outubro e gera o score | O modelo de linguagem, a partir do seu `.md` | *Parte 2* |
| **3. Notebook** | A sua análise do problema e a justificativa da estratégia | Você, diretamente | *Notebook de análise* |

Os dois arquivos entregues:

1. **`solucao_[seu_nome].md`** — um arquivo Markdown com instruções para um modelo de linguagem gerar a **solução**. Neste case, **"solução" é o conjunto das partes 1 e 2**: a interface e a simulação, geradas juntas, no mesmo programa (`main.py`) e na mesma pasta. O `.md` precisa descrever as duas.
2. **`analise_[seu_nome].ipynb`** — a **parte 3**. Um Jupyter Notebook com a sua análise do problema. Este arquivo é escrito por você, não pelo modelo, e não tem restrição de bibliotecas.

Falta qualquer uma das três partes e a entrega fica incompleta: o `.md` sem instruções para a interface gera uma solução sem Parte 1; sem o `--passo`, ela fica sem score; sem o notebook, não há como avaliar o seu raciocínio.

**Nome dos arquivos:** `[seu_nome]` deve usar apenas letras minúsculas sem acento, números e `_` (sem espaços). Exemplo: `solucao_maria_silva.md` e `analise_maria_silva.ipynb`.

**Notebook de análise:** deve ser entregue **já executado**: rode todas as células e salve o arquivo antes de enviar, para que os resultados (tabelas, gráficos e textos que cada célula produz) fiquem gravados no `.ipynb` e possam ser vistos sem precisar rodar nada. Se possível, use "Reiniciar o kernel e executar tudo" antes de salvar, para garantir que o notebook funciona de ponta a ponta. Salve-o numa subpasta ao lado de `dados/` (por exemplo, `notebook/`; ver *Estrutura sugerida*) e leia os dados por caminho relativo (por exemplo, `../dados/viagens.csv`), de modo que o avaliador também consiga reexecutá-lo a partir da estrutura do case. Pode usar qualquer biblioteca; liste-as numa célula no início. Nesse arquivo você pode usar os arquivos `*_baseline.csv` e os demais dados de simulação para fundamentar o diagnóstico (a restrição de uso dos dados descrita adiante vale só para a solução gerada pelo `.md`).

### Fluxo de correção

1. Você escreve o `.md` com instruções detalhadas.
2. Os avaliadores usarão o **Claude Sonnet 5.5** para gerar a solução a partir dele. A geração é feita **uma única vez**, em uma conversa nova, com o conteúdo do `.md` como única instrução. Não há correção manual do código gerado nem nova tentativa.
3. A solução gerada é colocada na pasta `solucao/`, executada e avaliada.

**O que o modelo recebe:** apenas o conteúdo do seu `.md`. Ele **não** tem acesso aos arquivos do case: não vê os CSVs, o dicionário de dados, o avaliador nem este enunciado, e não executa código durante a geração. Tudo o que ele precisar saber para escrever a solução (nomes de arquivos, colunas e formatos dos dados, contrato de entrada e saída do `--passo`, regras do avaliador, comandos e porta da interface) tem de estar escrito no seu `.md`.

**Como a resposta do modelo vira a pasta `solucao/`:** o modelo responde em texto, e os avaliadores transformam essa resposta em arquivos sem alterar nada. Para isso, o seu `.md` deve pedir ao modelo que escreva **cada arquivo completo, separadamente, com o nome do arquivo logo antes do código**. Por exemplo:

````
main.py
```python
...código completo do main.py...
```

index.html
```html
...código completo do index.html...
```
````

Cada bloco é salvo, do jeito que veio, em `solucao/` com o nome indicado. Se o modelo deixar algum arquivo incompleto (por exemplo, "resto do código igual ao anterior") ou sem nome, esse arquivo vai faltar ou quebrar na solução.

> Como o modelo pode gerar códigos diferentes a partir do mesmo `.md`, escreva instruções que reduzam essa variação: seja explícito sobre algoritmos, fórmulas e formatos. Recomendamos que o `.md` não passe de **50 KB**.

### Restrições técnicas

A solução gerada a partir do `.md` deve usar **apenas**:

- **Python 3.12**, com **qualquer módulo da biblioteca padrão** (o que já vem instalado com o Python)
- **HTML/CSS/JavaScript** para interface, se quiser

Alguns módulos da biblioteca padrão que costumam ser úteis aqui: `csv`, `json`, `datetime`, `math`, `statistics`, `collections`, `http.server`, `urllib`, `sys`, `os`, `re`, `itertools`, `functools`, `heapq`, `bisect`, `argparse`, `time`, `random`, `pathlib`. A lista é só ilustrativa; outros módulos da biblioteca padrão também valem.

**Não é permitido**: `pandas`, `numpy`, `scikit-learn`, `tensorflow`, `pytorch`, `FastAPI`, `Flask`, `Django`, `Streamlit`, `React`, ou qualquer coisa que exija `pip install`.

A restrição existe para que toda solução rode em qualquer ambiente e para avaliar raciocínio algorítmico, não conhecimento de framework.

### Quais dados a solução pode ler

A solução gerada (`main.py` em qualquer modo) deve aprender **somente com informação que existiria no momento da decisão**. Em `../dados/` ela **pode** ler:

| Pode ler | Observação |
|---|---|
| `estacoes.csv`, `viagens.csv`, `historico_status.csv`, `clima.csv`, `snapshot_atual.csv` | histórico de Jul–Set/2024 |
| `calendario.csv` | cobre até Nov/2024; feriados e eventos são conhecidos com antecedência |

Ela **não pode** ler: `intencoes_simulacao.csv`, `estado_inicial_simulacao.csv`, `status_simulacao.csv`, `clima_simulacao.csv`, `calendario_simulacao.csv`, `viagens_realizadas_baseline.csv` e `historico_status_baseline.csv`. Esses arquivos contêm o futuro de outubro (demanda exata, paradas e clima) ou saídas do avaliador. O que a solução precisa saber de outubro chega pelo JSON de cada chamada `--passo`.

Para garantir isso, a correção roda a solução com `dados/` contendo **apenas** os arquivos permitidos acima e, na simulação, com um cenário de outubro oculto, **do mesmo formato** e pasta indicada pelo avaliador. Uma solução que dependa de arquivos proibidos falhará nessa execução.

---

## Dados fornecidos

### Dados históricos — para análise e aprendizado

| Arquivo | Descrição | Registros |
|---------|-----------|-----------|
| `estacoes.csv` | Cadastro das 80 estações | 80 |
| `snapshot_atual.csv` | Estado da rede em 30/set/2024 14:30 | 80 |
| `historico_status.csv` | Status de cada estação a cada 15 min, Jul–Set/2024 | ~707k |
| `viagens.csv` | Viagens de usuários, Jul–Set/2024 | ~165k |
| `clima.csv` | Clima horário, Jul–Set/2024 | 2.208 |
| `calendario.csv` | Calendário Jul/2024 – **Nov/2024** | 153 |

### Dados de simulação — para a operação hora a hora

| Arquivo | Descrição | Registros |
|---------|-----------|-----------|
| `intencoes_simulacao.csv` | Intenções de viagem de Out/2024: cada pessoa que tentou retirar uma bicicleta | ~57k |
| `estado_inicial_simulacao.csv` | Bicicletas em cada estação em 01/out 00:00 | 80 |
| `status_simulacao.csv` | Status operacional de cada estação, por hora, Out/2024 | 59.520 |
| `clima_simulacao.csv` | Clima horário, Out/2024 | 744 |
| `calendario_simulacao.csv` | Calendário de Out/2024 com eventos | 31 |
| `viagens_realizadas_baseline.csv` | Desfecho de cada intenção se **nenhuma** bicicleta for movimentada | ~57k |
| `historico_status_baseline.csv` | Estoque de cada estação a cada 15 min no mesmo cenário | ~240k |

Os dois arquivos `*_baseline.csv` são saídas do avaliador (ver *Entradas e saídas do motor*) e mostram o que acontece em outubro sem nenhuma movimentação. Servem de referência para o seu diagnóstico **no notebook**.

Os arquivos de simulação servem para **você** testar localmente com o avaliador que acompanha o case em `avaliador/` (ver *Testando localmente*). Lembre: a solução gerada não pode lê-los (ver *Quais dados a solução pode ler*).

---

## Parte 1 — Interface para o operador

A Parte 1 é entregue **como uma interface**, não como relatório nem como saída de terminal. Imagine que a equipe de operações vai abrir essa tela para decidir o que fazer agora: ela precisa ser usada por pessoas que **não conhecem o seu código nem o seu modelo**, e que precisarão encontrar ali, claramente, as respostas às perguntas abaixo.

As perguntas se referem ao estado da rede em **um momento à sua escolha**. Pode ser o `snapshot_atual.csv` (30/set/2024 14:30) ou qualquer instante de `historico_status.csv`. Use o clima e o calendário correspondentes, e deixe claro na interface qual momento está sendo analisado. Em todas as perguntas, "próxima hora" é a hora seguinte a esse momento.

**1. Qual é a situação atual da rede?**
Visão geral: total de bicicletas, estações críticas, ocupação por zona. Uma estação é **crítica** se estiver quase vazia (`bikes_pct` ≤ 10%) ou quase cheia (≥ 90%); estações fora de operação (`inactive`/`maintenance`) devem aparecer à parte.

**2. Quais estações têm maior risco de indisponibilidade?**
Quais podem ficar vazias ou lotadas na próxima hora, e por quê. O risco deve ser quantificado (por exemplo, probabilidade ou número esperado de viagens perdidas), não só classificado pela faixa de `bikes_pct`.

**3. Quais são as 3 estações prioritárias para intervenção agora?**
Considerando o limite de 3 movimentações por hora. Aqui, **"estação prioritária" é a estação que motiva cada uma das 3 movimentações escolhidas**: a que será abastecida (destino da movimentação, quando está em risco de esvaziar) ou a que será aliviada (origem da movimentação, quando está em risco de lotar). Para cada movimentação, apresente também a outra ponta (de onde saem ou para onde vão as bicicletas) e a quantidade movida.

**4. Por que cada estação foi priorizada?**
Justificativa objetiva para cada uma das 3 estações, incluindo o efeito esperado da movimentação (por exemplo, viagens perdidas evitadas).

**5. Qual a confiança nas previsões?**
Apresente pelo menos **uma métrica de qualidade medida fora da amostra** (dados não usados para treinar, por exemplo os últimos dias de setembro) e as **limitações** do seu modelo, de forma honesta. Não há uma métrica obrigatória: escolha a mais adequada e justifique.

---

## Parte 2 — Simulação hora a hora

Esta parte gera o score da simulação. Nada roda ao vivo: não há relógio, servidor nem conexão aberta. O avaliador **simula outubro/2024 hora a hora**. A cada hora cheia, ele mostra à sua solução o estado da rede naquele instante e pergunta quais bicicletas mover. Depois, ele mesmo avança a simulação até a hora seguinte e repete.

O mesmo `main.py` atende às Partes 1 e 2. Ele tem dois modos obrigatórios e um opcional:

| Comando | O que faz | Dados usados |
|---|---|---|
| `python main.py` | análise e interface da Parte 1 | o momento que você escolheu (histórico Jul–Set) |
| `python main.py --passo` | decide as movimentações de **uma** hora de outubro | o JSON recebido no stdin |
| `python main.py --preparar` | opcional: pré-processa o histórico uma vez | arquivos permitidos de `../dados/` |

**Cada chamada é um processo novo.** O avaliador executa `python main.py --passo`, envia o estado, lê a resposta e o programa termina. Nada fica em memória de uma hora para a próxima. O que a solução precisa "lembrar" vem da própria entrada ou de arquivos que ela lê do disco (por exemplo, o cache gravado pelo `--preparar`).

### Cadência das chamadas

| | |
|---|---|
| Período | 01/out a 31/out/2024 |
| Chamadas por dia | **17** (05:00, 06:00, 07:00, … , 21:00) |
| Total no período | **527** |
| Movimentações por chamada | no máximo **3** |
| Entre 21:00 e 05:00 | nenhuma chamada |

### Linha do tempo de um dia

```
05:00 ─ chamada ─┐
                 │ viagens da hora (retiradas e devoluções)
06:00 ─ chamada ─┤
                 │ viagens da hora (retiradas e devoluções)
  …       …      │   …
21:00 ─ chamada ─┤  ← última chamada do dia
                 │ viagens das 21:00 às 21:59
22:00            │
                 │ janela noturna, sem chamadas:
                 │ não há retiradas; só as devoluções de viagens
                 │ ainda em andamento mexem no estoque
05:00 ─ chamada ─┘  ← primeira chamada do dia seguinte
```

Em todo intervalo entre chamadas, "viagens da hora" significa o mesmo: as retiradas que começam e as devoluções que terminam naquela hora. As leituras de estoque de 15 em 15 minutos continuam 24h por dia.

### Linha do tempo de uma hora

Em cada hora cheia `hh:00`, nesta ordem:

1. O avaliador atualiza o `status` das estações a partir de `status_simulacao.csv`. Paradas e manutenções são iguais para todos os candidatos. O `status` vale para a hora inteira e **a solução não recebe aviso de quando uma estação voltará a operar**.
2. Grava a leitura de estoque de `hh:00` (antes de qualquer movimentação).
3. Chama `python main.py --passo` e envia o estado em uma linha de JSON no stdin.
4. Aplica as movimentações devolvidas **instantaneamente, às `hh:00`** (não há tempo de deslocamento dos veículos), uma por uma, na ordem da lista.
5. Processa as viagens até a próxima chamada e grava leituras em `hh:15`, `hh:30` e `hh:45`. Depois da chamada das 21:00, este passo vai até as 05:00 do dia seguinte.

Uma viagem que começa exatamente às `hh:00` já encontra o estoque depois das movimentações. Cada leitura (`hh:15`, por exemplo) inclui as viagens até o instante anterior a ela.

### Comando

```bash
python main.py --passo
```

Seu programa deve:

1. Ler o estado da rede via **stdin** (uma linha de JSON)
2. Decidir até 3 movimentações
3. Escrever o resultado via **stdout** (só o JSON, nada mais)
4. **Encerrar imediatamente**, com código de saída 0 — não suba servidor, não fique em loop

**O stdin é suficiente para decidir.** Ler CSV de `../dados/` no `--passo` é opcional (por exemplo, o cache de perfis gerado pelo `--preparar`, ou os arquivos históricos permitidos). O avaliador **não** envia a lista das movimentações já feitas: a solução enxerga apenas o estado resultante da rede (`estacoes` e `historico`), que reflete as próprias decisões anteriores. Se quiser lembrar decisões passadas, grave um arquivo de estado na própria pasta.

O avaliador executa `--passo` e `--preparar` com a pasta da solução como diretório de trabalho. A pasta da solução fica ao lado de `dados/` (por exemplo, `solucao/`; ver *Estrutura sugerida*) e lê os arquivos por `../dados/<arquivo>`.

O JSON da entrada chega só com caracteres ASCII (acentos vêm escapados, como `\u00e7`), então `json.load(sys.stdin)` funciona em qualquer sistema. Os CSVs de `dados/` estão em UTF-8: abra com `encoding="utf-8"`.

### Entrada (stdin)

> **Este JSON é apenas um exemplo reduzido**, com 1 estação e 2 leituras de histórico para mostrar o formato. A entrada real traz as **80 estações** e **8 leituras de 15 min de cada estação** (640 itens em `historico`).

```json
{
  "timestamp": "2024-10-01 08:00:00",
  "estacoes": [
    {
      "station_id": "ST001",
      "name": "Praça da Sé",
      "zone": "Centro",
      "capacity": 21,
      "available_bikes": 8,
      "available_docks": 13,
      "status": "active"
    }
  ],
  "historico": [
    {"timestamp": "2024-10-01 06:15:00", "station_id": "ST001",
     "available_bikes": 7, "available_docks": 14},
    {"timestamp": "2024-10-01 06:30:00", "station_id": "ST001",
     "available_bikes": 6, "available_docks": 15}
  ],
  "clima": {
    "temperature_c": 22.5,
    "feels_like_c": 21.8,
    "humidity_pct": 65.0,
    "precipitation_mm": 0.0,
    "wind_speed_kmh": 8.5,
    "weather_condition": "clear",
    "uv_index": 5
  },
  "calendario": {
    "date": "2024-10-01",
    "day_of_week": 1,
    "day_name": "Terça-feira",
    "is_weekend": false,
    "is_holiday": false,
    "holiday_name": "",
    "special_event": ""
  }
}
```

| Campo | Conteúdo |
|-------|----------|
| `timestamp` | Hora cheia da decisão |
| `estacoes` | Estado das 80 estações **neste instante**. `available_docks = capacity - available_bikes` |
| `historico` | Últimas 8 leituras de 15 min (2h) de **cada** estação, para estimar tendência (detalhes abaixo) |
| `clima` | Condição climática da hora corrente (colunas de `clima.csv`, sem `timestamp`). Não há previsão para as horas seguintes |
| `calendario` | Informações do dia (colunas de `calendario.csv`, sem `school_vacation`). Eventos simultâneos vêm unidos por `" + "` |

Sobre o `historico`:

- A leitura mais recente é a da própria hora da chamada (`hh:00`), gravada **antes** das suas movimentações. Na chamada das 08:00, as leituras vão de 06:15 a 08:00. Na chamada das 05:00, cobrem a madrugada (03:15 a 05:00).
- Na primeira chamada (01/out 05:00), as 8 leituras repetem o `estado_inicial_simulacao.csv`, porque não há viagens antes das 05:00.
- É uma lista única, ordenada por `timestamp` e depois por `station_id`. Agrupe por `station_id` para ter a série de cada estação.
- As leituras vêm da **sua** rede simulada de outubro, não do `historico_status.csv` de Jul–Set.
- Elas são só contexto para estimar tendência. Não mudam a cadência: você continua sendo chamado de hora em hora.

**Importante:** `estacoes` e `historico` refletem as consequências das **suas próprias decisões anteriores**. Se você esvaziou uma estação na hora passada, ela vem esvaziada agora.

### Saída (stdout)

```json
{"movimentacoes": [
  {"origem": "ST001", "destino": "ST015", "quantidade": 5},
  {"origem": "ST023", "destino": "ST007", "quantidade": 3}
]}
```

Regras:

- Só as **3 primeiras** movimentações da lista contam; as demais são descartadas. O corte acontece **antes** da validação: uma movimentação inválida também ocupa uma das 3 posições.
- `quantidade` é um inteiro positivo, como `5`. O avaliador converte o valor com `int()`: um decimal como `5.9` é truncado para 5. Não conte com isso: devolva sempre um inteiro.
- Nada a fazer? Responda `{"movimentacoes": []}`.
- Cada movimentação é validada no momento em que é aplicada. Ela é **ignorada**, sem aviso, se uma das estações não existe, se alguma das duas não está `active`, se origem = destino, ou se `quantidade`, convertida com `int()`, não der um inteiro positivo (campo ausente, `null`, texto como `"5.9"`, zero ou negativo). Um item que não é objeto JSON também é ignorado.
- Se a quantidade passa do possível, o avaliador **recorta**: `real = min(quantidade, bicicletas na origem agora, vagas no destino agora)`. Se `real` dá 0, nada é movido. Como as movimentações são aplicadas em sequência, a segunda já enxerga o estoque deixado pela primeira.

### Exemplos

As estações, os horários e os números abaixo servem só para ilustrar as regras. Não refletem o padrão real de nenhuma estação: descobrir esse padrão faz parte do case. A entrada real traz as 80 estações e 8 leituras de cada uma; aqui ela foi reduzida.

**Exemplo A — uma chamada completa.** Terça, 08/out, 11:00.

```json
{"timestamp": "2024-10-08 11:00:00",
 "estacoes": [
  {"station_id": "ST002", "name": "Estação República", "zone": "Centro",
   "capacity": 20, "available_bikes": 3, "available_docks": 17, "status": "active"},
  {"station_id": "ST007", "name": "Largo do Arouche", "zone": "Centro",
   "capacity": 21, "available_bikes": 18, "available_docks": 3, "status": "active"}],
 "historico": [
  {"timestamp": "2024-10-08 09:15:00", "station_id": "ST002", "available_bikes": 9, "available_docks": 11},
  {"timestamp": "2024-10-08 09:15:00", "station_id": "ST007", "available_bikes": 17, "available_docks": 4},
  {"timestamp": "2024-10-08 10:15:00", "station_id": "ST002", "available_bikes": 6, "available_docks": 14},
  {"timestamp": "2024-10-08 10:15:00", "station_id": "ST007", "available_bikes": 18, "available_docks": 3},
  {"timestamp": "2024-10-08 11:00:00", "station_id": "ST002", "available_bikes": 3, "available_docks": 17},
  {"timestamp": "2024-10-08 11:00:00", "station_id": "ST007", "available_bikes": 18, "available_docks": 3}],
 "clima": {"weather_condition": "clear", "...": "..."},
 "calendario": {"date": "2024-10-08", "is_holiday": false, "special_event": "", "...": "..."}}
```

Raciocínio: ST002 perdeu 6 bicicletas desde 09:15. Se o modelo que você construiu com o histórico espera mais retiradas que devoluções na próxima hora, ela zera antes das 12:00. ST007 está quase cheia (3 vagas) e estável, então pode ceder bicicletas sem risco de faltar. Saída:

```json
{"movimentacoes": [{"origem": "ST007", "destino": "ST002", "quantidade": 8}]}
```

Às 11:00, ST007 fica com 10 bicicletas e ST002 com 11. As outras duas posições ficam livres para outras estações. Na simulação, a distância entre origem e destino não pesa: a movimentação é instantânea.

**Exemplo B — três horas seguidas.** Quarta, 02/out.

| Hora | Entrada mostra (ST002 / ST007) | Decisão | Logo após aplicar |
|---|---|---|---|
| 13:00 | 4 / 17 | mover 8 de ST007 para ST002 | 12 / 9 |
| 14:00 | 5 / 11 | mover 6 de ST007 para ST002 | 11 / 5 |
| 15:00 | 8 / 7 | nada nesse par; as 3 posições vão para outras estações | 8 / 7 |

- A entrada das 14:00 é consequência da decisão das 13:00. Entre 13:00 e 14:00, ST002 perdeu 7 bicicletas (12 → 5) e ST007 ganhou 2 (9 → 11). Sem a movimentação, ST002 teria zerado por volta de 13:30, e as retiradas seguintes falhariam.
- No `historico` das 14:00, a leitura de 13:00 de ST002 é **4** (antes da movimentação). A leitura de 13:15 já mostra o efeito.
- Às 15:00, ST007 já não tem folga. Mover mais dela agora só trocaria uma estação em risco por outra.

**Exemplo C — validação e recorte.** As decisões abaixo servem só para mostrar as regras. Estado às 10:00:

| Estação | `capacity` | `available_bikes` | `status` |
|---|---|---|---|
| ST005 | 26 | 4 | `active` |
| ST003 | 21 | 2 | `active` |
| ST006 | 18 | 10 | `maintenance` |
| ST010 | 12 | 3 | `active` |
| ST001 | 21 | 15 | `active` |

Saída da solução:

```json
{"movimentacoes": [
  {"origem": "ST005", "destino": "ST003", "quantidade": 10},
  {"origem": "ST006", "destino": "ST010", "quantidade": 3},
  {"origem": "ST003", "destino": "ST010", "quantidade": 5},
  {"origem": "ST001", "destino": "ST011", "quantidade": 4}
]}
```

O que o avaliador aplica:

| # | Pedido | Resultado | Estoque depois |
|---|---|---|---|
| 1 | ST005 → ST003, 10 | **recortada para 4**: ST005 só tem 4 | ST005 0, ST003 6 |
| 2 | ST006 → ST010, 3 | **ignorada**: ST006 está em `maintenance` | sem mudança |
| 3 | ST003 → ST010, 5 | **aplicada com 5**: sem a #1, ST003 teria só 2 e a movimentação seria recortada para 2 | ST003 1, ST010 8 |
| 4 | ST001 → ST011, 4 | **descartada**: passou do limite de 3, mesmo com a #2 inválida | sem mudança |

**Exemplo D — testar uma chamada à mão.** Antes de rodar o avaliador:

1. Use `solucao_inicial/entrada_exemplo.json`, uma entrada real completa da chamada de 01/out 08:00 (copie-a para a sua pasta com o nome `entrada.json`). Ou salve um JSON seu em `solucao/entrada.json`, por exemplo o do Exemplo A: nesse caso, troque os `"..."` pelos demais campos de `clima` e `calendario`, copiados do JSON completo de *Entrada (stdin)*. A entrada reduzida tem menos estações e leituras que a real; a solução não deve quebrar por isso. O avaliador envia o JSON em uma única linha; `json.load(sys.stdin)` aceita os dois formatos.
2. Se a sua solução usa cache, rode `python main.py --preparar` antes.
3. Rode, dentro de `solucao/`:

```bash
python main.py --passo < entrada.json                         # deve imprimir só o JSON
python main.py --passo < entrada.json | python -m json.tool   # falha se a saída não for JSON válido
```

No PowerShell, use `Get-Content entrada.json | python main.py --passo`. Confira que a saída tem a chave `movimentacoes`, no máximo 3 itens e `quantidade` inteira.

4. Volte para a pasta `case_quant/` (a que contém `dados/` e `avaliador/`) e rode um período curto: `python avaliador/avaliar.py solucao --ate 2024-10-01 --verbose`.

### Passo de preparação (opcional)

Se sua solução precisa pré-processar o histórico (construir perfis, treinar algo, montar cache), implemente:

```bash
python main.py --preparar
```

O avaliador chama esse comando **uma vez, antes da simulação**, com limite de 5 minutos. Use-o para gravar um cache em disco (na pasta da solução) que o `--passo` depois só carrega.

O avaliador chama `--preparar` **sempre**, mesmo que você não o implemente. Se não precisar dele, trate a opção e saia logo com código 0: o `main.py` não pode cair no modo normal e subir o servidor da interface. Se o `--preparar` falhar ou estourar o tempo, a simulação roda mesmo assim, sem aviso. Por isso, o `--passo` deve funcionar mesmo sem o cache (por exemplo, com uma regra mais simples), em vez de terminar com erro.

Arquivos que a solução grava na própria pasta (no `--preparar` ou no `--passo`) continuam lá nas chamadas seguintes. O avaliador não apaga nada entre execuções: um arquivo de estado deixado por uma rodada anterior continua no disco.

Isso existe porque `--passo` tem **timeout de 30 segundos** e é chamado 527 vezes. Reprocessar `viagens.csv` em cada chamada custa segundos por hora; com processamento pesado, estoura os 30 s.

### Esqueleto mínimo

```python
import sys
import json

if "--preparar" in sys.argv:
    construir_cache()           # opcional; se não usar, apenas saia
    sys.exit(0)

if "--passo" in sys.argv:
    dados = json.load(sys.stdin)
    movs = decidir(dados)       # sua lógica
    print(json.dumps({"movimentacoes": movs}))
    sys.exit(0)

# modo normal: análise, relatório, servidor web...
```

A pasta `solucao_inicial/` traz este esqueleto completo e funcionando: lê a entrada, agrupa o `historico` por estação, protege o formato da saída e escreve log no stderr. Ela nunca movimenta nada, então empata com o baseline. Copie-a para começar a sua versão. Ela também traz o `entrada_exemplo.json` citado no Exemplo D.

### Erros comuns

Se uma chamada falha, o avaliador não para: aquela hora fica **sem movimentação** e a simulação segue. Uma chamada falha por timeout, por código de saída diferente de 0 (mesmo que o JSON tenha sido impresso), por saída que não é um JSON válido, ou por um JSON que não é um objeto ou cujo `movimentacoes` não é uma lista. Exceção: saída vazia, ou JSON sem a chave `movimentacoes`, não é falha; vale como "nada a fazer".

| Erro | Consequência |
|---|---|
| Subir servidor, abrir a interface ou ficar em loop no `--passo` ou no `--preparar` | timeout (30 s por hora; 5 min no preparo) |
| Imprimir log ou mensagem no stdout | a saída deixa de ser um JSON válido. Use `print(..., file=sys.stderr)` |
| Ler e processar `viagens.csv` ou `historico_status.csv` em cada chamada | lentidão e risco de timeout. Faça isso no `--preparar` e grave um cache |
| Guardar estado em variável global e esperar que ela exista na próxima hora | o valor se perde: cada chamada é um processo novo |
| Ler `dados/arquivo.csv` em vez de `../dados/arquivo.csv` | arquivo não encontrado; a chamada termina com erro |
| Ler arquivos de simulação ou baseline (ver *Quais dados a solução pode ler*) | a solução falha na execução de correção, que não os fornece |
| Tratar `historico` como se viesse separado por estação | séries misturadas. Agrupe por `station_id` |
| Devolver `quantidade` como texto ou decimal | fora do contrato: o avaliador aplica `int()` e trunca decimais, ou ignora a movimentação se a conversão falhar. Converta com `int()` antes de imprimir |

---

## Como o score é calculado

O avaliador simula o período **viagem por viagem**. Cada linha de `intencoes_simulacao.csv` é uma pessoa que quer sair de uma estação, em um horário, rumo a outra estação. O avaliador segue cada uma delas em ordem cronológica:

1. **Retirada** (no `start_time`): se a estação de origem está `active` e tem bicicleta, a bicicleta sai e a viagem fica em andamento. Se não, é uma **falha de retirada**: a pessoa desiste, a viagem termina ali.
2. **Devolução** (no `end_time`): se a estação de destino está `active` e tem vaga, a viagem é **realizada**. Se não, é uma **falha de devolução**: a pessoa é redirecionada para a estação `active` mais próxima (distância em linha reta, por `latitude`/`longitude`) que tenha vaga naquele instante e devolve a bicicleta lá.
3. Se nenhuma estação `active` tem vaga, a bicicleta sai do sistema e a viagem registra a falha mesmo assim.

Cada intenção gera **no máximo uma falha**: quem falha na retirada não chega a devolver; quem é redirecionado não conta uma segunda falha.

A ordem de cada hora (status, leitura, chamada, movimentações, viagens) está em *Linha do tempo de uma hora*, na Parte 2. Paradas e manutenções valem também à noite, para as devoluções. Entre 21:00 e 05:00 não há chamadas; só as devoluções de viagens que terminam à noite mexem no estoque.

**Retiradas só acontecem entre 05:00 e 21:59** na simulação. O histórico de Jul–Set tem viagens noturnas, mas em outubro o sistema não aceita retiradas entre 22:00 e 05:00. Quem treina o perfil de demanda com todas as horas do histórico vai superestimar a demanda noturna.

```
score = total de viagens com falha no período   (menor é melhor)
```

Seu score é comparado com o **baseline imóvel** — uma solução que nunca movimenta nada:

```
viagens salvas = score_baseline − score_solucao
melhora (%)    = viagens salvas / score_baseline × 100
```

Nos dados de simulação fornecidos, o baseline imóvel tem **29.332 falhas** em ~57 mil intenções (14.812 de retirada e 14.520 de devolução). É esse o número que você precisa derrubar. A correção usa um cenário de outubro oculto, do mesmo formato e gerado da mesma forma; os números exatos serão diferentes.

### Entradas e saídas do motor

**Entradas** (da pasta de dados, `dados/` por padrão):

| Arquivo | Uso |
|---|---|
| `estacoes.csv` | `capacity`; `latitude`/`longitude` para o redirecionamento; `name`/`zone` repassados à solução |
| `estado_inicial_simulacao.csv` | estoque em 01/out 00:00 |
| `status_simulacao.csv` | status operacional por hora |
| `intencoes_simulacao.csv` | a demanda |
| `clima_simulacao.csv`, `calendario_simulacao.csv` | repassados à solução em cada `--passo` |
| a solução (`main.py`) | movimentações de cada hora |

**Saídas** (só com `--saida <pasta>`; o score sai sempre no terminal):

| Arquivo | Conteúdo |
|---|---|
| `viagens_realizadas_<nome>.csv` | o desfecho de cada intenção (abaixo) |
| `historico_status_<nome>.csv` | mesmo formato de `historico_status.csv` (`timestamp`, `station_id`, `available_bikes`, `available_docks`, `status`), uma leitura a cada 15 minutos, 24h por dia, do estoque produzido pela execução |
| `movimentacoes_<nome>.csv` | as movimentações que o avaliador de fato aplicou (`timestamp` da decisão, `origem`, `destino`, `quantidade` já recortada), uma linha por movimentação, na ordem em que foram aplicadas |

`viagens_realizadas_<nome>.csv` tem as colunas de `intencoes_simulacao.csv` mais `end_station_real` e `resultado` (`realizada`, `falha_retirada` ou `falha_devolucao`). `end_station_real` é igual a `end_station_id` em `realizada`, é a estação do redirecionamento em `falha_devolucao`, e fica vazio em `falha_retirada` ou quando a bicicleta sai do sistema. Há uma linha por intenção, na ordem do arquivo de intenções.

### Testando localmente

O avaliador acompanha o case, na pasta `avaliador/`. É exatamente o mesmo código usado na correção: as regras e o cálculo do score são idênticos.

```bash
# rode a partir da pasta case_quant/ (a que contém dados/ e avaliador/)

# avalia a sua solução no período completo
python avaliador/avaliar.py solucao

# período curto, para iterar rápido: vai até as 21:00 do dia indicado, inclusive
python avaliador/avaliar.py solucao --ate 2024-10-03

# lista as horas com movimentação aplicada ou viagem falhada: movimentações, falhas da hora e acumulado (a linha das 21:00 inclui a madrugada)
python avaliador/avaliar.py solucao --ate 2024-10-03 --verbose

# grava viagens_realizadas_, historico_status_ e movimentacoes_<nome>.csv na pasta indicada
python avaliador/avaliar.py solucao --saida saida_local

# várias versões suas competindo em paralelo, com placar ao vivo
python avaliador/corrida.py .
```

O `corrida.py` roda todas as subpastas que têm `main.py`. Deixe cada versão numa pasta ao lado de `dados/` (por exemplo, `v1/` e `v2/`), para que `../dados` continue funcionando.

O terminal mostra as falhas da solução e as do baseline no mesmo período. O stderr da solução não é exibido; a exceção é o último erro com código de saída diferente de 0, do qual aparecem os primeiros caracteres. Para ver onde as falhas acontecem, use `--saida` e analise `viagens_realizadas_<nome>.csv`.

**Atenção:** o avaliador local roda com todos os arquivos presentes em `dados/`, portanto **não detecta** o uso de arquivos proibidos. Confira você mesmo que o seu `main.py` não os lê.

---

## Critérios de avaliação

| Critério | O que é olhado |
|----------|----------------|
| **Score na simulação** (Parte 2) | Viagens salvas em relação ao baseline, no modo `--passo`, no cenário oculto |
| **Interface** (Parte 1) | Uma interface que responde às 5 perguntas, com justificativa clara para cada recomendação, e que outras pessoas conseguem usar sem ajuda: clareza, facilidade de uso, boa experiência |
| **Notebook de análise** (parte 3) | O `analise_[seu_nome].ipynb`: como você entendeu o problema e chegou à sua estratégia |
| **Qualidade do código gerado** | Clareza, organização, lógica correta, robustez |

**Sobre a interface:** não basta imprimir números no terminal nem entregar uma tela que só quem escreveu o código entende. Queremos ver a tela que o operador usaria para decidir, com a resposta para cada uma das 5 perguntas, e saber que você sabe construir uma solução que **outras pessoas conseguem usar**.

**Como a interface é executada:** `python main.py`, dentro de `solucao/`, deve calcular a análise da Parte 1, **subir um servidor local com `http.server` em `127.0.0.1:8000`** (aceitar `--porta` é opcional) e imprimir o endereço no terminal. O avaliador abre o endereço no navegador; não é necessário abrir o navegador automaticamente. Uma página HTML estática servida por esse servidor é aceita.

Solução que não implementa `--passo` fica sem score na simulação.

**Uso do score:** o score considera apenas viagens salvas; não há penalidade pelo número de movimentações usadas nem pelo volume de bicicletas movidas.

---

## Estrutura sugerida

```
case_quant/
├── avaliador/
├── dados/
├── descricao/
├── solucao_inicial/  # ponto de partida, vem com o case (esqueleto + entrada_exemplo.json)
├── notebook/
│   └── analise_[seu_nome].ipynb   # parte 3, escrita por você; lê ../dados/
└── solucao/          # gerada pelo modelo a partir do seu .md
    ├── main.py       # obrigatório: ponto de entrada; --passo obrigatório, --preparar opcional
    ├── analise.py    # sugestão: análise do histórico que alimenta a interface
    ├── index.html    # sugestão: interface gráfica — responde às 5 perguntas da Parte 1
    ├── style.css     # sugestão: estilos da interface
    └── README.md     # sugestão: como executar
```

Só são obrigatórios o `main.py` em `solucao/` (com os modos descritos acima) e o notebook numa subpasta ao lado de `dados/`. A divisão dos demais arquivos da solução é livre: por exemplo, o HTML pode ser gerado pelo próprio `main.py`.

---

## Dicas

1. **Comece pela interface.** Ela é o produto que a operação usaria. Construa a tela que responde às 5 perguntas de forma que alguém decida olhando para ela — e só depois ajuste o `--passo`.

2. **Três é muito pouco.** Com 80 estações e 3 movimentações por hora, o que separa uma solução boa de uma medíocre é o *critério de escolha*, não a sofisticação do modelo. Pergunte-se: esta movimentação evita mais viagens perdidas que a alternativa?

3. **Nem toda estação vazia é urgente.** Uma estação vazia num bairro residencial à meia-noite não custa nada. Uma estação de metrô que vai zerar às 18h custa dezenas de viagens. Pondere pelo movimento esperado.

4. **Antecipe, não reaja.** Quando o estoque já está em zero, a viagem já foi perdida. Use o perfil horário do histórico para abastecer *antes* do pico.

5. **Clima, feriado e dia da semana mudam a demanda.** Tempestade derruba a demanda a cerca de um quinto, e chuva a cerca de 40%. Essas informações chegam na entrada de cada chamada — use-as. **Eventos especiais** também aparecem no calendário, mas os dados não dizem onde acontecem; no histórico o efeito no total da rede é pequeno (algo entre 3% e 10% a mais) e ruidoso por estação. Avalie com cuidado se vale modelá-los.

6. **Prefira lógica que generaliza.** Constantes calibradas na mão para casar com os números exatos de um período costumam envelhecer mal. Uma regra derivada do padrão da estação é mais robusta que um limiar escolhido a dedo. Como a correção usa um cenário oculto, isso importa.

7. **Respeite o timeout.** 30s por chamada. Pré-processe no `--preparar`.

---

## Entrega

- **Formato**: dois arquivos, `solucao_[seu_nome].md` e `analise_[seu_nome].ipynb`
- **Nome**: use o mesmo `[seu_nome]` nos dois (regra de formato em *O que você entrega*)
- **Prazo**: segunda-feira, 09/nov/2026, às 12:00 (meio-dia, horário de Brasília)

Boa sorte.
