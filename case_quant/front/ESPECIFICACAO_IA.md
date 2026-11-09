# Especificação para a IA desenhar o front-end

## Papel e contexto

Você está desenhando a interface local de apoio à decisão para a operação de um
sistema de bicicletas compartilhadas em São Paulo. A pessoa usuária é do time de
operações: conhece a rede e precisa tomar decisões rápidas, mas não precisa
conhecer modelos estatísticos, código, MAE ou a função de perda.

A tela não é um relatório analítico nem um painel de engenharia. Ela existe para
responder, em poucos segundos, a estas perguntas:

1. Como a rede está agora?
2. Onde há maior risco na próxima hora?
3. Quais até três movimentações devem ser feitas, em qual ordem?
4. Por que cada uma ajuda?
5. Quão confiável é essa recomendação e quais são seus limites?

O momento analisado deve estar sempre visível. A referência inicial é o snapshot
de 30/09/2024 às 14:30, mas a tela deve renderizar qualquer instante fornecido
pelo arquivo local de dados.

## Restrições técnicas obrigatórias

- Entregar somente arquivos estáticos: `index.html`, `style.css` e `app.js`.
- Usar HTML5, CSS3 e JavaScript nativo compatível com navegadores modernos.
- Não usar React, Vue, Bootstrap, Tailwind, jQuery, TypeScript, npm, bundler,
  CDN, fontes externas, imagens remotas, APIs externas ou qualquer dependência.
- A página será servida localmente por `http.server` em `127.0.0.1:8000`.
  Portanto, todos os caminhos devem ser relativos e funcionar sem internet.
- Carregar apenas `dados_interface.json` no mesmo diretório, usando `fetch`.
  Se o arquivo estiver ausente ou inválido, mostrar uma mensagem de estado
  compreensível; não deixar a tela branca e não usar dados inventados em produção.
- Não implementar botões que executem a movimentação. A tela recomenda; a
  execução operacional acontece fora dela.
- Não expor arquivos históricos, CSVs, caminhos de máquina, código Python ou
  detalhes internos do modelo.
- Usar HTML semântico, foco visível, contraste adequado, rótulos textuais e
  navegação por teclado. Cor não pode ser a única forma de comunicar alerta.

## Princípios de experiência

### Decisão primeiro, detalhe quando solicitado

O topo da tela deve permitir que alguém identifique o estado da rede e as três
ações recomendadas sem rolar a página em um monitor desktop comum. Os detalhes
técnicos devem estar disponíveis, mas fechados por padrão.

Use divulgação progressiva:

- Ao lado de cada índice ou título ambíguo, usar um botão discreto `?` com
  `aria-label`, que abre explicação curta em tooltip acessível ou painel lateral.
- Incluir um botão “Como esta recomendação foi calculada?” que abre um
  `<dialog>` ou acordeão com linguagem simples. Nunca usar hover como único modo
  de acesso à explicação.
- Oferecer “Ver detalhes” para tabelas completas; no estado inicial, mostrar
  somente os itens mais acionáveis.
- Manter a seção “Limitações” visível, porém compacta. Um botão “Entender os
  limites” pode expandir explicações mais completas.

Evitar jargão na camada principal. Preferir “risco de ficar sem bicicleta” a
“perda de retirada”; se o nome técnico for necessário, apresentá-lo somente na
ajuda contextual.

### Linguagem operacional e honesta

- Diferenciar visualmente **observado agora** de **estimativa para a próxima
  hora** e de **qualidade histórica da previsão**.
- Usar “risco estimado”, “ganho previsto” e “pode reduzir”; nunca “garantido”,
  “certeza” ou “evita X viagens” como promessa.
- Quando o risco for zero, escrever “sem risco estimado neste horizonte”, não
  “sem risco”.
- Para estação indisponível, escrever “fora de operação” e não misturá-la a uma
  estação vazia ou cheia.
- Formatar números em português do Brasil: `43,2%`, `0,708`, `1.624`.

## Hierarquia e fluxo da tela

### 1. Barra de contexto fixa no topo

Exibir:

