import React, { useState, useEffect } from "react";
import { API_BASE } from './config';
import { motion } from "framer-motion";
import UploadTrigger from "./UploadReport";
import ReportsList from "./ReportsList";
import Profile from "./profile";
import { getUserIdFromToken } from "./utils/auth";
import { FileText, Table, ChevronDown, ChevronUp } from 'lucide-react';


const textVariants = {
  hidden: { opacity: 0, y: 30 },
  visible: {
    opacity: 1,
    y: 0,
    transition: { duration: 1.2 },
  },
};

function Dashboard() {
  const userId = getUserIdFromToken();
  const [selectedReport, setSelectedReport] = useState(null);
  const [analysisResult, setAnalysisResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState("");
  
  // États pour l'analyse par mots-clés
  const [keywordAnalysisResult, setKeywordAnalysisResult] = useState(null);
  const [loadingKeywords, setLoadingKeywords] = useState(false);
  const [keywordError, setKeywordError] = useState("");
  const [selectedLanguage, setSelectedLanguage] = useState("french");
  
  // États pour la comparaison
  const [comparisonMode, setComparisonMode] = useState(false);
  const [selectedReport1, setSelectedReport1] = useState(null);
  const [selectedReport2, setSelectedReport2] = useState(null);
  const [comparisonResult, setComparisonResult] = useState(null);
  const [loadingComparison, setLoadingComparison] = useState(false);
  const [comparisonError, setComparisonError] = useState("");
  const [reports, setReports] = useState([]);
  
  // États pour la comparaison par mots-clés
  const [keywordComparisonResult, setKeywordComparisonResult] = useState(null);
  const [loadingKeywordComparison, setLoadingKeywordComparison] = useState(false);
  const [keywordComparisonError, setKeywordComparisonError] = useState("");
  
  // État pour le mode d'analyse (IA ou mots-clés)
  const [analysisMode, setAnalysisMode] = useState("ai"); // "ai" ou "keywords"
  
  const [expandedParagraphs, setExpandedParagraphs] = useState(new Set());
  const [expandedTables, setExpandedTables] = useState(new Set());

  const [refreshingAI, setRefreshingAI] = useState(false);

  // Récupérer la liste des rapports pour la comparaison
  useEffect(() => {
    if (userId) {
      fetchReports();
    }
  }, [userId]);

  useEffect(() => {
  if (userId) {
    fetchUserStatistics();
  }
}, [userId]);


  const fetchUserStatistics = async () => {
    if (!userId) return;

    try {
      const res = await fetch(`${API_BASE}/analysis-history/by-user/${userId}`);
      const data = await res.json();
      
      if (data.status === "success") {
        setUserStatistics(data.statistics);
        // Vous pouvez aussi mettre à jour les historiques en même temps
        setAnalysisHistory(data.analyses || []);
        setComparisonHistory(data.comparisons || []);
      }
    } catch (error) {
      console.error("Erreur chargement statistiques utilisateur:", error);
    }
  };

  const fetchReports = async () => {
    try {
      const response = await fetch(`${API_BASE}/reports/${userId}`);
      if (response.ok) {
        const data = await response.json();
        setReports(data);
      }
    } catch (error) {
      console.error("Erreur lors de la récupération des rapports:", error);
    }
  };

  // Analyse IA existante
  const handleAnalyse = async () => {
  if (!selectedReport?.id) return;

  setLoading(true);
  setErrorMsg("");
  setAnalysisResult(null);

  try {
    const response = await fetch(
      `${API_BASE}/analyse-report/${selectedReport.id}?user_id=${userId}`,
      {
        method: "GET",
        headers: {
          "Content-Type": "application/json",
        },
      }
    );

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || "Erreur lors de l'analyse");
    }

    const data = await response.json();

    //  je stockes à la fois le texte de l’analyse et les scores
    setAnalysisResult({
      analysis_text: data.analysis_text,
      scores: data.scores,
      tokens_used: data.tokens_used,
    });

  } catch (error) {
    console.error("Analyse error:", error.message);
    setErrorMsg("❌ Échec de l'analyse : " + error.message);
  } finally {
    setLoading(false);
  }
};

const handleRefreshComparison = async () => {
  if (!selectedReport1 || !selectedReport2) return;

  setLoadingComparison(true);
  setComparisonError("");

  try {
    const response = await fetch(`${API_BASE}/refresh-comparison`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        user_id: userId,
        report1_id: selectedReport1.id,
        report2_id: selectedReport2.id
      })
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || "Erreur lors de la comparaison IA");
    }

    const data = await response.json();
    setComparisonResult(data);
  } catch (err) {
    setComparisonError("❌ Erreur lors du rafraîchissement de la comparaison IA : " + err.message);
  } finally {
    setLoadingComparison(false);
  }
};

  // NOUVELLE FONCTION : Analyse par mots-clés
  const handleKeywordAnalysis = async () => {
    if (!selectedReport?.id) return;

    setLoadingKeywords(true);
    setKeywordError("");
    setKeywordAnalysisResult(null);

    try {
      const response = await fetch(
        `${API_BASE}/analyze-keywords/${selectedReport.id}?language=${selectedLanguage}`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
        }
      );

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || "Erreur lors de l'analyse par mots-clés");
      }

      const data = await response.json();
      setKeywordAnalysisResult(data.analysis);
    } catch (error) {
      console.error("Keyword analysis error:", error.message);
      setKeywordError("❌ Échec de l'analyse par mots-clés : " + error.message);
    } finally {
      setLoadingKeywords(false);
    }
  };
  const handleRefreshAnalysis = async () => {
  if (!selectedReport || !userId) return;

  setRefreshingAI(true);
  setErrorMsg("");

  try {
    const response = await fetch(
      `/analyse-report/${selectedReport.id}/refresh?user_id=${userId}`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
      }
    );

    if (!response.ok) throw new Error("Erreur lors du rafraîchissement");

    const data = await response.json();

    setAnalysisResult({
      analysis_text: data.analysis_text,
      scores: data.scores,
      tokens_used: data.tokens_used,
    });

  } catch (err) {
    console.error(err);
    setErrorMsg("Une erreur est survenue lors du rafraîchissement de l’analyse IA.");
  } finally {
    setRefreshingAI(false);
  }
};
const refreshUserData = async () => {
  await fetchUserStatistics();
  if (selectedReport) {
    // Rafraîchir l'historique du rapport sélectionné
    try {
      const res = await fetch(`${API_BASE}/analysis-history/by-report/${selectedReport.id}`);
      const data = await res.json();
      if (data.status === "success") {
        setAnalysisHistory(data.history);
      }
    } catch (error) {
      console.error("Erreur refresh historique:", error);
    }
  }
};

  // Comparaison IA existante
