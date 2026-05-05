import sqlite3
import json
from datetime import datetime

def get_db_connection():
    conn = sqlite3.connect("esg_report.db")
    conn.row_factory = sqlite3.Row
    return conn

def create_users_table():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            first_name TEXT,
            last_name TEXT,
            email TEXT UNIQUE NOT NULL,
            hashed_password TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

def create_reports_table():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(""" 
        CREATE TABLE IF NOT EXISTS reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            filename TEXT NOT NULL,
            filepath TEXT NOT NULL,
            extracted_text TEXT,
            extracted_tables TEXT,
            upload_date TEXT,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    """)
    conn.commit()
    conn.close()

def drop_users_table():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DROP TABLE IF EXISTS users")
    conn.commit()
    conn.close()

def create_advanced_analysis_table():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS advanced_analyses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            report_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            analysis_text TEXT NOT NULL,
            scores_json TEXT NOT NULL,
            analysis_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            model_used TEXT DEFAULT 'gpt-4o',
            tokens_used INTEGER,
            FOREIGN KEY (report_id) REFERENCES reports (id),
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    conn.commit()
    conn.close()
    

def save_advanced_analysis(report_id: int, user_id: int, analysis_text: str, scores: dict, tokens_used: int = None, model_used: str = "gpt-4o"):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('''
            INSERT INTO advanced_analyses 
            (report_id, user_id, analysis_text, scores_json, tokens_used, model_used)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (report_id, user_id, analysis_text, json.dumps(scores), tokens_used, model_used))  # added model_used
        conn.commit()
        analysis_id = cursor.lastrowid  # get last inserted ID
        return analysis_id
    except Exception as e:
        conn.rollback()
        raise
    finally:
        conn.close()


def get_analysis_history(user_id: int = None, report_id: int = None, limit: int = 100):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        query = """
            SELECT a.*, r.filename
            FROM advanced_analyses a
            LEFT JOIN reports r ON a.report_id = r.id
        """
        conditions = []
        params = []
        if user_id is not None:
            conditions.append("a.user_id = ?")
            params.append(user_id)
        if report_id is not None:
            conditions.append("a.report_id = ?")
            params.append(report_id)
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        query += " ORDER BY a.id DESC LIMIT ?"
        params.append(limit)
        cursor.execute(query, params)
        rows = cursor.fetchall()
        results = []
        for row in rows:
            try:
                result = {
                    "id": row["id"],
                    "report_id": row["report_id"],
                    "user_id": row["user_id"],
                    "filename": row["filename"] if row["filename"] else f"Rapport {row['report_id']}",
                    "analysis_text": row["analysis_text"],
                    "analysis_date": row["analysis_date"],
                    "model_used": row["model_used"],
                    "tokens_used": row["tokens_used"] if "tokens_used" in row.keys() and row["tokens_used"] is not None else 0,
                    "scores": json.loads(row["scores_json"]) if row["scores_json"] else {}
                }
                results.append(result)
            except Exception as e:
                print(f"❌ Erreur traitement ligne analyse ID {row['id'] if 'id' in row.keys() else 'N/A'}: {e}")
        return results
    except Exception as e:
        print(f"❌ Erreur récupération historique analyses: {e}")
        return []
    finally:
        conn.close()

def get_latest_analysis(report_id: int, user_id: int):
    analyses = get_analysis_history(user_id=user_id, report_id=report_id, limit=1)
    if analyses:
        latest = analyses[0]
        return {
            "analysis_text": latest["analysis_text"],
            "scores": latest["scores"],
            "analysis_date": latest["analysis_date"],
            "model_used": latest["model_used"],
            "tokens_used": latest["tokens_used"]
        }
    return None


def create_ai_comparisons_table():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ai_comparisons (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            report1_id INTEGER NOT NULL,
            report2_id INTEGER NOT NULL,
            comparison_text TEXT NOT NULL,
            scores_json TEXT,
            comparison_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            model_used TEXT DEFAULT 'gpt-4o',
            tokens_used INTEGER,
            FOREIGN KEY(user_id) REFERENCES users(id),
            FOREIGN KEY(report1_id) REFERENCES reports(id),
            FOREIGN KEY(report2_id) REFERENCES reports(id)
        )
    ''')
    conn.commit()
    conn.close()

def save_ai_comparison(user_id: int, report1_id: int, report2_id: int, comparison_text: str, scores: dict, tokens_used: int = None , model_used="unknown"):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO ai_comparisons (user_id, report1_id, report2_id, comparison_text, scores_json, tokens_used)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (user_id, report1_id, report2_id, comparison_text, json.dumps(scores), tokens_used))
    conn.commit()
    conn.close()

def get_comparison_history(user_id: int = None, limit: int = 100):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        query = '''
            SELECT ac.*, r1.filename as filename1, r2.filename as filename2
            FROM ai_comparisons ac
            LEFT JOIN reports r1 ON ac.report1_id = r1.id
            LEFT JOIN reports r2 ON ac.report2_id = r2.id
        '''
        params = []
        if user_id is not None:
            query += " WHERE ac.user_id = ?"
            params.append(user_id)
        query += " ORDER BY ac.id DESC LIMIT ?"
        params.append(limit)
        cursor.execute(query, params)
        rows = cursor.fetchall()
        results = []
        for row in rows:
            try:
                result = {
                    "id": row["id"],
                    "report1_id": row["report1_id"],
                    "report2_id": row["report2_id"],
                    "filename1": row["filename1"] if row["filename1"] else f"Rapport {row['report1_id']}",
                    "filename2": row["filename2"] if row["filename2"] else f"Rapport {row['report2_id']}",
                    "comparison_text": row["comparison_text"],
                    "comparison_date": row["comparison_date"],
                    "model_used": row["model_used"],
                    "tokens_used": row["tokens_used"] or 0,
                    "scores": json.loads(row["scores_json"]) if row["scores_json"] else {}
                }
                results.append(result)
            except Exception as e:
                print(f"❌ Erreur traitement comparaison ID {row['id'] if 'id' in row.keys() else 'N/A'}: {e}")
        return results
    except Exception as e:
        print(f"❌ Erreur récupération historique comparaisons: {e}")
        return []
    finally:
        conn.close()

def get_latest_comparison(user_id: int, report1_id: int, report2_id: int):
    comparisons = get_comparison_history(user_id=user_id, limit=100)
    
    filtered = [
        comp for comp in comparisons
        if (comp["report1_id"] == report1_id and comp["report2_id"] == report2_id)
        or (comp["report1_id"] == report2_id and comp["report2_id"] == report1_id)
    ]
    
    if filtered:
        latest = filtered[0]
        return {
            "comparison_text": latest["comparison_text"],
            "scores": latest["scores"],
            "tokens_used": latest["tokens_used"],
            "comparison_date": latest["comparison_date"],
            "model_used": latest["model_used"]
        }
    
    return None


def initialize_advanced_features():
    print("🚀 Initialisation des fonctionnalités avancées...")
    try:
        create_advanced_analysis_table()
        create_ai_comparisons_table()
        print("✅ Toutes les tables avancées sont prêtes")
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM advanced_analyses")
        advanced_count = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM ai_comparisons")
        comparison_count = cursor.fetchone()[0]
        conn.close()
        print(f"📊 État actuel:\n   - {advanced_count} analyses avancées\n   - {comparison_count} comparaisons AI")
        return True
    except Exception as e:
        print(f"❌ Erreur initialisation: {e}")
        return False

if __name__ == "__main__":
    initialize_advanced_features()
