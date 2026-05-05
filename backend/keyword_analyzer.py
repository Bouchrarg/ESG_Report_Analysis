import json
import re
from typing import Dict, List, Tuple, Set
from collections import defaultdict, Counter
import os

class ESGKeywordAnalyzer:
    """
    Analyseur de mots-clés ESG basé sur les normes ESRS
    """
    
    def __init__(self, keywords_file_path: str = "esrs_keywords.json"):
        self.keywords_file = keywords_file_path
        self.keywords_data = self._load_keywords()
        self.context_window = 150  # Caractères autour du mot-clé pour le contexte
        
        # Nouveaux paramètres pour l'amélioration
        self.min_paragraph_length = 50  # Longueur minimale d'un paragraphe utile
        self.max_paragraph_length = 1000  # Longueur maximale pour éviter les blocs trop longs
        self.keyword_density_threshold = 0.02  # Densité minimale de mots-clés (2%)
        
        # Patterns pour détecter différents types de tableaux
        self.table_patterns = {
            'pipe_separated': r'\|.*\|',  # Tables avec |
            'tab_separated': r'\t.*\t',   # Tables avec tabs
            'aligned_columns': r'^\s*\w+\s{3,}\w+\s{3,}\w+',  # Colonnes alignées
            'dash_separated': r'-{3,}',   # Séparateurs avec tirets
            'structured_data': r'^\s*[\w\s]+:\s*[\d\w\s,.-]+$'  # Données structurées key:value
        }
    
    def _load_keywords(self) -> Dict:
        """Charge les mots-clés depuis le fichier JSON"""
        try:
            with open(self.keywords_file, 'r', encoding='utf-8') as file:
                return json.load(file)
        except FileNotFoundError:
            print(f"❌ Fichier {self.keywords_file} introuvable")
            return {}
        except json.JSONDecodeError as e:
            print(f"❌ Erreur de lecture JSON: {e}")
            return {}
    
    def extract_keywords_from_text(self, text: str, language: str = "french") -> Dict:
        """
        Extrait les mots-clés ESG du texte avec contexte et statistiques
        """
        if not text or not self.keywords_data:
            return {"error": "Texte vide ou mots-clés non chargés"}
        
        results = {
            "summary": {
                "total_keywords_found": 0,
                "categories_covered": [],
                "text_length": len(text),
                "analysis_date": None
            },
            "categories": {},
            "top_keywords": [],
            "coverage_score": 0,
            "recommendations": []
        }
        
        text_lower = text.lower()
        all_matches = []
        
        # Parcourir chaque catégorie ESRS
        for category_key, category_data in self.keywords_data.items():
            if "keywords" not in category_data:
                continue
                
            category_matches = {
                "category_name": category_data.get("sub_category", category_key),
                "matches": [],
                "total_occurrences": 0,
                "unique_keywords": 0
            }
            
            # Extraire les mots-clés de la langue sélectionnée
            keywords_list = category_data["keywords"].get(language, [])
            
            for keyword in keywords_list:
                # Recherche insensible à la casse avec mots entiers
                pattern = r'\b' + re.escape(keyword.lower()) + r'\b'
                matches = list(re.finditer(pattern, text_lower))
                
                if matches:
                    keyword_data = {
                        "keyword": keyword,
                        "occurrences": len(matches),
                        "positions": [],
                        "contexts": []
                    }
                    
                    # Extraire les contextes pour chaque occurrence
                    for match in matches:
                        start_pos = max(0, match.start() - self.context_window)
                        end_pos = min(len(text), match.end() + self.context_window)
                        context = text[start_pos:end_pos].strip()
                        
                        keyword_data["positions"].append(match.start())
                        keyword_data["contexts"].append({
                            "text": context,
                            "position": match.start()
                        })
                    
                    category_matches["matches"].append(keyword_data)
                    category_matches["total_occurrences"] += len(matches)
                    category_matches["unique_keywords"] += 1
                    
                    # Ajouter à la liste globale pour le top
                    all_matches.append({
                        "keyword": keyword,
                        "category": category_key,
                        "occurrences": len(matches)
                    })
            
            # Ajouter la catégorie aux résultats si elle a des matches
            if category_matches["matches"]:
                results["categories"][category_key] = category_matches
                results["summary"]["categories_covered"].append(category_data.get("sub_category", category_key))
        
        # Calculer les statistiques globales
        results["summary"]["total_keywords_found"] = len(all_matches)
        results["top_keywords"] = sorted(all_matches, key=lambda x: x["occurrences"], reverse=True)[:10]
        
        # Score de couverture (pourcentage de catégories ESRS couvertes)
        total_categories = len(self.keywords_data)
        covered_categories = len(results["categories"])
        results["coverage_score"] = round((covered_categories / total_categories) * 100, 2) if total_categories > 0 else 0
        
        # Recommandations basiques
        results["recommendations"] = self._generate_recommendations(results)
        all_found_keywords = [match["keyword"] for match in all_matches]

        # Extractions améliorées
        results["useful_paragraphs"] = self.extract_useful_paragraphs_enhanced(text, all_found_keywords, max_paragraphs=5)
        results["useful_tables"] = self.extract_useful_tables_enhanced(text, all_found_keywords, max_tables=3)
        
        # Nouvelles extractions
        results["key_sentences"] = self.extract_key_sentences(text, all_found_keywords, max_sentences=10)
        results["document_structure"] = self.analyze_document_structure(text, all_found_keywords)

        return results

    def extract_useful_paragraphs_enhanced(self, text: str, found_keywords: List[str], max_paragraphs: int = 5) -> List[str]:
        """
        Version améliorée de l'extraction de paragraphes avec scoring sophistiqué
        """
        if not found_keywords:
            return []
        
        # Différentes méthodes de segmentation des paragraphes
        paragraphs = []
        
        # 1. Segmentation par double saut de ligne
        paras_double_newline = [p.strip() for p in text.split('\n\n') if p.strip()]
        
        # 2. Segmentation par points + majuscule (phrases complètes)
        sentences = re.split(r'(?<=[.!?])\s+(?=[A-ZÀ-Ý])', text)
        
        # 3. Segmentation par sections (titres, sous-titres)
        sections = re.split(r'\n(?=[A-ZÀ-Ý][^\n]*:?\n)', text)
        
        # Combiner toutes les segmentations
        all_segments = paras_double_newline + sentences + sections
        
        # Filtrer et nettoyer
        paragraphs = []
        for segment in all_segments:
            segment = segment.strip()
            if (self.min_paragraph_length <= len(segment) <= self.max_paragraph_length and
                not self._is_header_or_footer(segment) and
                not self._is_table_of_contents(segment)):
                paragraphs.append(segment)
        
        # Supprimer les doublons en gardant l'ordre
        unique_paragraphs = []
        seen = set()
        for para in paragraphs:
            para_normalized = re.sub(r'\s+', ' ', para.lower())
            if para_normalized not in seen:
                seen.add(para_normalized)
                unique_paragraphs.append(para)
        
        # Scoring sophistiqué
        found_keywords_lower = [kw.lower() for kw in found_keywords]
        paragraph_scores = []
        
        for para in unique_paragraphs:
            para_lower = para.lower()
            score = self._calculate_paragraph_score(para, para_lower, found_keywords_lower)
            if score > 0:
                paragraph_scores.append((score, para))
        
        # Trier par score et prendre les meilleurs
        paragraph_scores.sort(key=lambda x: x[0], reverse=True)
        return [p[1] for p in paragraph_scores[:max_paragraphs]]
    
    def _calculate_paragraph_score(self, original_para: str, para_lower: str, keywords_lower: List[str]) -> float:
        """
        Calcule un score sophistiqué pour un paragraphe
        """
        score = 0.0
        
        # 1. Score basique : nombre d'occurrences de mots-clés
        keyword_count = sum(para_lower.count(kw) for kw in keywords_lower)
        score += keyword_count * 2
        
        # 2. Diversité des mots-clés (bonus si plusieurs mots-clés différents)
        unique_keywords_found = sum(1 for kw in keywords_lower if kw in para_lower)
        score += unique_keywords_found * 1.5
        
        # 3. Densité de mots-clés (éviter les paragraphes trop longs avec peu de mots-clés)
        word_count = len(para_lower.split())
        if word_count > 0:
            keyword_density = keyword_count / word_count
            if keyword_density >= self.keyword_density_threshold:
                score += keyword_density * 10
        
        # 4. Bonus pour les termes quantitatifs (chiffres, pourcentages, KPI)
        quantitative_patterns = [
            r'\d+%', r'\d+\s*tonnes?', r'\d+\s*kg', r'\d+\s*MW?h?',
            r'\d+\s*CO2', r'\d+\s*euros?', r'\d+\s*dollars?',
            r'réduction de \d+', r'augmentation de \d+', r'objectif.{0,20}\d+'
        ]
        for pattern in quantitative_patterns:
            if re.search(pattern, para_lower):
                score += 1.0
        
        # 5. Bonus pour les mots-clés de contexte ESG importants
        context_keywords = [
            'objectif', 'cible', 'indicateur', 'performance', 'mesure',
            'évaluation', 'risque', 'impact', 'amélioration', 'stratégie',
            'politique', 'engagement', 'conformité', 'certification'
        ]
        for ctx_kw in context_keywords:
            if ctx_kw in para_lower:
                score += 0.5
        
        # 6. Malus pour les phrases trop courtes ou trop génériques
        if len(original_para) < self.min_paragraph_length:
            score *= 0.5
        
        # 7. Bonus pour les sections importantes (titres avec mots-clés ESG)
        if self._is_important_section(original_para):
            score += 2.0
        
        return score
    
    def extract_useful_tables_enhanced(self, text: str, found_keywords: List[str], max_tables: int = 3) -> List[str]:
        """
        Version améliorée de l'extraction de tableaux avec détection multi-format
        """
        if not found_keywords:
            return []
        
        lines = text.split('\n')
        tables = []
        found_keywords_lower = [kw.lower() for kw in found_keywords]
        
        # 1. Détection de tableaux avec pipes (|)
        tables.extend(self._extract_pipe_tables(lines, found_keywords_lower))
        
        # 2. Détection de tableaux avec tabs ou espaces multiples
        tables.extend(self._extract_aligned_tables(lines, found_keywords_lower))
        
        # 3. Détection de données structurées (key-value pairs)
        tables.extend(self._extract_structured_data(lines, found_keywords_lower))
        
        # 4. Détection de listes avec valeurs numériques
        tables.extend(self._extract_data_lists(lines, found_keywords_lower))
        
        # Scoring et filtrage
        scored_tables = []
        for table in tables:
            score = self._calculate_table_score(table, found_keywords_lower)
            if score > 0:
                scored_tables.append((score, table))
        
        # Supprimer les doublons et trier
        unique_tables = self._remove_duplicate_tables(scored_tables)
        unique_tables.sort(key=lambda x: x[0], reverse=True)
        
        return [table[1] for table in unique_tables[:max_tables]]
    
    def _extract_pipe_tables(self, lines: List[str], keywords_lower: List[str]) -> List[str]:
        """Extrait les tableaux avec séparateurs |"""
        tables = []
        current_table = []
        in_table = False
        
        for line in lines:
            line = line.strip()
            if '|' in line and len(line.split('|')) >= 3:  # Au moins 2 colonnes
                current_table.append(line)
                in_table = True
            else:
                if in_table and current_table:
                    if self._table_contains_keywords(current_table, keywords_lower):
                        tables.append('\n'.join(current_table))
                    current_table = []
                    in_table = False
        
        # Traiter le dernier tableau si nécessaire
        if in_table and current_table and self._table_contains_keywords(current_table, keywords_lower):
            tables.append('\n'.join(current_table))
        
        return tables
    
    def _extract_aligned_tables(self, lines: List[str], keywords_lower: List[str]) -> List[str]:
        """Extrait les tableaux avec colonnes alignées"""
        tables = []
        current_table = []
        
        for i, line in enumerate(lines):
            line = line.strip()
            
            # Détecter les lignes qui ressemblent à des en-têtes de tableau
            if self._is_table_header(line) or self._is_aligned_data_row(line):
                current_table.append(line)
                
                # Regarder les lignes suivantes pour construire le tableau
                j = i + 1
                while j < len(lines) and (self._is_aligned_data_row(lines[j]) or lines[j].strip() == ''):
                    if lines[j].strip():
                        current_table.append(lines[j].strip())
                    j += 1
                
                if len(current_table) >= 2 and self._table_contains_keywords(current_table, keywords_lower):
                    tables.append('\n'.join(current_table))
                
                current_table = []
        
        return tables
    
    def _extract_structured_data(self, lines: List[str], keywords_lower: List[str]) -> List[str]:
        """Extrait les données structurées (key: value)"""
        tables = []
        current_block = []
        
        for line in lines:
            line = line.strip()
            
            # Détecter les lignes key:value
            if ':' in line and self._is_structured_data_line(line):
                current_block.append(line)
            elif current_block and line == '':
                # Fin d'un bloc
                if len(current_block) >= 3 and self._table_contains_keywords(current_block, keywords_lower):
                    tables.append('\n'.join(current_block))
                current_block = []
            elif not self._is_structured_data_line(line) and current_block:
                # Fin forcée du bloc
                if len(current_block) >= 3 and self._table_contains_keywords(current_block, keywords_lower):
                    tables.append('\n'.join(current_block))
                current_block = []
        
        # Traiter le dernier bloc
        if current_block and len(current_block) >= 3 and self._table_contains_keywords(current_block, keywords_lower):
            tables.append('\n'.join(current_block))
        
        return tables
    
    def _extract_data_lists(self, lines: List[str], keywords_lower: List[str]) -> List[str]:
        """Extrait les listes avec des données numériques"""
        tables = []
        current_list = []
        
        for line in lines:
            line = line.strip()
            
            # Détecter les éléments de liste avec données numériques
            if (line.startswith(('•', '-', '*', '○')) or 
                re.match(r'^\d+[\.\)]\s', line)) and self._contains_numeric_data(line):
                current_list.append(line)
            elif current_list:
                if len(current_list) >= 3 and self._table_contains_keywords(current_list, keywords_lower):
                    tables.append('\n'.join(current_list))
                current_list = []
        
        # Traiter la dernière liste
        if current_list and len(current_list) >= 3 and self._table_contains_keywords(current_list, keywords_lower):
            tables.append('\n'.join(current_list))
        
        return tables
    
    def extract_key_sentences(self, text: str, found_keywords: List[str], max_sentences: int = 10) -> List[str]:
        """
        Nouvelle fonction : extrait les phrases-clés les plus pertinentes
        """
        if not found_keywords:
            return []
        
        # Segmentation en phrases
        sentences = re.split(r'(?<=[.!?])\s+', text)
        sentences = [s.strip() for s in sentences if len(s.strip()) > 20]  # Filtrer les phrases trop courtes
        
        found_keywords_lower = [kw.lower() for kw in found_keywords]
        sentence_scores = []
        
        for sentence in sentences:
            sentence_lower = sentence.lower()
            score = 0
            
            # Score basé sur les mots-clés
            keyword_count = sum(sentence_lower.count(kw) for kw in found_keywords_lower)
            score += keyword_count * 2
            
            # Bonus pour les phrases avec des chiffres/KPI
            if re.search(r'\d+[%°]?|\d+\s*(tonnes?|kg|MW?h?|euros?|dollars?)', sentence_lower):
                score += 1
            
            # Bonus pour les phrases d'action/engagement
            action_words = ['objectif', 'engagement', 'réduction', 'amélioration', 'mise en œuvre', 'stratégie']
            if any(word in sentence_lower for word in action_words):
                score += 0.5
            
            if score > 0:
                sentence_scores.append((score, sentence))
        
        sentence_scores.sort(key=lambda x: x[0], reverse=True)
        return [s[1] for s in sentence_scores[:max_sentences]]
    
    def analyze_document_structure(self, text: str, found_keywords: List[str]) -> Dict:
        """
        Nouvelle fonction : analyse la structure du document
        """
        structure = {
            "total_sections": 0,
            "sections_with_esg": 0,
            "main_topics": [],
            "document_type": "unknown",
            "esg_distribution": {}
        }
        
        # Détecter les titres/sections
        sections = re.findall(r'^[A-ZÀ-Ý][^a-z\n]*$', text, re.MULTILINE)
        structure["total_sections"] = len(sections)
        
        # Analyser quelles sections contiennent des mots-clés ESG
        found_keywords_lower = [kw.lower() for kw in found_keywords]
        sections_with_keywords = 0
        
        for section in sections:
            if any(kw in section.lower() for kw in found_keywords_lower):
                sections_with_keywords += 1
        
        structure["sections_with_esg"] = sections_with_keywords
        
        # Détecter le type de document
        if "rapport annuel" in text.lower() or "annual report" in text.lower():
            structure["document_type"] = "rapport_annuel"
        elif "durabilité" in text.lower() or "sustainability" in text.lower():
            structure["document_type"] = "rapport_durabilite"
        elif "rse" in text.lower() or "csr" in text.lower():
            structure["document_type"] = "rapport_rse"
        
        return structure
    
    # Fonctions utilitaires améliorées
    def _is_header_or_footer(self, text: str) -> bool:
        """Détecter les en-têtes et pieds de page"""
        text_lower = text.lower()
        header_footer_patterns = [
            r'page \d+', r'^\d+$', r'copyright', r'tous droits réservés',
            r'confidentiel', r'document interne', r'version \d+',
            r'table des matières', r'sommaire'
        ]
        return any(re.search(pattern, text_lower) for pattern in header_footer_patterns)
    
    def _is_table_of_contents(self, text: str) -> bool:
        """Détecter les tables des matières"""
        return (text.count('...') > 3 or 
                text.count('..') > 3 or
                re.search(r'\d+\s*$', text))
    
    def _is_important_section(self, text: str) -> bool:
        """Détecter les sections importantes"""
        important_keywords = [
            'objectifs', 'stratégie', 'performance', 'résultats',
            'indicateurs', 'gouvernance', 'risques', 'opportunités'
        ]
        return any(kw in text.lower() for kw in important_keywords)
    
    def _is_table_header(self, line: str) -> bool:
        """Détecter les en-têtes de tableau"""
        return (len(line.split()) >= 2 and 
                not re.search(r'\d', line) and
                len(line) < 100)
    
    def _is_aligned_data_row(self, line: str) -> bool:
        """Détecter les lignes de données alignées"""
        return (re.search(r'\s{3,}', line) and  # Au moins 3 espaces consécutifs
                len(line.split()) >= 2 and
                any(c.isdigit() for c in line))
    
    def _is_structured_data_line(self, line: str) -> bool:
        """Détecter les lignes de données structurées"""
        return (':' in line and 
                not line.endswith(':') and
                len(line.split(':')) == 2)
    
    def _contains_numeric_data(self, line: str) -> bool:
        """Vérifier si une ligne contient des données numériques"""
        return re.search(r'\d+[%°]?|\d+\s*(kg|t|MW?h?|€|$|tonnes?)', line)
    
    def _table_contains_keywords(self, table_lines: List[str], keywords_lower: List[str]) -> bool:
        """Vérifier si un tableau contient des mots-clés"""
        table_text = ' '.join(table_lines).lower()
        return any(kw in table_text for kw in keywords_lower)
    
    def _calculate_table_score(self, table: str, keywords_lower: List[str]) -> float:
        """Calculer le score d'un tableau"""
        score = 0.0
        table_lower = table.lower()
        
        # Score basique : mots-clés trouvés
        keyword_count = sum(table_lower.count(kw) for kw in keywords_lower)
        score += keyword_count * 2
        
        # Bonus pour les données numériques
        numeric_matches = len(re.findall(r'\d+[%°]?|\d+\s*[a-zA-Z]+', table))
        score += numeric_matches * 0.5
        
        # Bonus pour la structure (nombre de lignes/colonnes)
        lines = table.split('\n')
        if len(lines) >= 3:  # Au moins 3 lignes
            score += 1
        
        return score
    
    def _remove_duplicate_tables(self, scored_tables: List[Tuple[float, str]]) -> List[Tuple[float, str]]:
        """Supprimer les tableaux dupliqués"""
        unique_tables = []
        seen_content = set()
        
        for score, table in scored_tables:
            # Normaliser le contenu pour la comparaison
            normalized = re.sub(r'\s+', ' ', table.lower().strip())
            if normalized not in seen_content:
                seen_content.add(normalized)
                unique_tables.append((score, table))
        
        return unique_tables
    
    def _generate_recommendations(self, analysis_results: Dict) -> List[str]:
        """Génère des recommandations basées sur l'analyse"""
        recommendations = []
        
        coverage_score = analysis_results["coverage_score"]
        categories_covered = len(analysis_results["categories"])
        
        if coverage_score < 40:
            recommendations.append("🔴 Couverture ESG insuffisante - Envisagez d'inclure plus de critères environnementaux")
        elif coverage_score < 70:
            recommendations.append("🟡 Couverture ESG partielle - Certaines catégories ESRS manquent")
        else:
            recommendations.append("🟢 Bonne couverture ESG - La plupart des catégories ESRS sont présentes")
        
        # Recommandations spécifiques par catégorie manquante
        all_categories = set(self.keywords_data.keys())
        covered_categories = set(analysis_results["categories"].keys())
        missing_categories = all_categories - covered_categories
        
        if "ESRS_E1_CLIMATE_CHANGE" in missing_categories:
            recommendations.append("⚠️ Ajoutez des informations sur le changement climatique (E1)")
        if "ESRS_E2_POLLUTION" in missing_categories:
            recommendations.append("⚠️ Incluez des données sur la pollution (E2)")
        if "ESRS_E3_WATER_MARINE" in missing_categories:
            recommendations.append("⚠️ Mentionnez la gestion de l'eau et des ressources marines (E3)")
        if "ESRS_E4_BIODIVERSITY" in missing_categories:
            recommendations.append("⚠️ Ajoutez des éléments sur la biodiversité (E4)")
        if "ESRS_E5_CIRCULAR_ECONOMY" in missing_categories:
            recommendations.append("⚠️ Intégrez des aspects d'économie circulaire (E5)")
        
        return recommendations