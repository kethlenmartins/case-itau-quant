# Rascunho de solução — Parte 2: política de simulação

> Este documento é uma seção pronta para integrar em
> `solucao_kethlen_martins_da_silva.md`. Ele ainda **não é a entrega final**:
> faltará acrescentar os arquivos completos da interface da Parte 1 e a instrução
> única para o modelo gerar todos os arquivos.

## Instrução para o modelo gerador

Você deve gerar uma solução local completa para a **Parte 2** de um case de
redistribuição de bicicletas. Nesta etapa, produza exatamente um arquivo
completo, com o nome antes do bloco:

```text
main.py
```python
# código completo aqui
```
```

Não escreva explicações fora do bloco. O código deve rodar em Python 3.12 usando
**somente a biblioteca padrão**. Não importe ou instale `pandas`, `numpy`,
`scipy`, bibliotecas web, bibliotecas de machine learning ou qualquer pacote de
terceiros.

O arquivo será colocado em uma pasta `solucao/`, irmã de `dados/`; portanto,
arquivos históricos ficam em `../dados/`. Os diretórios de protótipos ou outros
arquivos do projeto não existirão. Não importe código externo nem dependa de
arquivos que não estejam explicitamente permitidos abaixo.

## Modos de execução obrigatórios

Implemente os três ramos abaixo, nesta ordem de prioridade:

1. `python main.py --preparar`
2. `python main.py --passo`
3. `python main.py` (este ramo será integrado depois com a interface da Parte 1)

Nos modos `--preparar` e `--passo`, **não** iniciar servidor, não ficar em loop,
não abrir navegador e encerrar com código 0. Mensagens de diagnóstico podem ir
para `stderr`, nunca para `stdout` no modo `--passo`.

### `--preparar`

Construa, em no máximo cinco minutos, o arquivo local
`perfil_p13_cache.json`, no mesmo diretório de `main.py`. Leia somente:

- `../dados/viagens.csv`
- `../dados/historico_status.csv`

Não leia em nenhum modo os seguintes arquivos, pois são de simulação ou
baseline: `intencoes_simulacao.csv`, `estado_inicial_simulacao.csv`,
`status_simulacao.csv`, `clima_simulacao.csv`, `calendario_simulacao.csv`,
`viagens_realizadas_baseline.csv` ou `historico_status_baseline.csv`.

Os CSVs estão em UTF-8 e devem ser lidos com `csv.DictReader`.

#### Perfis de demanda

Em `viagens.csv`, as colunas são:

```text
trip_id,start_time,end_time,start_station_id,end_station_id,duration_min,user_type
```

`start_time` e `end_time` estão em formato ISO `YYYY-MM-DD HH:MM:SS`.

Crie perfis de média para cada chave:

```text
station_id | hora (0–23) | dia_da_semana (0=segunda, 6=domingo)
```

Para cada viagem:

- incremente uma retirada na chave de `start_station_id`, hora e dia da semana
  de `start_time`;
- incremente uma devolução na chave de `end_station_id`, hora e dia da semana
  de `end_time`.

Divida cada contagem pelo número de datas históricas distintas do respectivo dia
da semana. Inclua valor zero quando uma chave não existir na decisão. O cache
deve permitir consultar o par `(retiradas_médias, devoluções_médias)` em O(1).

#### Confiabilidade de status

Em `historico_status.csv`, as colunas são:

```text
timestamp,station_id,available_bikes,available_docks,status
```

Para a mesma chave estação–hora–dia da semana, calcule:

```text
confiabilidade = número de leituras com status == "active" / número total de leituras
```

Essa é uma frequência histórica, não um status futuro observado. Quando uma
chave estiver ausente na decisão, use confiabilidade `1.0`, para não descartar
uma estação sem evidência histórica.

Grave um JSON compacto e autocontido com os dois dicionários. Não grave dados de
simulação, estado recebido no stdin ou resultados de decisões anteriores.

### `--passo`

