# Especificação do MVP v1.0 — VistoriaApp

## 1. Visão geral

O **VistoriaApp** será uma aplicação desktop simples para padronização e geração de relatórios de vistoria de imóveis.

O objetivo principal é permitir que funcionários da empresa criem relatórios de vistoria de forma organizada, consistente e rápida, sem depender de edição manual complexa no Word.

A aplicação será executada localmente em Windows, sem necessidade de banco de dados, servidor, login ou conexão com a internet.

Ao final do preenchimento, o sistema deverá gerar um arquivo `.docx` editável e padronizado, pronto para eventual revisão e posterior envio ao Clicksign para assinatura eletrônica.

---

## 2. Objetivos do sistema

O sistema deverá permitir:

- criar uma nova vistoria;
- abrir e continuar uma vistoria existente;
- preencher dados gerais da vistoria;
- preencher dados do imóvel;
- preencher dados do locador;
- preencher dados do locatário;
- informar o responsável pela vistoria;
- criar, editar, duplicar, excluir e reordenar ambientes/seções;
- adicionar descrição e observações por ambiente;
- adicionar fotos por ambiente;
- adicionar legendas às fotos;
- reordenar fotos;
- salvar o progresso automaticamente;
- recuperar projetos após fechamento inesperado;
- manter projetos locais sem banco de dados;
- mover projetos inativos para uma lixeira interna;
- restaurar projetos da lixeira;
- excluir definitivamente projetos antigos;
- gerar um relatório final em Word (`.docx`);
- permitir que o usuário escolha onde salvar o Word;
- manter o documento final editável;
- funcionar de forma independente em cada computador.

---

## 3. Escopo do MVP

### 3.1 Incluído no MVP

O MVP deverá incluir:

- aplicação desktop para Windows;
- instalador `.exe`;
- funcionamento offline;
- armazenamento local;
- autosave;
- recuperação após falha;
- projetos recentes;
- lixeira interna;
- geração de Word;
- template de relatório;
- fotos com legendas;
- numeração automática das fotos;
- reordenação de ambientes e fotos;
- tela de revisão;
- validações;
- logs locais de erro;
- versionamento dos projetos;
- configurações locais da aplicação.

### 3.2 Fora do MVP

Não fazem parte da versão 1.0:

- usuários e senhas;
- banco de dados;
- servidor;
- API remota;
- armazenamento em nuvem;
- sincronização entre computadores;
- edição simultânea;
- painel web;
- aplicativo mobile;
- integração automática com Clicksign;
- envio de e-mail;
- assinatura dentro da aplicação;
- geração automática de PDF como requisito;
- inteligência artificial;
- reconhecimento de imagens;
- CRM;
- gestão financeira;
- gestão de contratos;
- atualização automática do aplicativo.

---

## 4. Plataforma e tecnologias

### 4.1 Plataforma oficial

- Windows 10
- Windows 11

### 4.2 Stack proposta

- Python
- PySide6 — interface gráfica
- python-docx — manipulação de documentos Word
- docxtpl — utilização de templates Word
- Pillow — processamento e otimização de imagens
- pytest — testes automatizados
- PyInstaller — empacotamento do aplicativo
- Git / GitHub — versionamento e distribuição

---

## 5. Fluxo principal da aplicação

O fluxo principal será:

1. Tela inicial
2. Dados gerais
3. Ambientes
4. Informações complementares
5. Revisão
6. Geração do Word

Após a criação do projeto, o usuário poderá navegar livremente entre as seções da aplicação, sem necessidade de seguir um assistente rígido.

---

# 6. Tela inicial

A tela inicial deverá conter:

- botão **Novo relatório**;
- botão **Abrir relatório existente**;
- lista de projetos recentes;
- acesso à lixeira;
- acesso às configurações.

Cada projeto recente deverá exibir:

- nome/título;
- data da última alteração;
- botão para abrir.

Exemplo:

```text
PROJETOS RECENTES

Vistoria Inicial - Rua ABC
Alterado hoje às 13:45
[ Abrir ]

Vistoria Final - Av. Brasil
Alterado ontem às 16:20
[ Abrir ]

[ Ver todos ]
[ Lixeira ]
```

