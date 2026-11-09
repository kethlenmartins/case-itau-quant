# Solução inicial

Ponto de partida para a Parte 2 do case. O `main.py` cumpre o contrato do avaliador (ver *Parte 2* em `descricao/CASE.md`), mas **nunca movimenta nada**: o score dele é igual ao do baseline. A estratégia fica por sua conta.

Esta pasta serve para você testar ideias localmente. Ela não faz parte da entrega: a solução avaliada é gerada a partir do seu `.md`.

## O que já está pronto

| Parte | O que faz |
|---|---|
| `--preparar` | sai logo com código 0. Use para montar um cache a partir de `../dados/` |
| `--passo` | lê o JSON do stdin, agrupa o `historico` por estação, chama `decidir()` e imprime só o JSON no stdout |
| `decidir()` | devolve `[]`. É aqui que entra a sua lógica |
| `limpar()` | mantém no máximo 3 movimentações e converte `quantidade` para inteiro |
| `log()` | escreve no stderr, para não quebrar o JSON do stdout |
| modo normal (`python main.py`) | só imprime uma mensagem. A Parte 1 (análise e interface) fica por sua conta |

`entrada_exemplo.json` é uma entrada real, gerada pelo avaliador: a chamada de 01/out/2024 08:00, sem nenhuma movimentação antes. Tem as 80 estações e 8 leituras de cada uma.

## Como testar

Dentro desta pasta:

```bash
python main.py --passo < entrada_exemplo.json
python main.py --passo < entrada_exemplo.json | python -m json.tool
```

No PowerShell: `Get-Content entrada_exemplo.json | python main.py --passo`.

Na pasta acima (a que contém `dados/` e `avaliador/`):

```bash
python avaliador/avaliar.py solucao_inicial --ate 2024-10-03
```

Para criar a sua versão, copie esta pasta para outra ao lado de `dados/` (por exemplo, `solucao/`), para que `../dados` continue funcionando.
