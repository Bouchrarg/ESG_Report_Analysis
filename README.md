# ESG Report Analysis

A tool for analyzing corporate sustainability reports against the ESRS taxonomy. Upload a PDF or XHTML report, extract its text and tables, and get a keyword based ESG score alongside an AI generated comparison between reports.

## Features

- Account creation and login, with a JWT protected API
- Upload PDF or XHTML sustainability reports and extract text, tables, and scores
- Keyword based ESG scoring through a dedicated analyzer
- AI assisted comparison between two reports, using an LLM through OpenRouter
- A dashboard, a report history view, and a per report detail page

## Tech stack

- Backend: FastAPI, SQLite, PyMuPDF and ReportLab for document handling, JWT for auth
- Frontend: React, Vite, Tailwind CSS, React Router

## Running locally

Backend:

```
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload
```

Create a `.env` file in `backend/` with `SECRET_KEY` and `OPENROUTER_API_KEY`.

Frontend:

```
cd frontend
npm install
npm run dev
```
