import React, { useState, useEffect } from "react";
import { API_BASE } from './config';
import { motion } from "framer-motion";
import { getUserIdFromToken } from "./utils/auth";
import { FileText, GitCompare, BarChart3, Calendar, Download, Eye } from "lucide-react";

const History = () => {
  const userId = getUserIdFromToken();
  const [activeTab, setActiveTab] = useState("analyses");
  const [historyData, setHistoryData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    if (userId) {
      fetchCompleteHistory();
    }
  }, [userId]);

  const fetchCompleteHistory = async () => {
    setLoading(true);
    setError("");

    try {
      const response = await fetch(`${API_BASE}/user-history/${userId}`);
      if (!response.ok) throw new Error("Erreur lors de la récupération de l'historique");

      const data = await response.json();
      if (data.status === "success") {
        setHistoryData(data);
      } else {
        throw new Error("Données invalides reçues");
      }
    } catch (err) {
      setError("❌ " + err.message);
    } finally {
      setLoading(false);
    }
  };

  const downloadJSON = (data, filenamePrefix, id, date) => {
    const blob = new Blob([JSON.stringify(data, null, 2)], {
      type: "application/json",
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${filenamePrefix}_${id}_${new Date(date).toISOString().slice(0, 10)}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const renderStatistics = () => {
    if (!historyData?.statistics) return null;
    const stats = historyData.statistics;

    return (
      <div className="mb-8 p-6 bg-gradient-to-r from-blue-50 to-indigo-50 rounded-xl border border-blue-200">
        <div className="flex items-center gap-3 mb-4">
          <BarChart3 className="w-6 h-6 text-blue-600" />
          <h2 className="text-xl font-bold text-blue-800">Statistiques d'utilisation</h2>
        </div>

        <div className="grid md:grid-cols-4 gap-4">
          <StatBox value={stats.total_analyses} label="Analyses totales" color="blue" />
          <StatBox value={stats.total_comparisons} label="Comparaisons totales" color="green" />
          <StatBox
            value={stats.tokens_usage.premium_model.total_tokens.toLocaleString()}
            label="Tokens Premium"
            color="purple"
          />
          <StatBox
            value={stats.tokens_usage.budget_model.total_tokens.toLocaleString()}
            label="Tokens Budget"
            color="orange"
          />
        </div>
      </div>
    );
  };

  const StatBox = ({ value, label, color }) => (
    <div className="text-center p-4 bg-white rounded-lg shadow-sm">
      <div className={`text-2xl font-bold text-${color}-600`}>{value}</div>
      <div className={`text-sm text-${color}-800`}>{label}</div>
    </div>
  );

  const renderAnalysesHistory = () => {
    const analyses = historyData?.analyses || [];

    if (analyses.length === 0) {
      return (
        <EmptyState icon={<FileText />} message="Aucune analyse trouvée" />
      );
    }

    return (
      <div className="space-y-4">
        {analyses.map((analysis) => (
          <motion.div
            key={analysis.id}
            className="bg-white rounded-lg border border-gray-200 hover:border-blue-300 hover:shadow-md transition-all duration-200"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
          >
            <div className="p-6">
              <Header
                title={analysis.filename}
                date={analysis.analysis_date}
                tokens={analysis.tokens_used}
                model={analysis.model_used}
                color="blue"
                onDownload={() =>
                  downloadJSON(analysis, "analyse", analysis.id, analysis.analysis_date)
                }
              />
              {analysis.scores?.global_score && (
                <div className="mb-4 p-3 bg-gray-50 rounded-lg text-sm text-gray-700">
                  <span className="font-medium">Score global ESG:</span> {analysis.scores.global_score}/100
                </div>
              )}
              <Details text={analysis.analysis_text} color="blue" />
            </div>
          </motion.div>
        ))}
      </div>
    );
  };

  const renderComparisonsHistory = () => {
    const comparisons = historyData?.comparisons || [];

    if (comparisons.length === 0) {
      return (
        <EmptyState icon={<GitCompare />} message="Aucune comparaison trouvée" />
      );
    }

    return (
      <div className="space-y-4">
        {comparisons.map((comparison) => (
          <motion.div
            key={comparison.id}
            className="bg-white rounded-lg border border-gray-200 hover:border-purple-300 hover:shadow-md transition-all duration-200"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
          >
            <div className="p-6">
              <Header
                title={`${comparison.filename1} vs ${comparison.filename2}`}
                date={comparison.comparison_date}
                tokens={comparison.tokens_used}
                model={comparison.model_used}
                color="purple"
                onDownload={() =>
                  downloadJSON(comparison, "comparaison", comparison.id, comparison.comparison_date)
                }
              />
              <Details text={comparison.comparison_text} color="purple" />
            </div>
          </motion.div>
        ))}
      </div>
    );
  };

  const Header = ({ title, date, tokens, model, onDownload, color }) => (
    <div className="flex justify-between items-start mb-4">
      <div>
        <h3 className="font-semibold text-gray-900 mb-2">{title}</h3>
        <div className="flex items-center gap-4 text-sm text-gray-600">
          <span className="flex items-center gap-1">
            <Calendar className="w-4 h-4" />
            {new Date(date).toLocaleString()}
          </span>
          <span>Tokens: {tokens || 0}</span>
          <span>Modèle: {model || "N/A"}</span>
        </div>
      </div>
      <button
        onClick={onDownload}
        className={`p-2 text-${color}-600 hover:bg-${color}-50 rounded-lg transition-colors`}
        title="Télécharger JSON"
      >
        <Download className="w-4 h-4" />
      </button>
    </div>
  );

  const Details = ({ text, color }) => (
    <details className="group">
      <summary className={`flex items-center gap-2 cursor-pointer text-${color}-600 hover:text-${color}-800 font-medium`}>
        <Eye className="w-4 h-4" />
        Voir le contenu
      </summary>
      <div className="mt-3 p-4 bg-gray-50 rounded-lg">
        <pre className="whitespace-pre-wrap text-sm text-gray-700 max-h-96 overflow-y-auto">{text}</pre>
      </div>
    </details>
  );

  const EmptyState = ({ icon, message }) => (
    <div className="text-center py-8 text-gray-500">
      <div className="w-12 h-12 mx-auto mb-4 text-gray-300">{icon}</div>
      <p>{message}</p>
    </div>
  );

  if (!userId) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-red-50 text-red-700 font-semibold text-lg">
        ❌ Utilisateur non connecté. Veuillez vous reconnecter.
      </div>
    );
  }

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4" />
          <p className="text-gray-600">Chargement de l'historique...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-tr from-indigo-100 via-purple-100 to-blue-200 text-gray-800 px-6">
      {/* Navigation */}
      <nav className="flex flex-col sm:flex-row justify-between items-center py-4 border-b border-indigo-300 mb-10">
        <h2 className="text-2xl font-bold text-indigo-800 text-center sm:text-left">
          ESG Report Analyser - Historique
        </h2>
        <div className="flex gap-4 mt-2 sm:mt-0">
          <a href="/dashboard" className="text-indigo-700 hover:text-indigo-900 font-medium text-base transition">🏠 Dashboard</a>
          <a href="/profile" className="text-indigo-700 hover:text-indigo-900 font-medium text-base transition">👤 Mon Profil</a>
        </div>
      </nav>

      <motion.div
        className="max-w-6xl mx-auto bg-white bg-opacity-80 backdrop-blur-md p-10 rounded-xl shadow-xl"
        initial={{ opacity: 0, y: 30 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6 }}
      >
        <h1 className="text-4xl font-extrabold mb-6 text-indigo-900">Historique de vos activités</h1>

        {error && (
          <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg text-red-700">
            {error}
          </div>
        )}

        {renderStatistics()}

        {/* Onglets */}
        <div className="mb-8">
          <div className="flex border-b border-gray-200">
            <button
              className={`px-6 py-3 font-medium transition-colors ${activeTab === "analyses" ? "border-b-2 border-blue-500 text-blue-600" : "text-gray-500 hover:text-gray-700"}`}
              onClick={() => setActiveTab("analyses")}
            >
              <div className="flex items-center gap-2">
                <FileText className="w-5 h-5" />
                Analyses ({historyData?.analyses?.length || 0})
              </div>
            </button>
            <button
              className={`px-6 py-3 font-medium transition-colors ${activeTab === "comparisons" ? "border-b-2 border-purple-500 text-purple-600" : "text-gray-500 hover:text-gray-700"}`}
              onClick={() => setActiveTab("comparisons")}
            >
              <div className="flex items-center gap-2">
                <GitCompare className="w-5 h-5" />
                Comparaisons ({historyData?.comparisons?.length || 0})
              </div>
            </button>
          </div>
        </div>

        <div className="min-h-96">
          {activeTab === "analyses" ? renderAnalysesHistory() : renderComparisonsHistory()}
        </div>
      </motion.div>
    </div>
  );
};

export default History;