---

# 7. Dados gerais da vistoria

## 7.1 Identificação

Campos:

- Tipo da vistoria
  - Inicial
  - Final
  - Periódica
  - Outra
- Título do relatório
- Código / referência
- Data da vistoria
- Data de emissão
- Responsável pela vistoria

O responsável pela vistoria terá apenas:

- Nome

Não haverá espaço de assinatura para o responsável pela vistoria.

---

# 8. Dados do imóvel

Campos:

- Tipo do imóvel
  - Casa
  - Apartamento
  - Sala comercial
  - Terreno
  - Outro
- Descrição resumida do imóvel
- Endereço
- Número
- Complemento
- Bairro
- Cidade
- Estado
- CEP

---

# 9. Dados das partes

## 9.1 Locador

Campos:

- Nome completo
- CPF / CNPJ
- Telefone
- E-mail
- Endereço

## 9.2 Locatário

Campos:

- Nome completo
- CPF / CNPJ
- Telefone
- E-mail
- Endereço

Os dados fazem parte da documentação contratual e devem estar disponíveis no relatório final.

---

# 10. Ambientes / seções

Os ambientes serão dinâmicos.

Não existirão campos fixos como `quarto1`, `quarto2`, `sala` ou `cozinha`.

O usuário poderá criar qualquer ambiente necessário.

Exemplos:

- Quintal - Frente
- Sala
- Cozinha
- Banheiro Externo
- Hall - Segundo Pavimento
- Quarto - Frente
- Sacada - Fundos

## 10.1 Estrutura de um ambiente

Cada ambiente conterá:

- Nome
- Descrição
- Observações
- Fotos

Estrutura conceitual:

```text
Ambiente
├── Nome
├── Descrição
├── Observações
└── Fotos
```

## 10.2 Ações disponíveis

O usuário poderá:

- adicionar ambiente;
- excluir ambiente;
- duplicar ambiente;
- renomear ambiente;
- mover para cima;
- mover para baixo.

A duplicação será útil para ambientes semelhantes, como múltiplos quartos.

---

# 11. Fotos

Cada ambiente poderá conter quantidade livre de fotos.

Formatos aceitos inicialmente:

- JPG
- JPEG
- PNG

Cada foto terá:

- arquivo;
- legenda;
- ordem.

Estrutura:

```text
Foto
├── Arquivo
├── Legenda
└── Ordem
```

## 11.1 Legendas

A legenda será suportada nativamente.

O usuário informará apenas o texto da legenda.

Exemplo:

```text
Vista geral da sala
```

O sistema produzirá automaticamente:

```text
Foto 01 — Vista geral da sala
```

## 11.2 Numeração

A numeração será global no documento.

Exemplo:

```text
Sala
Foto 01
Foto 02

Cozinha
Foto 03
Foto 04

Quarto
Foto 05
```

## 11.3 Reordenação

As fotos poderão ser reordenadas.

A ordem no aplicativo deverá ser a mesma ordem no relatório final.

Preferencialmente haverá suporte a arrastar e soltar, além de controles simples de movimentação.

## 11.4 Armazenamento

Ao adicionar uma foto, a aplicação deverá copiar o arquivo para dentro do projeto.

Não deverá depender permanentemente do caminho original da imagem.

---

# 12. Otimização de imagens

O arquivo original deverá ser preservado dentro do projeto.

Para geração do relatório, poderá ser criada uma versão otimizada.

Objetivos:

- reduzir o tamanho do `.docx`;
- manter boa qualidade visual;
- evitar relatórios com centenas de megabytes;
- preservar a proporção da imagem;
- evitar deformação.

---

# 13. Informações complementares

Campos:

- Quantidade de chaves entregues
- Medidor de energia
- Unidade consumidora / cliente
- Observações gerais
- Local de emissão

A estrutura deverá permitir a inclusão futura de outros campos, como:

- Medidor de água
- Medidor de gás
- Controle de garagem
- Tag de acesso
- Controle de portão

