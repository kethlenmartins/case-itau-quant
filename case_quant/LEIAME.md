# Case Quant

Comece por `descricao/CASE.md`. Ele traz o problema, o formato da entrega
e como testar a sua solucao localmente.

| Pasta | Conteudo |
|-------|----------|
| `descricao/` | Enunciado (`CASE.md`) e dicionario de dados |
| `dados/` | Historico Jul-Set/2024, simulacao de Out/2024 e saidas do baseline |
| `avaliador/` | O avaliador usado na correcao (Python 3.12, so biblioteca padrao) |
| `solucao_inicial/` | Ponto de partida da Parte 2: cumpre o contrato, mas nunca movimenta nada |

O histórico de hipóteses, critérios e resultados das políticas P1–P15 está em
[`EXPERIMENTOS.md`](EXPERIMENTOS.md).

O checklist para transformar os protótipos nos dois artefatos finais está em
[`TODO_ENTREGA.md`](TODO_ENTREGA.md).

A especificação pronta para a Parte 2 da solução está em
[`ESPECIFICACAO_PARTE2.md`](ESPECIFICACAO_PARTE2.md).

Rode os comandos a partir desta pasta, por exemplo:

```bash
python avaliador/avaliar.py solucao_inicial --ate 2024-10-03
```