const handleCompareReports = async () => {

  // Validation des rapports sélectionnés
  if (!selectedReport1?.id || !selectedReport2?.id) {
    setComparisonError("❌ Veuillez sélectionner deux rapports différents");
    return;
  }

  if (selectedReport1.id === selectedReport2.id) {
    setComparisonError("❌ Veuillez sélectionner deux rapports différents");
    return;
  }

  // Validation du userId récupéré
  if (!userId) {
    setComparisonError("❌ Utilisateur non connecté");
    return;
  }

  setLoadingComparison(true);
  setComparisonError("");
  setComparisonResult(null);

  try {
    console.log("🔄 Début comparaison:", {
      user_id: userId,
      report1_id: selectedReport1.id,
      report2_id: selectedReport2.id
    });

    const response = await fetch(`${API_BASE}/compare-reports`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        user_id: userId,           // Utilisation de userId récupéré
        report1_id: selectedReport1.id,
        report2_id: selectedReport2.id,
      }),
    });

    console.log("📡 Réponse HTTP status:", response.status);

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ 
        detail: `Erreur HTTP ${response.status}` 
      }));
      console.error("❌ Erreur serveur:", errorData);
      throw new Error(errorData.detail || "Erreur lors de la comparaison");
    }

    const data = await response.json();
    console.log("✅ Comparaison réussie:", data);
    setComparisonResult(data);

  } catch (error) {
    console.error("❌ Comparison error:", error.message);
    setComparisonError("❌ Échec de la comparaison : " + error.message);
  } finally {
    setLoadingComparison(false);
  }
};

  // NOUVELLE FONCTION : Comparaison par mots-clés
  const handleKeywordComparison = async () => {
    if (!selectedReport1?.id || !selectedReport2?.id) {
      setKeywordComparisonError("❌ Veuillez sélectionner deux rapports différents");
      return;
    }

    if (selectedReport1.id === selectedReport2.id) {
      setKeywordComparisonError("❌ Veuillez sélectionner deux rapports différents");
      return;
    }

    setLoadingKeywordComparison(true);
    setKeywordComparisonError("");
    setKeywordComparisonResult(null);

    try {
      const response = await fetch(`${API_BASE}/compare-keywords?language=${selectedLanguage}`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          user_id: userId,
          report1_id: selectedReport1.id,
          report2_id: selectedReport2.id,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || "Erreur lors de la comparaison par mots-clés");
      }

      const data = await response.json();
      setKeywordComparisonResult(data.data);
    } catch (error) {
      console.error("Keyword comparison error:", error.response?.data || error.message || error);      setKeywordComparisonError("❌ Échec de la comparaison par mots-clés : " + error.message);
    } finally {
      setLoadingKeywordComparison(false);
    }
  };

  const resetComparison = () => {
    setComparisonMode(false);
    setSelectedReport1(null);
    setSelectedReport2(null);
    setComparisonResult(null);
    setComparisonError("");
    setKeywordComparisonResult(null);
    setKeywordComparisonError("");
  };

  // NOUVELLE FONCTION : Reset de l'analyse individuelle
  const resetAnalysis = () => {
    setAnalysisResult(null);
    setKeywordAnalysisResult(null);
    setErrorMsg("");
    setKeywordError("");
    setExpandedParagraphs(new Set());
    setExpandedTables(new Set());
  };

  // Fonctions de téléchargement existantes
