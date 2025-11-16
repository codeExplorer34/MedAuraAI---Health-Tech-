import React from "react";
import { NavLink } from "react-router-dom";

export default function Footer() {
  const linkClass = ({ isActive }) =>
    "footer-link" + (isActive ? " footer-link-active" : "");

  return (
    <footer className="footer">
      <div className="footer-container">
        <div className="footer-column">
          <div className="footer-brand">
            <div className="footer-logo-container">
              <img 
                src="/MedAuraAI Logo.png" 
                alt="MedAura AI Logo" 
                className="footer-logo-icon"
              />
              <span className="footer-brand-name">MedAura AI</span>
            </div>
            <p className="footer-tagline">Powered by multi-specialist AI agents</p>
            <p className="footer-description">
              MedAura AI delivers exceptional diagnostic accuracy through advanced 
              artificial intelligence. Your privacy and data security are our top priorities, 
              ensuring trusted, confidential medical analysis with enterprise-grade protection.
            </p>
          </div>
        </div>

        <div className="footer-column">
          <h3 className="footer-column-title">Quick Links</h3>
          <nav className="footer-nav">
            <NavLink to="/" className={linkClass} end>
              Home
            </NavLink>
            <NavLink to="/cases/new" className={linkClass}>
              Analyze Case
            </NavLink>
            <NavLink to="/cases" className={linkClass}>
              Previous Analyses
            </NavLink>
            <NavLink to="/about" className={linkClass}>
              About Us
            </NavLink>
          </nav>
        </div>

        <div className="footer-column">
          <h3 className="footer-column-title">Powered By</h3>
          <div className="footer-tech-stack">
            <div className="tech-item">
              <span className="tech-dot tech-dot-react"></span>
              <span>React</span>
            </div>
            <div className="tech-item">
              <span className="tech-dot tech-dot-node"></span>
              <span>Node.js</span>
            </div>
            <div className="tech-item">
              <span className="tech-dot tech-dot-ai"></span>
              <span>Tailwind CSS</span>
            </div>
            <div className="tech-item">
              <span className="tech-dot tech-dot-python"></span>
              <span>Python</span>
            </div>
            <div className="tech-item">
              <span className="tech-dot tech-dot-fastapi"></span>
              <span>FastAPI</span>
            </div>
          </div>
          
        </div>
      </div>
      <div className="footer-bottom">
        <p className="footer-copyright">
          © 2025 MedAura AI. All rights reserved. Built with precision for healthcare innovation.
        </p>
      </div>
    </footer>
  );
}

