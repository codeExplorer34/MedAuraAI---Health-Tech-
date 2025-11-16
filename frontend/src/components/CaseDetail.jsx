import React, { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { getCase, rerunAgents } from "../api/api";

function StatusBadge({ status }) {
  const s = (status || "").toLowerCase();
  let cls = "status-badge status-badge-queued";
  if (s === "running") cls = "status-badge status-badge-running";
  if (s === "completed") cls = "status-badge status-badge-completed";
  if (s === "error") cls = "status-badge status-badge-error";

  return <span className={cls}>{status || "Unknown"}</span>;
}

export default function CaseDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [caseData, setCaseData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [rerunning, setRerunning] = useState(false);

  useEffect(() => {
    async function fetchCase() {
      try {
        setLoading(true);
        const data = await getCase(id);
        setCaseData(data);
      } catch (err) {
        console.error("Error loading case:", err);
        setError("Could not load case. It may not exist.");
      } finally {
        setLoading(false);
      }
    }

    if (id) {
      fetchCase();
      // Poll for updates if case is running
      const interval = setInterval(() => {
        if (caseData?.status === "Running" || caseData?.status === "Queued") {
          fetchCase();
        }
      }, 3000);
      return () => clearInterval(interval);
    }
  }, [id, caseData?.status]);

  const handleRerun = async () => {
    try {
      setRerunning(true);
      await rerunAgents(id);
      // Refresh case data
      const data = await getCase(id);
      setCaseData(data);
    } catch (err) {
      console.error("Error rerunning agents:", err);
      alert("Failed to rerun agents. Please try again.");
    } finally {
      setRerunning(false);
    }
  };

  if (loading) {
    return (
      <section className="hero-card">
        <p className="field-hint">Loading case details...</p>
      </section>
    );
  }

  if (error || !caseData) {
    return (
      <section className="hero-card">
        <h2 className="title">Case Not Found</h2>
        <p className="subtitle">{error || "The case you're looking for doesn't exist."}</p>
        <button className="btn btn-primary-lg" onClick={() => navigate("/cases")}>
          Back to Cases
        </button>
      </section>
    );
  }

  const { agentResults } = caseData;
  const specialists = agentResults?.specialists || {};
  const teamSummary = agentResults?.teamSummary || {};
  const treatmentOptions = agentResults?.treatmentOptions || [];

  return (
    <section className="hero-card">
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "24px" }}>
        <div>
          <h2 className="title">Case #{caseData.patientId || id}</h2>
          <p className="subtitle">
            {caseData.name} {caseData.age && `• ${caseData.age} years`} {caseData.gender && `• ${caseData.gender}`}
          </p>
        </div>
        <div style={{ display: "flex", gap: "12px", alignItems: "center" }}>
          <StatusBadge status={caseData.status} />
          {caseData.status === "Completed" && (
            <button
              className="btn btn-outline"
              onClick={handleRerun}
              disabled={rerunning}
            >
              {rerunning ? "Rerunning..." : "Rerun Agents"}
            </button>
          )}
        </div>
      </div>

      {caseData.chiefComplaint && (
        <div style={{ marginBottom: "32px", padding: "20px", background: "rgba(30, 41, 59, 0.4)", borderRadius: "12px" }}>
          <h3 style={{ fontSize: "1.1rem", fontWeight: "600", marginBottom: "12px", color: "#e2e8f0" }}>
            Chief Complaint
          </h3>
          <p style={{ color: "#cbd5e1", lineHeight: "1.6" }}>{caseData.chiefComplaint}</p>
        </div>
      )}

      {caseData.status === "Running" || caseData.status === "Queued" ? (
        <div style={{ textAlign: "center", padding: "40px" }}>
          <div style={{ fontSize: "3rem", marginBottom: "16px" }}>⏳</div>
          <p className="subtitle">
            AI agents are analyzing this case. This may take a few minutes...
          </p>
          <p className="field-hint" style={{ marginTop: "8px" }}>
            The page will update automatically when complete.
          </p>
        </div>
      ) : caseData.status === "Error" ? (
        <div className="alert-warning">
          <strong>Error:</strong> {caseData.error || "An error occurred while processing this case."}
          <button
            className="btn btn-primary-lg"
            onClick={handleRerun}
            disabled={rerunning}
            style={{ marginTop: "12px" }}
          >
            {rerunning ? "Rerunning..." : "Try Again"}
          </button>
        </div>
      ) : (
        <>
          {/* Team Summary */}
          {teamSummary.diagnoses && teamSummary.diagnoses.length > 0 && (
            <div style={{ marginBottom: "32px" }}>
              <h3 style={{ fontSize: "1.3rem", fontWeight: "700", marginBottom: "20px", color: "#f1f5f9" }}>
                Team Diagnosis Summary
              </h3>
              <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
                {teamSummary.diagnoses.map((diagnosis, idx) => (
                  <div
                    key={idx}
                    style={{
                      padding: "20px",
                      background: "rgba(30, 41, 59, 0.5)",
                      borderRadius: "12px",
                      border: "1px solid rgba(148, 163, 184, 0.2)"
                    }}
                  >
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "12px" }}>
                      <h4 style={{ fontSize: "1.1rem", fontWeight: "600", color: "#e2e8f0" }}>
                        #{diagnosis.rank}: {diagnosis.condition}
                      </h4>
                      <span style={{ fontSize: "0.9rem", color: "#94a3b8" }}>
                        {diagnosis.confidence}% confidence
                      </span>
                    </div>
                    <p style={{ color: "#cbd5e1", marginBottom: "12px", lineHeight: "1.6" }}>
                      {diagnosis.primary_reason}
                    </p>
                    {diagnosis.next_steps && diagnosis.next_steps.length > 0 && (
                      <div style={{ marginTop: "12px" }}>
                        <strong style={{ color: "#e2e8f0", fontSize: "0.9rem" }}>Next Steps:</strong>
                        <ul style={{ marginTop: "8px", paddingLeft: "20px", color: "#cbd5e1" }}>
                          {diagnosis.next_steps.map((step, i) => (
                            <li key={i} style={{ marginBottom: "4px" }}>{step}</li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Specialist Reports */}
          {Object.keys(specialists).length > 0 && (
            <div style={{ marginBottom: "32px" }}>
              <h3 style={{ fontSize: "1.3rem", fontWeight: "700", marginBottom: "20px", color: "#f1f5f9" }}>
                Specialist Reports
              </h3>
              <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(300px, 1fr))", gap: "16px" }}>
                {Object.entries(specialists).map(([specialist, report]) => (
                  <div
                    key={specialist}
                    style={{
                      padding: "20px",
                      background: "rgba(30, 41, 59, 0.5)",
                      borderRadius: "12px",
                      border: "1px solid rgba(148, 163, 184, 0.2)"
                    }}
                  >
                    <h4 style={{ fontSize: "1rem", fontWeight: "600", color: "#0ea5e9", marginBottom: "12px" }}>
                      {specialist}
                    </h4>
                    {report && report.primary_assessment ? (
                      <>
                        <p style={{ color: "#cbd5e1", fontSize: "0.9rem", marginBottom: "8px" }}>
                          <strong>Assessment:</strong> {report.primary_assessment || "N/A"}
                        </p>
                        <p style={{ color: "#94a3b8", fontSize: "0.85rem" }}>
                          Confidence: {report.overall_confidence || 0}%
                        </p>
                        {report.recommendations && report.recommendations.length > 0 && (
                          <div style={{ marginTop: "12px" }}>
                            <strong style={{ color: "#e2e8f0", fontSize: "0.85rem" }}>Recommendations:</strong>
                            <ul style={{ marginTop: "6px", paddingLeft: "18px", color: "#cbd5e1", fontSize: "0.85rem" }}>
                              {report.recommendations.slice(0, 3).map((rec, i) => (
                                <li key={i}>{rec}</li>
                              ))}
                            </ul>
                          </div>
                        )}
                      </>
                    ) : (
                      <div style={{ padding: "16px", background: "rgba(220, 38, 38, 0.1)", borderRadius: "8px", border: "1px solid rgba(220, 38, 38, 0.3)" }}>
                        <p style={{ color: "#fca5a5", fontSize: "0.9rem", margin: 0 }}>
                          ⚠️ No report available. The {specialist} agent may have encountered an error during processing. 
                          Please check the backend logs or try rerunning the analysis.
                        </p>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Treatment Options */}
          {treatmentOptions && treatmentOptions.length > 0 && (
            <div style={{ marginBottom: "32px" }}>
              <h3 style={{ fontSize: "1.3rem", fontWeight: "700", marginBottom: "20px", color: "#f1f5f9" }}>
                Treatment Options
              </h3>
              <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
                {treatmentOptions.slice(0, 3).map((option, idx) => (
                  <div
                    key={idx}
                    style={{
                      padding: "24px",
                      background: "rgba(30, 41, 59, 0.5)",
                      borderRadius: "12px",
                      border: "1px solid rgba(148, 163, 184, 0.2)"
                    }}
                  >
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "16px" }}>
                      <div>
                        <h4 style={{ fontSize: "1.1rem", fontWeight: "600", color: "#e2e8f0", marginBottom: "8px" }}>
                          {option.primary_name || `Option ${option.option_number || idx + 1}`}
                        </h4>
                        <p style={{ color: "#94a3b8", fontSize: "0.9rem" }}>
                          {option.match_percentage || 0}% match • {option.success_rate || 0}% success rate
                        </p>
                      </div>
                    </div>
                    <p style={{ color: "#cbd5e1", marginBottom: "12px", lineHeight: "1.6" }}>
                      {option.overview}
                    </p>
                    <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))", gap: "12px", marginTop: "16px" }}>
                      {option.duration && (
                        <div>
                          <strong style={{ color: "#94a3b8", fontSize: "0.85rem" }}>Duration:</strong>
                          <p style={{ color: "#cbd5e1", fontSize: "0.9rem" }}>{option.duration}</p>
                        </div>
                      )}
                      {option.cost_estimate && (
                        <div>
                          <strong style={{ color: "#94a3b8", fontSize: "0.85rem" }}>Cost:</strong>
                          <p style={{ color: "#cbd5e1", fontSize: "0.9rem" }}>{option.cost_estimate}</p>
                        </div>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {!agentResults && (
            <p className="field-hint">No agent results available yet. The case may still be processing.</p>
          )}
        </>
      )}

      <div style={{ marginTop: "32px", paddingTop: "24px", borderTop: "1px solid rgba(148, 163, 184, 0.2)" }}>
        <button className="btn btn-outline" onClick={() => navigate("/cases")}>
          ← Back to Cases
        </button>
      </div>
    </section>
  );
}
