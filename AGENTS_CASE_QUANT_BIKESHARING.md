# Handoff para Codex — Case Quant: Redistribuição de Bicicletas em São Paulo

> **Objetivo deste documento:** registrar o entendimento do problema, a formulação matemática, as descobertas no código do avaliador, as decisões e hipóteses discutidas e um plano de execução para o agente Codex. **Comece pela análise exploratória dos dados (EDA), não pela implementação precipitada de uma estratégia final.**
>
> **Status:** planejamento técnico; **nenhuma análise empírica dos CSVs ou comparação de políticas foi realizada nesta conversa**. Não inventar resultados, taxas de melhoria ou conclusões empíricas.

## 1. Contexto, objetivo e entregáveis

Desafio de redistribuição de bicicletas compartilhadas com **80 estações em cinco zonas de São Paulo**. Em cada hora operacional, uma política observa o estado da rede e pode executar **até três transferências** de bicicletas entre estações. O objetivo é **minimizar o total de intenções de viagem não atendidas** (falhas de retirada e de devolução), sem simplesmente deslocar os problemas de uma estação para outra.

Há duas entregas finais distintas:

1. `solucao_[nome].md`: prompt autossuficiente para **Claude Sonnet 5.5** gerar o código completo da solução, incluindo `main.py`. A avaliação chama o modelo **uma única vez, em conversa nova, apenas com esse Markdown**: não contará com o enunciado, os CSVs ou o histórico desta conversa. O prompt precisa especificar os arquivos, interfaces, regras, algoritmos e formatos de saída com precisão. O código gerado só pode usar **Python 3.12 standard library** e HTML/CSS/JS nativos; sem pandas, numpy, scipy, Flask, React etc.
2. `analise_[nome].ipynb`: notebook **produzido pela candidata**, com análise de dados, modelagem, experimentos, comparações e conclusões, **executado e salvo com outputs**. Pode usar bibliotecas científicas. Colocá-lo em `notebook/`, lendo os CSVs por `../dados/`.

O `main.py` gerado deverá implementar:

- **Parte 1, interface:** `python main.py` inicia servidor `http.server` em `127.0.0.1:8000`, exibe estado da rede em um instante histórico (snapshot 2024-09-30 14:30), risco de escassez/lotação na próxima hora, até três transferências prioritárias, quantidades, justificativas, estimativas de perdas evitadas e medida de confiança baseada em validação fora da amostra. Separar estações inativas; indicar ocupação por zona e estações críticas (≤10% ou ≥90%).
- **Parte 2, política operacional:** `python main.py --passo` lê **um JSON do stdin** e escreve **somente** `{"movimentacoes":[{"origem":"ST001","destino":"ST015","quantidade":5}]}` no stdout, com 0–3 movimentações; logs apenas no stderr. Cada chamada inicia um processo novo e tem limite de **30 segundos**. Não iniciar servidor nesse modo.
- **Preparação opcional:** `python main.py --preparar`, uma vez, até **300 segundos**; pode construir cache a partir dos arquivos históricos autorizados. `--passo` deve funcionar mesmo sem cache.

**Prazo informado no case:** segunda-feira, **09/11/2026, 12h, horário de Brasília**. Priorizar uma solução válida, testável e documentada antes de sofisticações que ameacem a entrega.

## 2. Fontes e estrutura esperada

Arquivos de referência já examinados na conversa: `dicionario_dados.md`, `avaliador/motor.py`, `avaliador/avaliar.py`, `avaliador/corrida.py`. Se estiverem em outros diretórios, localize-os no repositório. O dicionário é a fonte dos esquemas e o motor é a fonte do comportamento operacional efetivo.

### Dados históricos permitidos para a solução gerada

- `estacoes.csv`: 80 estações; IDs, nomes, zonas, latitude, longitude, capacidade, tipo.
- `viagens.csv`: aproximadamente 165 mil viagens **realizadas** de julho a setembro/2024, com horários, origens, destinos e duração; **não inclui transferências operacionais nem todas as tentativas frustradas**.
- `historico_status.csv`: aproximadamente 707 mil observações a cada 15 minutos de julho a setembro/2024.
- `clima.csv`: condições meteorológicas horárias de julho a setembro/2024.
- `calendario.csv`: informações diárias de julho a novembro/2024.
- `snapshot_atual.csv`: estado de 80 estações em 30/09/2024 às 14:30.

### Dados de simulação — apenas para análise local, nunca lidos pela solução gerada

