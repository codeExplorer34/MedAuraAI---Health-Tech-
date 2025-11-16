import React from "react";
import { useNavigate } from "react-router-dom";

export default function AboutPage() {
  const navigate = useNavigate();

  return (
    <section className="about-page">
      <div className="about-container">
        <div className="about-header">
          <h1 className="about-title about-title-glow">About MedAura AI</h1>
          <p className="about-subtitle">
            Intelligent Multi-Specialist Healthcare AI Platform
          </p>
        </div>

        <div className="about-content">
          <div className="about-section">
            <h2 className="about-section-title">How It Works</h2>
            <p className="about-text">
              MedAura AI is an advanced clinical decision support system that uses artificial intelligence 
              to analyze medical reports, laboratory results, and imaging summaries. Our platform orchestrates 
              multiple specialist AI agents — including Internist, Cardiologist, Neurologist, Gastroenterologist, 
              and Psychiatrist — to provide comprehensive clinical insights.
            </p>
            <p className="about-text">
              Simply upload your medical documents, and our system will automatically extract key information, 
              identify potential risks, and generate evidence-based recommendations from multiple specialist 
              perspectives in a unified, easy-to-understand format.
            </p>
          </div>

          <div className="about-section">
            <h2 className="about-section-title">Key Features</h2>
            <div className="features-grid">
              <div className="feature-card">
                <div className="feature-icon">🤖</div>
                <h3 className="feature-title">Multi-Agent Analysis</h3>
                <p className="feature-description">
                  Five specialist AI agents work in parallel to provide comprehensive clinical insights
                </p>
              </div>
              <div className="feature-card">
                <div className="feature-icon">⚡</div>
                <h3 className="feature-title">Rapid Processing</h3>
                <p className="feature-description">
                  Typical case review completed in under 2 minutes with real-time updates
                </p>
              </div>
              <div className="feature-card">
                <div className="feature-icon">🔍</div>
                <h3 className="feature-title">Explainable AI</h3>
                <p className="feature-description">
                  Transparent reasoning with traceable agent logic and evidence-backed recommendations
                </p>
              </div>
              <div className="feature-card">
                <div className="feature-icon">📋</div>
                <h3 className="feature-title">Unified View</h3>
                <p className="feature-description">
                  All specialist insights consolidated into one clear, actionable clinical summary
                </p>
              </div>
            </div>
          </div>

          <div className="about-section">
            <h2 className="about-section-title">Security & Privacy</h2>
            <p className="about-text">
              We take data security and patient privacy seriously. All medical documents are processed 
              with enterprise-grade encryption, and we comply with healthcare data protection standards. 
              Your information is stored securely and is never shared with third parties. You maintain 
              full control over your data and can delete cases at any time.
            </p>
          </div>

          <div className="about-section">
            <h2 className="about-section-title">Value Proposition</h2>
            <p className="about-text">
              MedAura AI helps healthcare providers, researchers, and patients make more informed clinical 
              decisions by providing rapid, multi-specialist AI analysis. Our platform reduces the time 
              needed for comprehensive case review while maintaining high standards of accuracy and 
              clinical relevance. Whether you're screening cases, validating diagnoses, or seeking 
              second opinions, MedAura AI serves as your intelligent clinical copilot.
            </p>
          </div>

          <div className="about-section">
            <h2 className="about-section-title">Our Team</h2>
            <p className="about-text">
              MedAura AI is built by a dedicated team of developers, designers, and healthcare technology experts 
              committed to advancing clinical decision support through innovative AI solutions.
            </p>
            <div className="team-grid">
              <div className="team-member-card">
                <div className="team-member-icon">👨‍💻</div>
                <h3 className="team-member-name">Mohammed Yaser Hameed</h3>
                <p className="team-member-role">Lead Frontend Developer</p>
              </div>
              <div className="team-member-card">
                <div className="team-member-icon">⚙️</div>
                <h3 className="team-member-name">Suhayb Muzammil Shaik</h3>
                <p className="team-member-role">Lead Backend Developer</p>
              </div>
              <div className="team-member-card">
                <div className="team-member-icon">💻</div>
                <h3 className="team-member-name">Murtaza Mohammed</h3>
                <p className="team-member-role">Frontend Developer</p>
              </div>
              <div className="team-member-card">
                <div className="team-member-icon">🎨</div>
                <h3 className="team-member-name">Rohan Rao</h3>
                <p className="team-member-role">UI/UX Designer & API Integration</p>
              </div>
              <div className="team-member-card">
                <div className="team-member-icon">🎨</div>
                <h3 className="team-member-name">Raheel Ahmed</h3>
                <p className="team-member-role">UI/UX Designer</p>
              </div>
            </div>
          </div>

          <div className="about-cta">
            <button
              className="btn btn-primary-lg"
              onClick={() => navigate("/cases/new")}
            >
              Start Your First Analysis →
            </button>
            <button
              className="btn btn-ghost-lg"
              onClick={() => navigate("/")}
            >
              Return to Home
            </button>
          </div>
        </div>
      </div>
    </section>
  );
}

