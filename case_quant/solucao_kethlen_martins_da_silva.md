# Instruções para gerar a solução do Case Quant — Kethlen Martins da Silva

> **Rascunho em construção.** A Parte 2 está especificada abaixo. Antes da
> entrega, integrar nesta instrução os arquivos completos da Parte 1
> (`index.html`, `style.css` e `app.js`) produzidos pela IA de design e remover
> este aviso. Não enviar este rascunho como entrega final enquanto a Parte 1 não
> estiver completa.

Você deve gerar todos os arquivos de uma solução local para um sistema de
bicicletas compartilhadas. O ambiente terá Python 3.12 e os dados em uma pasta
`../dados/`, irmã da pasta da solução. Você não terá acesso ao enunciado, aos
CSVs, a nenhum código existente ou a esta conversa: todas as regras necessárias
estão nesta instrução.

## Formato obrigatório da sua resposta

Responda somente com os arquivos completos, cada qual precedido pelo nome exato
do arquivo e seguido por um bloco de código. Não omita partes, não use
reticências, não escreva “continua” e não deixe arquivos para o usuário
completar. Use este formato:

````text
main.py
```python
# arquivo completo
```

index.html
```html
<!-- arquivo completo -->
```
````

Arquivos que ainda não possuem especificação completa nesta versão do rascunho
serão acrescentados posteriormente. Por enquanto, concentre-se em gerar o
`main.py` completo conforme a Parte 2 abaixo.

## Estrutura final esperada

Sua resposta final deverá formar esta estrutura. Os arquivos marcados como
“gerado em execução” não precisam ser emitidos como blocos de código: o
`main.py` os cria quando necessário.

```text
solucao/
├── main.py                    # obrigatório; Partes 1 e 2
├── index.html                 # Parte 1; interface estática local
├── style.css                  # Parte 1; estilos da interface
├── app.js                     # Parte 1; renderização e interações nativas
├── README.md                  # instruções curtas de execução
├── dados_interface.json       # gerado em execução pelo modo normal
└── perfil_p13_cache.json      # gerado em execução por --preparar
```

Regras para a estrutura:

- O avaliador executará `python main.py`, `python main.py --preparar` e
  `python main.py --passo` dentro de `solucao/`.
- A pasta `solucao/` fica ao lado de `dados/`; portanto, use caminhos relativos
  resolvidos a partir do diretório do próprio `main.py`, como
  `Path(__file__).resolve().parent.parent / "dados"`.
- `dados_interface.json` e `perfil_p13_cache.json` são artefatos locais de
  execução. Eles podem não existir na primeira chamada e devem ser recriados ou
  tratados de modo seguro.
- Não criar dependências em pastas externas, protótipos, arquivos ocultos ou
  instalações de pacotes.

## Restrições globais

- Use somente Python 3.12 e módulos da biblioteca padrão; para a interface, use
  somente HTML, CSS e JavaScript nativos.
- Não use `pandas`, `numpy`, `scipy`, scikit-learn, bibliotecas web, React,
  Vue, npm, CDN, fontes externas, APIs externas ou qualquer pacote de terceiros.
- Abra CSVs em UTF-8 com `csv.DictReader` e processe datas com
  `datetime.fromisoformat`.
- Não leia os arquivos proibidos em nenhum modo:
  `intencoes_simulacao.csv`, `estado_inicial_simulacao.csv`,
  `status_simulacao.csv`, `clima_simulacao.csv`, `calendario_simulacao.csv`,
  `viagens_realizadas_baseline.csv` e `historico_status_baseline.csv`.
- A solução pode ler apenas os históricos permitidos:
  `estacoes.csv`, `viagens.csv`, `historico_status.csv`, `clima.csv`,
  `calendario.csv` e `snapshot_atual.csv`.
- Nunca escreva logs em `stdout` no modo `--passo`; use `stderr` se necessário.

# Parte 2 — Simulação hora a hora

Implemente os três ramos abaixo nesta ordem:

