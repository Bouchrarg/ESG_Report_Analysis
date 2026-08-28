from fastapi import FastAPI, HTTPException, Depends,Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
from fastapi import FastAPI, File, UploadFile, Form
from fastapi.responses import JSONResponse, Response, StreamingResponse
import shutil
import sqlite3
import json 
from typing import List
from database import get_db_connection ,create_users_table, create_reports_table,drop_users_table,create_advanced_analysis_table,save_advanced_analysis,initialize_advanced_features,get_latest_analysis,create_ai_comparisons_table,save_ai_comparison,get_latest_comparison,get_comparison_history,get_analysis_history
from utils import hash_password, verify_password
from datetime import datetime
import jwt
import os
from extractors import extract_text_from_pdf, extract_tables_from_pdf, extract_text_and_tables_from_xhtml,extract_scores
import fitz 
import httpx
import io
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
import asyncio
from fastapi.middleware.cors import CORSMiddleware
from keyword_analyzer import ESGKeywordAnalyzer
from dotenv import load_dotenv
from seed_demo_data import seed_demo_data
import re

load_dotenv()

app = FastAPI()

create_users_table()
create_reports_table()
create_advanced_analysis_table()
create_ai_comparisons_table()
initialize_advanced_features()
seed_demo_data()


origins = [
    origin.strip()
    for origin in os.getenv(
        "ALLOWED_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173"
    ).split(",")
    if origin.strip()
]
print(f"🌐 CORS allowed origins: {origins}")


app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_MODEL_PREMIUM = "openai/gpt-4o"  # Modèle premium
OPENROUTER_MODEL_BUDGET = "openai/gpt-3.5-turbo"  # Modèle moins cher
SECRET_KEY = os.getenv("SECRET_KEY")

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True) #Crée le dossier d'upload s'il n'existe pas 

#we create classes using pydantic for automatic validation of the data
class ESGReport(BaseModel):
    report1: str  
    report2: str  


class ReportComparison(BaseModel):
    user_id: int
    report1_id: int
    report2_id: int


class UserCreate(BaseModel):
    email: EmailStr
    password: str
    first_name: str | None = None
    last_name: str | None = None

class UserLogin(BaseModel):
    email: EmailStr
    password: str

#fucntion to create jwt token , it accepts a dictionary as data and returns a token
def create_token(data: dict):
    return jwt.encode(data, SECRET_KEY, algorithm="HS256")

@app.post("/register")
def register(user: UserCreate): #user in an instance of UserCreate 
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE email = ?",(user.email,))
    existing_user = cursor.fetchone()
    if existing_user:
        conn.close()
        raise HTTPException(status_code=400, detail="Email déjà utilisé")
    hashed= hash_password(user.password)
    cursor.execute("INSERT INTO users (email, hashed_password, first_name, last_name) VALUES (?,?,?,?)",(user.email,hashed,user.first_name,user.last_name))
    conn.commit()
    conn.close()
    return{"msg":"Utilisateur créé avec succés"}

@app.post("/login")
def login(user: UserLogin):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE email = ?",(user.email,))
    db_user=cursor.fetchone()
    if not db_user:
        conn.close()
        raise HTTPException(status_code=400, detail="Email ou mot de passe invalide")
    if not verify_password(user.password,db_user["hashed_password"]):
        conn.close()
        raise HTTPException(status_code=400, detail="Email ou mot de passe invalide")
    token = create_token({"user_id": db_user["id"],"email": db_user["email"]})
    conn.close()
    return {"access_token": token, "token_type":"bearer"}