Leia uma única entrada JSON de `stdin` com `json.load(sys.stdin)`. O objeto tem:

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
  "historico": [],
  "clima": {},
  "calendario": {}
}
```

Na entrada real há 80 estações e um histórico de leituras de 15 em 15 minutos.
Nesta política, o histórico, clima e calendário não precisam ser usados; eles
devem ser aceitos sem causar erro. A decisão usa o estado atual e o cache
histórico preparado. Não use informação de outubro que não esteja no JSON.

Imprima em `stdout` exatamente um único JSON válido, sem prefixos nem logs:

```json
{"movimentacoes":[{"origem":"ST001","destino":"ST015","quantidade":5}]}
```

A lista pode ter de zero a três objetos, nesta ordem. Todo objeto deve ter:

- `origem`: ID de estação existente e ativa;
- `destino`: ID de estação existente e ativa, diferente da origem;
- `quantidade`: inteiro positivo e fisicamente viável no estado deixado pelas
  movimentações anteriores.

Se qualquer erro inesperado ocorrer, registre-o somente em `stderr` e imprima
`{"movimentacoes":[]}` com código de saída 0.

## Política P13 a implementar

Use esta política exatamente. Ela é uma aproximação interpretável de perda
esperada em duas horas e foi escolhida após ablações locais.

### 1. Estado elegível

Crie uma cópia mutável apenas das estações com `status == "active"`. Preserve,
para cada uma, ID, capacidade, bicicletas disponíveis e vagas disponíveis.
Estações inativas ou em manutenção não podem ser origem nem destino.

### 2. Perfil em um instante

Para uma estação e um instante `t`, consulte as médias históricas de retirada
`r(t)` e devolução `a(t)` pela chave estação–hora–dia da semana. Entre 22:00 e
04:59, force `r(t) = 0`, pois a simulação não aceita retiradas nesse período;
devoluções continuam possíveis.

### 3. Perda de uma estação

Para estoque `b`, capacidade `C`, retiradas previstas `r` e devoluções previstas
`a`, use:

```text
perda(b, C, r, a) = max(r - b, 0) + max(a - (C - b), 0)
```

A primeira parcela representa retiradas que podem falhar por falta de bicicleta;
a segunda, devoluções que podem falhar por falta de vaga.

### 4. Risco P13 em duas horas

Para cada estação e estoque hipotético `b` após uma movimentação:

1. calcule a perda da hora corrente com `r0` e `a0`;
2. estime o estoque da hora seguinte:

   ```text
   b1 = min(C, max(0, b - r0 + a0))
   ```

3. consulte `r1` e `a1` para uma hora depois;
4. consulte a confiabilidade histórica `p_active` da estação para a hora
   seguinte;
5. retorne:

   ```text
   risco(b) = perda(b, C, r0, a0) + p_active * perda(b1, C, r1, a1)
   ```

O multiplicador de confiabilidade vale somente para a segunda hora. O status
atual já é observado no JSON. Não tente prever ou ler o status real futuro.

### 5. Seleção de até três movimentos

Repita até três vezes, sempre usando o estado que sobrou da rodada anterior:

1. para cada quantidade inteira `q` de 1 a 10, calcule para toda estação ativa:

   ```text
   custo_origem = risco(b - q) - risco(b), se b >= q
   beneficio_destino = risco(b) - risco(b + q), se vagas >= q
   ```

2. ordene origens por menor `custo_origem` e destinos por maior
   `beneficio_destino`;
3. combine somente as cinco melhores origens com os cinco melhores destinos da
   mesma quantidade, ignorando pares com origem igual a destino;
4. escolha o par e quantidade com maior:

   ```text
   ganho_liquido = beneficio_destino - custo_origem
   ```

5. para desempate determinístico, compare a tupla
   `(ganho_liquido, q, origem_id, destino_id)` de forma decrescente;
6. se o melhor ganho for menor ou igual a zero, pare: não inclua movimentação
   sem benefício previsto positivo;
7. caso contrário, acrescente a movimentação à saída e atualize imediatamente:

   ```text
   bikes_origem -= q
   docks_origem += q
   bikes_destino += q
   docks_destino -= q
   ```

O limite de `q = 10` é uma limitação deliberada da busca. Uma ablação que
considerou toda a quantidade fisicamente possível teve desempenho pior no
backtest; não substitua esse limite por uma constante de ocupação ou por um
percentual fixo de capacidade.

### 6. Cache ausente ou inválido

`--passo` deve continuar válido se `perfil_p13_cache.json` não existir ou estiver
corrompido. Nesse caso, não releia CSVs a cada chamada. Use um fallback simples:

- considere estações ativas;
- para até três rodadas, escolha a estação com maior fração
  `available_bikes / capacity` como origem e a de menor fração como destino;
- só mova se origem e destino forem distintos e a fração da origem for
  estritamente maior que a do destino;
- mova `min(10, bikes_origem, docks_destino)` bicicletas, se o resultado for
  positivo; atualize o estado e repita.

O fallback protege o contrato e o prazo, mas o caminho normal deve usar o cache
de P13. Não imprima aviso em `stdout`.

## Requisitos de robustez e desempenho

- O avaliador inicia um processo novo a cada hora e impõe 30 segundos para
  `--passo`. Carregue somente o JSON compacto em cada chamada; não processe CSV
  no caminho normal.
- `--preparar` pode ser chamado mais de uma vez. Recrie o cache de modo seguro e
  compacto.
- Caminhos devem ser construídos a partir de `Path(__file__).resolve().parent`,
  para funcionar mesmo se o diretório atual for diferente do esperado.
- Use `datetime.fromisoformat`, `csv`, `json`, `collections.defaultdict`,
  `pathlib.Path`, `math` e outros módulos padrão quando necessário.
- Nunca suponha que existam exatamente 80 estações; aceite também entradas
  reduzidas de teste.
- Nunca use `available_docks` como fonte de verdade quando atualizar uma cópia:
  mantenha bikes e docks consistentes com a capacidade.
- Use `ensure_ascii=False` em `json.dumps` se desejar; o avaliador aceita JSON
  UTF-8, e a única saída precisa ser o objeto solicitado.

## Testes de aceite após a geração

Dentro da pasta gerada `solucao/`:

```bash
python main.py --preparar
python main.py --passo < entrada.json | python -m json.tool
```

O segundo comando deve emitir somente a chave `movimentacoes`, com no máximo três
objetos válidos. Depois, a partir da pasta que contém `dados/` e `avaliador/`:

```bash
python avaliador/avaliar.py solucao --ate 2024-10-03
python avaliador/avaliar.py solucao
```

Antes da entrega, verifique que o código gerado não cita arquivos proibidos e
não importa pacotes fora da biblioteca padrão.