Esses campos adicionais não fazem parte obrigatoriamente do MVP.

---

# 14. Termos finais

Os termos finais serão textos padrão configuráveis.

Eles não deverão ficar escritos diretamente no código-fonte.

Exemplos de categorias:

- condições gerais de conservação;
- condições de devolução;
- prazo para apontamento de irregularidades.

A aplicação deverá utilizar os termos definidos no modelo/configuração do relatório.

---

# 15. Assinaturas

O documento final deverá possuir espaço visual para assinatura de:

- Locador
- Locatário

Formato esperado:

```text
____________________________________
NOME DO LOCADOR
LOCADOR


____________________________________
NOME DO LOCATÁRIO
LOCATÁRIO
```

Embora exista a linha de assinatura como em um documento presencial, a assinatura será realizada posteriormente de forma eletrônica pelo Clicksign.

Não haverá espaço de assinatura para o responsável pela vistoria.

---

# 16. Estrutura do relatório Word

A estrutura geral será:

1. Capa
2. Dados da vistoria
3. Dados do imóvel
4. Partes envolvidas
5. Vistoria dos ambientes
6. Informações complementares
7. Termos finais
8. Assinaturas

---

# 17. Capa

A capa deverá ser simples e profissional.

Exemplo:

```text
[ LOGO DA EMPRESA ]

RELATÓRIO DE VISTORIA

Vistoria Inicial
Casa

Rua X, nº 123
Bairro - Cidade/RJ

Data da vistoria: 24/09/2026
```

---

# 18. Organização dos ambientes no Word

Cada ambiente seguirá o mesmo padrão.

Exemplo:

```text
4.1 SALA

Descrição
────────────────────────────
Texto da descrição...

Observações
────────────────────────────
Texto das observações...

Registro fotográfico
────────────────────────────

[ FOTO ]        [ FOTO ]

Foto 01 — ...   Foto 02 — ...

[ FOTO ]        [ FOTO ]

Foto 03 — ...   Foto 04 — ...
```

---

# 19. Layout das fotos

Padrão inicial:

- duas fotos por linha;
- largura padronizada;
- proporção preservada;
- centralização;
- legenda abaixo da imagem;
- numeração automática;
- imagem e legenda não devem ser separadas entre páginas sempre que possível.

Se houver quantidade ímpar de fotos, a última permanecerá com o mesmo tamanho padrão.

---

# 20. Estilo do Word

Diretrizes iniciais:

- fonte principal: Arial;
- aparência profissional e neutra;
- títulos hierárquicos;
- paginação;
- cabeçalho discreto;
- rodapé;
- logo da empresa;
- margens tradicionais.

Sugestão inicial de margens:

- superior: 2,0 cm;
- inferior: 2,0 cm;
- esquerda: 2,5 cm;
- direita: 2,0 cm.

Esses valores poderão ser ajustados no template sem exigir mudanças relevantes no código.

---

# 21. Template Word

O arquivo `modelo_relatorio.docx` será responsável por grande parte da apresentação.

Deverá conter:

- logo;
- fontes;
- estilos;
- margens;
- cabeçalho;
- rodapé;
- paginação;
- textos fixos;
- estrutura das assinaturas.

O código deverá ficar responsável principalmente por:

- preencher dados;
- inserir ambientes;
- inserir textos;
- inserir fotos;
- inserir legendas;
- gerar o documento final.

---

# 22. Campos vazios

Campos opcionais vazios não deverão aparecer no relatório final.

Exemplo:

Se `Unidade consumidora` estiver vazia, o Word não deverá exibir:

```text
Unidade consumidora:
```

sem conteúdo.

---

# 23. Tela de revisão

Antes de gerar o Word, haverá uma tela de revisão.

Exemplo:

```text
REVISÃO DA VISTORIA

✓ Dados gerais
✓ Dados do imóvel
✓ Locador
✓ Locatário

Ambientes
✓ Quintal - Frente
✓ Sala
✓ Cozinha
⚠ Quarto 1 - sem fotos

Informações complementares
✓ Preenchidas

[ Voltar e editar ]
[ Gerar relatório ]
```