1. `python main.py --preparar`
2. `python main.py --passo`
3. `python main.py` — será detalhado na Parte 1 a integrar depois

Nos modos `--preparar` e `--passo`, não iniciar servidor, não abrir navegador,
não ficar em loop e encerrar com código 0.

## Modo `--preparar`

Crie o arquivo `perfil_p13_cache.json` na pasta de `main.py`, usando somente:

- `../dados/viagens.csv`
- `../dados/historico_status.csv`

O preparo tem até cinco minutos e pode ser chamado mais de uma vez. Gere um JSON
compacto, autocontido e válido.

### Perfis de demanda

`viagens.csv` contém as colunas:

```text
trip_id,start_time,end_time,start_station_id,end_station_id,duration_min,user_type
```

`start_time` e `end_time` usam o formato `YYYY-MM-DD HH:MM:SS`.

Para cada chave `station_id | hora | dia_da_semana`, em que segunda-feira é 0 e
domingo é 6:

- conte retiradas por `start_station_id`, hora e dia da semana de `start_time`;
- conte devoluções por `end_station_id`, hora e dia da semana de `end_time`;
- divida cada contagem pelo número de datas históricas distintas daquele dia da
  semana.

O cache deve consultar em O(1) o par `(retiradas_médias, devoluções_médias)`.
Na ausência de chave, a decisão deve usar `(0.0, 0.0)`.

### Confiabilidade de status

`historico_status.csv` contém:

```text
timestamp,station_id,available_bikes,available_docks,status
```

Para cada mesma chave estação–hora–dia da semana, calcule:

```text
confiabilidade = leituras com status == "active" / total de leituras
```

Essa é uma frequência histórica, não conhecimento do status futuro. Na ausência
de chave, use `1.0`.

Grave perfis e confiabilidade no cache. Não grave dados de simulação, resultados
de decisões anteriores ou qualquer estado recebido por stdin.

## Modo `--passo`

Leia uma única linha JSON de stdin com `json.load(sys.stdin)`. A entrada terá a
forma:

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

A entrada real tem 80 estações e oito leituras de 15 minutos por estação em
`historico`. Aceite os campos `historico`, `clima` e `calendario` sem falhar; a
política abaixo usa somente o estado atual e o cache histórico permitido.

Em stdout, imprima somente um objeto JSON válido nesta forma:

```json
{"movimentacoes":[{"origem":"ST001","destino":"ST015","quantidade":5}]}
```

Retorne de zero a três objetos. Cada objeto deve usar IDs de estações ativas,
origem diferente do destino e quantidade inteira positiva fisicamente viável no
estado deixado pelas movimentações anteriores. Se ocorrer erro inesperado,
registre-o apenas em stderr, imprima `{"movimentacoes":[]}` e encerre com código
0.

## Política P13

Implemente exatamente a política abaixo. Ela combina médias históricas de demanda
por estação–hora–dia da semana, horizonte de duas horas e frequência histórica
de atividade para a segunda hora.

### Estado elegível

Trabalhe sobre uma cópia mutável somente das estações com `status == "active"`.
Guarde ID, capacidade, bicicletas e vagas. Estações `inactive` ou `maintenance`
não podem ser origem nem destino.

### Perfil e perda por estação

Para uma estação e instante `t`, consulte retiradas médias `r(t)` e devoluções
médias `a(t)` no cache. Entre 22:00 e 04:59, force `r(t) = 0`, pois a simulação
não aceita retiradas nesse período; devoluções continuam possíveis.

Para estoque `b`, capacidade `C`, retiradas previstas `r` e devoluções previstas
`a`, calcule:

```text
perda(b, C, r, a) = max(r - b, 0) + max(a - (C - b), 0)
```

A primeira parcela aproxima retiradas que podem falhar por falta de bicicleta; a
segunda aproxima devoluções que podem falhar por falta de vaga.

### Risco em duas horas

Para uma estação e estoque hipotético `b` depois de um movimento:

1. calcule a perda corrente com `r0` e `a0`;
2. estime o estoque da hora seguinte:

   ```text
   b1 = min(C, max(0, b - r0 + a0))
   ```