- nome do produto: “Central de Redistribuição”;
- data e hora do snapshot;
- período previsto: por exemplo, “Próxima janela: 15:00–16:00”;
- selo discreto “Dados locais” ou “Análise do snapshot”.

Não ocupar o topo com navegação complexa, avatar, notificações artificiais ou
elementos de marketing.

### 2. Resumo operacional — pergunta 1

Logo abaixo, mostrar de quatro a cinco cartões compactos:

- bicicletas disponíveis;
- vagas disponíveis;
- ocupação total da rede;
- estações ativas e fora de operação;
- estações críticas por baixa e alta ocupação.

Cada cartão precisa de título claro e, quando aplicável, botão `?` explicando a
medida. Use números grandes, rótulos curtos e leitura rápida. Não usar gráficos
ornamentais.

Em seguida, apresentar ocupação por zona em barras horizontais rotuladas. Cada
linha deve mostrar zona, percentual, estações ativas e quantidade de estações
críticas. O gráfico deve funcionar também em escala de cinza: percentual e texto
são obrigatórios.

Ao lado ou abaixo, colocar uma lista curta das estações críticas observadas,
separando:

- “quase sem bicicletas”;
- “quase sem vagas”;
- “fora de operação”.

Mostrar inicialmente no máximo cinco itens de cada categoria e disponibilizar
“ver todas”.

### 3. Risco de indisponibilidade — pergunta 2

Criar um bloco intitulado “O que pode acontecer na próxima hora?”. Explicar em
uma frase: “Estimativa baseada no padrão histórico desta estação, neste horário e
dia da semana.”

Exibir inicialmente uma tabela curta ou lista priorizada com no máximo seis
estações. Para cada item, mostrar:

- estação e zona;
- estoque atual em texto (“1 bicicleta · 21 vagas”);
- risco estimado de ficar sem bicicleta;
- risco estimado de ficar sem vaga;
- risco total no horizonte de duas horas.

Ordenar por risco total. Usar um indicador textual além de cor: “alto”, “médio”
ou “baixo”, quando esses rótulos forem derivados dos dados recebidos. Caso não
existam categorias no JSON, mostrar apenas números e a ordenação, sem inventar
limiares fixos.

O botão `?` dessa seção precisa explicar que o número é uma quantidade esperada
de falhas, não uma probabilidade nem um número de pessoas já perdidas.

### 4. Ações prioritárias — perguntas 3 e 4

Este é o bloco visualmente dominante da tela. Apresentar até três cartões, em
ordem explícita: “1º movimento”, “2º movimento”, “3º movimento”.

Cada cartão deve ter:

- estação prioritária destacada — o destino se a ação abastece uma estação em
  risco de esvaziar; a origem se alivia uma estação em risco de lotar;
- rota legível `ORIGEM → DESTINO`, incluindo nome, ID e zona nas duas pontas;
- quantidade inteira de bicicletas em destaque;
- ganho líquido **previsto** no horizonte de duas horas;
- justificativa em uma ou duas frases de linguagem natural;
- um detalhe expansível com “efeito na origem” e “efeito no destino”.

Se houver menos de três recomendações, não criar cartões vazios. Mostrar uma
mensagem como “Não há outra movimentação com ganho previsto positivo”.

Caso a variação de risco da origem seja negativa, explicar: “Esta retirada também
reduz o risco de falta de vagas na origem.” Nunca chamá-la de custo negativo.
Caso seja positiva, chamar de “trade-off na origem” e informar o aumento previsto
de risco.

### 5. Confiança e limites — pergunta 5

Mostrar uma faixa ou cartão no final, mas ainda facilmente visível, contendo:

- métricas de validação fora da amostra: MAE, RMSE e viés de retiradas e
  devoluções, com texto curto sobre período de treino e validação;
- um rótulo “qualidade histórica da previsão”, nunca uma porcentagem inventada
  de confiança;
- três limitações sempre visíveis, em linguagem simples:
  1. viagens históricas incluem apenas trajetos realizados;
  2. a demanda futura é estimada, não observada;
  3. indisponibilidades futuras de estação são incertas.

O botão “Entender os limites” deve revelar o texto detalhado enviado no JSON.
Essa área deve ser sóbria e informativa, sem aparência de aviso de erro se a
recomendação estiver válida.

