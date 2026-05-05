import { useState } from 'react';
import axios from 'axios';

function AnalyseESG({ reportId }) {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState("");
  const [error, setError] = useState("");

  const handleAnalyse = async () => {
    setLoading(true);
    setError("");
    try {
      const response = await axios.post(`http://127.0.0.1:8000/generate-esg-environment/${reportId}`);
      setResult(response.data.esg_environment_report);
    } catch (err) {
      setError("Erreur lors de l'analyse : " + err.response?.data?.detail || err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="p-4 border rounded bg-white shadow">
      <h2 className="text-xl font-semibold mb-2">Analyse ESG – Environnement</h2>
      <button 
        className="bg-blue-600 text-white px-4 py-2 rounded mb-4"
        onClick={handleAnalyse}
        disabled={loading}
      >
        {loading ? "Analyse en cours..." : "Lancer l'analyse"}
      </button>

      {error && <p className="text-red-600">{error}</p>}

      {result && (
        <div className="whitespace-pre-wrap bg-gray-50 p-4 border mt-4 rounded max-h-[400px] overflow-y-auto">
          {result}
        </div>
      )}
    </div>
  );
}

export default AnalyseESG;
