import React from "react";
import { useNavigate } from "react-router-dom";

export default function LandingPage() {
  const navigate = useNavigate();

  return (
    <section className="hero">
      <div className="hero-heading">
        <h1>
          <span>Reimagining</span>
          <br />
          <span className="hero-gradient-text">Clinical Case Review.</span>
        </h1>
        <p className="hero-subtitle">
          MedAura AI reads medical reports, labs and imaging summaries, then
          orchestrates multiple specialist agents — Internist, Cardiologist,
          Neurologist, Gastroenterologist and Psychiatrist — to surface the
          key risks and recommendations in one calm, unified view.
        </p>
      </div>

      <div className="hero-actions">
        <button
          className="btn btn-primary-lg"
          onClick={() => navigate("/cases/new")}
        >
          Start Free Case Analysis →
        </button>
        <button
          className="btn btn-ghost-lg"
          onClick={() => navigate("/cases")}
        >
          View Previous Cases
        </button>
      </div>

      <div className="hero-welcome-section">
        <div className="welcome-content">
          <h2 className="welcome-title">Why Choose MedAura AI?</h2>
          <p className="welcome-description">
            Experience the future of clinical decision support with our intelligent multi-agent platform
          </p>
        </div>

        <div className="benefits-grid">
          <div className="benefit-card">
            <div className="benefit-icon-wrapper">
              <svg className="benefit-icon" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M12 2L2 7L12 12L22 7L12 2Z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                <path d="M2 17L12 22L22 17" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                <path d="M2 12L12 17L22 12" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
              </svg>
            </div>
            <h3 className="benefit-title">Multi-Agent Intelligence</h3>
            <p className="benefit-text">
              Five specialist AI agents collaborate to provide comprehensive clinical insights
            </p>
          </div>

          <div className="benefit-card">
            <div className="benefit-icon-wrapper">
              <svg className="benefit-icon" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="2"/>
                <polyline points="12 6 12 12 16 14" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
              </svg>
            </div>
            <h3 className="benefit-title">Rapid Analysis</h3>
            <p className="benefit-text">
              Get comprehensive case reviews in under 2 minutes with real-time processing
            </p>
          </div>

          <div className="benefit-card">
            <div className="benefit-icon-wrapper">
              <svg className="benefit-icon" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M1 12S5 4 12 4S23 12 23 12S19 20 12 20S1 12 1 12Z" stroke="currentColor" strokeWidth="2"/>
                <circle cx="12" cy="12" r="3" stroke="currentColor" strokeWidth="2"/>
              </svg>
            </div>
            <h3 className="benefit-title">Transparent & Explainable</h3>
            <p className="benefit-text">
              Traceable agent reasoning with evidence-backed recommendations you can trust
            </p>
          </div>

          <div className="benefit-card">
            <div className="benefit-icon-wrapper">
              <svg className="benefit-icon" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <rect x="3" y="3" width="18" height="18" rx="2" stroke="currentColor" strokeWidth="2"/>
                <path d="M9 9H15M9 15H15M9 12H15" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
              </svg>
            </div>
            <h3 className="benefit-title">Unified Clinical View</h3>
            <p className="benefit-text">
              All specialist insights consolidated into one clear, actionable summary
            </p>
          </div>
        </div>

        <div className="hero-cta-secondary">
          <button
            className="btn btn-ghost-lg"
            onClick={() => navigate("/about")}
          >
            Learn More About MedAura AI
          </button>
        </div>
      </div>

      {/* Vision 2031 Section */}
      <section className="vision-2031-section">
        <h2 className="vision-title">
          <span className="vision-title-white">UAE</span>{" "}
          <span className="vision-title-green">Vision 2031</span>
        </h2>
        
        <div className="vision-cards-container">
          <div className="vision-card vision-card-left">
            <img 
              src="/UAE_2031.jpg" 
              alt="UAE Vision 2031" 
              className="vision-card-image"
            />
          </div>

          <div className="vision-card vision-card-right">
            <h3 className="vision-card-title">
              Accelerating Healthcare Innovation for a Sustainable Future
            </h3>
            <p className="vision-card-text">
              UAE Vision 2031 outlines a bold roadmap to build a world-leading, sustainable and knowledge-driven economy. 
              In healthcare, it emphasizes early detection, precision medicine, and AI-powered solutions to enhance patient 
              outcomes and operational efficiency across the national health ecosystem.
            </p>
            <div className="vision-focus-areas">
              <div className="vision-focus-item">
                <span className="vision-check">✓</span>
                <span><strong>Patient-centric care:</strong> Faster, more accurate diagnostics and timely interventions.</span>
              </div>
              <div className="vision-focus-item">
                <span className="vision-check">✓</span>
                <span><strong>AI & data-driven systems:</strong> Scaling precision radiology and predictive insights.</span>
              </div>
              <div className="vision-focus-item">
                <span className="vision-check">✓</span>
                <span><strong>Sustainable excellence:</strong> Streamlined workflows and better clinical outcomes.</span>
              </div>
            </div>
          </div>
        </div>
      </section>
    </section>
  );
}