Avisos não críticos não impedirão a geração.

---

# 24. Validações

## 24.1 Validações obrigatórias

Antes da geração, o sistema deverá verificar campos essenciais.

Exemplos:

- tipo da vistoria;
- tipo do imóvel;
- endereço;
- cidade;
- estado;
- data da vistoria.

## 24.2 Validações leves

A aplicação poderá auxiliar no formato de:

- CPF / CNPJ;
- telefone;
- CEP;
- e-mail.

A validação não deverá ser excessivamente rígida a ponto de dificultar o uso legítimo.

---

# 25. Autosave

O sistema deverá salvar automaticamente o projeto a cada:

- 60 segundos, caso existam alterações.

Também deverá salvar quando houver:

- troca de ambiente;
- adição de foto;
- remoção de foto;
- reordenação de foto;
- criação de ambiente;
- exclusão de ambiente;
- geração de Word;
- fechamento da aplicação.

A interface poderá exibir:

```text
✓ Salvo às 14:32
```

ou:

```text
Salvando...
```

---

# 26. Salvamento seguro

O arquivo principal não deverá ser sobrescrito diretamente durante a gravação.

Fluxo:

```text
projeto.json
      ↓
cria projeto.tmp
      ↓
grava conteúdo
      ↓
valida
      ↓
substitui projeto.json
```

Também deverá existir uma cópia de segurança da versão anterior.

Exemplo:

```text
projeto.json
projeto.backup.json
```

---

# 27. Recuperação após falha

Caso o aplicativo tenha sido encerrado inesperadamente, na próxima abertura poderá apresentar:

```text
Encontramos uma vistoria que estava em edição.

Vistoria Inicial - Rua ABC
Último salvamento: hoje às 14:31

[ Continuar edição ]
[ Ir para tela inicial ]
```

---

# 28. Estrutura dos projetos

Estrutura inicial:

```text
Documentos/
└── Vistorias/
    ├── Projetos/
    │   └── vistoria-rua-abc/
    │       ├── projeto.json
    │       ├── projeto.backup.json
    │       └── imagens/
    │           ├── foto-001.jpg
    │           ├── foto-002.jpg
    │           └── foto-003.jpg
    │
    └── Lixeira/
```

Posteriormente o projeto poderá ser empacotado em um único arquivo, por exemplo:

```text
Vistoria Rua ABC.vistoria
```

Isso não é obrigatório para o MVP.

---

# 29. Versionamento do formato dos projetos

Todo projeto deverá possuir uma versão de estrutura.

Exemplo:

```json
{
  "version": 1
}
```

Isso permitirá futuras migrações.

Exemplo:

```text
Projeto v1
↓
Aplicativo futuro
↓
Migração
↓
Projeto v2
```

---

# 30. Limpeza automática

Regra padrão:

```text
7 dias sem alteração
→ mover para lixeira

30 dias na lixeira
→ excluir definitivamente
```

O usuário poderá restaurar projetos antes da exclusão definitiva.

Projetos poderão ser marcados como protegidos:

```text
☑ Não excluir automaticamente
```

Projetos protegidos não entrarão na limpeza automática.

---

# 31. Word exportado

O arquivo `.docx` gerado será independente da pasta do projeto.

O usuário escolherá onde salvar.

Exemplos:

- Área de Trabalho
- Documentos
- pasta do cliente
- OneDrive
- outra pasta local

A exclusão do projeto interno da aplicação nunca deverá apagar documentos Word já exportados.

---

# 32. Configurações

## 32.1 Primeira execução

A primeira execução poderá solicitar:

- Nome da empresa
- Logo
- Pasta de projetos
- Prazo para mover à lixeira
- Prazo para exclusão definitiva

## 32.2 Configurações disponíveis

### Empresa

- Nome
- Logo

### Armazenamento

- Pasta dos projetos

### Limpeza automática

- Dias até a lixeira
- Dias até exclusão definitiva

### Relatório

- Modelo padrão

### Sobre

- Nome da aplicação
- Versão
- Link do GitHub

---

# 33. Armazenamento das configurações

As configurações serão locais.

Exemplo:

