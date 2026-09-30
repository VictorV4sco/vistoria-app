# VistoriaApp

Aplicação desktop para criação e padronização de relatórios de vistoria de imóveis.

## Estado atual

O projeto está no início do desenvolvimento do MVP v1.0.

## Requisitos de desenvolvimento

- Python 3.13
- Docker + Docker Compose (opcional, recomendado para testes)
- Git

## Rodando testes com Docker

```bash
docker compose build
docker compose run --rm test
```

## Rodando lint com Docker

```bash
docker compose run --rm lint
```

## Desenvolvimento local

Crie um ambiente virtual:

```bash
python3.13 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

Execute os testes:

```bash
pytest
```

Execute a aplicação:

```bash
python -m app.main
```

A janela inicial permite escolher Vistoria Inicial (padrão) ou Vistoria Final.
O botão **Continuar** cria um novo relatório em memória e abre uma tela provisória
com o tipo escolhido; **Voltar** retorna à seleção. Os formulários e o salvamento
ainda não estão conectados à interface.

Os testes de interface usam `pytest-qt`. No Docker, o Qt roda com
`QT_QPA_PLATFORM=offscreen`, sem precisar de um servidor gráfico. Para testar
localmente em um ambiente sem tela:

```bash
QT_QPA_PLATFORM=offscreen pytest
```

## Princípio de desenvolvimento

Para novas regras de negócio:

1. escrever o teste;
2. executar e confirmar que ele falha;
3. implementar o mínimo necessário;
4. executar os testes;
5. refatorar;
6. executar a suíte novamente.

## Documentação

- `docs/especificacao-mvp-v1.md`
- `docs/backlog-implementacao-mvp-v1.md`
