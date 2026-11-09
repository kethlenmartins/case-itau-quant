# Registro de hipóteses e experimentos

Este documento registra a evolução das políticas avaliadas localmente. Ele é
complementar ao notebook: aqui estão as decisões experimentais e os resultados;
no notebook estão a auditoria dos dados, gráficos, validação temporal e análise
dos erros.

## Protocolo comum

- **Objetivo:** reduzir intenções não atendidas (falhas de retirada e devolução).
- **Dados de preparação:** somente arquivos históricos permitidos de julho a
  setembro (`estacoes.csv`, `viagens.csv`, `historico_status.csv`, `clima.csv`
  quando aplicável). Nenhuma política lê arquivos de simulação de outubro.
- **Avaliação:** `avaliador/avaliar.py`; outubro é usado exclusivamente como
  backtest local. O recorte inicial foi de 01 a 03/out, com 51 decisões.
- **Critério de promoção:** menos falhas que a política-controle no recorte,
  saída válida, zero erros e ampla margem para o limite de 30 s por chamada.
  Variantes promovidas são avaliadas em todo outubro (527 decisões).
- **Comparabilidade:** cada experimento altera um componente da política de
  referência e preserva a restrição de até três movimentos sequenciais e viáveis.
- **Cuidado:** os resultados abaixo não são estimativas de desempenho no cenário
  oculto. Eles orientam a escolha por evidência retrospectiva e simplicidade.

## Resumo de resultados

| Política | Melhor resultado medido | Tempo/chamada | Decisão |
|---|---:|---:|---|
| P0 — sem transferências | 29.332 falhas (outubro) | — | Referência do avaliador |
| P1 — ocupação | 5.372 falhas (outubro) | 72 ms | Superada |
| P2 — perda marginal | 4.748 falhas (outubro) | 611 ms | Superada |
| P3 — perda rápida | 4.477 falhas (outubro) | 146 ms | Controle inicial |
| P4 — beam conjunto | 362 falhas (01–03/out) | 92–99 ms | Rejeitada |
| P5 — quantidades físicas | 491 falhas (01–03/out) | 100 ms | Rejeitada |
| P6 — reserva dinâmica | 402 falhas (01–03/out) | 104 ms | Rejeitada |
| P7 — horizonte de 2 h | 4.046 falhas (outubro) | 119 ms | Controle final anterior |
| P8 — quantis empíricos | 354 falhas (01–03/out, P70/P75) | 107–128 ms | Rejeitada |
| P9 — perda Poisson | 321 falhas (01–03/out) | 141 ms | Rejeitada |
| P10 — noite às 21h | 306 falhas (01–03/out) | 213 ms | Rejeitada |
| P11 — suavização por zona | 343 falhas (01–03/out) | 154 ms | Rejeitada |
| P12 — clima corrente | 330 falhas (01–03/out) | 204 ms | Rejeitada |
| P13 — confiabilidade de status | **3.951 falhas (outubro)** | **159 ms** | Candidata atual |
| P14 — transição de status | 312 falhas (01–03/out) | 140 ms | Rejeitada |
| P15 — demanda por estoque | 480 falhas (01–03/out) | 248 ms | Rejeitada |

No mesmo outubro, P13 salvou 25.381 das 29.332 falhas do baseline (86,5%),
contra 25.286 (86,2%) de P7: 95 falhas a menos.

## Políticas base

### P1 — Rebalanceamento por ocupação

- **Hipótese:** uma regra direta de enviar bicicletas de estações muito cheias
  para muito vazias reduz falhas mesmo sem previsão de demanda.
- **Método:** regra baseada na ocupação observada, com origem acima de 80% e
  destino abaixo de 20%.
- **Critério de sucesso:** melhorar substancialmente o baseline imóvel, com
  movimentos válidos e execução rápida.
- **Resultado:** 5.372 falhas em outubro; 23.960 viagens salvas (81,7%); 72 ms.
- **Conclusão:** confirmou que rebalancear ajuda, mas a regra ignora hora,
  direção da demanda e custo de tirar bicicletas da origem.

### P2 — Perda marginal por perfil histórico

- **Hipótese:** perfis de retiradas e devoluções por estação–hora–dia da semana
  permitem trocar uma ocupação fixa por benefício marginal previsto.
- **Método:** média histórica e função de perda
  `max(retiradas - bikes, 0) + max(devoluções - vagas, 0)`; busca gulosa de
  origem, destino e quantidade viável.