- `intencoes_simulacao.csv`: tentativas de viagem de outubro, inclusive as que podem falhar.
- `estado_inicial_simulacao.csv`, `status_simulacao.csv`, `clima_simulacao.csv`, `calendario_simulacao.csv`.
- `viagens_realizadas_baseline.csv`, `historico_status_baseline.csv`.

**Regra anti-leakage:** os arquivos de simulação podem ser usados no notebook para **avaliação retrospectiva**, análise de erros e comparação de políticas, mas **jamais** para previsão em tempo de decisão, treinamento de caches usados por `main.py` ou codificação de respostas específicas do cenário de outubro. O cenário oculto terá outros valores. Não ajustar a política diretamente às intenções futuras conhecidas.

## 3. Formalização matemática consolidada

### 3.1 Conjuntos, parâmetros e estados

- \(N=\{1,\dots,80\}\): estações; \(Z=\{1,\dots,5\}\): zonas.
- \(T\): instantes de decisão horária (05:00, 06:00, ..., 21:00), **17 decisões/dia**, 527 em outubro.
- \(s_i\): tipo da estação \(i\); \(C_i\): capacidade **fixa**, dada no cadastro.
- \(B_{i,t}\): bicicletas disponíveis; \(D_{i,t}\): vagas livres.
- \(a_{i,t}\in\{0,1\}\): estação ativa (status `active`) ou não (`inactive`/`maintenance`).

Invariantes:

\[
B_{i,t},D_{i,t}\in\{0,\ldots,C_i\},\quad B_{i,t}+D_{i,t}=C_i.
\]

**Validação por tipo** (não é decisão de capacidade):

| Tipo | Intervalo de capacidade |
|---|---|
| `standard` | 15–24 |
| `premium` | 20–30 |
| `express` | 12–18 |

O limite global é \(12\le C_i\le30\) para os tipos cadastrados, **não** \(0\le C_i\le30\): zero é permitido para **estoque ou vagas**, não para capacidade física. Conferir tipo/capacidade e usar sempre o valor efetivo de `capacity` fornecido pelo cadastro/entrada; não substituí-lo pelo máximo do tipo. `available_docks > 0` e `available_bikes > 0` **não** são requisitos para toda estação: estações vazias ou cheias são estados válidos que exigem atenção.

### 3.2 Contexto exógeno e previsão

Covariáveis candidatas: hora do dia, dia da semana, `is_weekend`, `is_holiday`, `school_vacation`, `special_event`, `weather_condition`, `temperature_c`, `precipitation_mm`; explorar também umidade, sensação térmica e outras variáveis se agregarem valor.

**Atenção:** o JSON de `--passo` usa o campo `calendario` montado pelo motor e inclui `date`, `day_of_week`, `day_name`, `is_weekend`, `is_holiday`, `holiday_name`, `special_event`; **não inclui `school_vacation`**. Não depender dessa chave em tempo de execução. O campo `clima` contém temperatura, sensação térmica, umidade, precipitação, vento, condição e UV quando disponível.

Estimativas por estação/hora:

\[
\widehat R_{i,t}=f_R(i,X_t,H_t),\qquad
\widehat A_{i,t}=f_A(i,X_t,H_t),
\]

com \(R\) = retiradas e \(A\) = chegadas/devoluções; \(H_t\) é o histórico disponível até \(t\). Alternativa probabilística inicial: contagens Poisson com intensidades \(\lambda^R_{i,t}\) e \(\lambda^A_{i,t}\), **a verificar empiricamente** (dispersão, heterogeneidade, dependência, eventos). As viagens históricas são **observadas/realizadas**, não demanda irrestrita; há censura por indisponibilidade. A chegada em uma hora pode vir de retirada anterior, e os destinos pretendidos podem ser redirecionados.

### 3.3 Decisões e viabilidade

Uma movimentação ordenada é \(m_k=(o_k,d_k,q_k)\), com origem, destino e quantidade inteira positiva. A política devolve uma **lista ordenada** \(M_t=(m_1,\ldots,m_K)\), \(0\le K\le3\). A ordem importa porque o motor aplica as transferências sequencialmente.

Formulação agregada auxiliar: \(x_{ij,t}\in\mathbb Z_{\ge0}\) quantidade de \(i\) para \(j\), \(y_{ij,t}\in\{0,1\}\) ativação de um par, com

