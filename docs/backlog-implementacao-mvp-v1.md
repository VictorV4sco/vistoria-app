# Backlog de Implementação — VistoriaApp MVP v1.0

## Política de retenção vigente

Atualmente, os projetos são mantidos localmente por tempo indeterminado.
A política automática de retenção está desabilitada. Não há limpeza na
inicialização, em background ou pelo menu. Itens já existentes na Lixeira
não são restaurados nem excluídos automaticamente.

As referências abaixo à política de 7/30 dias e à restauração descrevem
planejamento histórico, inativo e reservado para uma decisão futura.

## 1. Estratégia geral

A implementação seguirá uma ordem de baixo risco:

1. Estrutura do projeto e qualidade
2. Modelos de domínio
3. Persistência local
4. Autosave, backup e recuperação
5. Fotos e otimização
6. Geração do Word
7. Regras de revisão e validação
8. Interface gráfica
9. Infraestrutura de lixeira e limpeza automática (atualmente desabilitada)
10. Configurações
11. Integração final
12. Empacotamento e release

Regra de desenvolvimento:

```text
Teste
↓
Teste falha
↓
Implementação mínima
↓
Teste passa
↓
Refatoração
↓
Commit
```

---

# Épico 0 — Fundação do projeto

## Objetivo

Criar uma base limpa e testável antes de qualquer funcionalidade.

## Tarefas

- criar repositório;
- criar `pyproject.toml`;
- configurar ambiente virtual;
- adicionar dependências iniciais;
- criar estrutura de pastas;
- configurar `pytest`;
- configurar lint/format;
- criar `.gitignore`;
- criar README inicial;
- adicionar documento de especificação em `docs/`;
- definir versão inicial do aplicativo.

## Critério de aceite

- aplicação possui ponto de entrada;
- `pytest` executa com sucesso;
- projeto possui estrutura definida;
- primeira pipeline/local check passa.

---

# Épico 1 — Modelos de domínio

## Objetivo

Representar os dados da vistoria sem interface e sem persistência.

## Entidades iniciais

### Report

Campos:

- id;
- version;
- tipo;
- título;
- código;
- data da vistoria;
- data de emissão;
- responsável;
- imóvel;
- locador;
- locatário;
- ambientes;
- informações complementares;
- criado em;
- atualizado em;
- protegido contra limpeza.

### Property

Campos:

- tipo;
- descrição;
- endereço;
- número;
- complemento;
- bairro;
- cidade;
- estado;
- CEP.

### Party

Campos:

- nome;
- CPF/CNPJ;
- telefone;
- e-mail;
- endereço.

Será utilizado inicialmente para:

- locador;
- locatário.

### Section

Campos:

- id;
- nome;
- descrição;
- observações;
- ordem;
- fotos.

### Photo

Campos:

- id;
- arquivo;
- legenda;
- ordem.

## Testes

- criação de relatório;
- criação de ambiente;
- criação de foto;
- adição e remoção de ambientes;
- reordenação de ambientes;
- adição e remoção de fotos;
- reordenação de fotos;
- valores padrão;
- serialização básica.

## Critério de aceite

Toda a estrutura de uma vistoria deve poder existir em memória sem depender da interface gráfica.

---

# Épico 2 — Persistência local

## Objetivo

Salvar e abrir projetos locais.

## Tarefas

- criar `ProjectService`;
- criar projeto em pasta própria;
- salvar `projeto.json`;
- carregar `projeto.json`;
- criar pasta `imagens`;
- implementar serialização;
- implementar desserialização;
- preservar `version`;
- atualizar `updated_at`;
- implementar caminhos relativos das imagens.

## Testes

- salvar projeto;
- carregar projeto;
- salvar e carregar mantendo os mesmos dados;
- projeto inexistente;
- JSON inválido;
- diretório sem permissão;
- caminhos relativos.

## Critério de aceite

Um relatório criado em memória deve poder ser salvo, fechar a aplicação e ser carregado novamente sem perda de dados.

---

# Épico 3 — Salvamento seguro e recuperação

## Objetivo

Evitar perda ou corrupção do trabalho.

## Tarefas

