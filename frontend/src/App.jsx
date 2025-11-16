import React from "react";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import Navbar from "./components/Navbar";
import Footer from "./components/Footer";
import LandingPage from "./components/LandingPage";
import AboutPage from "./components/AboutPage";
import CaseDashboard from "./components/CaseDashboard";
import CaseIntakeWizard from "./components/CaseIntakeWizard";
import CaseDetail from "./components/CaseDetail";

function NotFound() {
  return (
    <section className="hero-card">
      <h2 className="title">Page not found</h2>
      <p className="subtitle">
        The page you are looking for does not exist. Please use the navbar
        to navigate.
      </p>
    </section>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <div className="app-root">
        <Navbar />
        <main className="page">
          <Routes>
            <Route path="/" element={<LandingPage />} />
            <Route path="/about" element={<AboutPage />} />
            <Route path="/cases" element={<CaseDashboard />} />
            <Route path="/cases/new" element={<CaseIntakeWizard />} />
            <Route path="/cases/:id" element={<CaseDetail />} />
            <Route path="*" element={<NotFound />} />
          </Routes>
        </main>
        <Footer />
      </div>
    </BrowserRouter>
  );
}