\[
\sum_{i\ne j}y_{ij,t}\le3,\qquad
 y_{ij,t}\le x_{ij,t}\le M_{ij}y_{ij,t},
\]

\[
B^+_{i,t}=B_{i,t}-\sum_jx_{ij,t}+\sum_jx_{ji,t},\qquad
0\le B^+_{i,t}\le C_i,
\]

\[
y_{ij,t}\le a_{i,t},\quad y_{ij,t}\le a_{j,t},\quad i\ne j.
\]

**Importante:** restrições agregadas não asseguram viabilidade da **sequência**. Na implementação, manter cópia dos estoques e, para cada \(m_k\), verificar status ativo, IDs válidos, origem diferente de destino, \(q_k>0\), \(q_k\le B_{o_k}^{(k-1)}\) e \(q_k\le C_{d_k}-B_{d_k}^{(k-1)}\); atualizar os estoques após cada movimento. O motor **recorta** uma quantidade solicitada ao mínimo viável e ignora movimentos inválidos, mas a política deve produzir quantidades válidas de propósito.

### 3.4 Dinâmica e objetivo

Após as transferências, a rede evolui por eventos individuais. Aproximação agregada:

\[
B_{i,t+1}=B^+_{i,t}-R^{ok}_{i,t}+A^{ok}_{i,t},
\]

mas a ordem dos eventos, viagens em trânsito, falhas e redirecionamentos torna essa equação insuficiente como simulador fiel.

**Objetivo real:** minimizar o total de intenções não atendidas ao longo do cenário, não a distância da ocupação de 50%:

\[
\min_{\pi}\ \mathbb E\left[\sum_t\left(F_t^R+F_t^D\right)\right],
\]

onde \(\pi\) é a política que mapeia observações para até três movimentos. Uma intenção conta **no máximo uma falha**. Para decidir online, considerar o benefício esperado de uma **combinação inteira** de transferências:

\[
M_t^*=\arg\min_{M\in\mathcal F(S_t)}\widehat{\mathbb E}\left[\sum_{h=0}^{H-1}\gamma^h F_{t+h}\mid S_t,M\right].
\]

Horizontes \(H=1,2,3\) são **hipóteses a testar**, não decisões fechadas. Para \(H>1\), explicitar como as futuras decisões são tratadas (por exemplo, política de continuação ou reotimização/MPC); não fingir que o primeiro plano fica congelado. Às 21h, considerar devoluções noturnas e ausência de novas intervenções até as 05h.

A ideia central é que \(G(m_1,m_2,m_3)\) **não é em geral** \(G(m_1)+G(m_2)+G(m_3)\): movimentos competem por estoque/vagas e alteram riscos. Por isso a seleção conjunta das três movimentações é o foco de otimização.

## 4. Descobertas confirmadas no código do avaliador

### `motor.py`

- Constantes: `HORA_INICIO_OP=5`, `HORA_FIM_OP=22` (limite superior exclusivo), `MAX_MOV_HORA=3`, `JANELA_HISTORICO=8`, `TIMEOUT_PASSO=30`, `TIMEOUT_PREPARAR=300`.
- Em `Participante.montar_entrada`: JSON com `timestamp`, `estacoes` (80 linhas, cada uma com ID, nome, zona, capacidade, bikes, docks e status), `historico` (até oito leituras de 15 minutos por estação), `clima`, `calendario`.
- A leitura das `hh:00` ocorre **antes** das transferências da hora. A janela `historico` reflete a trajetória da **própria solução**, inclusive movimentos passados; não é o `historico_status.csv` histórico.
- Em `Participante.chamar`: cada `--passo` é subprocesso independente, lê JSON no stdin, valida JSON de saída, trunca `movimentacoes` às **primeiras três**. Timeout/erro equivale a não mover.
- Em `Participante.aplicar_movimentacoes`: valida par distinto, quantidade positiva, status `active`; aplica sequencialmente `real=min(qtd,bikes_origem,capacity_destino-bikes_destino)`. Inválidas são silenciosamente ignoradas. Não há custo logístico explícito, restrição de distância, nem exigência de mesma zona.
- Em `Participante.processar_eventos`: eventos em ordem temporal; **retiradas antes de devoluções em empate**. Retirada falha se estação não ativa ou sem bicicleta. Se retirada ocorrer, agenda devolução no horário previsto. Devolução falha se destino inativo ou sem vaga; bicicleta é redirecionada para a **estação ativa com vaga mais próxima por Haversine**, ou sai da rede se nenhuma existir. Cada intenção falha no máximo uma vez.
- A função de vizinhança para redirecionamento depende de latitude/longitude, mesmo que transferências operacionais não tenham custo de distância.
- `avancar_hora`: processa 15 em 15 minutos, e a chamada das 21h avança até as 05h do dia seguinte; no encerramento processa devoluções remanescentes.
- `verificar`: conservação do total de bicicletas considerando estoque, viagens em trânsito e bicicletas perdidas; score igual à contagem de intenções cujo resultado não é `realizada`.

