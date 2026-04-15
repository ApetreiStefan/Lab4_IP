# 📘 AI Service -- E-Learning Adaptive Tutor

## 🧠 Descriere

Acest serviciu reprezintă modulul de AI al aplicației e-learning.

## 🧱 Structura proiectului
```
ai-service/
│
├── api/                    # API layer (FastAPI routers)
│   ├── ai_gateway.py
│   ├── results_api.py
│   ├── context_receiver.py
│
├── services/              # Business logic
│   ├── quiz_service.py
│   ├── test_service.py
│   ├── explanation_service.py
│   ├── results_service.py
│   ├── context_service.py
│
├── core/                  # AI logic
│   ├── prompt_engine.py
│   ├── llm_client.py
│
├── models/                # DTO / request-response models
│   ├── quiz_models.py
│   ├── result_models.py
│
├── db/                    # persistence
│   ├── database.py
│   ├── repositories.py
│
├── main.py                # entrypoint FastAPI
└── .env
```
## 🔌 api/

-   ai_gateway.py → endpoint-uri principale
-   results_api.py → rezultate
-   context_receiver.py → context elev

## ⚙️ services/

-   quiz_service.py → generare quiz
-   test_service.py → generare teste
-   explanation_service.py → explicații
-   results_service.py → scoruri
-   context_service.py → progres elev

## 🤖 core/

-   prompt_engine.py → prompturi AI
-   llm_client.py → comunicare AI

## 🧩 models/

-   quiz_models.py → modele quiz
-   result_models.py → modele rezultate

## 🗄️ db/

-   database.py → conexiune DB
-   repositories.py → acces DB

## 🚀 main.py

Entry point FastAPI

## ▶️ Cum rulezi serviciul (FastAPI)

Din root-ul repo-ului:

1) Intră în folderul serviciului

```bash
cd ai-service
```

2) Instalează dependențele

```bash
python -m pip install -r requirements.txt
```

3) Pornește serverul

```bash
python -m uvicorn main:app --reload
```

4) Testează în browser

- http://127.0.0.1:8000/
- http://127.0.0.1:8000/docs

## 🔑 .env

API keys (nu se urcă pe GitHub)