## Sistema visual

- Estética: painel operacional calmo, confiável e direto; não usar visual de
  trading, gamificação, mapa decorativo ou cartões excessivos.
- Fundo claro de baixo contraste, painéis brancos, tipografia sem serifa do
  sistema e bastante espaço em branco.
- Cor principal: verde escuro para estado normal e recomendações; âmbar para
  atenção; vermelho para risco alto; azul ou cinza para previsão/informação.
- Manter contraste AA. Sempre acompanhar cor de texto, ícone ou rótulo.
- Usar ícones somente se forem desenhados em CSS/HTML ou caracteres Unicode
  simples e se acrescentarem significado. Não buscar bibliotecas de ícones.
- Desktop: largura máxima de aproximadamente 1.200–1.280 px, grade em duas
  colunas para blocos secundários e três cartões de movimento.
- Mobile: uma coluna, cartões empilhados, tabela com rolagem horizontal limitada
  ou versão em lista; nenhuma informação pode depender de hover.

## Contrato de dados esperado

O JavaScript deve renderizar a interface a partir de um objeto JSON local com
esta forma. Campos extras devem ser ignorados de forma segura; listas vazias
devem produzir estados vazios compreensíveis.

```json
{
  "meta": {
    "timestamp": "2024-09-30 14:30:00",
    "periodo_previsao": "15:00–16:00",
    "fonte": "snapshot_atual.csv"
  },
  "rede": {
    "bicicletas": 702,
    "vagas": 922,
    "capacidade": 1624,
    "ocupacao_pct": 43.2,
    "estacoes_ativas": 77,
    "estacoes_indisponiveis": 3,
    "criticas_baixas": 13,
    "criticas_altas": 9
  },
  "zonas": [
    {"nome": "Centro", "ocupacao_pct": 53.8, "ativas": 14, "criticas": 5}
  ],
  "criticas": [
    {"station_id": "ST010", "name": "Mercado Municipal", "zone": "Centro", "ocupacao_pct": 0, "tipo": "baixa"}
  ],
  "indisponiveis": [
    {"station_id": "ST099", "name": "Exemplo", "zone": "Centro", "status": "maintenance"}
  ],
  "riscos": [
    {"station_id": "ST043", "name": "Parque Villa-Lobos", "zone": "Zona Oeste", "bikes": 1, "docks": 21, "retirada_1h": 1.714, "devolucao_1h": 0, "total_2h": 4.0}
  ],
  "movimentacoes": [
    {"ordem": 1, "origem": {"id": "ST006", "nome": "Praça da Liberdade", "zona": "Centro"}, "destino": {"id": "ST043", "nome": "Parque Villa-Lobos", "zona": "Zona Oeste"}, "quantidade": 10, "variacao_risco_origem": -3.643, "beneficio_destino": 4.0, "ganho_liquido": 7.643, "justificativa": "..."}
  ],
  "validacao": {
    "periodo_treino": "jul–ago/2024",
    "periodo_validacao": "set/2024",
    "retiradas": {"mae": 0.699, "rmse": 1.061, "vies": 0.017},
    "devolucoes": {"mae": 0.708, "rmse": 1.125, "vies": 0.017}
  },
  "limitacoes": ["texto curto", "texto curto", "texto curto"],
  "detalhes_modelo": ["texto detalhado opcional"]
}
```

## Critérios de aceite

- Uma pessoa não técnica entende as três ações recomendadas sem abrir nenhuma
  ajuda contextual.
- Cada índice tem explicação acessível sob demanda, sem texto técnico poluindo a
  visualização inicial.
- As cinco perguntas do case são encontradas por título ou rótulo claro.
- A tela funciona sem internet, sem dependências e sem erros no console quando
  `dados_interface.json` existe.
- A ausência de recomendações, estações críticas ou dados adicionais não quebra
  o layout.
- A interface deixa explícitas as limitações e não confunde previsão com fato.
- O resultado final contém arquivos completos e nomeados, prontos para serem
  incluídos no `solucao_kethlen_martins_da_silva.md`.