### `avaliar.py` e `corrida.py`

- `avaliar.py` roda uma política e o baseline imóvel; opções `--ate`, `--verbose`, `--saida`, `--dados`.
- `corrida.py` compara **várias políticas no mesmo cenário**, cada uma com estoque próprio; exibe falhas, viagens salvas, número de movimentos, bicicletas transferidas e tempo. Pode usar `--ate` para testes curtos.
- `--saida` gera `viagens_realizadas_<nome>.csv`, `historico_status_<nome>.csv`, `movimentacoes_<nome>.csv` e equivalentes baseline. Úteis para diagnóstico de erros e ablação.
- O avaliador local usa intenções de outubro para **medir** o score. Ele **não pode** ser usado como oráculo de demanda futura dentro da solução; o cenário oculto será diferente.

## 5. Estratégia algorítmica proposta — hipóteses, não resultados

Prioridade de pesquisa: **selecionar conjuntamente até três pares origem–destino e suas quantidades**, maximizando redução esperada de falhas, com execução eficiente em Python padrão.

### 5.1 Pipeline candidato

1. **Estimar demanda** de retiradas e devoluções por estação e hora, usando histórico, calendário, clima e sinais recentes; calibrar com validação temporal. Considerar padrões origem–destino e duração para modelar chegadas.
2. **Estimar função de perda** para cada estação e nível de estoque, por exemplo \(L_i(b,t)\) = falhas esperadas associadas à estação se começar com \(b\) bikes, considerando retiradas e devoluções. Tratar com cuidado as interações entre estações e o redirecionamento; funções separáveis são apenas aproximação.
3. **Gerar candidatos**: estações que podem ceder bicicletas com baixo custo marginal e estações que se beneficiam de receber bicicletas; testar múltiplas quantidades inteiras viáveis, não apenas uma regra fixa de ocupação.
4. **Buscar a melhor combinação** de até três movimentos. Comparar (a) guloso com recálculo marginal, (b) busca combinatória restrita + busca local/beam search, (c) avaliação por simulação de cenários com sequências de eventos, se viável. Recalcular estoque e risco após cada movimento.
5. **Devolver JSON válido** e medir impacto no avaliador. Permitir **zero movimentos** se nenhuma intervenção tiver ganho esperado positivo.

### 5.2 Modelos e cuidados

- **Não assumir que 50% de ocupação é ótimo**: estoques desejáveis dependem do padrão de retiradas, chegadas e horário.
- **Não assumir que mais movimentos sempre ajudam**: o benefício marginal pode ser negativo.
- **Não assumir Poisson sem testar**; comparar médias históricas condicionais, suavização por estação/zona, correções de clima e modelos probabilísticos simples.
- **Não confundir saldo líquido de viagens com falhas**: dentro da hora, a ordem importa; duas estações com saldo líquido zero ainda podem apresentar falhas.
- **Não confundir demanda realizada com intenções**: `viagens.csv` contém apenas viagens realizadas, e pode subestimar demanda em estações frequentemente vazias/cheias.
- **Não presumir que otimização de uma hora é ótima para outubro**: decisões afetam estoque futuro. Testar horizontes 1–3 e efeitos noturnos.
- Se avaliar alternativas por Monte Carlo, reutilizar **os mesmos cenários aleatórios** para comparar políticas (common random numbers), garantindo reprodutibilidade e reduzindo ruído.
- Um simulador interno aproximado pode servir para **pontuar candidatos durante a decisão**; o **avaliador oficial continua sendo a referência final para backtesting**, evitando reconstruir todo o motor sem necessidade.
- O limite de 30 segundos por passo inclui inicialização do Python, carregamento de cache, previsão e otimização. Projetar tempo de execução para margem de segurança; considerar `--preparar` para pré-agregações e fallback simples.

### 5.3 Políticas de comparação e ablação