- **Critério de sucesso:** superar P1 sem exceder o prazo operacional.
- **Resultado:** 4.748 falhas; 24.584 viagens salvas (83,8%); 611 ms.
- **Conclusão:** a previsão simples acrescenta valor, mas a busca exaustiva é
  mais lenta do que o necessário.

### P3 — Perda marginal com busca rápida

- **Hipótese:** o ganho de P2 pode ser preservado ao separar custo marginal da
  origem e benefício marginal do destino, mantendo apenas candidatos fortes.
- **Método:** mesma função de perda de P2, com pré-seleção de pontas e recálculo
  após cada movimento.
- **Critério de sucesso:** reduzir tempo de P2 sem perda relevante de score.
- **Resultado:** 4.477 falhas; 24.855 viagens salvas (84,7%); 146 ms.
- **Conclusão:** aprovada como novo controle: mais rápida e melhor que P2.

## Busca e restrições de quantidade

### P4 — Busca beam dos três movimentos

- **Hipótese:** avaliar combinações de movimentos em vez de escolhê-las apenas
  de forma gulosa melhora a interação entre as três transferências.
- **Método:** beam search com larguras 2 e 3 e listas de 5 ou 8 candidatos,
  preservando a mesma previsão de P3.
- **Critério de sucesso:** menos de 331 falhas no recorte de 01–03/out (P3).
- **Resultado:** 362 falhas nas duas configurações testadas; 92–99 ms.
- **Conclusão:** rejeitada. A busca adicional não compensou a qualidade dos
  candidatos fornecidos pela função de perda separável.

### P5 — Todas as quantidades fisicamente viáveis

- **Hipótese:** limitar as transferências a 10 bicicletas impede movimentos
  benéficos de maior porte.
- **Método:** removeu o limite de quantidade e avaliou toda a faixa viável de
  cada origem e destino.
- **Critério de sucesso:** superar P3 no recorte sem custo proibitivo.
- **Resultado:** 491 falhas, contra 331 de P3; 100 ms.
- **Conclusão:** rejeitada. Quantidades grandes amplificaram erros do perfil
  médio; o limite operacional implícito de P3 se mostrou mais robusto neste
  backtest, sem ser interpretado como regra universal.

### P6 — Reserva dinâmica

- **Hipótese:** reservar estoque e vagas em função da previsão reduz decisões
  excessivas, sem uma regra fixa de ocupação.
- **Método:** reserva baseada em demanda prevista e sua raiz quadrada para
  origem e destino.
- **Critério de sucesso:** superar P3 no recorte.
- **Resultado:** 402 falhas; 104 ms.
- **Conclusão:** rejeitada. A proteção adicional restringiu transferências que
  eram úteis segundo o avaliador.

## Horizonte e distribuição de demanda

### P7 — Horizonte de duas horas

- **Hipótese:** otimizar somente a hora corrente desloca problemas para a hora
  seguinte; incluir uma segunda hora produz escolhas mais estáveis.
- **Método:** risco = perda prevista na hora corrente + perda da hora seguinte,
  após propagar o estoque esperado e reotimizar a cada decisão.
- **Critério de sucesso:** superar P3 no recorte e confirmar no mês completo.
- **Resultado no mês:** 4.046 falhas; 25.286 viagens salvas (86,2%); 119 ms.
  P3 teve 4.477 falhas.
- **Conclusão:** aprovada. O horizonte curto trouxe ganho material sem ameaçar
  o orçamento de tempo.

### P8 — Perfis por quantis empíricos

- **Hipótese:** médias subestimam picos; quantis de retiradas e devoluções
  devem proteger melhor estações voláteis.
- **Método:** substituiu as médias por quantis das contagens históricas,
  incluindo zeros, por estação–hora–dia da semana. Foram testados P50, P70 e P75.
- **Critério de sucesso:** menos de 306 falhas (P7) e sem trocar falhas de
  retirada por devoluções.
- **Resultado:** P50: 384 falhas; P70/P75: 354 falhas; 107–128 ms.
- **Conclusão:** rejeitada. A amostra de aproximadamente 13 observações por
  combinação tornou P70 e P75 equivalentes e não superou a média.

### P9 — Perda esperada Poisson

- **Hipótese:** uma perda esperada sobre a distribuição de contagens modela o
  risco de ruptura melhor que aplicar perda apenas à média.
- **Método:** aproximou retiradas e devoluções por Poisson com média histórica e
  calculou tabelas de perda de cauda para cada estoque possível.