const downloadAnalysisHTML = () => {
  if (!analysisResult || !analysisResult.analysis_text) return;

  const htmlContent = `
    <html>
      <head>
        <meta charset="UTF-8">
        <title>Analyse ESG</title>
        <style>
          body { font-family: Arial, sans-serif; padding: 20px; white-space: pre-wrap; }
          h1 { color: #2c3e50; }
        </style>
      </head>
      <body>
        <h1>Analyse ESG</h1>
        <pre>${analysisResult.analysis_text}</pre>
      </body>
    </html>
  `;

  const blob = new Blob([htmlContent], { type: "text/html" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `analyse_esg_${selectedReport.id}_${new Date().toISOString().slice(0, 10)}.html`;
  a.click();
  URL.revokeObjectURL(url);
};
const downloadAnalysisJSON = () => {
  if (!analysisResult) return;

  const jsonString = JSON.stringify(analysisResult, null, 2); // Beautify
  const blob = new Blob([jsonString], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `analyse_esg_${selectedReport.id}_${new Date().toISOString().slice(0, 10)}.json`;
  a.click();
  URL.revokeObjectURL(url);
};


  // NOUVELLE FONCTION : Téléchargement analyse mots-clés
  const downloadKeywordAnalysisJSON = async () => {
    if (!selectedReport?.id) return;
    
    try {
      const response = await fetch(`${API_BASE}/export-keywords-analysis/${selectedReport.id}?format=json`, {
        method: 'GET',
        headers: { 'Content-Type': 'application/json' }
      });
      
      if (response.ok) {
        const blob = await response.blob();
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `keywords_analysis_${selectedReport.id}_${new Date().toISOString().slice(0,10)}.json`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
      }
    } catch (error) {
      console.error('Erreur téléchargement JSON mots-clés:', error);
    }
  };

const downloadComparisonHTML = async () => {
  const userId = getUserIdFromToken();  // Directement ici
  if (!selectedReport1?.id || !selectedReport2?.id || !userId) {
    alert("Veuillez sélectionner deux rapports et être connecté.");
    return;
  }

  try {
    const response = await fetch(`${API_BASE}/download-comparison-pdf`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        user_id: userId,
        report1_id: selectedReport1.id,
        report2_id: selectedReport2.id,
      }),
    });

    if (!response.ok) throw new Error("Erreur lors du téléchargement HTML");

    const blob = await response.blob();
    const url = window.URL.createObjectURL(blob);

    const a = document.createElement("a");
    a.href = url;
    a.download = `comparaison_${selectedReport1.id}_vs_${selectedReport2.id}.html`;
    document.body.appendChild(a);
    a.click();
    a.remove();
    URL.revokeObjectURL(url);
  } catch (error) {
    console.error("❌ Erreur HTML:", error);
    alert("Échec du téléchargement HTML");
  }
};


  const toggleParagraph = (index) => {
  const newExpanded = new Set(expandedParagraphs);
  if (newExpanded.has(index)) {
    newExpanded.delete(index);
  } else {
    newExpanded.add(index);
  }
  setExpandedParagraphs(newExpanded);
};

const toggleTable = (index) => {
  const newExpanded = new Set(expandedTables);
  if (newExpanded.has(index)) {
    newExpanded.delete(index);
  } else {
    newExpanded.add(index);
  }
  setExpandedTables(newExpanded);
};

