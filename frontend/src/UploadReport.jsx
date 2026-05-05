import React, { useRef, useState } from "react";
import axios from "axios";

function UploadTrigger({ userId }) {
  const fileInputRef = useRef(null);
  const [uploading, setUploading] = useState(false);
  const [message, setMessage] = useState(null);
  const [error, setError] = useState(null);

  const handleFileChange = async (e) => {
    const file = e.target.files[0];
    if (!file) return;
    setMessage(null);
    setError(null);
    await handleUpload(file);
  };

  const handleUpload = async (file) => {
    setUploading(true);
    const formData = new FormData();
    formData.append("file", file);
    formData.append("user_id", userId);

    try {
      await axios.post("http://localhost:8000/upload-report", formData, {
        headers: { "Content-type": "multipart/form-data" },
      });
      setMessage("Fichier uploadé avec succès !");
    } catch {
      setError("Erreur lors de l'upload du fichier.");    
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="text-center">
      <button
        onClick={() => fileInputRef.current.click()}
        className="inline-block bg-indigo-500 hover:bg-indigo-600 text-white rounded-full px-6 py-3 font-semibold shadow-md transition"
        disabled={uploading}
      >
        {uploading ? "Chargement..." : "Uploader un nouveau rapport PDF"}
      </button>

      <input
        type="file"
        accept=".pdf,.xhtml"
        ref={fileInputRef}
        onChange={handleFileChange}
        className="hidden"
      />

      {message && <p className="text-green-400 mt-3">{message}</p>}
      {error && <p className="text-red-400 mt-3">{error}</p>}
    </div>
  );
}

export default UploadTrigger;
