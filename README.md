# IT Support Ticket Classification System

**Automatically triages IT support tickets into the right category using a layered ensemble — a fast keyword pass, classical ML over TF-IDF, and a transformer path — behind a production-shaped FastAPI service with auth and an audit trail.**

![FastAPI](https://img.shields.io/badge/FastAPI-009688?logo=fastapi&logoColor=white)
![scikit-learn](https://img.shields.io/badge/scikit--learn-F7931E?logo=scikit-learn&logoColor=white)
![React](https://img.shields.io/badge/React-61DAFB?logo=react&logoColor=black)

---

## What it does

Routes free-text tickets into **7 categories** (Hardware, Software, Network, Security, Access, Email, Other) using a **layered ensemble** rather than a single model:

1. **Keyword classifier** — cheap, high-precision rules for the obvious cases.
2. **Classical ML over TF-IDF** — Multinomial Naive Bayes, Random Forest, and SVM (unigram + bigram, 5k features).
3. **Transformer path** — a Hugging Face model wired in for the harder, ambiguous tickets.

A decision layer combines the signals and returns a category + confidence.

## Engineering

- **FastAPI** service with a clean service/model/util layering, JWT auth, structured logging, a Prometheus client, and an **activity/audit trail**.
- **React + TypeScript** frontend for submitting tickets and viewing analytics.
- Proper Python packaging (`pyproject.toml`, CLI entry point), SQLAlchemy models, custom exceptions.

## Run it

```bash
pip install -r requirements.txt
uvicorn src.api.main:app --reload        # backend
cd frontend && npm install && npm run dev # frontend
```

## Stack

FastAPI · scikit-learn (NB / RandomForest / SVM) · TF-IDF · Hugging Face Transformers · spaCy / NLTK · SQLAlchemy · JWT · React / TypeScript

## Honest scope

The current decision layer leans on the **keyword + classical-ML** ensemble; the transformer path is integrated but not yet the primary driver of the final label, and the models are trained at runtime rather than shipped with a fixed evaluation split — so treat it as a working triage pipeline and ops-tooling demo rather than a benchmarked classifier. The value is the layered design + the production-shaped API (auth, audit, packaging).