```text
config.json
```

Dados possíveis:

- nome da empresa;
- caminho interno da logo;
- pasta de projetos;
- prazo da lixeira;
- prazo de exclusão;
- modelo padrão.

Dados pessoais de locadores, locatários ou vistorias não deverão ser armazenados em configurações globais.

---

# 34. Distribuição

O aplicativo será distribuído inicialmente por GitHub Releases.

Exemplo:

```text
VistoriaApp-Setup-1.0.0.exe
```

O funcionário deverá poder:

1. baixar;
2. instalar;
3. abrir;
4. usar.

Não deverá precisar instalar:

- Python;
- pip;
- dependências;
- ambiente virtual.

---

# 35. Instalação

A preferência é utilizar um instalador Windows.

O programa poderá ser instalado em:

```text
C:\Program Files\VistoriaApp\
```

Os dados permanecerão separados, por exemplo:

```text
Documentos\Vistorias\
```

Desinstalar ou atualizar a aplicação não deverá excluir os projetos.

---

# 36. Versionamento da aplicação

Será utilizado versionamento semântico.

Exemplo:

```text
1.0.0
1.0.1
1.1.0
2.0.0
```

Interpretação:

- PATCH — correções;
- MINOR — novas funcionalidades compatíveis;
- MAJOR — mudanças estruturais relevantes.

---

# 37. Atualização

No MVP, a atualização será manual.

Fluxo:

```text
Nova versão publicada
↓
Funcionário baixa instalador
↓
Executa instalação
↓
Aplicação é atualizada
↓
Projetos permanecem intactos
```

Atualização automática fica fora do MVP.

---

# 38. Tratamento de erros

## 38.1 Imagem inválida

Se uma imagem estiver em formato não suportado:

```text
Arquivo não suportado.

Formatos aceitos:
JPG, JPEG e PNG.
```

## 38.2 Imagem corrompida

A imagem não deverá ser adicionada ao projeto.

## 38.3 Word aberto

Caso o arquivo de destino esteja em uso:

```text
Não foi possível substituir o arquivo.

O documento pode estar aberto em outro programa.

[ Tentar novamente ]
[ Salvar com outro nome ]
```

## 38.4 Projeto corrompido

Se o arquivo principal estiver corrompido e houver backup:

```text
Não foi possível abrir a versão mais recente.

Existe uma cópia de segurança disponível.

[ Restaurar backup ]
[ Cancelar ]
```

---

# 39. Geração segura do Word

A geração do documento deverá utilizar arquivo temporário.

Fluxo:

```text
Dados do projeto
↓
Geração temporária
↓
Validação
↓
Movimentação para destino final
↓
Sucesso
```

Falhas durante a exportação nunca deverão corromper o projeto de origem.

---

# 40. Logs

A aplicação deverá manter logs técnicos locais para diagnóstico.

Exemplo:

```text
logs/
└── app.log
```

O log poderá conter:

- data e hora;
- versão da aplicação;
- operação executada;
- tipo do erro;
- mensagem técnica.

Deverá evitar registrar:

- CPF;
- CNPJ;
- telefone;
- e-mail;
- endereço;
- conteúdo completo da vistoria;
- dados pessoais desnecessários.

---

# 41. Privacidade e segurança

A aplicação trabalhará com informações pessoais e contratuais.

No MVP:

- dados permanecem localmente;
- fotos permanecem localmente;
- nenhum dado será enviado automaticamente para servidor;
- nenhum analytics será necessário;
- internet não será necessária para o uso principal.

Criptografia de projetos poderá ser considerada futuramente, mas não faz parte da versão 1.0.

---

# 42. Funcionamento offline

Deverá funcionar offline para:

- criar vistoria;
- editar vistoria;
- salvar;
- adicionar fotos;
- abrir projetos;
- gerar Word.

A indisponibilidade de internet nunca deverá impedir o uso principal da aplicação.

---

# 43. Resolução de tela

A interface deverá funcionar confortavelmente em notebooks a partir de aproximadamente:

```text
1366 × 768
```

Deverá utilizar rolagem quando necessário.

