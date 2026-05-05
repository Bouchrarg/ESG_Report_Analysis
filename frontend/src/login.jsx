import React, { useState } from "react";
import axios from "axios";
import { useNavigate } from "react-router-dom";  // <-- IMPORT

function Login() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();  // <-- INITIALISATION

  const handleSubmit = async (e) => {
    e.preventDefault();
    console.log("handleSubmit déclenché");
    setError(null);
    setLoading(true);  // <-- activation du loading

    try {
      const response = await axios.post("http://localhost:8000/login", {
        email,
        password,
      });
      const token = response.data.access_token;
      localStorage.setItem("token", token);
      alert("Connexion réussie !");
      console.log("Redirection vers dashboard");
      navigate("/dashboard");
    } catch (err) {
      setError(err.response?.data?.detail || "Erreur serveur");
    } finally {
      setLoading(false);  // <-- désactivation du loading
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-indigo-900 via-purple-900 to-pink-900 flex items-center justify-center px-4">
      <div className="bg-white bg-opacity-90 backdrop-blur-lg rounded-3xl shadow-2xl max-w-md w-full p-10 animate-fadeIn">
        <h2 className="text-4xl font-extrabold mb-8 text-center text-gray-900 drop-shadow-md">
          Connexion
        </h2>
        <form onSubmit={handleSubmit} className="space-y-6">
          <div>
            <label
              htmlFor="email"
              className="block text-gray-700 font-semibold mb-2"
            >
              Adresse Email
            </label>
            <input
              id="email"
              type="email"
              placeholder="exemple@domaine.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              className="w-full px-5 py-3 border border-gray-300 rounded-xl focus:outline-none focus:ring-4 focus:ring-indigo-500 transition"
              autoComplete="email"
            />
          </div>

          <div>
            <label
              htmlFor="password"
              className="block text-gray-700 font-semibold mb-2"
            >
              Mot de passe
            </label>
            <input
              id="password"
              type="password"
              placeholder="Votre mot de passe"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              className="w-full px-5 py-3 border border-gray-300 rounded-xl focus:outline-none focus:ring-4 focus:ring-indigo-500 transition"
              autoComplete="current-password"
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className={`w-full py-3 rounded-xl text-white font-bold tracking-wide 
              bg-gradient-to-r from-indigo-600 to-purple-700
              hover:from-purple-700 hover:to-indigo-600 
              transition duration-300 shadow-lg
              ${loading ? "opacity-50 cursor-not-allowed" : ""}
            `}
          >
            {loading ? "Connexion..." : "Se connecter"}
          </button>
        </form>

        {error && (
          <p className="mt-6 text-center text-red-600 font-semibold animate-shake">
            {error}
          </p>
        )}

        <p className="mt-8 text-center text-gray-600">
          Pas encore de compte?{" "}
          <a href="/register" className="text-indigo-600 hover:underline font-semibold">
            Inscrivez-vous ici
          </a>
        </p>
      </div>

      <style>{`
        @keyframes fadeIn {
          from { opacity: 0; transform: translateY(10px); }
          to { opacity: 1; transform: translateY(0); }
        }
        .animate-fadeIn {
          animation: fadeIn 0.7s ease forwards;
        }
        @keyframes shake {
          0%, 100% { transform: translateX(0); }
          20%, 60% { transform: translateX(-8px); }
          40%, 80% { transform: translateX(8px); }
        }
        .animate-shake {
          animation: shake 0.4s ease;
        }
      `}</style>
    </div>
  );
}

export default Login;