- **Critério de sucesso:** superar P7 no recorte.
- **Resultado:** 321 falhas; 1.782 viagens salvas; 141 ms.
- **Conclusão:** rejeitada. A hipótese probabilística paramétrica não produziu
  melhores pares de movimentação nesta amostra.

### P10 — Horizonte noturno às 21h

- **Hipótese:** às 21h não há novas intervenções até 05h; antecipar devoluções
  noturnas evita lotação no encerramento.
- **Método:** apenas às 21h, estendeu o horizonte até 05h, zerando retiradas
  noturnas conforme a dinâmica do avaliador; nas demais horas manteve 2 h.
- **Critério de sucesso:** reduzir falhas noturnas e melhorar P7.
- **Resultado:** 306 falhas e 1.797 viagens salvas, exatamente como P7; 213 ms.
- **Conclusão:** rejeitada. Não alterou o score e quase dobrou o custo por passo.

## Sinais adicionais

### P11 — Suavização por zona

- **Hipótese:** combinar perfil local com a média da zona reduz ruído em
  estação–hora–dia com poucas observações.
- **Método:** 80% do perfil da estação e 20% do perfil da zona, mantendo P7.
- **Critério de sucesso:** superar 306 falhas no recorte.
- **Resultado:** 343 falhas; 1.760 viagens salvas; 154 ms.
- **Conclusão:** rejeitada. A regularização diluiu diferenças locais que eram
  relevantes para a decisão.

### P12 — Ajuste por clima corrente

- **Hipótese:** a condição meteorológica observada no instante contém sinal
  para ajustar demanda agregada de retirada e devolução.
- **Método:** calculou multiplicadores históricos por condição–hora–dia da
  semana; aplicou-os apenas à hora corrente, pois clima futuro não está no JSON
  operacional.
- **Critério de sucesso:** superar P7 sem usar previsão futura de clima.
- **Resultado:** 330 falhas; 1.773 viagens salvas; 204 ms.
- **Conclusão:** rejeitada. O sinal agregado não reposicionou bem bicicletas
  entre estações no recorte.

### P13 — Confiabilidade marginal de status

- **Hipótese:** parte importante do erro residual vem de estações que estarão
  indisponíveis na hora seguinte; descontar seu risco futuro evita movimentos
  com benefício operacional improvável.
- **Método:** em P7, pondera a perda projetada da segunda hora pela frequência
  histórica de `active` por estação–hora–dia da semana. O status futuro não é
  consultado na decisão.
- **Critério de sucesso:** superar P7 no recorte e confirmar no mês completo.
- **Resultado:** 304 falhas no recorte, contra 306 de P7; no mês, 3.951 falhas,
  25.381 viagens salvas (86,5%) e 159 ms por chamada.
- **Conclusão:** aprovada como política candidata. A validação mensal melhora
  P7 em 95 falhas, mantendo margem ampla de tempo.

### P14 — Transição condicional de status

- **Hipótese:** condicionado ao fato de uma estação estar ativa agora, a
  probabilidade `P(active em t+1 | active em t)` é mais informativa que a
  frequência marginal usada em P13.
- **Método:** substituiu o peso de P13 pela frequência histórica de transição
  ativa para ativa, por estação–hora–dia da semana.
- **Critério de sucesso:** superar P13 no recorte.
- **Resultado:** 312 falhas; 1.791 viagens salvas; 140 ms.
- **Conclusão:** rejeitada. A amostra por combinação é pequena para a transição;
  a frequência marginal de P13 foi mais robusta.

### P15 — Demanda condicionada ao estoque

- **Hipótese:** a demanda realizada varia com a ocupação observada no início da
  hora; perfis condicionados ao estoque melhorariam previsões nos extremos.
- **Método:** dividiu a ocupação relativa em quatro faixas e estimou médias por
  estação–hora–dia–faixa, com fallback ao perfil-base quando ausente.
- **Critério de sucesso:** superar P13 no recorte.
- **Resultado:** 480 falhas; 1.623 viagens salvas; 248 ms.
- **Conclusão:** rejeitada. A segmentação elevou a variância e também mistura
  demanda latente com viagens censuradas por indisponibilidade de bikes ou vagas.

## Próximo uso deste registro

P13 é a referência para a Parte 1 e para a futura solução final. As políticas
rejeitadas permanecem úteis como ablações: justificam por que a solução não usa
busca beam, quantis, clima ou segmentação agressiva. Antes da entrega, convém
reexecutar P13 após consolidar o `main.py` final e registrar esse resultado sem
alterar o protocolo de preparação.
