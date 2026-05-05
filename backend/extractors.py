import fitz  # PyMuPDF
import pdfplumber
import pandas as pd
from bs4 import BeautifulSoup
import tabula
import camelot
from typing import List, Tuple
import re
import io

def extract_text_from_pdf(file_path: str) -> str:

    extracted_text = ""
    
    # Méthode 1: PyMuPDF (fitz) - Rapide et efficace
    try:
        doc = fitz.open(file_path)
        text_parts = []
        
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            text = page.get_text()
            if text.strip():  # Vérifier que le texte n'est pas vide
                text_parts.append(text)
        
        doc.close()
        extracted_text = "\n".join(text_parts)
        
        if extracted_text.strip():
            print(f"✅ Extraction PyMuPDF réussie: {len(extracted_text)} caractères")
            return extracted_text
            
    except Exception as e:
        print(f"❌ Erreur PyMuPDF: {e}")
    
    # Méthode 2: pdfplumber - Meilleur pour les PDFs complexes
    try:
        with pdfplumber.open(file_path) as pdf:
            text_parts = []
            
            for page in pdf.pages:
                text = page.extract_text()
                if text and text.strip():
                    text_parts.append(text)
            
            extracted_text = "\n".join(text_parts)
            
            if extracted_text.strip():
                print(f"✅ Extraction pdfplumber réussie: {len(extracted_text)} caractères")
                return extracted_text
                
    except Exception as e:
        print(f"❌ Erreur pdfplumber: {e}")
    
    # Méthode 3: OCR avec PyMuPDF (pour PDFs scannés)
    try:
        import pytesseract
        from PIL import Image
        
        doc = fitz.open(file_path)
        text_parts = []
        
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            
            # Convertir la page en image
            mat = fitz.Matrix(2.0, 2.0)  # Zoom x2 pour meilleure qualité OCR
            pix = page.get_pixmap(matrix=mat)
            img_data = pix.tobytes("ppm")
            
            # OCR sur l'image
            image = Image.open(io.BytesIO(img_data))
            text = pytesseract.image_to_string(image, lang='fra+eng')
            
            if text.strip():
                text_parts.append(text)
        
        doc.close()
        extracted_text = "\n".join(text_parts)
        
        if extracted_text.strip():
            print(f"✅ Extraction OCR réussie: {len(extracted_text)} caractères")
            return extracted_text
            
    except Exception as e:
        print(f"❌ Erreur OCR: {e}")
    
    print(f"⚠️ Aucune méthode d'extraction n'a fonctionné pour {file_path}")
    return ""

def extract_tables_from_pdf(file_path: str) -> List[dict]:
    """
    Extraction de tableaux depuis un PDF avec plusieurs méthodes
    """
    tables_data = []
    
    # Méthode 1: camelot (très efficace pour les tableaux)
    try:
        tables = camelot.read_pdf(file_path, pages='all', flavor='lattice')
        
        for i, table in enumerate(tables):
            if not table.df.empty:
                # Nettoyer le DataFrame
                df_cleaned = clean_dataframe(table.df)
                tables_data.append({
                    'table_id': i,
                    'method': 'camelot_lattice',
                    'data': df_cleaned.to_dict('records'),
                    'shape': df_cleaned.shape,
                    'confidence': table.accuracy if hasattr(table, 'accuracy') else None
                })
        
        if tables_data:
            print(f"✅ Camelot lattice: {len(tables_data)} tableaux extraits")
            return tables_data
            
    except Exception as e:
        print(f"❌ Erreur camelot lattice: {e}")
    
    # Méthode 2: camelot stream (pour tableaux sans bordures)
    try:
        tables = camelot.read_pdf(file_path, pages='all', flavor='stream')
        
        for i, table in enumerate(tables):
            if not table.df.empty:
                df_cleaned = clean_dataframe(table.df)
                tables_data.append({
                    'table_id': i,
                    'method': 'camelot_stream',
                    'data': df_cleaned.to_dict('records'),
                    'shape': df_cleaned.shape
                })
        
        if tables_data:
            print(f"✅ Camelot stream: {len(tables_data)} tableaux extraits")
            return tables_data
            
    except Exception as e:
        print(f"❌ Erreur camelot stream: {e}")
    
    # Méthode 3: tabula (alternative robuste)
    try:
        tables = tabula.read_pdf(file_path, pages='all', multiple_tables=True)
        
        for i, df in enumerate(tables):
            if not df.empty:
                df_cleaned = clean_dataframe(df)
                tables_data.append({
                    'table_id': i,
                    'method': 'tabula',
                    'data': df_cleaned.to_dict('records'),
                    'shape': df_cleaned.shape
                })
        
        if tables_data:
            print(f"✅ Tabula: {len(tables_data)} tableaux extraits")
            return tables_data
            
    except Exception as e:
        print(f"❌ Erreur tabula: {e}")
    
    # Méthode 4: pdfplumber pour tableaux simples
    try:
        with pdfplumber.open(file_path) as pdf:
            for page_num, page in enumerate(pdf.pages):
                tables = page.extract_tables()
                
                for i, table in enumerate(tables):
                    if table and len(table) > 1:  # Au moins 2 lignes
                        df = pd.DataFrame(table[1:], columns=table[0])
                        df_cleaned = clean_dataframe(df)
                        
                        if not df_cleaned.empty:
                            tables_data.append({
                                'table_id': f"page_{page_num}_table_{i}",
                                'method': 'pdfplumber',
                                'data': df_cleaned.to_dict('records'),
                                'shape': df_cleaned.shape,
                                'page': page_num
                            })
        
        if tables_data:
            print(f"✅ pdfplumber: {len(tables_data)} tableaux extraits")
            return tables_data
            
    except Exception as e:
        print(f"❌ Erreur pdfplumber tables: {e}")
    
    print(f"⚠️ Aucun tableau extrait de {file_path}")
    return []

