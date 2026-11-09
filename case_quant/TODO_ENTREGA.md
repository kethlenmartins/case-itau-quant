# To-do de entrega final

## Situação atual

- Política experimental candidata: **P13**, com 3.951 falhas no backtest local
  de outubro e 159 ms por chamada. Ela combina perfil de demanda por
  estação–hora–dia da semana, horizonte de duas horas e confiabilidade histórica
  de status para a segunda hora.
- Notebook: [notebook/analise_candidato.ipynb](notebook/analise_candidato.ipynb)
  contém EDA, validação temporal, ablações P1–P15 e células que respondem às cinco
  perguntas da interface no snapshot de 30/set às 14:30.
- Registro de experimentos: [EXPERIMENTOS.md](EXPERIMENTOS.md).
- Ainda **não existe** o artefato final `solucao_kethlen_martins_da_silva.md`. As pastas `p1` a
  `p15` são protótipos locais; elas não são a entrega da Parte 2 e não devem ser
  entregues como substitutas do Markdown solicitado.

## Nomenclatura definida

- [x] Nome definido: `kethlen_martins_da_silva`.
- [ ] Entregar com o mesmo sufixo: `solucao_kethlen_martins_da_silva.md` e
  `analise_kethlen_martins_da_silva.ipynb`.

Os itens abaixo usam esse nome definitivo.

---

## Parte 1 — Interface do operador

### Resultado esperado

Ao executar `python main.py` dentro de `solucao/`, o programa deve calcular a
análise do snapshot escolhido, subir `http.server` em `127.0.0.1:8000`, imprimir
o endereço e servir uma interface utilizável. Não basta gerar relatório no
terminal.

### Pendências

- [ ] Especificar no `solucao_kethlen_martins_da_silva.md` que a interface usará
  `snapshot_atual.csv` (30/09/2024 às 14:30) e exibirá claramente esse momento.
- [x] Criar o protótipo estático em `front/` (`index.html`, `style.css` e
  `app.js`), com as cinco perguntas e fallback demonstrativo.
- [x] Registrar requisitos de experiência, divulgação progressiva, acessibilidade
  e contrato de dados em `front/ESPECIFICACAO_IA.md` para incorporar ao prompt
  da solução.
- [ ] Pedir uma página HTML/CSS/JS responsiva e legível, gerada em arquivos
  completos e nomeados (por exemplo: `main.py`, `index.html`, `style.css`,
  `README.md`). O modelo que receber o Markdown não terá acesso ao case nem aos
  CSVs; todo schema necessário precisa estar na instrução.
- [ ] Especificar as cinco respostas obrigatórias na tela:

  1. estado observado da rede: bicicletas, vagas, ocupação, zonas, críticas
     (≤10% e ≥90%) e estações indisponíveis separadas;
  2. risco quantificado de retirada e devolução na próxima hora por estação;
  3. até três movimentações priorizadas, com origem, destino, quantidade e ordem;
  4. justificativa de cada ação por benefício no destino e variação de risco na
     origem, sem prometer resultado realizado;
  5. confiança: MAE/RMSE/viés de validação temporal e limitações explícitas.

- [ ] Pedir que a interface diferencie visualmente **observação**, **previsão** e
  **resultado retrospectivo**. O backtest de outubro não pode ser exibido como
  informação disponível no snapshot.
- [ ] Definir um formato seguro para levar os cálculos Python ao HTML (por
  exemplo, `dados_interface.json` gerado no modo normal e servido como arquivo
  estático, ou HTML já preenchido). Não exigir servidor externo, API ou biblioteca
  não padrão.
- [ ] Testar manualmente: iniciar o servidor, abrir `http://127.0.0.1:8000`,
  conferir as cinco respostas, legibilidade e ausência de erros no navegador.

### Como endereçar

O prompt da solução deve solicitar uma única implementação Python padrão que
reutilize o mesmo motor de perfis e perda de P13 para a interface e para
`--passo`. As células da seção 8 do notebook são a especificação visual e
numérica de referência para conferir a tela gerada.

---

## Parte 2 — Política de simulação

### Resultado esperado

`python main.py --passo` lê uma linha JSON, devolve **somente** um objeto JSON
com até três movimentos e encerra com código 0. `python main.py --preparar`
constrói o cache uma vez e também encerra sem iniciar o servidor.

### Pendências

- [ ] Escrever no `solucao_kethlen_martins_da_silva.md` a implementação autossuficiente de P13;
  não depender dos diretórios experimentais `p2_*` ou `p13_*`.
- [x] Preparar a especificação autossuficiente da Parte 2 em
  `ESPECIFICACAO_PARTE2.md`, pronta para integração ao Markdown final.
- [x] Inserir a Parte 2 e a estrutura de pastas recomendada no rascunho
  `solucao_kethlen_martins_da_silva.md`.
- [ ] Descrever todos os contratos que o Claude não conhecerá:
  diretório de trabalho `solucao/`, dados em `../dados/`, colunas usadas,
  estrutura do JSON de entrada, formato estrito da saída, máximo de três ações,
  aplicação sequencial e estações `active`.
- [ ] Exigir exclusivamente Python 3.12 e biblioteca padrão. Proibir de forma
  explícita `pandas`, `numpy`, instalações, serviços externos e leitura de
  arquivos de simulação/baseline.
- [ ] Especificar o cache de `--preparar`: médias de retiradas/devoluções por
  estação–hora–dia da semana e frequência histórica de `active` por
  estação–hora–dia da semana, usando apenas `viagens.csv` e
  `historico_status.csv`. Definir fallback seguro quando o cache não existir.
