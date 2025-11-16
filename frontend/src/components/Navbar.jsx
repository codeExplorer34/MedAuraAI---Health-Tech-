import React from "react";
import { NavLink, useNavigate } from "react-router-dom";

export default function Navbar() {
  const navigate = useNavigate();
  const linkClass = ({ isActive }) =>
    "navbar-link" + (isActive ? " navbar-link-active" : "");

  return (
    <header className="navbar">
      <div className="navbar-inner">
        <div className="navbar-brand navbar-brand-prominent" onClick={() => navigate("/")} style={{ cursor: "pointer" }}>
          <div className="navbar-logo-container">
            <img 
              src="/MedAuraAI Logo.png" 
              alt="MedAura AI Logo" 
              className="navbar-logo-icon"
            />
            <div className="navbar-brand-text">
              <span className="navbar-logo">MedAura AI</span>
              <span className="navbar-tagline">Clinical AI Copilot</span>
            </div>
          </div>
        </div>

        <nav className="navbar-pill">
          <NavLink to="/" className={linkClass} end>
            Home
          </NavLink>
          <NavLink to="/about" className={linkClass}>
            About
          </NavLink>
          <NavLink to="/cases/new" className={linkClass}>
            Upload Case
          </NavLink>
          <NavLink to="/cases" className={linkClass}>
            Results
          </NavLink>
        </nav>
      </div>
    </header>
  );
}
