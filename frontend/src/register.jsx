import React, { useState } from "react";
import axios from "axios";

function Register() {
  const [firstName, setFirstName] = useState("");
  const [lastName, setLastName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [message, setMessage] = useState(null);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setMessage(null);
    setError(null);

    if (password !== confirmPassword) {
      setError("Les mots de passe ne correspondent pas.");
      return;
    }

    setLoading(true);

    try {
      const res = await axios.post("http://localhost:8000/register", {
      first_name: firstName,
      last_name: lastName,
      email,
      password,
    })
      setMessage(res.data.msg);
      setFirstName("");
      setLastName("");
      setEmail("");
      setPassword("");
      setConfirmPassword("");
    } catch (err) {
      setError(err.response?.data?.detail || "Erreur serveur");
    } finally {
      setLoading(false);
    }
  };

  return (
<div className="min-h-screen bg-gradient-to-br from-indigo-900 via-purple-900 to-pink-900 flex items-center justify-center px-4 py-10">
      <div className="bg-white bg-opacity-90 backdrop-blur-lg rounded-3xl shadow-2xl max-w-md w-full p-10 animate-fadeIn">
        <h2 className="text-4xl font-extrabold mb-8 text-center text-gray-900 drop-shadow-md">
          Inscription
        </h2>
        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Prénom */}
          <div>
            <label
              htmlFor="firstName"
              className="block text-gray-700 font-semibold mb-2"
            >
              Prénom
            </label>
            <input
              id="firstName"
              type="text"
              placeholder="Votre prénom"
              value={firstName}
              onChange={(e) => setFirstName(e.target.value)}
              required
              className="w-full px-5 py-3 border border-gray-300 rounded-xl focus:outline-none focus:ring-4 focus:ring-indigo-500 transition"
              autoComplete="given-name"
            />
          </div>

          {/* Nom */}
          <div>
            <label
              htmlFor="lastName"
              className="block text-gray-700 font-semibold mb-2"
            >
              Nom
            </label>
            <input
              id="lastName"
              type="text"
              placeholder="Votre nom"
              value={lastName}
              onChange={(e) => setLastName(e.target.value)}
              required
              className="w-full px-5 py-3 border border-gray-300 rounded-xl focus:outline-none focus:ring-4 focus:ring-indigo-500 transition"
              autoComplete="family-name"
            />
          </div>

          {/* Email */}
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

          {/* Mot de passe */}
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
              autoComplete="new-password"
            />
          </div>

          {/* Confirmation mot de passe */}
          <div>
            <label
              htmlFor="confirmPassword"
              className="block text-gray-700 font-semibold mb-2"
            >
              Confirmer le mot de passe
            </label>
            <input
              id="confirmPassword"
              type="password"
              placeholder="Confirmez votre mot de passe"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              required
              className="w-full px-5 py-3 border border-gray-300 rounded-xl focus:outline-none focus:ring-4 focus:ring-indigo-500 transition"
              autoComplete="new-password"
            />
          </div>

          {/* Bouton */}
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
            {loading ? "Inscription..." : "S'inscrire"}
          </button>
        </form>

        {/* Messages */}
        {message && (
          <p className="mt-6 text-center text-green-600 font-semibold animate-fadeIn">
            {message}
          </p>
        )}
        {error && (
          <p className="mt-6 text-center text-red-600 font-semibold animate-shake">
            {error}
          </p>
        )}

        <p className="mt-8 text-center text-gray-600">
          Déjà un compte ?{" "}
          <a href="/login" className="text-indigo-600 hover:underline font-semibold">
            Connectez-vous ici
          </a>
        </p>
      </div>

      {/* Styles des animations */}
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

export default Register;