def extract_text_and_tables_from_xhtml(file_path: str) -> Tuple[str, List[dict]]:
    """
    Extraction de texte et tableaux depuis XHTML/HTML
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
    except UnicodeDecodeError:
        # Essayer avec d'autres encodages
        for encoding in ['latin-1', 'cp1252', 'iso-8859-1']:
            try:
                with open(file_path, 'r', encoding=encoding) as file:
                    content = file.read()
                break
            except UnicodeDecodeError:
                continue
        else:
            print(f"❌ Impossible de lire le fichier {file_path}")
            return "", []
    
    soup = BeautifulSoup(content, 'html.parser')
    
    # Extraction du texte
    # Supprimer les scripts et styles
    for script in soup(["script", "style"]):
        script.decompose()
    
    # Extraire le texte principal
    text = soup.get_text()
    
    # Nettoyer le texte
    lines = (line.strip() for line in text.splitlines())
    chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
    extracted_text = ' '.join(chunk for chunk in chunks if chunk)
    
    # Extraction des tableaux
    tables_data = []
    tables = soup.find_all('table')
    
    for i, table in enumerate(tables):
        try:
            # Convertir le tableau HTML en DataFrame
            df = pd.read_html(str(table))[0]
            df_cleaned = clean_dataframe(df)
            
            if not df_cleaned.empty:
                tables_data.append({
                    'table_id': i,
                    'method': 'html_parsing',
                    'data': df_cleaned.to_dict('records'),
                    'shape': df_cleaned.shape
                })
        except Exception as e:
            print(f"❌ Erreur extraction tableau HTML {i}: {e}")
    
    print(f"✅ XHTML/HTML: {len(extracted_text)} caractères, {len(tables_data)} tableaux")
    return extracted_text, tables_data

def clean_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Nettoie un DataFrame extrait
    """
    # Supprimer les lignes et colonnes entièrement vides
    df = df.dropna(how='all').dropna(axis=1, how='all')
    
    # Remplacer les valeurs NaN par des chaînes vides
    df = df.fillna('')
    
    # Nettoyer les espaces en début/fin de chaîne
    df = df.applymap(lambda x: x.strip() if isinstance(x, str) else x)
    
    # Supprimer les lignes où toutes les cellules sont vides
    df = df[~(df == '').all(axis=1)]
    
    return df

def test_extraction(file_path: str):
    """
    Fonction de test pour débugger l'extraction
    """
    print(f"🔍 Test d'extraction pour: {file_path}")
    
    if file_path.lower().endswith('.pdf'):
        text = extract_text_from_pdf(file_path)
        tables = extract_tables_from_pdf(file_path)
        
        print(f"📄 Texte extrait: {len(text)} caractères")
        print(f"📊 Tableaux extraits: {len(tables)}")
        
        if text:
            print(f"Aperçu du texte: {text[:200]}...")
        
        return text, tables
    
    elif file_path.lower().endswith(('.html', '.xhtml')):
        text, tables = extract_text_and_tables_from_xhtml(file_path)
        
        print(f"📄 Texte extrait: {len(text)} caractères")
        print(f"📊 Tableaux extraits: {len(tables)}")
        
        if text:
            print(f"Aperçu du texte: {text[:200]}...")
        
        return text, tables
    
    else:
        print("❌ Format de fichier non supporté")
        return "", []

import re

def extract_scores(gpt_reply: str):
    """
    Extrait les scores ESG du texte de la réponse GPT.
    Retourne un dictionnaire avec global_score et E1 à E5.
    """
    scores = {
        "global_score": None,
        "e1_score": None,
        "e2_score": None,
        "e3_score": None,
        "e4_score": None,
        "e5_score": None,
    }

    # Extraction score global (sur 100)
    match_global = re.search(r"Score global.*?(\d{1,3})", gpt_reply, re.IGNORECASE)
    if match_global:
        scores["global_score"] = int(match_global.group(1))

    # Extraction scores E1 à E5 (sur 20)
    for i in range(1, 6):
        pattern = rf"Score E{i}.*?(\d{{1,2}})"
        match = re.search(pattern, gpt_reply, re.IGNORECASE)
        if match:
            scores[f"e{i}_score"] = int(match.group(1))

    return scores