- salvar primeiro em arquivo temporário;
- validar arquivo temporário;
- substituir arquivo principal atomicamente;
- manter `projeto.backup.json`;
- restaurar backup;
- detectar projeto corrompido;
- detectar projeto recentemente aberto;
- registrar último projeto em edição.

## Testes

- salvamento atômico;
- falha durante gravação;
- backup anterior preservado;
- arquivo principal corrompido;
- restauração do backup;
- falha de restauração.

## Critério de aceite

Uma falha simulada durante o salvamento não pode destruir a última versão válida do projeto.

---

# Épico 4 — Autosave

## Objetivo

Salvar alterações automaticamente.

## Regras

- intervalo padrão: 60 segundos;
- salvar somente se houver alterações;
- salvar ao trocar de ambiente;
- salvar ao adicionar/remover/reordenar foto;
- salvar ao criar/excluir/reordenar ambiente;
- salvar ao gerar Word;
- salvar ao fechar.

## Tarefas

- criar `AutosaveService`;
- implementar flag `dirty`;
- implementar temporizador;
- integrar com `ProjectService`;
- expor estado de salvamento para a interface.

## Testes

- não salvar sem alteração;
- salvar quando `dirty`;
- limpar flag após sucesso;
- manter flag se salvamento falhar.

## Critério de aceite

Alterações não devem permanecer mais de aproximadamente 60 segundos sem tentativa de persistência.

---

# Épico 5 — Gerenciamento de fotos

## Objetivo

Adicionar e organizar fotos de forma segura.

## Tarefas

- validar extensão;
- validar se imagem pode ser aberta;
- copiar imagem para o projeto;
- gerar nome interno único;
- remover foto;
- reordenar foto;
- editar legenda;
- preservar original;
- criar versão otimizada para relatório.

## Formatos

- JPG;
- JPEG;
- PNG.

## Testes

- importar JPG;
- importar PNG;
- rejeitar arquivo não suportado;
- rejeitar imagem corrompida;
- cópia para o projeto;
- nomes duplicados;
- remoção;
- reordenação;
- otimização preservando proporção.

## Critério de aceite

Excluir ou mover a imagem original do computador não pode quebrar o projeto depois que ela foi importada.

---

# Épico 6 — Gerador de Word

## Objetivo

Transformar um projeto em um `.docx` padronizado.

## Tarefas

- criar `DocumentGenerator`;
- carregar `modelo_relatorio.docx`;
- preencher capa;
- preencher dados da vistoria;
- preencher imóvel;
- preencher locador;
- preencher locatário;
- gerar ambientes dinamicamente;
- inserir descrição;
- inserir observações;
- inserir fotos;
- inserir legendas;
- numerar fotos globalmente;
- duas fotos por linha;
- preservar proporção;
- gerar informações complementares;
- incluir termos finais;
- criar linhas de assinatura de locador e locatário;
- omitir campos vazios;
- gerar arquivo temporário;
- mover para destino apenas após sucesso.

## Testes

- documento válido é criado;
- dados aparecem no Word;
- ambientes aparecem na ordem correta;
- fotos aparecem na ordem correta;
- numeração global das fotos;
- legenda correta;
- campos vazios omitidos;
- relatório sem fotos;
- relatório com número ímpar de fotos;
- falha de escrita não danifica projeto;
- destino existente/em uso.

## Critério de aceite

Dado um projeto válido, o sistema deve gerar um `.docx` editável contendo todas as informações e fotos na ordem correta.

---

# Épico 7 — Validação e revisão

## Objetivo

Separar erros bloqueantes de avisos.

## Tarefas

- criar serviço/regra de validação;
- definir campos obrigatórios;
- validar dados gerais;
- validar imóvel;
- validar partes;
- gerar avisos para ambientes sem fotos;
- gerar aviso para fotos sem legenda;
- retornar localização do problema.

## Resultado esperado

A validação deverá produzir algo semelhante a:

```text
Erros
- Endereço do imóvel ausente

Avisos
- Quarto 2 não possui fotos
- Foto 08 não possui legenda
```

## Testes