---

# 44. Confirmações destrutivas

Ações com risco de perda deverão solicitar confirmação.

Exemplos:

- excluir ambiente;
- excluir foto;
- excluir projeto definitivamente;
- esvaziar lixeira.

Exemplo:

```text
Excluir "Sala"?

A descrição e as 8 fotos associadas serão removidas.

[ Cancelar ]
[ Excluir ]
```

---

# 45. Modelo de dados conceitual

## 45.1 Relatório

```text
Relatório
├── ID
├── Versão
├── Tipo
├── Título
├── Código
├── Data da vistoria
├── Data de emissão
├── Responsável
├── Imóvel
├── Locador
├── Locatário
├── Ambientes
├── Informações complementares
├── Criado em
├── Atualizado em
└── Protegido contra limpeza
```

## 45.2 Ambiente

```text
Ambiente
├── ID
├── Nome
├── Descrição
├── Observações
├── Ordem
└── Fotos
```

## 45.3 Foto

```text
Foto
├── ID
├── Arquivo
├── Legenda
└── Ordem
```

---

# 46. Estrutura inicial do código

```text
vistoria-app/
│
├── app/
│   ├── main.py
│   │
│   ├── ui/
│   │   ├── main_window.py
│   │   ├── new_report.py
│   │   ├── report_editor.py
│   │   └── settings.py
│   │
│   ├── models/
│   │   ├── report.py
│   │   ├── section.py
│   │   └── photo.py
│   │
│   ├── services/
│   │   ├── project_service.py
│   │   ├── autosave_service.py
│   │   ├── cleanup_service.py
│   │   └── document_generator.py
│   │
│   └── utils/
│
├── templates/
│   └── modelo_relatorio.docx
│
├── tests/
│
├── assets/
│   └── logo.png
│
├── pyproject.toml
├── README.md
└── .gitignore
```

---

# 47. Responsabilidades principais

```text
ui/
→ interface gráfica

models/
→ estrutura dos dados

project_service
→ abrir, salvar e recuperar projetos

autosave_service
→ salvamento periódico

cleanup_service
→ limpeza e lixeira

document_generator
→ geração do Word
```

A interface gráfica não deverá concentrar a lógica de negócio.

---

# 48. Estratégia de testes

O projeto deverá seguir uma abordagem orientada a testes sempre que possível.

Fluxo:

```text
Nova funcionalidade
↓
Escrever teste
↓
Teste falha
↓
Implementar mínimo necessário
↓
Teste passa
↓
Refatorar
↓
Próxima funcionalidade
```

Deverão existir testes para:

- modelos;
- criação de projetos;
- salvamento;
- carregamento;
- backups;
- autosave;
- limpeza;
- lixeira;
- restauração;
- manipulação de imagens;
- geração do Word;
- migração de versões;
- validações.

A lógica principal deverá ser testável sem necessidade de abrir a interface gráfica.

---

# 49. Critérios principais de sucesso do MVP

A versão 1.0 será considerada bem-sucedida se um funcionário conseguir:

1. instalar a aplicação sem Python;
2. criar uma nova vistoria;
3. preencher os dados gerais;
4. cadastrar locador e locatário;
5. cadastrar o imóvel;
6. criar ambientes;
7. escrever descrições e observações;
8. adicionar e legendar fotos;
9. reorganizar ambientes e fotos;
10. fechar e continuar posteriormente;
11. não perder o trabalho graças ao autosave;
12. revisar o conteúdo;
13. gerar um Word visualmente padronizado;
14. editar o Word posteriormente, se necessário;
15. enviar o documento gerado ao Clicksign.

---

# 50. Princípio do produto

O objetivo do VistoriaApp não é substituir o Word como editor de documentos.

O objetivo é permitir que o funcionário se concentre no conteúdo da vistoria enquanto a aplicação cuida de:

- estrutura;
- padronização;
- organização;
- fotos;
- legendas;
- numeração;
- aparência do documento;
- salvamento;
- segurança do progresso.

Em resumo:

```text
O funcionário cuida da vistoria.
O VistoriaApp cuida do padrão.
```
