// File: src/components/CaseDashboard.jsx
import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { listCases } from "../api/api";

const MOCK_CASES = [
  {
    id: "100232",
    patientId: "100232",
    name: "Anna Thompson",
    age: 35,
    gender: "Female",
    chiefComplaint: "Abdominal bloating, irregular bowel movements, cramping pain",
    createdAt: "2024-12-10T10:15:00Z",
    status: "Completed"
  },
  {
    id: "100233",
    patientId: "100233",
    name: "John Miller",
    age: 58,
    gender: "Male",
    chiefComplaint: "Exertional chest pain, shortness of breath",
    createdAt: "2024-12-11T09:20:00Z",
    status: "Running"
  },
  {
    id: "100234",
    patientId: "100234",
    name: "Sara Lee",
    age: 42,
    gender: "Female",
    chiefComplaint: "Persistent headaches, visual disturbances",
    createdAt: "2024-12-11T11:05:00Z",
    status: "Queued"
  }
];

function formatDate(iso) {
  if (!iso) return "—";
  const d = new Date(iso);
  return d.toLocaleString();
}

function StatusBadge({ status }) {
  const s = (status || "").toLowerCase();
  let cls = "status-badge status-badge-queued";
  if (s === "running") cls = "status-badge status-badge-running";
  if (s === "completed") cls = "status-badge status-badge-completed";
  if (s === "error") cls = "status-badge status-badge-error";

  return <span className={cls}>{status || "Unknown"}</span>;
}

export default function CaseDashboard() {
  const [cases, setCases] = useState([]);
  const [q, setQ] = useState("");
  const [statusFilter, setStatusFilter] = useState("all");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const navigate = useNavigate();

  useEffect(() => {
    let cancelled = false;

    async function fetchCases() {
      setLoading(true);
      setError("");

      try {
        // Try actual backend first
        const data = await listCases({});
        if (cancelled) return;

        // Expecting { items: [...] } from backend; fallback if array only
        const items = Array.isArray(data?.items) ? data.items : Array.isArray(data) ? data : [];
        if (!items.length) {
          // If backend returns empty, show mock for now
          setCases(MOCK_CASES);
        } else {
          setCases(items);
        }
      } catch (err) {
        console.error("Error loading cases, using mock:", err);
        if (!cancelled) {
          setError("Could not load cases from backend. Showing demo data.");
          setCases(MOCK_CASES);
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    fetchCases();
    return () => {
      cancelled = true;
    };
  }, []);

  const filtered = cases.filter((c) => {
    const matchesQ =
      !q ||
      c.name?.toLowerCase().includes(q.toLowerCase()) ||
      c.patientId?.toLowerCase().includes(q.toLowerCase()) ||
      c.chiefComplaint?.toLowerCase().includes(q.toLowerCase());
    const matchesStatus =
      statusFilter === "all" ||
      (c.status || "").toLowerCase() === statusFilter.toLowerCase();
    return matchesQ && matchesStatus;
  });

  return (
    <section className="hero-card">
      <div className="cases-header">
        <div>
          <h2 className="title">Cases</h2>
          <p className="subtitle">
            Review patients whose reports have been analyzed by MedAuraAI’s
            specialist agents.
          </p>
        </div>

        <button
          className="btn btn-primary-lg cases-new-btn"
          onClick={() => navigate("/cases/new")}
        >
          + New Case
        </button>
      </div>

      {error && <div className="alert-warning">{error}</div>}

      <div className="cases-filters">
        <input
          className="input"
          type="text"
          placeholder="Search by patient name, ID, or complaint…"
          value={q}
          onChange={(e) => setQ(e.target.value)}
        />

        <select
          className="input input-select"
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
        >
          <option value="all">All statuses</option>
          <option value="Queued">Queued</option>
          <option value="Running">Running</option>
          <option value="Completed">Completed</option>
          <option value="Error">Error</option>
        </select>
      </div>

      {loading ? (
        <p className="field-hint" style={{ marginTop: 16 }}>
          Loading cases…
        </p>
      ) : filtered.length === 0 ? (
        <p className="field-hint" style={{ marginTop: 16 }}>
          No cases match your filters.
        </p>
      ) : (
        <div className="cases-list">
          {filtered.map((c) => (
            <button
              key={c.id}
              className="case-row"
              onClick={() => navigate(`/cases/${c.id}`)}
            >
              <div className="case-main">
                <div className="case-title">
                  <span className="case-name">{c.name || "Unnamed"}</span>
                  <span className="case-id">#{c.patientId || c.id}</span>
                </div>
                <div className="case-complaint">
                  {c.chiefComplaint || "No chief complaint provided."}
                </div>
              </div>

              <div className="case-meta">
                <StatusBadge status={c.status} />
                <div className="case-age-gender">
                  {c.age ? `${c.age} yrs` : "—"} · {c.gender || "—"}
                </div>
                <div className="case-date">{formatDate(c.createdAt)}</div>
              </div>
            </button>
          ))}
        </div>
      )}
    </section>
  );
}
