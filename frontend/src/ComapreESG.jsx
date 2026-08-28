import React, { useState } from "react";
import { API_BASE } from './config';
import axios from "axios";

export default function CompareESG() {
  const [report1, setReport1] = useState("");
  const [report2, setReport2] = useState("");
  const [result, setResult] = useState("");
  const [loading, setLoading] = useState(false);

  const handleCompare = async () => {
    setLoading(true);
    try {
      const response = await axios.post(`${API_BASE}/compare-esg/`, {
        report1,
        report2,
      });
      setResult(response.data.response);
    } catch (error) {
      console.error("Erreur:", error);
      setResult("Erreur lors de la comparaison.");
    }
    setLoading(false);
  };

  return (
    <div className="max-w-4xl mx-auto p-4">
      <h2 className="text-2xl font-semibold mb-4">Comparer 2 rapports ESG (E1 à E5)</h2>
      <textarea
        className="w-full border p-2 mb-3 h-40 rounded"
        placeholder="Contenu du Rapport 1"
        value={report1}
        onChange={(e) => setReport1(e.target.value)}
      />
      <textarea
        className="w-full border p-2 mb-3 h-40 rounded"
        placeholder="Contenu du Rapport 2"
        value={report2}
        onChange={(e) => setReport2(e.target.value)}
      />
      <button
        onClick={handleCompare}
        className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700"
      >
        {loading ? "Analyse en cours..." : "Lancer la comparaison"}
      </button>
      {result && (
        <div className="mt-6 p-4 bg-gray-100 rounded border">
          <h3 className="font-bold mb-2">Résultat :</h3>
          <pre className="whitespace-pre-wrap">{result}</pre>
        </div>
      )}
    </div>
  );
}