const truncateText = (text, maxLength = 200) => {
  if (text.length <= maxLength) return text;
  return text.substring(0, maxLength) + "...";
};
  const downloadComparisonJSON = async () => {
  const userId = getUserIdFromToken();  // récupère l'user ID depuis le token (localStorage, cookie, etc.)

  if (!selectedReport1?.id || !selectedReport2?.id || !userId) {
    alert("Veuillez sélectionner deux rapports et être connecté.");
    return;
  }

  try {
    const response = await fetch(`${API_BASE}/download-comparison-json`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        user_id: userId,
        report1_id: selectedReport1.id,
        report2_id: selectedReport2.id,
      }),
    });

    if (!response.ok) throw new Error("Erreur lors du téléchargement JSON");

    const blob = await response.blob();
    const url = window.URL.createObjectURL(blob);

    const a = document.createElement("a");
    a.href = url;
    a.download = `comparaison_${selectedReport1.id}_vs_${selectedReport2.id}.json`;
    document.body.appendChild(a);
    a.click();
    a.remove();
    URL.revokeObjectURL(url);
  } catch (error) {
    console.error("❌ Erreur JSON:", error);
    alert("Échec du téléchargement JSON");
  }
};


  // NOUVELLE FONCTION : Rendu des résultats d'analyse par mots-clés
  const renderKeywordAnalysisResults = () => {
    if (!keywordAnalysisResult) return null;

    const { summary, categories, top_keywords, coverage_score, recommendations } = keywordAnalysisResult;

    return (
      <div className="mt-8 p-6 border rounded-lg bg-emerald-50">
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-xl font-bold text-emerald-800">
            🔍 Analyse par mots-clés ESRS
          </h3>
          <div className="flex gap-2">
            <button
              onClick={downloadKeywordAnalysisJSON}
              className="px-4 py-2 bg-emerald-600 text-white rounded hover:bg-emerald-700 transition text-sm font-medium"
              title="Télécharger l'analyse détaillée"
            >
              📊 Export JSON
            </button>
          </div>
        </div>

        {/* Résumé global */}
        <div className="bg-white p-4 rounded-lg shadow-sm mb-4">
          <div className="grid md:grid-cols-3 gap-4 mb-4">
            <div className="text-center p-3 bg-blue-50 rounded">
              <div className="text-2xl font-bold text-blue-600">{summary.total_keywords_found}</div>
              <div className="text-sm text-blue-800">mots-clés trouvés</div>
            </div>
            <div className="text-center p-3 bg-green-50 rounded">
              <div className="text-2xl font-bold text-green-600">{coverage_score}%</div>
              <div className="text-sm text-green-800">couverture ESRS</div>
            </div>
            <div className="text-center p-3 bg-purple-50 rounded">
              <div className="text-2xl font-bold text-purple-600">{summary.categories_covered.length}</div>
              <div className="text-sm text-purple-800">catégories couvertes</div>
            </div>
          </div>
        </div>

        {/* Recommandations */}
        {recommendations && recommendations.length > 0 && (
          <div className="bg-white p-4 rounded-lg shadow-sm mb-4">
            <h4 className="font-semibold text-gray-800 mb-2">📋 Recommandations :</h4>
            <ul className="space-y-1">
              {recommendations.map((rec, index) => (
                <li key={index} className="text-sm text-gray-700">{rec}</li>
              ))}
            </ul>
          </div>
        )}

        {/* Top mots-clés */}
        {top_keywords && top_keywords.length > 0 && (
          <div className="bg-white p-4 rounded-lg shadow-sm mb-4">
            <h4 className="font-semibold text-gray-800 mb-2">🏆 Mots-clés les plus fréquents :</h4>
            <div className="flex flex-wrap gap-2">
              {top_keywords.slice(0, 10).map((keyword, index) => (
                <span 
                  key={index}
                  className="px-3 py-1 bg-indigo-100 text-indigo-800 rounded-full text-sm font-medium"
                >
                  {keyword.keyword} ({keyword.occurrences})
                </span>
              ))}
            </div>
          </div>
        )}
        
        {/* Détail par catégorie */}
        <div className="bg-white p-4 rounded-lg shadow-sm">
          <h4 className="font-semibold text-gray-800 mb-3">📊 Détail par catégorie ESRS :</h4>
          <div className="space-y-3">
            {Object.entries(categories).map(([categoryKey, categoryData]) => (
              <div key={categoryKey} className="border-l-4 border-indigo-400 pl-4">
                <div className="flex justify-between items-center mb-2">
                  <h5 className="font-medium text-gray-800">{categoryData.category_name}</h5>
                  <span className="text-sm text-gray-600">
                    {categoryData.unique_keywords} mots-clés • {categoryData.total_occurrences} occurrences
                  </span>
                </div>
                <div className="flex flex-wrap gap-1">
                  {categoryData.matches.slice(0, 5).map((match, index) => (
                    <span 
                      key={index}
                      className="px-2 py-1 bg-gray-100 text-gray-700 rounded text-xs"
                      title={`${match.occurrences} occurrence(s)`}
                    >
                      {match.keyword}
                    </span>
                  ))}
                  {categoryData.matches.length > 5 && (
                    <span className="px-2 py-1 bg-gray-200 text-gray-600 rounded text-xs">
                      +{categoryData.matches.length - 5} autres...
                    </span>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
          {renderParagraphsAndTables()}

      </div>
    );
  };
const renderParagraphsAndTables = () => {
  if (!keywordAnalysisResult) return null;

  return (
    <div className="space-y-6">
      {/* Paragraphes les plus pertinents - Version améliorée */}
      {keywordAnalysisResult.useful_paragraphs && keywordAnalysisResult.useful_paragraphs.length > 0 && (
        <div className="bg-gradient-to-r from-blue-50 to-indigo-50 rounded-xl shadow-sm border border-blue-200">
          <div className="p-6">
            <div className="flex items-center gap-3 mb-6">
              <div className="p-2 bg-blue-100 rounded-lg">
                <FileText className="w-5 h-5 text-blue-600" />
              </div>
              <h4 className="text-xl font-semibold text-gray-900">
                Paragraphes les plus pertinents
              </h4>
              <span className="px-3 py-1 bg-blue-100 text-blue-700 rounded-full text-sm font-medium">
                {keywordAnalysisResult.useful_paragraphs.length} trouvé(s)
              </span>
            </div>
            
            <div className="space-y-4">
              {keywordAnalysisResult.useful_paragraphs.map((para, idx) => {
                const isExpanded = expandedParagraphs.has(idx);
                const shouldTruncate = para.length > 200;
                
                return (
                  <div
                    key={idx}
                    className="bg-white rounded-lg border border-gray-200 hover:border-blue-300 transition-all duration-200 hover:shadow-md"
                  >
                    <div className="p-5">
                      <div className="flex items-start justify-between mb-3">
                        <span className="inline-flex items-center px-2 py-1 bg-blue-100 text-blue-800 text-xs font-medium rounded-full">
                          Paragraphe {idx + 1}
                        </span>
                        {shouldTruncate && (
                          <button
                            onClick={() => toggleParagraph(idx)}
                            className="flex items-center gap-1 px-3 py-1 text-sm text-blue-600 hover:text-blue-800 hover:bg-blue-50 rounded-md transition-colors"
                          >
                            {isExpanded ? (
                              <>
                                <ChevronUp className="w-4 h-4" />
                                Réduire
                              </>
                            ) : (
                              <>
                                <ChevronDown className="w-4 h-4" />
                                Voir plus
                              </>
                            )}
                          </button>
                        )}
                      </div>
                      <p className="text-gray-700 leading-relaxed text-justify">
                        {isExpanded || !shouldTruncate ? para : truncateText(para)}
                      </p>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      )}

      {/* Tableaux détectés - Version améliorée */}
      {keywordAnalysisResult.useful_tables && keywordAnalysisResult.useful_tables.length > 0 && (
        <div className="bg-gradient-to-r from-emerald-50 to-teal-50 rounded-xl shadow-sm border border-emerald-200">
          <div className="p-6">
            <div className="flex items-center gap-3 mb-6">
              <div className="p-2 bg-emerald-100 rounded-lg">
                <Table className="w-5 h-5 text-emerald-600" />
              </div>
              <h4 className="text-xl font-semibold text-gray-900">
                Tableaux détectés
              </h4>
              <span className="px-3 py-1 bg-emerald-100 text-emerald-700 rounded-full text-sm font-medium">
                {keywordAnalysisResult.useful_tables.length} trouvé(s)
              </span>
            </div>
            
            <div className="space-y-4">
              {keywordAnalysisResult.useful_tables.map((tableStr, idx) => {
                const isExpanded = expandedTables.has(idx);
                const lines = tableStr.split('\n');
                const shouldTruncate = lines.length > 6;
                const displayLines = isExpanded || !shouldTruncate ? lines : lines.slice(0, 6);
                
                return (
                  <div
                    key={idx}
                    className="bg-white rounded-lg border border-gray-200 hover:border-emerald-300 transition-all duration-200 hover:shadow-md"
                  >
                    <div className="p-5">
                      <div className="flex items-start justify-between mb-3">
                        <span className="inline-flex items-center px-2 py-1 bg-emerald-100 text-emerald-800 text-xs font-medium rounded-full">
                          Tableau {idx + 1}
                        </span>
                        {shouldTruncate && (
                          <button
                            onClick={() => toggleTable(idx)}
                            className="flex items-center gap-1 px-3 py-1 text-sm text-emerald-600 hover:text-emerald-800 hover:bg-emerald-50 rounded-md transition-colors"
                          >
                            {isExpanded ? (
                              <>
                                <ChevronUp className="w-4 h-4" />
                                Réduire
                              </>
                            ) : (
                              <>
                                <ChevronDown className="w-4 h-4" />
                                Voir plus ({lines.length - 6} lignes)
                              </>
                            )}
                          </button>
                        )}
                      </div>
                      <div className="bg-gray-50 rounded-lg p-4 border border-gray-200">
                        <pre className="text-sm text-gray-800 font-mono whitespace-pre-wrap overflow-x-auto">
                          {displayLines.join('\n')}
                          {shouldTruncate && !isExpanded && '\n...'}
                        </pre>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

  const renderKeywordComparisonResults = () => {
    if (!keywordComparisonResult) return null;

    const { report1, report2, comparison } = keywordComparisonResult;

    return (
      <div className="mt-8 p-6 border rounded-lg bg-gradient-to-r from-emerald-50 to-teal-50">
        <h3 className="text-xl font-bold text-emerald-800 mb-4">
          🔍 Comparaison par mots-clés ESRS
        </h3>

        {/* Scores de couverture */}
        <div className="bg-white p-4 rounded-lg shadow-sm mb-4">
          <h4 className="font-semibold text-gray-800 mb-3">📊 Scores de couverture :</h4>
          <div className="grid md:grid-cols-3 gap-4">
            <div className="text-center p-3 bg-blue-50 rounded">
              <div className="text-lg font-bold text-blue-600">{comparison.coverage_comparison.report1_score}%</div>
              <div className="text-sm text-blue-800">{report1.filename}</div>
            </div>
            <div className="text-center p-3 bg-purple-50 rounded">
              <div className="text-lg font-bold text-purple-600">{comparison.coverage_comparison.report2_score}%</div>
              <div className="text-sm text-purple-800">{report2.filename}</div>
            </div>
            <div className="text-center p-3 bg-gray-50 rounded">
              <div className={`text-lg font-bold ${comparison.coverage_comparison.difference > 0 ? 'text-green-600' : comparison.coverage_comparison.difference < 0 ? 'text-red-600' : 'text-gray-600'}`}>
                {comparison.coverage_comparison.difference > 0 ? '+' : ''}{comparison.coverage_comparison.difference.toFixed(1)}%
              </div>
              <div className="text-sm text-gray-800">Différence</div>
            </div>
          </div>
        </div>

        {/* Mots-clés communs */}
        {comparison.common_keywords.length > 0 && (
          <div className="bg-white p-4 rounded-lg shadow-sm mb-4">
            <h4 className="font-semibold text-gray-800 mb-2">🤝 Mots-clés communs ({comparison.common_keywords.length}) :</h4>
            <div className="flex flex-wrap gap-2">
              {comparison.common_keywords.slice(0, 15).map((keyword, index) => (
                <span key={index} className="px-2 py-1 bg-green-100 text-green-800 rounded text-sm">
                  {keyword}
                </span>
              ))}
              {comparison.common_keywords.length > 15 && (
                <span className="px-2 py-1 bg-gray-200 text-gray-600 rounded text-sm">
                  +{comparison.common_keywords.length - 15} autres...
                </span>
              )}
            </div>
          </div>
        )}

        {/* Mots-clés uniques */}
        <div className="grid md:grid-cols-2 gap-4">
          {comparison.unique_to_report1.length > 0 && (
            <div className="bg-white p-4 rounded-lg shadow-sm">
              <h4 className="font-semibold text-blue-800 mb-2">
                🔹 Uniques à {report1.filename} ({comparison.unique_to_report1.length}) :
              </h4>
              <div className="flex flex-wrap gap-1">
                {comparison.unique_to_report1.slice(0, 10).map((keyword, index) => (
                  <span key={index} className="px-2 py-1 bg-blue-100 text-blue-800 rounded text-xs">
                    {keyword}
                  </span>
                ))}
                {comparison.unique_to_report1.length > 10 && (
                  <span className="px-2 py-1 bg-gray-200 text-gray-600 rounded text-xs">
                    +{comparison.unique_to_report1.length - 10}...
                  </span>
                )}
              </div>
            </div>
          )}

          {comparison.unique_to_report2.length > 0 && (
            <div className="bg-white p-4 rounded-lg shadow-sm">
              <h4 className="font-semibold text-purple-800 mb-2">
                🔸 Uniques à {report2.filename} ({comparison.unique_to_report2.length}) :
              </h4>
              <div className="flex flex-wrap gap-1">
                {comparison.unique_to_report2.slice(0, 10).map((keyword, index) => (
                  <span key={index} className="px-2 py-1 bg-purple-100 text-purple-800 rounded text-xs">
                    {keyword}
                  </span>
                ))}
                {comparison.unique_to_report2.length > 10 && (
                  <span className="px-2 py-1 bg-gray-200 text-gray-600 rounded text-xs">
                    +{comparison.unique_to_report2.length - 10}...
                  </span>
                )}
              </div>
            </div>
          )}
        </div>
      </div>
    );
  };


  if (!userId)
    return (
      <div className="min-h-screen flex items-center justify-center bg-red-50 text-red-700 font-semibold text-lg">
        ❌ Utilisateur non connecté. Veuillez vous reconnecter.
      </div>
    );

  return (
    <div className="min-h-screen bg-gradient-to-tr from-indigo-100 via-purple-100 to-blue-200 text-gray-800 px-6">
      <nav className="flex flex-col sm:flex-row justify-between items-center py-4 border-b border-indigo-300 mb-10">
        <h2 className="text-2xl font-bold text-indigo-800 text-center sm:text-left">
          ESG Report Analyser
        </h2>

        <div className="flex gap-4 mt-2 sm:mt-0">
          <a
            href="/history"
            className="text-indigo-700 hover:text-indigo-900 font-medium text-base transition"
          >
            📊 Historique
          </a>
          <a
            href="/profile"
            className="text-indigo-700 hover:text-indigo-900 font-medium text-base transition"
          >
            👤 Mon Profil
          </a>
        </div>
      </nav>


      <motion.div
        className="max-w-6xl mx-auto bg-white bg-opacity-80 backdrop-blur-md p-10 rounded-xl shadow-xl"
        variants={textVariants}
        initial="hidden"
        animate="visible"
      >
        <h1 className="text-4xl font-extrabold mb-4 text-indigo-900">
          Tableau de bord
        </h1>
        <p className="mb-8  leading-relaxed text-gray-700">
          Bienvenue dans votre espace personnel. Vous pouvez gérer vos rapports ESG, importer de nouveaux fichiers PDF, et consulter les analyses générées par IA ou par détection de mots-clés ESRS.
        </p>

        <UploadTrigger userId={userId} />

        {/* Boutons de mode principal */}
        <div className="mt-8 flex justify-center gap-4">
          <button
            className={`px-6 py-3 rounded-lg font-semibold transition ${
              !comparisonMode
                ? "bg-purple-600 text-white hover:bg-indigo-800"
                : "bg-gray-200 text-gray-700 hover:bg-gray-300"
            }`}
            onClick={() => {
              setComparisonMode(false);
              resetComparison();
            }}
          >
            📊 Analyse individuelle
          </button>
          <button
            className={`px-6 py-3 rounded-lg font-semibold transition ${
              comparisonMode
                ? "bg-purple-600 text-white"
                : "bg-gray-200 text-gray-700 hover:bg-gray-300"
            }`}
            onClick={() => setComparisonMode(true)}
          >
            🔀 Comparaison de rapports
          </button>
        </div>

        {!comparisonMode ? (
          // Mode analyse individuelle
          <>
            <div className="mt-10">
              <h2 className="text-2xl font-semibold text-indigo-800 mb-4">Mes rapports uploadés</h2>
              <ReportsList userId={userId} onSelectReport={(report) => {
                setSelectedReport(report);
                resetAnalysis();
              }} />
            </div>

            {selectedReport && (
              <div className="mt-8 p-6 border rounded-lg bg-indigo-50">
                <h3 className="text-xl font-bold mb-2">📄 Rapport sélectionné :</h3>
                <p>
                  <strong>Nom :</strong> {selectedReport.filename}
                </p>
                <p>
                  <strong>Date d'upload :</strong>{" "}
                  {new Date(selectedReport.upload_date).toLocaleString()}
                </p>

                {/* Sélecteur de mode d'analyse */}
              <div className="mt-8 mb-6 p-4 bg-gray-50 rounded-lg shadow-sm">
                <h4 className="text-lg font-semibold text-gray-800 mb-4">🧠 Mode d'analyse</h4>
                <div className="flex flex-wrap gap-4 justify-center">
                  <button
                    className={`px-4 py-2 rounded-lg font-medium transition ${
                      analysisMode === "ai"
                        ? "bg-blue-600 text-white"
                        : "bg-white border border-blue-300 text-blue-600 hover:bg-blue-50"
                    }`}
                    onClick={() => {
                      setAnalysisMode("ai");
                      resetAnalysis();
                    }}
                  >
                    🤖 Analyse IA (GPT)
                  </button>
                  <button
                    className={`px-4 py-2 rounded-lg font-medium transition ${
                      analysisMode === "keywords"
                        ? "bg-emerald-600 text-white"
                        : "bg-white border border-emerald-300 text-emerald-600 hover:bg-emerald-50"
                    }`}
                    onClick={() => {
                      setAnalysisMode("keywords");
                      resetAnalysis();
                    }}
                  >
                    🔍 Analyse par mots-clés ESRS
                  </button>
                </div>
              </div>

              {/* Bouton de rafraîchissement IA */}
              {analysisMode === "ai" && (
                <div className="mb-6 text-center">
                  <button
                    className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition disabled:opacity-50 text-sm"
                    onClick={handleRefreshAnalysis}
                    disabled={refreshingAI}
                  >
                    {refreshingAI ? "⏳ Rafraîchissement..." : "♻️ Rafraîchir l'analyse IA"}
                  </button>
                </div>
              )}

              {/* Options de langue pour analyse mots-clés */}
              {analysisMode === "keywords" && (
                <div className="mb-6 p-4 bg-emerald-50 rounded-lg">
                  <label className="block text-sm font-medium text-emerald-800 mb-2">
                    Langue d'analyse :
                  </label>
                  <select
                    value={selectedLanguage}
                    onChange={(e) => setSelectedLanguage(e.target.value)}
                    className="w-full px-3 py-2 border border-emerald-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-500"
                  >
                    <option value="french">🇫🇷 Français</option>
                    <option value="english">🇬🇧 English</option>
                  </select>
                </div>
              )}

              {/* Boutons de lancement de l'analyse */}
              <div className="text-center mt-6">
                {analysisMode === "ai" ? (
                  <button
                    className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition disabled:opacity-50 disabled:cursor-not-allowed"
                    onClick={handleAnalyse}
                    disabled={loading}
                  >
                    {loading ? "⏳ Analyse IA en cours..." : "🤖 Analyser avec l'IA"}
                  </button>
                ) : (
                  <button
                    className="px-6 py-3 bg-emerald-600 text-white rounded-lg hover:bg-emerald-700 transition disabled:opacity-50 disabled:cursor-not-allowed"
                    onClick={handleKeywordAnalysis}
                    disabled={loadingKeywords}
                  >
                    {loadingKeywords ? "⏳ Analyse mots-clés en cours..." : "🔍 Analyser par mots-clés"}
                  </button>
                )}
              </div>


                {/* Affichage des erreurs */}
                {errorMsg && (
                  <div className="text-red-600 mt-4 font-medium p-3 bg-red-50 rounded border border-red-200">
                    {errorMsg}
                  </div>
                )}
                {keywordError && (
                  <div className="text-red-600 mt-4 font-medium p-3 bg-red-50 rounded border border-red-200">
                    {keywordError}
                  </div>
                )}
              </div>
            )}

            {/* Résultats d'analyse IA */}
            {analysisResult && analysisMode === "ai" && (
              <div className="mt-8 p-6 border rounded-lg bg-green-50">
                <div className="flex justify-between items-center mb-4">
                  <h3 className="text-xl font-bold text-green-800">
                    🤖 Résultats d'analyse IA (GPT)
                  </h3>
                  <div className="flex gap-2">
                    <button
                      onClick={downloadAnalysisHTML}
                      className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 transition text-sm font-medium"
                      title="Télécharger en HTML"
                    >
                      📄 HTML
                    </button>
                    <button
                      onClick={downloadAnalysisJSON}
                      className="px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700 transition text-sm font-medium"
                      title="Télécharger en JSON"
                    >
                      📊 JSON
                    </button>
                  </div>
                </div>
                <div className="bg-white p-4 rounded shadow-sm">
                  <div className="prose max-w-none">
                    <div className="whitespace-pre-wrap text-gray-800 leading-relaxed">
                      {analysisResult.analysis_text}
                    </div>

                    {analysisResult.scores && (
                      <div className="mt-4 text-sm text-gray-700">
                        <p>🔢 Score global ESG : {analysisResult.scores.global_score}/100</p>
                        <p>🌍 E1 - Climat : {analysisResult.scores.e1_score}/20</p>
                        <p>💨 E2 - Pollution : {analysisResult.scores.e2_score}/20</p>
                        <p>💧 E3 - Ressources hydriques : {analysisResult.scores.e3_score}/20</p>
                        <p>🌱 E4 - Biodiversité : {analysisResult.scores.e4_score}/20</p>
                        <p>♻️ E5 - Économie circulaire : {analysisResult.scores.e5_score}/20</p>
                      </div>
                    )}

                    <p className="text-xs text-gray-500 mt-2">
                      Tokens utilisés : {analysisResult.tokens_used ?? "?"}
                    </p>
                  </div>
                </div>
              </div>
            )}


            {/* Résultats d'analyse par mots-clés */}
            {keywordAnalysisResult && analysisMode === "keywords" && renderKeywordAnalysisResults()}
          </>
        ) : (
          // Mode comparaison
          <>
            <div className="mt-10">
              <h2 className="text-2xl font-semibold text-purple-800 mb-4">
                Comparaison de rapports ESG
              </h2>
              
              {reports.length < 2 ? (
                <div className="p-6 bg-yellow-50 border border-yellow-200 rounded-lg">
                  <p className="text-yellow-800">
                    ⚠️ Vous devez avoir au moins 2 rapports uploadés pour effectuer une comparaison.
                  </p>
                </div>
              ) : (
                <>
                  <div className="grid md:grid-cols-2 gap-6">
                    {/* Sélection rapport 1 */}
                    <div className="p-6 border rounded-lg bg-purple-50">
                      <h3 className="text-lg font-semibold mb-3">📄 Premier rapport</h3>
                      <select
                        className="w-full p-3 border rounded-lg"
                        value={selectedReport1?.id || ""}
                        onChange={(e) => {
                          const report = reports.find(r => r.id === parseInt(e.target.value));
                          setSelectedReport1(report);
                        }}
                      >
                        <option value="">Sélectionner un rapport...</option>
                        {reports.map(report => (
                          <option key={report.id} value={report.id}>
                            {report.filename}
                          </option>
                        ))}
                      </select>
                      {selectedReport1 && (
                        <div className="mt-3 text-sm text-gray-600">
                          <p><strong>Date :</strong> {new Date(selectedReport1.upload_date).toLocaleString()}</p>
                        </div>
                      )}
                    </div>

                    {/* Sélection rapport 2 */}
                    <div className="p-6 border rounded-lg bg-purple-50">
                      <h3 className="text-lg font-semibold mb-3">📄 Deuxième rapport</h3>
                      <select
                        className="w-full p-3 border rounded-lg"
                        value={selectedReport2?.id || ""}
                        onChange={(e) => {
                          const report = reports.find(r => r.id === parseInt(e.target.value));
                          setSelectedReport2(report);
                        }}
                      >
                        <option value="">Sélectionner un rapport...</option>
                        {reports.map(report => (
                          <option key={report.id} value={report.id}>
                            {report.filename}
                          </option>
                        ))}
                      </select>
                      {selectedReport2 && (
                        <div className="mt-3 text-sm text-gray-600">
                          <p><strong>Date :</strong> {new Date(selectedReport2.upload_date).toLocaleString()}</p>
                        </div>
                      )}
                    </div>
                  </div>

                  {/* Sélecteur de mode de comparaison */}
                  {selectedReport1 && selectedReport2 && (
                    <div className="mt-6 p-4 bg-gray-50 rounded-lg">
                      <h4 className="text-lg font-semibold mb-3">Mode de comparaison :</h4>
                      <div className="flex gap-3 justify-center">
                        <button
                          className={`px-4 py-2 rounded-lg font-medium transition ${
                            analysisMode === "ai"
                              ? "bg-blue-600 text-white"
                              : "bg-gray-200 text-gray-700 hover:bg-gray-300"
                          }`}
                          onClick={() => {
                            setAnalysisMode("ai");
                            setComparisonResult(null);
                            setKeywordComparisonResult(null);
                            setComparisonError("");
                            setKeywordComparisonError("");
                          }}
                        >
                          🤖 Comparaison IA (GPT)
                        </button>
                        <button
                          className={`px-4 py-2 rounded-lg font-medium transition ${
                            analysisMode === "keywords"
                              ? "bg-emerald-600 text-white"
                              : "bg-gray-200 text-gray-700 hover:bg-gray-300"
                          }`}
                          onClick={() => {
                            setAnalysisMode("keywords");
                            setComparisonResult(null);
                            setKeywordComparisonResult(null);
                            setComparisonError("");
                            setKeywordComparisonError("");
                          }}
                        >
                          🔍 Comparaison par mots-clés ESRS
                        </button>
                      </div>

                      {/* Options pour la comparaison par mots-clés */}
                      {analysisMode === "keywords" && (
                        <div className="mt-3 text-center">
                          <label className="inline-block text-sm font-medium text-emerald-800 mr-2">
                            Langue :
                          </label>
                          <select
                            value={selectedLanguage}
                            onChange={(e) => setSelectedLanguage(e.target.value)}
                            className="px-3 py-1 border border-emerald-300 rounded focus:outline-none focus:ring-2 focus:ring-emerald-500"
                          >
                            <option value="french">🇫🇷 Français</option>
                            <option value="english">🇬🇧 English</option>
                          </select>
                        </div>
                      )}
                    </div>
                  )}
                </>
              )}

              {/* Boutons de comparaison */}
              {reports.length >= 2 && selectedReport1 && selectedReport2 && (
                <div className="mt-6 text-center">
                  {analysisMode === "ai" ? (
                      <div className="flex flex-col items-center gap-3">
                        <button
                          className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition disabled:opacity-50 disabled:cursor-not-allowed"
                          onClick={handleCompareReports}
                          disabled={loadingComparison}
                        >
                          {loadingComparison ? "⏳ Comparaison IA en cours..." : "🤖 Comparer avec l'IA"}
                        </button>

                        {comparisonResult && (
                          <button
                            onClick={handleRefreshComparison}
                            className="px-5 py-2 bg-red-600 text-white rounded hover:bg-red-700 transition text-sm font-medium"
                          >
                            ♻️ Rafraîchir la comparaison IA
                          </button>
                        )}
                      </div>
                    ) : (
                      <button
                        className="px-6 py-3 bg-emerald-600 text-white rounded-lg hover:bg-emerald-700 transition disabled:opacity-50 disabled:cursor-not-allowed"
                        onClick={handleKeywordComparison}
                        disabled={loadingKeywordComparison}
                      >
                        {loadingKeywordComparison ? "⏳ Comparaison mots-clés en cours..." : "🔍 Comparer par mots-clés"}
                      </button>
                    )}

                </div>
              )}

              {/* Affichage des erreurs de comparaison */}
              {comparisonError && (
                <div className="mt-4 text-red-600 font-medium p-3 bg-red-50 rounded border border-red-200">
                  {comparisonError}
                </div>
              )}
              {keywordComparisonError && (
                <div className="mt-4 text-red-600 font-medium p-3 bg-red-50 rounded border border-red-200">
                  {keywordComparisonError}
                </div>
              )}
            </div>

            {/* Résultats de comparaison IA */}
            {comparisonResult && analysisMode === "ai" && (
              <div className="mt-8 p-6 border rounded-lg bg-gradient-to-r from-purple-50 to-indigo-50">
                <div className="flex justify-between items-center mb-4">
                  <h3 className="text-xl font-bold text-purple-800">
                    🤖 Résultats de la comparaison IA
                  </h3>
                  <div className="flex gap-2">
                    <button
                      onClick={downloadComparisonHTML}
                      className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 transition text-sm font-medium"
                      title="Télécharger en HTML"
                    >
                      📄 HTML
                    </button>
                    <button
                      onClick={downloadComparisonJSON}
                      className="px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700 transition text-sm font-medium"
                      title="Télécharger en JSON"
                    >
                      📊 JSON
                    </button>
                  </div>
                </div>
                <div className="mb-4 p-3 bg-white rounded border">
                  <p className="font-semibold text-gray-700">
                    <span className="text-purple-600">Rapport 1:</span> {comparisonResult.report1.filename}
                  </p>
                  <p className="font-semibold text-gray-700">
                    <span className="text-indigo-600">Rapport 2:</span> {comparisonResult.report2.filename}
                  </p>
                </div>
                <div className="bg-white p-4 rounded shadow-sm">
                  <div className="prose max-w-none">
                    <div className="whitespace-pre-wrap text-gray-800 leading-relaxed">
                      {comparisonResult.comparison_analysis}
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* Résultats de comparaison par mots-clés */}
            {keywordComparisonResult && analysisMode === "keywords" && renderKeywordComparisonResults()}
          </>
        )}
      </motion.div>
    </div>
  );
}

export default Dashboard;