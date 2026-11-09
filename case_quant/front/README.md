# Protótipo da interface

Este diretório contém o front-end local da Parte 1. Ele não é, por si só, a
entrega: a entrega será `solucao_kethlen_martins_da_silva.md`, contendo os
arquivos completos que o modelo deverá gerar.

A especificação de experiência e de restrições para gerar ou revisar a interface
está em [ESPECIFICACAO_IA.md](ESPECIFICACAO_IA.md).

Para pré-visualizar o protótipo:

```bash
cd front
python -m http.server 8000 --bind 127.0.0.1
```

Abra `http://127.0.0.1:8000`. O arquivo `dados_interface.json` atual é uma
demonstração baseada no snapshot analisado no notebook. Na solução final,
`main.py` deverá gerar esse JSON com dados e recomendações reais antes de subir o
mesmo servidor.
