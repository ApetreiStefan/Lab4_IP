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

## DATABASE (ai_database)
```
1) ai_cache : contine explicatiile pentru paragrafele alese de cei mai multi elevi
   -content_hash
   -cached_response
   -created_at

2) ai_records : aici se salveaza quiz-urile generate de AI
   -id
   -user_id
   -record_type (popquiz, finaltest)
   -subject_tag
   -difficulty
   -context_text
   -content
   -created_at

3) student_mastery : contine informatii despre situatia elevilor la o anumita materie pentru statistici, adaptarea AI-ului pentru fiecare elev
   -id
   -user_id
   -topic_name
   -mastery_score
   -wrong_answers_count
   -last_practiced

4) student_profiles : informatii generale despre nivelul elevilor
   -user_id
   -current_level
   -preferred_difficulty
   -total_quizzes_taken
   -updated_at
```
## Ultimele modificari

- db/schema.sql este scriptul de creare a bazei de date
- db/database.py si db/repositories.py au fost completate
- Prompturile au fost puse separat in core/prompt_engine.py
- Pentru generarea de popquiz-uri si teste finale a fost adaugat si parametrul difficulty (easy,medium,hard)
- services/generate_explanation_paragraphs.py : a fost modificat sa caute in ai_cache daca exista deja explicatia pentru un paragraf, in caz contrar este generata de AI si dupa salvata in tabelul ai_cache
- TO DO: introducerea functionalitatii de salvare a datelor aferente tabelelor ai_records, student_mastery, student_profiles

## 🔑 .env

API keys (nu se urcă pe GitHub)
