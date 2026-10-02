# VistoriaApp

Aplicação desktop para criação, organização e padronização de relatórios de vistoria de imóveis.

O VistoriaApp foi desenvolvido para simplificar o trabalho de vistoria imobiliária, permitindo preencher dados do imóvel, locador, locatário, ambientes, observações e fotografias em uma interface desktop e gerar um relatório editável em Word (`.docx`).

O aplicativo funciona localmente e não depende de servidor, banco de dados, login ou conexão com a internet.

## Funcionalidades

O MVP atual inclui:

- criação de vistoria inicial e vistoria final;
- cadastro dos dados da vistoria;
- cadastro do imóvel;
- cadastro de locador e locatário;
- criação dinâmica de ambientes;
- descrição e observações por ambiente;
- importação e organização de fotografias;
- legendas para fotos;
- reordenação de ambientes e fotografias;
- revisão dos dados antes da geração;
- geração de relatório Word editável;
- template Word customizado;
- fotos organizadas em duas colunas;
- numeração automática das fotos;
- autosave após 2 segundos de inatividade;
- autosave de segurança a cada 60 segundos;
- salvamento manual com `Ctrl+S`;
- backup local do projeto;
- recuperação manual de backup;
- armazenamento centralizado dos projetos;
- retenção local de projetos por tempo indeterminado;
- abertura da pasta do relatório gerado.

## Tipos de vistoria

Atualmente o aplicativo suporta dois tipos:

- Vistoria Inicial
- Vistoria Final

Algumas informações e seções do documento gerado são adaptadas automaticamente de acordo com o tipo selecionado.

## Armazenamento local

Os projetos são armazenados automaticamente em uma pasta gerenciada pelo aplicativo.

No Windows, a estrutura padrão é:

```text
Documentos/
└── VistoriaApp/
    ├── Projetos/
    │   └── vistoria-<id>/
    │       ├── projeto.json
    │       ├── projeto.backup.json
    │       ├── imagens/
    │       │   ├── originals/
    │       │   └── optimized/
    │       └── relatorios/
    │           └── relatorio-vistoria.docx
    └── Lixeira/
```

Os relatórios gerados permanecem independentes do aplicativo e podem ser editados normalmente no Microsoft Word ou em outro software compatível.

O envio para Google Drive ou outros serviços é feito manualmente pelo usuário.

## Política de retenção

Atualmente, os projetos são mantidos localmente por tempo indeterminado.
A política automática de retenção está desabilitada: não há limpeza na
inicialização, em background ou pelo menu do aplicativo.

Projetos existentes em `Projetos/` e `Lixeira/` permanecem intactos, sem
movimentação, restauração ou exclusão automática. A infraestrutura de limpeza
permanece reservada para uma decisão futura.

## Tecnologias

Principais tecnologias utilizadas:

- Python 3.13
- PySide6
- python-docx
- docxtpl
- Pillow
- pytest
- pytest-qt
- Ruff
- PyInstaller
- Docker
- Docker Compose

## Estrutura do projeto

```text
app/
├── models/
├── services/
├── ui/
└── utils/

assets/
templates/
tests/
scripts/
docs/
```

A arquitetura mantém separação entre:

- domínio;
- serviços de aplicação e infraestrutura;
- interface gráfica;
- utilitários compartilhados.

## Desenvolvimento local

### Requisitos

- Python 3.13
- Git

Opcionalmente:

- Docker
- Docker Compose

### Ambiente virtual no Linux

```bash
python3.13 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

### Ambiente virtual no Windows PowerShell

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
```

## Executando a aplicação

```bash
python -m app.main
```

## Testes

### Localmente

```bash
pytest
```

### Com Docker

```bash
docker compose build
docker compose run --rm test
```

Os testes de interface usam `pytest-qt`.

No ambiente Docker, o Qt é executado em modo offscreen:

```text
QT_QPA_PLATFORM=offscreen
```

## Lint

Com Docker:

```bash
docker compose run --rm lint
```

Ou com o ambiente local configurado:

```bash
ruff check .
```

## Desenvolvimento orientado a testes

O projeto utiliza TDD como princípio de desenvolvimento.

Para novas regras:

1. escrever o teste;
2. executar e confirmar a falha;
3. implementar o mínimo necessário;
4. executar os testes;
5. refatorar;
6. executar a suíte novamente.

## Geração de relatórios

O relatório Word é gerado utilizando o template:

```text
templates/modelo_relatorio.docx
```

Os recursos estáticos utilizados em runtime são resolvidos de maneira compatível tanto com desenvolvimento quanto com builds PyInstaller.

O relatório final é salvo em:

```text
<projeto>/relatorios/relatorio-vistoria.docx
```

## Build Windows

O projeto está preparado para distribuição com PyInstaller.

O build oficial deve ser realizado em Windows.

Configuração atual:

- PyInstaller;
- modo `onedir`;
- aplicação `windowed`;
- template Word incluído;
- logo incluído;
- sem UPX;
- sem `hiddenimports` adicionados manualmente.

Script de build:

```powershell
.\scripts\build_windows.ps1 -Clean
```

O executável será gerado em:

```text
dist\VistoriaApp\VistoriaApp.exe
```

Para detalhes sobre o processo de build:

```text
docs/build-windows.md
```

## Escopo do MVP

O VistoriaApp é propositalmente uma aplicação local.

Não fazem parte do MVP:

- autenticação;
- banco de dados;
- backend;
- sincronização em nuvem;
- integração com Google Drive;
- integração com Clicksign;
- envio de e-mail;
- assinatura eletrônica interna;
- aplicação web;
- aplicativo mobile;
- inteligência artificial;
- atualização automática.

## Documentação

Documentos principais:

- `docs/especificacao-mvp-v1.md`
- `docs/backlog-implementacao-mvp-v1.md`
- `docs/build-windows.md`

## Status

O MVP funcional está concluído e atualmente está na fase de validação do build Windows e preparação da distribuição.
