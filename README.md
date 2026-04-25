# Estoque Marceneiro

Sistema simples para controle de estoque de uma marcenaria, com tela de login, cadastro de produtos e organizacao dos dados.

## Tecnologias Utilizadas

- Python
- Flask
- HTML
- CSS
- JavaScript
- SQLite
- Git e GitHub

## Estrutura do Projeto

```text
estoque-marceneiro/
├── app/
│   ├── database.py
│   ├── main.py
│   ├── models/
│   ├── routes/
│   ├── services/
│   ├── static/
│   │   ├── css/
│   │   └── js/
│   └── templates/
├── requirements.txt
├── README.md
└── database.db
```

### Principais pastas e arquivos

- `app/`: nucleo da aplicacao Flask
- `app/routes/`: rotas e fluxos de navegacao do sistema
- `app/templates/`: telas HTML
- `app/static/`: arquivos estaticos, como CSS e JavaScript
- `app/database.py`: conexao, criacao e evolucao da estrutura do banco SQLite
- `app/models/`: modelos de dominio utilizados pelo projeto
- `app/main.py`: ponto de entrada da aplicacao Flask
- `requirements.txt`: dependencias Python
- `README.md`: documentacao principal do projeto

## Como Executar o Projeto

### VS Code ou terminal

```bash
git clone URL_DO_REPOSITORIO
cd estoque-marceneiro
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python -m app.main
```

## Autenticacao e E-mail

O projeto le o arquivo `.env` automaticamente ao iniciar.

O `.env` guarda somente o e-mail remetente do sistema.
Ele e configurado uma unica vez.
Os clientes recebem o codigo no e-mail digitado na tela de criacao de conta.

### Exemplo de `.env` com Gmail

```env
EMAIL_PROVIDER=gmail
SMTP_HOST=
SMTP_PORT=
SMTP_USER=seu_remetente_do_sistema@gmail.com
SMTP_PASSWORD=sua_senha_de_app_do_google
SMTP_FROM=seu_remetente_do_sistema@gmail.com
```

### Provedores suportados

- `gmail`
- `outlook`
- `hotmail`
- `yahoo`
- `icloud`
- `hostinger`
- `uol`
- `bol`
- `custom`

## Estrategia de Branches

### Branches principais

- `main`: somente versoes estaveis
- `develop`: branch principal de desenvolvimento

### Branches de funcionalidade

- `feature/auth-login`
- `feature/produtos`
- `feature/clientes`
- `feature/orcamentos`
- `feature/dashboard`
- `feature/database`
- `feature/readme-docs`

### Branches de correcao

- `fix/nome-da-correcao`

### Fluxo recomendado

1. Criar a branch a partir de `develop`
2. Fazer alteracoes pequenas e focadas
3. Criar commits curtos e descritivos
4. Validar localmente
5. Integrar em `develop`
6. Levar para `main` apenas quando estiver estavel

## Funcionalidades Atuais

- Login por e-mail
- Criacao de conta com validacao por codigo enviado por e-mail
- Recuperacao de senha por e-mail
- Cadastro e consulta de produtos
- Cadastro de clientes
- Emissao de orcamentos
- Dashboard com resumo da operacao

## Boas Praticas para Evolucao

- Nao desenvolver diretamente na `main`
- Separar cada frente de trabalho por branch
- Evitar misturar mudancas de telas, banco e documentacao no mesmo commit
- Priorizar commits pequenos e claros