- relatório válido;
- campo obrigatório ausente;
- múltiplos erros;
- aviso não bloqueante;
- ausência de fotos não impede geração.

---

# Épico 8 — Interface base

## Objetivo

Criar a janela principal e navegação.

## Tarefas

- criar `MainWindow`;
- criar navegação;
- tela inicial;
- projetos recentes;
- novo relatório;
- abrir relatório;
- acesso a configurações;
- acesso à lixeira (planejado; inativo);
- exibir versão.

## Critério de aceite

O usuário deve conseguir abrir a aplicação e iniciar ou continuar um projeto.

---

# Épico 9 — Tela de dados gerais

## Objetivo

Editar todos os dados principais da vistoria.

## Tarefas

Criar grupos para:

- identificação;
- imóvel;
- locador;
- locatário;
- responsável;
- datas.

Adicionar:

- máscaras leves;
- validação visual;
- integração com autosave.

Na criação da vistoria, usar radio buttons ou outro controle de seleção exclusiva
para `Vistoria Inicial` e `Vistoria Final`, associados aos valores `Inicial` e
`Final` do domínio. Não permitir digitação livre nem outros tipos.

## Critério de aceite

Todos os dados gerais previstos na especificação devem ser editáveis e persistidos.

---

# Épico 10 — Editor de ambientes

## Objetivo

Criar o principal fluxo de trabalho do funcionário.

## Layout

- lista de ambientes à esquerda;
- editor do ambiente à direita.

## Tarefas

- adicionar ambiente;
- renomear;
- duplicar;
- excluir;
- mover;
- editar descrição;
- editar observações;
- selecionar ambiente;
- integração com autosave.

## Critério de aceite

O usuário deve conseguir montar livremente a estrutura de ambientes de qualquer imóvel.

---

# Épico 11 — Editor de fotos

## Objetivo

Permitir gerenciamento visual das fotos.

## Tarefas

- botão adicionar fotos;
- miniaturas;
- campo de legenda;
- excluir;
- reordenar;
- drag and drop se viável;
- feedback de importação;
- erro de imagem inválida.

## Critério de aceite

O usuário deve visualizar, legendar e organizar as fotos na mesma ordem em que aparecerão no relatório.

---

# Épico 12 — Informações complementares

## Tarefas

Criar campos para:

- quantidade de chaves;
- medidor de energia;
- unidade consumidora;
- observações gerais;
- local de emissão.

Integrar com persistência e autosave.

---

# Épico 13 — Tela de revisão

## Objetivo

Apresentar erros e avisos antes da exportação.

## Tarefas

- resumo dos dados;
- lista de ambientes;
- indicadores de completude;
- erros;
- avisos;
- ação para voltar e corrigir;
- botão gerar relatório.

## Critério de aceite

Erros obrigatórios impedem geração; avisos permitem prosseguir.

---

# Épico 14 — Lixeira e limpeza (referência histórica; desabilitado)

## Objetivo

A versão atual preserva todos os projetos por tempo indeterminado.
O serviço permanece com testes isolados, sem coordenação pela UI.
As regras e tarefas deste épico são históricas e não estão ativas.

## Regras

- 7 dias sem alteração → lixeira;
- 30 dias na lixeira → exclusão definitiva;
- projetos protegidos não são movidos automaticamente.

## Tarefas

- criar `CleanupService`;
- mover projeto inteiro;
- restaurar;
- excluir definitivamente;
- proteger/desproteger projeto;
- executar limpeza ao iniciar aplicação ou em momento seguro.

## Testes

- projeto recente permanece;
- projeto inativo é movido;
- projeto protegido permanece;
- restauração;
- exclusão após prazo;
- fotos acompanham projeto.

---

# Épico 15 — Configurações

## Tarefas

Implementar:

- nome da empresa;
- logo;
- pasta de projetos;
- dias até lixeira (planejado; inativo);
- dias até exclusão (planejado; inativo);
- modelo padrão;
- versão;
- link do GitHub;
- restauração de padrões.

## Persistência

```text
config.json
```

## Critério de aceite

Configurações sobrevivem ao fechamento da aplicação sem guardar dados pessoais das vistorias.

