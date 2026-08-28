import React, { useEffect, useState } from "react";
import { API_BASE } from './config';

function ReportsList({ userId, onSelectReport }) {
  const [reports, setReports] = useState([]);
  const [error, setError] = useState("");

  useEffect(() => {
    fetch(`${API_BASE}/reports/${userId}`)
      .then((res) => {
        if (!res.ok) throw new Error("Erreur de chargement");
        return res.json();
      })
      .then((data) => {
        setReports(data);
        setError("");
      })
      .catch((err) => {
        console.error(err);
        setError("Impossible de charger les rapports.");
      });
  }, [userId]);

  if (error)
    return <p className="text-red-600 font-medium my-4">{error}</p>;

  if (reports.length === 0)
    return <p className="text-gray-500">Aucun rapport trouvé pour cet utilisateur.</p>;

  return (
    <div className="grid gap-4">
      {reports.map((report) => (
        <div
          key={report.id}
          onClick={() => onSelectReport(report)}
          className="flex items-center justify-between bg-white border border-indigo-200 rounded-lg p-4 shadow-sm hover:shadow-md hover:bg-indigo-50 transition cursor-pointer"
        >
          <div className="flex items-center space-x-3">
            <span className="text-2xl">📄</span>
            <div>
              <p className="font-semibold text-indigo-900">{report.filename}</p>
              <p className="text-sm text-gray-500">
                Uploadé le : {new Date(report.upload_date).toLocaleDateString()}
              </p>
            </div>
          </div>
          <span className="text-sm text-indigo-500">Cliquer pour analyser 🔍</span>
        </div>
      ))}
    </div>
  );
}

export default ReportsList;
