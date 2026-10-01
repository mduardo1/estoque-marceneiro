# Estoque Marceneiro

Sistema web em Flask para controle de estoque de uma marcenaria, com autenticacao por e-mail, cadastro de clientes, cadastro de produtos, orcamentos e dashboard.

## Objetivo

Organizar o controle operacional de uma marcenaria em uma aplicacao simples, local e baseada em SQLite, mantendo produtos, clientes e orcamentos em um unico fluxo.

## Funcionalidades

- Login por e-mail e senha.
- Criacao de conta com codigo de verificacao enviado por e-mail.
- Recuperacao de senha por e-mail.
- Cadastro, listagem e remocao de produtos.
- Cadastro, listagem e remocao de clientes.
- Emissao de orcamentos com baixa de estoque.
- Dashboard com resumo da operacao.

## Tecnologias Utilizadas

- Python
- Flask
- SQLite
- HTML
- CSS
- JavaScript
- python-dotenv

## Estrutura do Projeto

```text
estoque-marceneiro/
|-- app/
|   |-- database.py
|   |-- main.py
|   |-- models/
|   |-- routes/
|   |-- services/
|   |-- static/
|   |   |-- css/
|   |   `-- js/
|   `-- templates/
|-- .env.example
|-- .gitignore
|-- README.md
|-- requirements.txt
`-- database.db
```

### Principais Pastas e Arquivos

- `app/`: codigo principal da aplicacao Flask.
- `app/main.py`: ponto de entrada da aplicacao.
- `app/database.py`: conexao e criacao das tabelas SQLite.
- `app/routes/`: rotas HTTP e fluxos de navegacao.
- `app/templates/`: paginas HTML renderizadas pelo Flask.
- `app/static/`: arquivos CSS e JavaScript.
- `.env.example`: modelo seguro das variaveis de ambiente.
- `requirements.txt`: dependencias Python do projeto.
- `database.db`: banco SQLite local, ignorado pelo Git.

## Instalacao no Windows

Clone o repositorio e entre na pasta do projeto:

```powershell
git clone URL_DO_REPOSITORIO
cd estoque-marceneiro
```

Crie e ative um ambiente virtual:

```powershell
python -m venv venv
venv\Scripts\activate
```

Instale as dependencias:

```powershell
pip install -r requirements.txt
```

## Configuracao do `.env`

Copie o arquivo de exemplo:

```powershell
copy .env.example .env
```

Depois edite o `.env` local com as configuracoes reais de e-mail:

```env
EMAIL_PROVIDER=gmail
SMTP_HOST=
SMTP_PORT=
SMTP_USER=seuemail@gmail.com
SMTP_PASSWORD=sua_senha_de_aplicativo_do_google
SMTP_FROM=seuemail@gmail.com
SECRET_KEY=troque_por_uma_chave_secreta_segura
```

Para Gmail, use uma senha de aplicativo do Google em `SMTP_PASSWORD`. Nao use a senha normal da conta Google. Com `EMAIL_PROVIDER=gmail`, `SMTP_HOST` e `SMTP_PORT` podem ficar vazios; o sistema usa `smtp.gmail.com` na porta `587` com STARTTLS.

Provedores suportados:

- `gmail`
- `outlook`
- `hotmail`
- `yahoo`
- `icloud`
- `hostinger`
- `uol`
- `bol`
- `custom`

## Como Iniciar

Com o ambiente virtual ativado, execute:

```powershell
python -m app.main
```

Por padrao, o Flask inicia em:

```text
http://127.0.0.1:5000
```

## Cuidados de Seguranca

- Nunca envie credenciais reais para o GitHub.
- Mantenha o arquivo `.env` apenas no ambiente local.
- Use `.env.example` somente com valores ficticios ou placeholders.
- O banco `database.db` contem dados locais e deve permanecer fora do Git.
- Revise `git status` antes de qualquer commit para confirmar que arquivos sensiveis nao foram adicionados.

## Dependencias

As dependencias estao fixadas em `requirements.txt`:

```text
Flask==3.1.0
python-dotenv==1.0.1
```