---

# Épico 16 — Logs e tratamento de erros

## Tarefas

- configurar logging;
- rotação simples de logs;
- mensagens amigáveis;
- não registrar dados pessoais;
- tratar erro de arquivo em uso;
- tratar falta de permissão;
- tratar falha de disco;
- tratar falha de exportação.

## Critério de aceite

Erros técnicos devem ser diagnosticáveis sem expor conteúdo contratual desnecessário.

---

# Épico 17 — Integração e testes de fluxo

## Cenários principais

### Cenário 1

```text
Criar vistoria
→ preencher dados
→ criar ambientes
→ adicionar fotos
→ fechar
→ abrir novamente
→ dados continuam disponíveis
```

### Cenário 2

```text
Criar vistoria
→ adicionar fotos
→ gerar Word
→ abrir Word
→ conferir dados, fotos e legendas
```

### Cenário 3

```text
Editar projeto
→ simular falha durante salvamento
→ reiniciar
→ recuperar versão válida
```

### Cenário 4 — histórico/futuro; inativo na versão atual

```text
Projeto fica inativo
→ vai para lixeira
→ usuário restaura
→ projeto volta completo
```

---

# Épico 18 — Build e distribuição

## Tarefas

- criar script de build;
- configurar PyInstaller;
- incluir templates;
- incluir assets;
- validar execução sem Python instalado;
- criar ícone;
- criar instalador;
- testar Windows 10;
- testar Windows 11;
- criar release `1.0.0`.

## Critério de aceite

Um computador Windows sem ambiente Python deve conseguir instalar, abrir e utilizar o aplicativo.

---

# Ordem recomendada de implementação

## Fase 1 — Núcleo

```text
Épico 0
Épico 1
Épico 2
Épico 3
Épico 4
```

Resultado: projetos já podem existir, ser salvos e recuperados sem interface.

## Fase 2 — Conteúdo do relatório

```text
Épico 5
Épico 6
Épico 7
```

Resultado: já é possível gerar Word completo através de testes/código, mesmo sem GUI.

## Fase 3 — Aplicação utilizável

```text
Épico 8
Épico 9
Épico 10
Épico 11
Épico 12
Épico 13
```

Resultado: funcionário consegue criar uma vistoria pela interface e gerar relatório.

## Fase 4 — Operação segura

```text
Épico 14
Épico 15
Épico 16
Épico 17
```

Resultado: aplicação pronta para uso cotidiano.

## Fase 5 — Distribuição

```text
Épico 18
```

Resultado: instalador do MVP v1.0.

---

# Primeiro marco funcional

O primeiro marco não será a interface.

Será:

```text
Criar relatório em Python
↓
adicionar imóvel
↓
adicionar partes
↓
adicionar ambientes
↓
adicionar fotos
↓
salvar projeto
↓
fechar
↓
carregar projeto
↓
gerar Word
```

Quando isso funcionar com testes automatizados, o núcleo do sistema estará validado.

A interface será construída sobre uma base já funcional.

---

# Regra para uso de IA durante o desenvolvimento

A IA deverá seguir este fluxo para qualquer funcionalidade:

```text
1. Ler especificação e testes existentes
2. Definir comportamento esperado
3. Escrever ou atualizar teste
4. Executar teste e confirmar falha
5. Implementar o mínimo necessário
6. Executar testes
7. Refatorar sem quebrar testes
8. Executar suíte novamente
```

A IA não deverá implementar uma nova regra de negócio antes de existir um teste correspondente, salvo código estritamente visual ou infraestrutura em que um teste automatizado não seja razoável.

Mocks deverão ser usados para dependências externas e efeitos colaterais quando fizer sentido, mas não como substituto indiscriminado dos próprios objetos de domínio.

---

# Próximo passo técnico

Começar pelo **Épico 0 — Fundação do projeto**.

A primeira entrega deverá conter:

```text
vistoria-app/
├── app/
├── tests/
├── docs/
├── templates/
├── assets/
├── pyproject.toml
├── README.md
└── .gitignore
```

E o primeiro teste deverá validar a criação do modelo mais básico de relatório.