| ID | Política | Pergunta experimental |
|---|---|---|
| P0 | Sem transferências | Baseline |
| P1 | Rebalanceamento por ocupação | Quanto melhora uma regra simples? |
| P2 | Guloso por perdas previstas | Quanto agrega a previsão de demanda? |
| P3 | Seleção conjunta / busca combinatória | Quanto agrega otimizar as três decisões juntas? |
| P4 | Simulação de cenários + busca | A dinâmica estocástica melhora o score? |
| P5 | Horizonte multi-hora | Vale antecipar picos futuros? |

Estas são **candidatas**, não obrigação de implementar todas antes de obter uma primeira solução funcional.

## 6. Próxima tarefa imediata do Codex: EDA orientada à decisão

**Primeiro inspecione o repositório e os CSVs reais.** Não presuma que todos estão presentes. Leia o dicionário, confira os cabeçalhos e as datas, e produza uma análise reproduzível. O objetivo da EDA não é apenas visualizar dados: é fornecer estimativas e evidências para a função de perda e a seleção de transferências.

### 6.1 Auditoria e qualidade

- Conferir tamanho, colunas, tipos, intervalos temporais, duplicatas, faltantes, IDs desconhecidos e ordenação.
- Verificar capacidade por `station_type`; \(B+D=C\); status operacionais; cobertura das leituras de 15 minutos.
- Verificar viagens com horários inconsistentes, durações anômalas, estações de origem/destino inválidas, distribuição de viagens noturnas e por tipo de usuário.
- Verificar cobertura de clima e calendário, eventos especiais, feriados e possíveis descontinuidades.
- Distinguir `viagens.csv` de `intencoes_simulacao.csv` e registrar explicitamente o risco de censura.

### 6.2 Demanda e sazonalidade

- Contar retiradas e devoluções por **estação × hora × dia da semana**, com volume, média, mediana, quantis, variância, proporção de zeros e dispersão.
- Examinar diferenças entre dias úteis, fins de semana, feriados, eventos e faixas de temperatura/clima; não confundir correlação com causalidade.
- Identificar horários de pico, estações de saída/chegada, desequilíbrio líquido e pares origem–destino mais relevantes.
- Estimar distribuição de duração das viagens e fração de devoluções que chega em outra hora.
- Comparar demanda histórica e sinais recentes (últimas oito leituras), lembrando que mudanças de estoque também podem refletir transferências operacionais não registradas.

### 6.3 Risco de estoque e falhas

- Distribuição de ocupação por estação, zona, tipo e horário; tempo em faixas críticas (≤10%, ≥90%), separando inativas.
- Analisar relação entre ocupação e viagens realizadas, identificando indícios de demanda censurada.
- No notebook **somente para avaliação retrospectiva**, examinar baseline de outubro: falhas por tipo, hora, zona e estação; estações que concentram perdas; efeitos de redirecionamento; conservação de bicicletas e eventuais perdas físicas do sistema.
- Investigar se estações críticas por ocupação são também as de maior **potencial de falhas evitáveis** (não necessariamente).

### 6.4 Validação temporal e modelagem

- Criar baseline preditivo por estação/hora/dia da semana; suavizar grupos de baixa amostra usando zona ou média global.
- Fazer validação **cronológica** dentro de julho–setembro (por exemplo, treinar julho–agosto e validar setembro; avaliar cobertura efetiva antes de fixar datas).
- Métricas: MAE/RMSE para contagens, erro/bias por faixa horária e estação; se probabilístico, log-score/calibração e dispersão. Medir separadamente retiradas e devoluções.
- Testar impacto de clima e calendário contra modelo sem essas variáveis; atenção à extrapolação de eventos raros.
- Construir um protótipo de \(L_i(b,t)\) ou de score de movimentações e comparar políticas no avaliador.

### 6.5 Experimentos com avaliador

Após implementar uma **primeira política válida**, executar testes curtos e completos quando houver tempo:

```bash
python avaliador/avaliar.py caminho/para/solucao --ate 2024-10-03 --verbose
python avaliador/avaliar.py caminho/para/solucao --saida saida_local
python avaliador/corrida.py pasta_com_politicas --ate 2024-10-07 --sem-animacao
```

Rodar os comandos a partir da raiz do projeto, com os dados no local esperado. Medir: falhas totais, falhas de retirada, falhas de devolução, viagens salvas vs baseline, percentual de melhoria, número de transferências aplicadas, quantidade de bicicletas movidas, erros, tempo por chamada e evolução do score ao longo dos dias. Verificar resultados também em períodos distintos; não selecionar hiperparâmetros somente pelo score de outubro.