@app.get("/users/{user_id}")
def get_user(user_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, first_name, last_name,email FROM users WHERE id = ?",(user_id,))
    user=cursor.fetchone()
    if not user:
        raise HTTPException(status_code=404,detail="Utilisateur non trouvé")
    return dict(user)

@app.post("/upload-report")
async def upload_report(file: UploadFile = File(...), user_id: int = Form(...)):
    filename = file.filename
    saved_path = os.path.join(UPLOAD_DIR, filename)
    
    try:
        # Sauvegarde du fichier uploadé
        with open(saved_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Extraction du contenu selon l'extension
        ext = filename.split(".")[-1].lower()
        extracted_text = ""
        extracted_tables = []
        
        if ext == "pdf":
            extracted_text = extract_text_from_pdf(saved_path)
            extracted_tables = extract_tables_from_pdf(saved_path)
        elif ext in ["xhtml", "html"]:
            extracted_text, extracted_tables = extract_text_and_tables_from_xhtml(saved_path)
        else:
            extracted_text = ""
            extracted_tables = []
        
        print(f"Texte extrait (longueur: {len(extracted_text)}): {extracted_text[:200]}...")
        print(f"Tables extraites: {len(extracted_tables)}")
        
        # Vérifier la taille avant insertion
        if len(extracted_text) > 10_000_000:
            extracted_text = extracted_text[:10_000_000] + "... [TRONQUÉ]"
            print("⚠️ Texte tronqué car trop volumineux")
        
        if len(extracted_tables) > 1000:
            extracted_tables = extracted_tables[:1000]
            print("⚠️ Tables limitées à 1000")
        
        # Vérifier que la sérialisation JSON fonctionne
        try:
            tables_json = json.dumps(extracted_tables, ensure_ascii=False)
            if len(tables_json) > 50_000_000:
                print("⚠️ JSON des tables trop volumineux, limitation appliquée")
                extracted_tables = extracted_tables[:100]
                tables_json = json.dumps(extracted_tables, ensure_ascii=False)
        except (TypeError, ValueError) as json_error:
            print(f"❌ Erreur sérialisation JSON: {json_error}")
            cleaned_tables = []
            for table in extracted_tables[:100]:
                if isinstance(table, dict):
                    cleaned_table = {}
                    for key, value in table.items():
                        try:
                            json.dumps(value)
                            cleaned_table[key] = value
                        except:
                            cleaned_table[key] = str(value)
                    cleaned_tables.append(cleaned_table)
                else:
                    cleaned_tables.append(str(table))
            tables_json = json.dumps(cleaned_tables, ensure_ascii=False)
        
        # Insertion dans la base
        conn = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute("SELECT 1")
            
            cursor.execute("""
                INSERT INTO reports (user_id, filename, filepath, upload_date, extracted_text, extracted_tables)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                user_id, 
                filename, 
                saved_path, 
                datetime.now().isoformat(),
                extracted_text, 
                tables_json
            ))
            conn.commit()
            report_id = cursor.lastrowid
            
            print(f"✅ Rapport inséré avec ID: {report_id}")
            
            return JSONResponse(content={
        "status": "success",
        "report": {
            "id": report_id,
            "filename": filename,
            "filepath": saved_path,
            "user_id": user_id,
            "text_length": len(extracted_text),
            "tables_count": len(extracted_tables),
            "upload_date": datetime.now().isoformat()
        }
})

            
        except sqlite3.Error as db_error:
            print(f"❌ Erreur base de données: {db_error}")
            raise HTTPException(status_code=500, detail=f"Erreur base de données: {str(db_error)}")
        except Exception as db_unexpected:
            print(f"❌ Erreur inattendue DB: {db_unexpected}")
            raise HTTPException(status_code=500, detail=f"Erreur DB inattendue: {str(db_unexpected)}")
        finally:
            if conn:
                conn.close()
    
    except HTTPException:
        if os.path.exists(saved_path):
            os.remove(saved_path)
        raise
    except Exception as e:
        print(f"❌ Erreur générale: {e}")
        print(f"❌ Type d'erreur: {type(e).__name__}")
        import traceback
        print(f"❌ Traceback: {traceback.format_exc()}")
        
        if os.path.exists(saved_path):
            os.remove(saved_path)
        raise HTTPException(status_code=500, detail=f"Erreur lors du traitement: {str(e)}")

def clean_data_for_db(data):
    """Nettoie les données pour éviter les erreurs de base de données"""
    if isinstance(data, str):
        import re
        data = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]', '', data)
        return data
    return data

@app.get("/reports/{user_id}")
def get_reports(user_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, filename, upload_date FROM reports WHERE user_id = ?", (user_id,))
    reports = cursor.fetchall()
    conn.close()

    if not reports:
        return []

    return [dict(report) for report in reports]

async def call_ai_model(prompt: str, max_tokens: int = 1000, use_budget_model: bool = False):

    if use_budget_model:
        return await _call_openrouter(prompt, max_tokens, OPENROUTER_MODEL_BUDGET)
    else:
        try:
            return await _call_openrouter(prompt, max_tokens, OPENROUTER_MODEL_PREMIUM)
        except HTTPException as e:
            if e.status_code == 402:  # Crédits épuisés
                print(" Crédits épuisés pour GPT-4o, basculement vers GPT-3.5-turbo...")
                return await _call_openrouter(prompt, max_tokens, OPENROUTER_MODEL_BUDGET)
            else:
                raise e

async def _call_openrouter(prompt: str, max_tokens: int, model: str = None):
    """Appel à OpenRouter avec modèle spécifié"""
    if not model:
        model = OPENROUTER_MODEL_PREMIUM
        
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": "Tu es un expert ESG. Réponds de manière concise et professionnelle."},
            {"role": "user", "content": prompt}
        ],
        "max_tokens": max_tokens,
        "temperature": 0.3
    }
    
    async with httpx.AsyncClient(timeout=60) as client:
        response = await client.post("https://openrouter.ai/api/v1/chat/completions", json=payload, headers=headers)
    
    if response.status_code == 402:
        raise HTTPException(status_code=402, detail="Crédits OpenRouter épuisés")
    elif response.status_code != 200:
        raise HTTPException(status_code=500, detail="Erreur OpenRouter: " + response.text)
    
    result = response.json()
    return {
        "content": result["choices"][0]["message"]["content"],
        "model_used": model,
        "tokens_used": result.get("usage", {}).get("total_tokens", max_tokens)
    }

@app.get("/analyse-report/{report_id}")
async def analyse_report(report_id: int, user_id: int = Query(...), use_budget_model: bool = Query(False)):
    conn = None
    try:
        # Vérifier si l'analyse existe déjà
        existing = get_latest_analysis(report_id, user_id)
        if existing and not use_budget_model:
            return {
                "report_id": report_id,
                "status": "cached",
                "analysis_text": existing["analysis_text"],
                "scores": existing["scores"],
                "tokens_used": existing["tokens_used"],
                "analysis_date": existing["analysis_date"],
                "model_used": existing["model_used"]
            }
    
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT id, filename, extracted_text, extracted_tables FROM reports WHERE id = ?", (report_id,))
        report = cursor.fetchone()
        
        if not report:
            raise HTTPException(status_code=404, detail=f"Rapport avec ID {report_id} introuvable")

        extracted_text = report["extracted_text"]
        extracted_tables = json.loads(report["extracted_tables"]) if report["extracted_tables"] else []
        
        if not extracted_text or extracted_text.strip() == "":
            raise HTTPException(status_code=400, detail="Le texte extrait est vide")

        # Limiter le texte selon le modèle utilisé
        text_limit = 3000 if use_budget_model else 4000  # GPT-3.5 a une limite plus basse
        limited_text = extracted_text[:text_limit]
        
        # Analyse des tableaux si disponibles
        tables_summary = ""
        if extracted_tables:
            tables_summary = f"\n\nTABLEAUX DÉTECTÉS ({len(extracted_tables)} tableaux):\n"
            for i, table in enumerate(extracted_tables[:3]):
                if isinstance(table, dict) and 'data' in table:
                    table_data = table['data'][:5]
                    tables_summary += f"Tableau {i+1}: {table_data}\n"

        prompt = f"""
        Tu es un expert ESG senior. Effectue une analyse AVANCÉE et DÉTAILLÉE de ce rapport selon les normes ESRS.

        TEXTE DU RAPPORT:
        {limited_text}
        {tables_summary}

        ANALYSE DEMANDÉE (structure obligatoire):

        ## 1. SYNTHÈSE EXÉCUTIVE
        - Résumé en 3 points clés
        - Score global ESG sur 100

        ## 2. ANALYSE ENVIRONNEMENTALE (E1-E5)
        ### E1 - Changement climatique
        - Émissions GES mentionnées
        - Objectifs de réduction
        - Score E1: X/20

        ### E2 - Pollution
        - Types de pollution abordés
        - Mesures de prévention
        - Score E2: X/20

        ### E3 - Ressources hydriques et marines
        - Gestion de l'eau
        - Impact sur écosystèmes marins
        - Score E3: X/20

        ### E4 - Biodiversité et écosystèmes
        - Protection de la biodiversité
        - Restauration écologique
        - Score E4: X/20

        ### E5 - Économie circulaire
        - Gestion des déchets
        - Recyclage et réutilisation
        - Score E5: X/20

        ## 3. CONFORMITÉ RÉGLEMENTAIRE
        - Respect des normes ESRS
        - Lacunes identifiées
        - Recommandations prioritaires

        ## 4. POINTS D'AMÉLIORATION
        - 5 recommandations concrètes
        - Plan d'action suggéré

        ## 5. COMPARAISON SECTORIELLE
        - Positionnement vs standards du secteur
        - Bonnes pratiques observées

        Réponds en français, de manière structurée et professionnelle.
        """

        # Ajustement des tokens selon le modèle
        max_tokens = 800 if use_budget_model else 1000
        
        # Appel à l'IA avec fallback automatique
        ai_response = await call_ai_model(prompt, max_tokens=max_tokens, use_budget_model=use_budget_model)
        
        gpt_reply = ai_response["content"]
        model_used = ai_response["model_used"]
        tokens_used = ai_response["tokens_used"]
        
        scores = extract_scores(gpt_reply)
        save_advanced_analysis(report_id, user_id, gpt_reply, scores, tokens_used, model_used)

        return {
            "report_id": report_id,
            "status": "new",
            "analysis_text": gpt_reply,
            "scores": scores,
            "tokens_used": tokens_used,
            "model_used": model_used
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"Erreur dans analyse_report: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erreur interne: {str(e)}")
    finally:
        if conn:
            conn.close()

@app.post("/analyse-report/{report_id}/refresh")
async def refresh_analysis(report_id: int, user_id: int = Query(...), use_budget_model: bool = Query(False)):
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, filename, extracted_text, extracted_tables FROM reports WHERE id = ?", (report_id,))
        report = cursor.fetchone()
        if not report:
            raise HTTPException(status_code=404, detail=f"Rapport avec ID {report_id} introuvable")

        extracted_text = report["extracted_text"]
        extracted_tables = json.loads(report["extracted_tables"]) if report["extracted_tables"] else []

        if not extracted_text or extracted_text.strip() == "":
            raise HTTPException(status_code=400, detail="Le texte extrait est vide")

        text_limit = 3000 if use_budget_model else 4000
        limited_text = extracted_text[:text_limit]
        tables_summary = ""
        if extracted_tables:
            tables_summary += f"\n\nTABLEAUX DÉTECTÉS ({len(extracted_tables)} tableaux):\n"
            for i, table in enumerate(extracted_tables[:3]):
                if isinstance(table, dict) and 'data' in table:
                    table_data = table['data'][:5]
                    tables_summary += f"Tableau {i+1}: {table_data}\n"

        prompt = f"""
        Tu es un expert ESG senior. Effectue une analyse AVANCÉE et DÉTAILLÉE de ce rapport selon les normes ESRS.

        TEXTE DU RAPPORT:
        {limited_text}
        {tables_summary}

        ANALYSE DEMANDÉE (structure obligatoire):

        ## 1. SYNTHÈSE EXÉCUTIVE
        - Résumé en 3 points clés
        - Score global ESG sur 100

        ## 2. ANALYSE ENVIRONNEMENTALE (E1-E5)
        ### E1 - Changement climatique
        - Émissions GES mentionnées
        - Objectifs de réduction
        - Score E1: X/20

        ### E2 - Pollution
        - Types de pollution abordés
        - Mesures de prévention
        - Score E2: X/20

        ### E3 - Ressources hydriques et marines
        - Gestion de l'eau
        - Impact sur écosystèmes marins
        - Score E3: X/20

        ### E4 - Biodiversité et écosystèmes
        - Protection de la biodiversité
        - Restauration écologique
        - Score E4: X/20

        ### E5 - Économie circulaire
        - Gestion des déchets
        - Recyclage et réutilisation
        - Score E5: X/20

        ## 3. CONFORMITÉ RÉGLEMENTAIRE
        - Respect des normes ESRS
        - Lacunes identifiées
        - Recommandations prioritaires

        ## 4. POINTS D'AMÉLIORATION
        - 5 recommandations concrètes
        - Plan d'action suggéré

        ## 5. COMPARAISON SECTORIELLE
        - Positionnement vs standards du secteur
        - Bonnes pratiques observées

        Réponds en français, de manière structurée et professionnelle.
        """

        max_tokens = 800 if use_budget_model else 1000
        
        # Appel à l'IA avec fallback automatique
        ai_response = await call_ai_model(prompt, max_tokens=max_tokens, use_budget_model=use_budget_model)
        
        gpt_reply = ai_response["content"]
        model_used = ai_response["model_used"]
        tokens_used = ai_response["tokens_used"]

        scores = extract_scores(gpt_reply)
        save_advanced_analysis(report_id, user_id, gpt_reply, scores, tokens_used, model_used)

        return {
            "report_id": report_id,
            "status": "refreshed",
            "analysis_text": gpt_reply,
            "scores": scores,
            "tokens_used": tokens_used,
            "model_used": model_used
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if conn:
            conn.close()

@app.post("/compare-reports")
async def compare_reports(comparison: ReportComparison, use_budget_model: bool = Query(False)):
    user_id = comparison.user_id
    report1_id = comparison.report1_id
    report2_id = comparison.report2_id

    # Vérifie si une comparaison existe déjà
    if not use_budget_model:
        cached = get_latest_comparison(user_id, report1_id, report2_id)
        if cached:
            return {
                "status": "cached",
                "comparison_analysis": cached["comparison_text"],
                "scores": cached["scores"],
                "tokens_used": cached["tokens_used"],
                "comparison_date": cached["comparison_date"],
                "model_used": cached.get("model_used", "unknown"),
                "report1": {"filename": "N/A"},
                "report2": {"filename": "N/A"}
            }


    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT id, filename, extracted_text FROM reports WHERE id = ?", (report1_id,))
        report1 = cursor.fetchone()
        cursor.execute("SELECT id, filename, extracted_text FROM reports WHERE id = ?", (report2_id,))
        report2 = cursor.fetchone()

        if not report1 or not report2:
            raise HTTPException(status_code=404, detail="Un ou plusieurs rapports introuvables")

        if not report1["extracted_text"] or not report2["extracted_text"]:
            raise HTTPException(status_code=400, detail="Texte extrait manquant dans au moins un des rapports")

        limit = 1200 if use_budget_model else 1500
        text1 = report1["extracted_text"][:limit]
        text2 = report2["extracted_text"][:limit]

        prompt = f"""
Compare ces 2 rapports ESG selon les critères environnementaux ESRS (E1 à E5) :

**RAPPORT 1 - {report1["filename"]} :**
{text1}

**RAPPORT 2 - {report2["filename"]} :**
{text2}

Analyse structurée :
1. **SYNTHÈSE ENVIRONNEMENTALE** (2 lignes)
2. **POINTS COMMUNS** (E1 à E5)
3. **DIFFÉRENCES CLÉS**
4. **FORCES/FAIBLESSES** de chaque rapport
5. **RECOMMANDATIONS**
6. **SCORE ENVIRONNEMENTAL** sur 10

Réponds en français, de manière professionnelle.
"""

        max_tokens = 1200 if use_budget_model else 1500

        # Appel à l'IA avec fallback automatique
        ai_response = await call_ai_model(prompt, max_tokens=max_tokens, use_budget_model=use_budget_model)
        
        gpt_reply = ai_response["content"]
        model_used = ai_response["model_used"]
        tokens_used = ai_response["tokens_used"]

        # Extraction des scores via regex
        score_matches = re.findall(r"(\d{1,2})/10", gpt_reply)
        scores = {}
        if len(score_matches) >= 2:
            scores = {
                "report1_score": int(score_matches[0]),
                "report2_score": int(score_matches[1])
            }

        # Sauvegarde en base
        save_ai_comparison(user_id, report1_id, report2_id, gpt_reply, scores, tokens_used, model_used)


        return {
            "status": "new",
            "comparison_analysis": gpt_reply,
            "scores": scores,
            "tokens_used": tokens_used,
            "model_used": model_used,
            "report1": {"filename": report1["filename"]},
            "report2": {"filename": report2["filename"]}
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur serveur: {str(e)}")
    finally:
        if conn:
            conn.close()

@app.post("/refresh-comparison")
async def refresh_comparison(comparison: ReportComparison, use_budget_model: bool = Query(False)):
    user_id = comparison.user_id
    report1_id = comparison.report1_id
    report2_id = comparison.report2_id

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT id, filename, extracted_text FROM reports WHERE id = ?", (report1_id,))
        report1 = cursor.fetchone()
        cursor.execute("SELECT id, filename, extracted_text FROM reports WHERE id = ?", (report2_id,))
        report2 = cursor.fetchone()

        if not report1 or not report2:
            raise HTTPException(status_code=404, detail="Rapport introuvable")

        if not report1["extracted_text"] or not report2["extracted_text"]:
            raise HTTPException(status_code=400, detail="Texte manquant pour au moins un des rapports")

        limit = 1200 if use_budget_model else 1500
        text1 = report1["extracted_text"][:limit]
        text2 = report2["extracted_text"][:limit]

        prompt = f"""
Compare ces 2 rapports ESG selon les critères environnementaux ESRS (E1 à E5) :

**RAPPORT 1 - {report1["filename"]} :**
{text1}

**RAPPORT 2 - {report2["filename"]} :**
{text2}

Analyse structurée :
1. **SYNTHÈSE ENVIRONNEMENTALE** (2 lignes)
2. **POINTS COMMUNS** (E1 à E5)
3. **DIFFÉRENCES CLÉS**
4. **FORCES/FAIBLESSES** de chaque rapport
5. **RECOMMANDATIONS**
6. **SCORE ENVIRONNEMENTAL** sur 10

Réponds en français, de manière professionnelle.
"""

        max_tokens = 1200 if use_budget_model else 1500

        # Appel à l'IA avec fallback automatique
        ai_response = await call_ai_model(prompt, max_tokens=max_tokens, use_budget_model=use_budget_model)
        
        gpt_reply = ai_response["content"]
        model_used = ai_response["model_used"]
        tokens_used = ai_response["tokens_used"]

        # Extraction des scores
        score_matches = re.findall(r"(\d{1,2})/10", gpt_reply)
        scores = {}
        if len(score_matches) >= 2:
            scores = {
                "report1_score": int(score_matches[0]),
                "report2_score": int(score_matches[1])
            }

        # Ajouter une nouvelle comparaison
        save_ai_comparison(user_id, report1_id, report2_id, gpt_reply, scores, tokens_used, model_used)

        return {
            "status": "refreshed",
            "comparison_analysis": gpt_reply,
            "scores": scores,
            "tokens_used": tokens_used,
            "model_used": model_used
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur serveur: {str(e)}")
    finally:
        conn.close()

# Endpoint pour vérifier le statut des modèles IA
@app.get("/ai-models/status")
async def check_ai_models_status():
    """
    Vérifie le statut et la disponibilité des modèles IA
    """
    status = {
        "gpt4o": {
            "model": OPENROUTER_MODEL_PREMIUM,
            "available": False,
            "error": None
        },
        "gpt35": {
            "model": OPENROUTER_MODEL_BUDGET,
            "available": False,
            "error": None
        }
    }
    
    # Test GPT-4o
    try:
        test_response = await _call_openrouter("Test de connexion", max_tokens=10, model=OPENROUTER_MODEL_PREMIUM)
        status["gpt4o"]["available"] = True
    except Exception as e:
        status["gpt4o"]["error"] = str(e)
    
    # Test GPT-3.5-turbo
    try:
        test_response = await _call_openrouter("Test de connexion", max_tokens=10, model=OPENROUTER_MODEL_BUDGET)
        status["gpt35"]["available"] = True
    except Exception as e:
        status["gpt35"]["error"] = str(e)
    
    return {
        "status": "success",
        "models": status,
        "fallback_enabled": True,
        "cost_optimization": "GPT-3.5-turbo utilisé comme modèle économique"
    }

# Endpoint pour forcer l'utilisation d'un modèle spécifique
@app.post("/set-preferred-model")
def set_preferred_model(model: str = Query(..., regex="^(premium|budget)$")):
    """
    Définit le modèle IA préféré (premium=GPT-4o, budget=GPT-3.5-turbo)
    """
    if model == "premium":
        return {
            "message": f"Modèle préféré défini sur GPT-4o",
            "model": OPENROUTER_MODEL_PREMIUM,
            "provider": "openrouter",
            "cost": "élevé"
        }
    elif model == "budget":
        return {
            "message": f"Modèle préféré défini sur GPT-3.5-turbo",
            "model": OPENROUTER_MODEL_BUDGET,
            "provider": "openrouter",
            "cost": "économique"
        }

@app.get("/debug-report/{report_id}")
def debug_report(report_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM reports WHERE id = ?", (report_id,))
    report = cursor.fetchone()
    conn.close()
    
    if not report:
        raise HTTPException(status_code=404, detail="Rapport introuvable")
    
    report_dict = dict(report)
    if report_dict.get('extracted_text'):
        report_dict['extracted_text_preview'] = report_dict['extracted_text'][:500] + "..."
        report_dict['extracted_text_length'] = len(report_dict['extracted_text'])
    
    return report_dict

@app.post("/analyze-keywords/{report_id}")
def analyze_keywords_in_report(report_id: int, language: str = "french"):
    """
    Analyse les mots-clés ESG dans un rapport spécifique
    """
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT id, filename, extracted_text, upload_date FROM reports WHERE id = ?", (report_id,))
        report = cursor.fetchone()
        
        if not report:
            raise HTTPException(status_code=404, detail=f"Rapport {report_id} introuvable")
        
        if not report["extracted_text"]:
            raise HTTPException(status_code=400, detail="Aucun texte extrait disponible pour ce rapport")
        
        analyzer = ESGKeywordAnalyzer("esrs_keywords.json")
        keyword_analysis = analyzer.extract_keywords_from_text(report["extracted_text"], language)
        
        keyword_analysis["report_info"] = {
            "id": report["id"],
            "filename": report["filename"],
            "upload_date": report["upload_date"],
            "text_length": len(report["extracted_text"])
        }
        
        keyword_analysis["summary"]["analysis_date"] = datetime.now().isoformat()
        
        return {
            "status": "success",
            "report_id": report_id,
            "analysis": keyword_analysis
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Erreur analyse mots-clés: {e}")
        raise HTTPException(status_code=500, detail=f"Erreur lors de l'analyse: {str(e)}")
    finally:
        if conn:
            conn.close()

@app.post("/compare-keywords")
def compare_keywords_between_reports(comparison: ReportComparison, language: str = Query("french")):
    """
    Compare les mots-clés ESG entre deux rapports
    """
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT id, filename, extracted_text FROM reports WHERE id = ?", (comparison.report1_id,))
        report1 = cursor.fetchone()
        
        cursor.execute("SELECT id, filename, extracted_text FROM reports WHERE id = ?", (comparison.report2_id,))
        report2 = cursor.fetchone()
        
        if not report1 or not report2:
            raise HTTPException(status_code=404, detail="Un ou plusieurs rapports introuvables")
        
        if not report1["extracted_text"] or not report2["extracted_text"]:
            raise HTTPException(status_code=400, detail="Texte extrait manquant pour un ou plusieurs rapports")
        
        analyzer = ESGKeywordAnalyzer("esrs_keywords.json")
        
        analysis1 = analyzer.extract_keywords_from_text(report1["extracted_text"], language)
        analysis2 = analyzer.extract_keywords_from_text(report2["extracted_text"], language)
        
        comparison_result = {
            "report1": {
                "id": report1["id"],
                "filename": report1["filename"],
                "analysis": analysis1
            },
            "report2": {
                "id": report2["id"],
                "filename": report2["filename"],
                "analysis": analysis2
            },
            "comparison": {
                "coverage_comparison": {
                    "report1_score": analysis1["coverage_score"],
                    "report2_score": analysis2["coverage_score"],
                    "difference": analysis2["coverage_score"] - analysis1["coverage_score"]
                },
                "common_keywords": [],
                "unique_to_report1": [],
                "unique_to_report2": [],
                "category_coverage": {}
            }
        }
        
        keywords1 = set()
        keywords2 = set()
        
        for category in analysis1["categories"].values():
            for match in category["matches"]:
                keywords1.add(match["keyword"])
        
        for category in analysis2["categories"].values():
            for match in category["matches"]:
                keywords2.add(match["keyword"])
        
        comparison_result["comparison"]["common_keywords"] = list(keywords1.intersection(keywords2))
        comparison_result["comparison"]["unique_to_report1"] = list(keywords1 - keywords2)
        comparison_result["comparison"]["unique_to_report2"] = list(keywords2 - keywords1)
        
        all_categories = set(analysis1["categories"].keys()).union(set(analysis2["categories"].keys()))
        
        for category in all_categories:
            cat1_count = len(analysis1["categories"].get(category, {}).get("matches", []))
            cat2_count = len(analysis2["categories"].get(category, {}).get("matches", []))
            
            comparison_result["comparison"]["category_coverage"][category] = {
                "report1_keywords": cat1_count,
                "report2_keywords": cat2_count,
                "difference": cat2_count - cat1_count
            }
        
        return {
            "status": "success",
            "comparison_date": datetime.now().isoformat(),
            "data": comparison_result
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Erreur comparaison mots-clés: {e}")
        raise HTTPException(status_code=500, detail=f"Erreur lors de la comparaison: {str(e)}")
    finally:
        if conn:
            conn.close()

@app.get("/keywords-stats/{report_id}")
def get_keywords_statistics(report_id: int):
    """
    Retourne des statistiques détaillées sur les mots-clés d'un rapport
    """
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT id, filename, extracted_text FROM reports WHERE id = ?", (report_id,))
        report = cursor.fetchone()
        
        if not report:
            raise HTTPException(status_code=404, detail=f"Rapport {report_id} introuvable")
        
        analyzer = ESGKeywordAnalyzer("esrs_keywords.json")
        analysis = analyzer.extract_keywords_from_text(report["extracted_text"])
        
        stats = {
            "report_info": {
                "id": report["id"],
                "filename": report["filename"]
            },
            "global_stats": {
                "total_keywords": analysis["summary"]["total_keywords_found"],
                "coverage_score": analysis["coverage_score"],
                "categories_covered": len(analysis["categories"]),
                "total_categories": len(analyzer.keywords_data)
            },
            "category_breakdown": {},
            "keyword_density": {},
            "recommendations": analysis["recommendations"]
        }
        
        for cat_key, cat_data in analysis["categories"].items():
            stats["category_breakdown"][cat_key] = {
                "unique_keywords": cat_data["unique_keywords"],
                "total_occurrences": cat_data["total_occurrences"],
                "top_keywords": sorted(
                    cat_data["matches"], 
                    key=lambda x: x["occurrences"], 
                    reverse=True
                )[:5]
            }
        
        word_count = len(report["extracted_text"].split())
        if word_count > 0:
            stats["keyword_density"]["per_1000_words"] = round(
                (analysis["summary"]["total_keywords_found"] / word_count) * 1000, 2
            )
        
        return {
            "status": "success",
            "statistics": stats
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur calcul statistiques: {str(e)}")
    finally:
        if conn:
            conn.close()
@app.get("/analysis-history/by-user/{user_id}", tags=["Historique"])
async def get_analysis_history_by_user(user_id: int):
    """
    Récupère l'historique des analyses pour un utilisateur donné
    """
    try:
        history = get_analysis_history(user_id=user_id)
        
        return {
            "status": "success",
            "user_id": user_id,
            "history": history,
            "total_analyses": len(history)
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Erreur historique analyses utilisateur : {str(e)}"
        )
@app.get("/export-keywords-analysis/{report_id}")
def export_keywords_analysis(report_id: int, format: str = "json"):
    """
    Exporte l'analyse des mots-clés dans différents formats
    """
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT id, filename, extracted_text, upload_date FROM reports WHERE id = ?", (report_id,))
        report = cursor.fetchone()
        
        if not report:
            raise HTTPException(status_code=404, detail=f"Rapport {report_id} introuvable")
        
        analyzer = ESGKeywordAnalyzer("esrs_keywords.json")
        analysis = analyzer.extract_keywords_from_text(report["extracted_text"])
        
        export_data = {
            "export_info": {
                "report_id": report["id"],
                "report_filename": report["filename"],
                "upload_date": report["upload_date"],
                "export_date": datetime.now().isoformat(),
                "format": format
            },
            "analysis": analysis
        }
        
        if format.lower() == "json":
            return Response(
                content=json.dumps(export_data, ensure_ascii=False, indent=2),
                media_type="application/json",
                headers={
                    "Content-Disposition": f"attachment; filename=keywords_analysis_{report_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                }
            )
        else:
            raise HTTPException(status_code=400, detail="Format non supporté. Utilisez 'json'")
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur export: {str(e)}")
    finally:
        if conn:
            conn.close()

# Endpoint pour tester la configuration des modèles OpenRouter
@app.get("/test-models")
async def test_models_configuration():
    """
    Teste la configuration et la connexion des modèles OpenRouter
    """
    results = {
        "gpt4o": {"status": "unknown", "error": None, "response": None},
        "gpt35": {"status": "unknown", "error": None, "response": None}
    }
    
    # Test GPT-4o
    try:
        test_prompt = "Réponds simplement 'GPT-4o fonctionne' en français."
        response = await _call_openrouter(test_prompt, max_tokens=20, model=OPENROUTER_MODEL_PREMIUM)
        results["gpt4o"]["status"] = "success"
        results["gpt4o"]["response"] = response["content"]
    except Exception as e:
        results["gpt4o"]["status"] = "error"
        results["gpt4o"]["error"] = str(e)
    
    # Test GPT-3.5-turbo
    try:
        test_prompt = "Réponds simplement 'GPT-3.5 fonctionne' en français."
        response = await _call_openrouter(test_prompt, max_tokens=20, model=OPENROUTER_MODEL_BUDGET)
        results["gpt35"]["status"] = "success"
        results["gpt35"]["response"] = response["content"]
    except Exception as e:
        results["gpt35"]["status"] = "error"
        results["gpt35"]["error"] = str(e)
    
    return {
        "status": "completed",
        "models": {
            "premium": {
                "name": OPENROUTER_MODEL_PREMIUM,
                "cost": "élevé",
                "quality": "maximum",
                "test_result": results["gpt4o"]
            },
            "budget": {
                "name": OPENROUTER_MODEL_BUDGET,
                "cost": "économique",
                "quality": "standard",
                "test_result": results["gpt35"]
            }
        },
        "recommendations": [
            "Utilisez le modèle budget pour les analyses simples",
            "Utilisez le modèle premium pour les analyses complexes",
            "Le fallback automatique est activé en cas d'épuisement des crédits"
        ]
    }

@app.get("/user-history/{user_id}")
def get_user_history(user_id: int):
    try:
        analyses = get_analysis_history(user_id=user_id)
        comparisons = get_comparison_history(user_id=user_id)

        # Calcul des tokens
        total_tokens_premium = sum(a["tokens_used"] for a in analyses if a["model_used"] == "gpt-4")
        total_tokens_budget = sum(a["tokens_used"] for a in analyses if a["model_used"] == "gpt-3.5")

        return {
            "status": "success",
            "analyses": analyses,
            "comparisons": comparisons,
            "statistics": {
                "total_analyses": len(analyses),
                "total_comparisons": len(comparisons),
                "tokens_usage": {
                    "premium_model": {"total_tokens": total_tokens_premium},
                    "budget_model": {"total_tokens": total_tokens_budget},
                }
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/analysis-history/by-report/{report_id}", tags=["Historique"])
async def get_analysis_history_by_report(report_id: int):
    """
    Récupère l'historique des analyses individuelles pour un rapport donné
    """
    try:
        history = get_analysis_history(report_id)
        
        if not history:
            return {
                "status": "success",
                "report_id": report_id,
                "message": "Aucun historique trouvé pour ce rapport",
                "history": []
            }
        
        return {
            "status": "success",
            "report_id": report_id,
            "history": history
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Erreur historique analyse : {str(e)}"
        )

@app.get("/comparison-history/{user_id}", tags=["Historique"])
async def get_comparison_history_by_user(user_id: int):
    """
    Récupère l'historique des comparaisons pour un utilisateur donné
    """
    try:
        history = get_comparison_history(user_id)
        
        return {
            "status": "success",
            "user_id": user_id,
            "comparisons": history,
            "total_comparisons": len(history)
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Erreur historique comparaison : {str(e)}"
        )

@app.get("/user-history/{user_id}", tags=["Historique"])
def get_complete_user_history(user_id: int):
    """
    Récupère l'historique complet (analyses + comparaisons + statistiques) pour un utilisateur
    """
    try:
        # Utilise tes fonctions existantes
        analyses = get_analysis_history(user_id)
        comparisons = get_comparison_history(user_id)
        
        # Calcul des statistiques
        total_tokens_premium = 0
        total_tokens_budget = 0
        
        for analysis in analyses:
            tokens_used = analysis["tokens_used"] if analysis["tokens_used"] else 0
            model_used = analysis["model_used"] if analysis["model_used"] else ""
            
            if "gpt-4" in model_used.lower():  # ✅ Recherche "gpt-4" au lieu de "premium"
                total_tokens_premium += tokens_used
            elif "gpt-3.5" in model_used.lower():  # ✅ Recherche "gpt-3.5" au lieu de "budget"
                total_tokens_budget += tokens_used

        # Même correction pour les comparaisons
        for comparison in comparisons:
            tokens_used = comparison["tokens_used"] if comparison["tokens_used"] else 0
            model_used = comparison["model_used"] if comparison["model_used"] else ""
            
            if "gpt-4" in model_used.lower():
                total_tokens_premium += tokens_used
            elif "gpt-3.5" in model_used.lower():
                total_tokens_budget += tokens_used
        return {
            "status": "success",
            "user_id": user_id,
            "data": {
                "analyses": analyses,
                "comparisons": comparisons,
                "statistics": {
                    "total_analyses": len(analyses),
                    "total_comparisons": len(comparisons),
                    "tokens_usage": {
                        "premium_model": {
                            "model": OPENROUTER_MODEL_PREMIUM,
                            "total_tokens": total_tokens_premium
                        },
                        "budget_model": {
                            "model": OPENROUTER_MODEL_BUDGET,
                            "total_tokens": total_tokens_budget
                        }
                    }
                }
            }
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Erreur récupération historique complet : {str(e)}"
        )        
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
        