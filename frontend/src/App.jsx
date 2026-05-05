import React from "react";
import { Link } from "react-router-dom";
import { motion } from "framer-motion";

const textVariants = {
  hidden: { opacity: 0, y: 30 },
  visible: { 
    opacity: 1, 
    y: 0,
    transition: { duration: 1.5 }
  },
};

function App() {
  return (
    <div className="min-h-screen bg-gradient-to-r from-blue-700 via-indigo-800 to-purple-900 flex flex-col justify-center items-center text-white px-6">
      <motion.div
        className="flex flex-col justify-center items-center"
        variants={textVariants}
        initial="hidden"
        animate="visible"
      >
        <header className="mb-12 text-center max-w-3xl">
          <h1 className="text-5xl font-extrabold mb-6 tracking-tight drop-shadow-lg">
            ESG Report Analyser
          </h1>
          <p className="text-lg md:text-xl max-w-xl mx-auto leading-relaxed drop-shadow-md">
            Analysez et visualisez facilement vos rapports ESG. 
            Un outil intelligent pour des décisions durables et responsables.
          </p>
        </header>

        <nav className="flex gap-6">
          <Link
            to="/login"
            className="px-8 py-3 rounded-lg bg-indigo-500 hover:bg-indigo-600 bg-opacity-20 hover:bg-opacity-40 transition font-semibold shadow-lg"
          >
            Connexion
          </Link>
          <Link
            to="/register"
            className="px-8 py-3 rounded-lg bg-indigo-600 hover:bg-indigo-500 transition font-semibold shadow-lg"
          >
            Inscription
          </Link>
        </nav>

        <footer className="mt-20 text-sm text-indigo-200 opacity-70">
          © 2025 ESG Report Builder. Tous droits réservés.
        </footer>
      </motion.div>
    </div>
  );
}

export default App;
