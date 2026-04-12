# estoque-marceneiro
Sistema web para controle de estoque e agenda de entregas de uma marcenaria, desenvolvido com Flask, HTML, CSS e JavaScript.
# Sistema de Estoque - Marcenaria

Sistema para controle de estoque e produtos de marcenaria.

---

##  Arquitetura do Projeto
estoque-marceneiro/
│
├── app/
│ ├── main.py
│ ├── database.py
│
│ ├── models/
│ │ ├── user_model.py
│ │ ├── product_model.py
│ │ └── delivery_model.py
│
│ ├── routes/
│ │ ├── auth_routes.py
│ │ ├── product_routes.py
│ │ └── delivery_routes.py
│
│ ├── services/
│ │ ├── auth_service.py
│ │ ├── product_service.py
│ │ └── delivery_service.py
│
│ ├── templates/
│ │ ├── login.html
│ │ ├── dashboard.html
│ │ ├── products.html
│ │ └── deliveries.html
│
│ └── static/
│ ├── css/style.css
│ └── js/app.js
│
├── database.db
├── requirements.txt
└── README.md

---

##  Fluxo do Sistema

### Login

---

## Tecnologias

- Python
- Flask
- SQLite
- HTML / CSS / JS

---

## ▶ Como rodar

```bash
pip install -r requirements.txt
python -m app.main

---

##  Passo 3: salvar e subir

No terminal:

```bash
git add .
git commit -m "adicionando arquitetura no README"
git push origin main
