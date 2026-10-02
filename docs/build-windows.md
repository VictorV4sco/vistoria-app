# Build Windows — VistoriaApp

O build Windows deve ser feito no Windows. O PyInstaller não faz cross-compilation:
um build Linux não é equivalente a um executável Windows.

## Requisitos e preparação

- Windows 10/11 e Python 3.13 (o projeto exige `>=3.13,<3.14`).
- Ambiente virtual dedicado, preferencialmente Python e Windows de 64 bits.
- Checkout completo, incluindo `templates/modelo_relatorio.docx` e `assets/logo_alger.png`.
- PowerShell e dependências de desenvolvimento/build instaladas explicitamente.

Na raiz do projeto, no PowerShell:

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev,build]"
python -m app.main
```

Se a política local bloquear scripts, libere-os apenas para a sessão, conforme a
política da empresa: `Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned`.
O script de build não instala dependências nem altera essa política.

## Testes e build

```powershell
python -m pytest
python -m ruff check .
.\scripts\build_windows.ps1
```

O script executa os testes antes do build e interrompe ao encontrar falhas.
Opções: `-Clean` remove somente `build/` e `dist/` na raiz deste checkout;
`-SkipTests` pula os testes quando já tiverem sido executados nesse ambiente.

```powershell
.\scripts\build_windows.ps1 -Clean
# Alternativa direta, após os testes:
python -m PyInstaller --noconfirm VistoriaApp.spec
```

Resultado: `dist\VistoriaApp\VistoriaApp.exe`. Distribua **toda a pasta
`dist\VistoriaApp`**, incluindo `_internal`; copiar apenas o `.exe` não funciona.
O primeiro build usa **onedir**, **windowed** (sem console), sem UPX e com ícone padrão.
Ainda não há instalador.

## Recursos e dados

O `.spec` inclui somente os dois recursos estáticos acima como dados da aplicação.
O PyInstaller coleta as dependências importadas e seus recursos por hooks padrão,
incluindo Qt/PySide6, Pillow, docxtpl e python-docx; não há hiddenimports manuais.
A logo também já está incorporada ao template Word. O conteúdo do template é preservado.

`resource_path` resolve recursos pela raiz do código em desenvolvimento e por
`sys._MEIPASS` no bundle, sem depender da pasta atual nem criar diretórios.
Recursos são tratados como somente leitura. Os dados continuam em
`Documentos/VistoriaApp/Projetos` e `Documentos/VistoriaApp/Lixeira`, obtidos via
`QStandardPaths` (inclusive quando Documentos estiver redirecionado).
O Word permanece em `<projeto>/relatorios/relatorio-vistoria.docx`, fora do bundle.

Testes, documentos de desenvolvimento, segredos e projetos de clientes não são
incluídos como dados do bundle. Build, dist e artefatos gerados são ignorados pelo Git.

## Validação no Windows

Os testes no Ubuntu verificam caminhos simulados e documentos, mas não validam
DLLs nem plugins Qt de Windows. Após gerar o build:

1. Copie a pasta distribuível para um Windows 10/11 sem Python instalado.
2. Abra o `.exe` a partir de outra pasta e de um atalho.
3. Crie/abra uma vistoria, adicione JPG/PNG, confira miniaturas e gere o Word.
4. Confira logo, termos e layout; use “Abrir pasta do relatório”.
5. Confirme que projetos e relatórios estão em Documentos, fora de `dist`.

Se houver falha de plugin Qt ou de importação, inspecione as mensagens do build e
`build/VistoriaApp/warn-VistoriaApp.txt` antes de acrescentar hooks/hiddenimports.
A pasta `_internal` precisa acompanhar o executável. Não há validação Windows
concluída apenas por passar testes no Linux.

Referências: [recursos em runtime](https://pyinstaller.org/en/stable/runtime-information.html)
e [arquivos spec](https://pyinstaller.org/en/stable/spec-files.html).