3. consulte `r1` e `a1` uma hora depois;
4. consulte `p_active`, a confiabilidade histórica da estação na hora seguinte;
5. calcule:

   ```text
   risco(b) = perda(b, C, r0, a0) + p_active * perda(b1, C, r1, a1)
   ```

O multiplicador de confiabilidade vale somente para a segunda hora: o status da
hora atual já está observado na entrada. Não tente ler ou inferir o status real
futuro de outubro.

### Busca de até três movimentações

Repita até três vezes, sempre com o estoque atualizado após a escolha anterior.
Para cada quantidade inteira `q` de 1 a 10:

1. para cada estação ativa com `b >= q`, calcule:

   ```text
   custo_origem = risco(b - q) - risco(b)
   ```

2. para cada estação ativa com vagas suficientes, calcule:

   ```text
   beneficio_destino = risco(b) - risco(b + q)
   ```

3. ordene origens por menor `custo_origem` e destinos por maior
   `beneficio_destino`;
4. combine as cinco melhores origens com os cinco melhores destinos para a mesma
   quantidade, ignorando origem igual a destino;
5. escolha o candidato com maior:

   ```text
   ganho_liquido = beneficio_destino - custo_origem
   ```

6. em empate, use a comparação determinística decrescente da tupla
   `(ganho_liquido, q, origem_id, destino_id)`;
7. se o melhor ganho for menor ou igual a zero, pare sem preencher ações
   artificialmente;
8. se for positivo, acrescente a movimentação e atualize na cópia mutável:

   ```text
   bikes_origem -= q
   docks_origem += q
   bikes_destino += q
   docks_destino -= q
   ```

O máximo de 10 bicicletas é uma limitação deliberada da busca: uma ablação local
que considerou todas as quantidades fisicamente possíveis piorou o resultado. Não
substitua-o por uma meta fixa de ocupação ou por percentual de capacidade.

### Fallback sem cache

Se `perfil_p13_cache.json` não existir ou for inválido, o modo `--passo` precisa
continuar válido e não deve reler CSVs. Use este fallback simples:

1. considere apenas estações ativas;
2. até três vezes, escolha a maior fração `available_bikes / capacity` como
   origem e a menor como destino;
3. mova `min(10, bikes_origem, docks_destino)` se origem e destino forem
   distintos, a fração da origem for estritamente maior e a quantidade for
   positiva;
4. atualize a cópia e repita.

Nunca escreva aviso em stdout.

## Robustez e desempenho

- O processo de `--passo` é novo a cada chamada e tem timeout de 30 segundos.
  No caminho normal, carregue somente o JSON compacto; não releia CSVs.
- Resolva todos os caminhos com `Path(__file__).resolve().parent`.
- Não suponha que a entrada de teste tenha exatamente 80 estações.
- Mantenha `available_bikes + available_docks == capacity` ao atualizar cópias.
- O avaliador aplica as ações em sequência; devolva-as já viáveis e ordenadas.
- Use `json.dumps` uma única vez para a saída de `--passo`.

## Testes de aceite da Parte 2

Depois de gerar a solução, executar dentro de `solucao/`:

```bash
python main.py --preparar
python main.py --passo < entrada.json | python -m json.tool
```

Depois, a partir da pasta que contém `dados/` e `avaliador/`:

```bash
python avaliador/avaliar.py solucao --ate 2024-10-03
python avaliador/avaliar.py solucao
```

O código não pode citar arquivos proibidos ou importar bibliotecas fora da
biblioteca padrão.

# Parte 1 — interface do operador (pendente de integração)

Quando os arquivos definitivos do front-end estiverem disponíveis, acrescente
aqui a especificação da interface e exija que o modo normal gere
`dados_interface.json`, inicie `http.server` em `127.0.0.1:8000` e sirva
`index.html`, `style.css` e `app.js`. A Parte 1 deverá responder claramente às
cinco perguntas do case e usar o mesmo motor P13 da Parte 2 para riscos e
movimentações.