- [ ] Fixar, no prompt, a função de perda, a projeção de duas horas e a regra de
  busca gulosa de P13, incluindo atualização do estado após cada movimento. Isso
  reduz variação na geração única do código.
- [ ] Exigir que logs usem apenas `stderr`; `stdout` no modo `--passo` deve conter
  somente o JSON. O modo normal não pode ser chamado nos modos `--passo` e
  `--preparar`.
- [ ] Exigir que a solução não assuma estado em memória entre chamadas e não
  dependa de clima/calendário futuros. Pode ignorar sinais que foram rejeitados
  nas ablações (clima, zona, quantis e segmentação por estoque).
- [ ] Depois de gerar a solução a partir do Markdown, testar o contrato:

  ```bash
  cd solucao
  python main.py --preparar
  python main.py --passo < entrada.json | python -m json.tool
  cd ..
  python avaliador/avaliar.py solucao --ate 2024-10-03
  python avaliador/avaliar.py solucao --saida saida_final_local
  ```

- [ ] Verificar antes da entrega que a solução final não contém nomes de arquivos
  proibidos (`intencoes_simulacao`, `*_simulacao`, `*_baseline`) nem imports fora
  da biblioteca padrão.
- [ ] Registrar score, erros e tempo da solução gerada. O score de P13 local é
  referência de desenvolvimento, não garantia para o cenário oculto nem promessa
  a incluir na interface.

### Como endereçar

Produzir primeiro um rascunho preciso de `solucao_kethlen_martins_da_silva.md`, pedir ao modelo
arquivos completos com nome antes de cada bloco de código e validar a pasta
gerada como se fosse a correção. O Markdown deve permanecer abaixo de 50 KB.

---

## Parte 3 — Notebook de análise

### Resultado esperado

Um notebook executado e salvo em subpasta ao lado de `dados/`, com caminho
relativo, que mostra como os dados levaram à política escolhida e às respostas da
interface.

### Pendências

- [ ] Renomear ou copiar o notebook final para
  `notebook/analise_kethlen_martins_da_silva.ipynb`.
- [ ] Fazer leitura editorial final: remover repetições entre a seção 4
  (evidências iniciais da interface) e a seção 8 (síntese final), preservando a
  seção 8 como resposta definitiva após os experimentos.
- [ ] Confirmar que a introdução lista seção 8 e que a primeira célula registra
  as bibliotecas usadas no notebook.
- [ ] Conferir que as seções 1–3 cobrem qualidade, demanda, ocupação, status,
  clima/calendário e o risco de censura de `viagens.csv`.
- [ ] Conferir que a seção 5 apresenta validação cronológica, MAE, RMSE e viés
  de retiradas/devoluções, com treino anterior à validação.
- [ ] Manter as seções 6–7 como trilha de decisão: função de perda, P1–P15,
  critério de promoção e diagnóstico de erros residuais. O arquivo
  `EXPERIMENTOS.md` é referência complementar, não substitui essa narrativa.
- [ ] Confirmar que a seção 8 mostra outputs das cinco perguntas: estado,
  risco, movimentos, justificativas e confiança.
- [ ] Reiniciar o kernel e executar tudo em ambiente local; salvar os outputs.
  O notebook deve abrir sem células com erro e sem depender do diretório de onde
  o Jupyter foi iniciado.
- [ ] Fazer revisão final de clareza: separar explicitamente dados permitidos
  para a solução dos dados de simulação usados apenas para backtest no notebook.

### Como endereçar

Usar o notebook atual como base, executar de ponta a ponta e revisar apenas os
trechos redundantes ou provisórios. Não criar novos modelos sem hipótese e
critério de aceitação; a evidência atual já sustenta P13.

---

## Ordem recomendada de execução

1. [x] Escolher o nome e congelar a política P13 como referência.
2. [ ] Integrar a especificação da Parte 1 ao rascunho já criado em
   `solucao_kethlen_martins_da_silva.md`, tornando-o completo e autocontido para
   as Partes 1 e 2.
3. [ ] Gerar os arquivos da solução a partir do Markdown e validar os três modos
   (`normal`, `--preparar`, `--passo`). Corrigir o Markdown, não apenas o código
   gerado, se houver falha.
4. [ ] Rodar avaliador curto e completo na solução gerada; registrar o resultado.
5. [ ] Ajustar a interface gerada até responder claramente às cinco perguntas.
6. [ ] Fazer limpeza editorial e execução final do notebook.
7. [ ] Conferir os dois arquivos finais, os nomes idênticos, o tamanho do
   Markdown (<50 KB), a ausência de arquivos proibidos na lógica e a abertura do
   notebook com outputs salvos.

## Definition of done

- [ ] `solucao_kethlen_martins_da_silva.md` é autossuficiente, tem menos de 50 KB e pede arquivos
  completos/nomeados ao modelo.
- [ ] A solução gerada usa somente Python padrão + HTML/CSS/JS, inicia interface
  em `127.0.0.1:8000`, e passa o contrato de `--preparar` e `--passo`.
- [ ] A interface responde às cinco perguntas de forma clara e honesta.
- [ ] A solução gerada foi testada no avaliador local sem erros e com tempo bem
  abaixo de 30 s por chamada.
- [ ] `analise_kethlen_martins_da_silva.ipynb` está executado, salvo, lê caminhos relativos e
  documenta EDA, validação, experimentos e decisão.
- [ ] Os dois arquivos usam o mesmo nome válido e são os únicos artefatos
  exigidos para envio.