## 7. Interface: decisões de produto já discutidas

A interface da Parte 1 deve responder claramente:

1. **Como está a rede agora?** Total de bicicletas, estações críticas, ocupação por zona, inativas separadas.
2. **O que pode acontecer na próxima hora?** Risco quantificado de ficar vazia/cheia por estação; distinguir previsão de observação.
3. **Quais são as até três melhores movimentações?** Origem, destino, quantidade, ordem e justificativa.
4. **Por que elas ajudam?** Estimativa de falhas evitadas e trade-off na origem/destino.
5. **Quão confiável é a previsão?** Métrica obtida em validação fora da amostra, cobertura, limites e incerteza.

Priorizar interface clara, verificável e responsiva em HTML/CSS/JS puro, servida por `http.server`. A mesma lógica de previsão/otimização deve alimentar interface e `--passo`, respeitando diferenças entre snapshot histórico e entrada operacional.

## 8. Plano de execução recomendado

1. **Inspeção:** mapear pastas, ler arquivos de referência, verificar presença dos CSVs, registrar ambiente e comandos de execução.
2. **EDA reproduzível:** iniciar `analise_[nome].ipynb`, auditar dados, estudar padrões de demanda, risco e efeitos do calendário/clima; executar e salvar saídas.
3. **Baseline funcional:** criar `main.py --passo` mínimo válido, sem bibliotecas externas; rodar o avaliador para confirmar protocolo, tempo e integridade.
4. **Previsão simples e interpretável:** agregações históricas + suavização + fatores temporais e climáticos, validadas cronologicamente.
5. **Otimização:** implementar função de perda e candidatos; primeiro guloso marginal, depois seleção conjunta das três movimentações com busca limitada, sempre com viabilidade sequencial.
6. **Experimentos:** comparar P0/P1/P2/P3; acrescentar P4/P5 somente se houver ganho plausível e tempo suficiente; registrar evidências, limitações e riscos de overfitting.
7. **Interface:** usar o snapshot e a lógica consolidada para responder às cinco perguntas.
8. **Entrega:** escrever `solucao_[nome].md` autossuficiente para Claude Sonnet 5.5 e concluir `analise_[nome].ipynb` com outputs, interpretação e instruções de reprodução. **Não entregar `main.py` como substituto do Markdown pedido.**

## 9. Instruções de trabalho para o agente

- **Não assumir resultados de EDA ou ganhos de score que ainda não foram calculados.** Mostrar tabelas, gráficos e métricas efetivamente obtidos.
- Antes de grandes mudanças, comunicar diagnóstico, hipótese, experimento e critério de sucesso.
- Priorizar experimentos que respondam: **quais estações devem ceder/receber, quantas bicicletas e qual é a melhor combinação de até três transferências?**
- Manter separação rigorosa entre **dados históricos permitidos**, **observações online**, **dados de simulação apenas para avaliação** e **hipóteses**.
- Preservar reprodutibilidade: sementes, divisões temporais, comandos, versões e parâmetros.
- Evitar complexidade sem evidência; otimização combinatória e simulação só valem se melhorarem score, robustez e/ou interpretação dentro do limite de tempo.
- Documentar o que foi confirmado no motor, o que foi medido nos dados e o que permanece hipótese.

## 10. Perguntas em aberto para decidir com evidências

1. Qual é a melhor representação da demanda: contagens médias condicionais, Poisson, distribuição superdispersa ou cenários de eventos?
2. Como corrigir o viés de `viagens.csv`, que observa viagens realizadas, não todas as intenções?
3. Como estimar falhas de devolução considerando redirecionamentos e viagens em trânsito?
4. Qual é a melhor estratégia de geração de candidatos e de quantidades inteiras?
5. Qual é o ganho real da busca conjunta frente ao guloso, sob o mesmo modelo preditivo?
6. Qual horizonte (1, 2, 3 horas ou janela especial às 21h) oferece melhor trade-off entre antecipação e erro?
7. Como manter a política robusta a cenário oculto, eventos raros, dados ausentes e inicialização sem cache?

**Próxima ação esperada:** localizar e ler os CSVs, produzir o primeiro diagnóstico de EDA e apresentar achados que ajudem a escolher a função de perda e o método de seleção das três transferências. Não pular diretamente para uma solução complexa sem medir os padrões da rede.
