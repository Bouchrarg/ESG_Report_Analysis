import React, { useEffect, useState } from "react";
import { getUserIdFromToken } from "./utils/auth";

function Profile() {
  const [user, setUser] = useState(null);
  const userId = getUserIdFromToken();

  useEffect(() => {
    const fetchUser = async () => {
      try {
        const res = await fetch(`http://localhost:8000/users/${userId}`);
        if (res.ok) {
          const data = await res.json();
          setUser(data);
        }
      } catch (err) {
        console.error("Erreur lors du chargement du profil", err);
      }
    };

    if (userId) fetchUser();
  }, [userId]);

  if (!user) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-red-50 text-red-700 font-semibold text-lg">
        ❌ Utilisateur non connecté ou erreur de chargement.
      </div>
    );
  }
  const handleLogout=() =>{
    localStorage.removeItem("token");
    window.location.href="/login";
  }

  return (
    <div className="min-h-screen bg-gradient-to-tr from-indigo-100 via-purple-100 to-blue-200 px-6">
      <nav className="flex justify-between items-center py-4 border-b border-indigo-300 mb-10">
        <a href="/dashboard" className="text-2xl font-bold text-indigo-800 hover:text-indigo-600 transition">
          ESG Report Analyser
        </a>
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

      <div className="max-w-3xl mx-auto bg-white bg-opacity-80 backdrop-blur-md p-10 rounded-xl shadow-xl">
        <h1 className="text-3xl font-bold mb-6 text-indigo-900">Profil</h1>
        <div className="space-y-4 text-gray-700">
          <p><strong>Nom :</strong> {user.last_name}</p>
          <p><strong>Prénom :</strong> {user.first_name}</p>
          <p><strong>Email :</strong> {user.email}</p>
          <button
            onClick={handleLogout}
            className=" text-red-600 hover:text-red-800 font-medium text-base transition"
          >
            🔓 Se déconnecter
          </button>

          </div>
      </div>
    </div>
  );
}

export default Profile;
