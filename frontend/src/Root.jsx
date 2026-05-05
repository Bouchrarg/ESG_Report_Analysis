import React from "react";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import App from "./App";
import Login from "./login";
import Register from "./register";
import Dashboard from "./Dashboard";
import UploadReport from "./UploadReport";
import Profile from "./profile";
import History from './History';

function Root() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<App />} />
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />
        <Route path="/profile" element={<Profile/>}/>
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/upload" element={<UploadReport />} />
        <Route path="/history" element={<History />} />

      </Routes>
    </BrowserRouter>
  );
}

export default Root;
