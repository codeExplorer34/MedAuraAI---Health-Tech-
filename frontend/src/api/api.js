// File: src/api/api.js

const BASE_URL =
  import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

/**
 * Small helper to call backend.
 * - If `isFormData` is true, body should be FormData and we don't set JSON headers.
 */
async function request(path, { method = "GET", body, isFormData = false } = {}) {
  const headers = {};

  if (body && !isFormData) {
    headers["Content-Type"] = "application/json";
  }

  const res = await fetch(`${BASE_URL}${path}`, {
    method,
    headers,
    body: body
      ? isFormData
        ? body
        : JSON.stringify(body)
      : undefined
  });

  const contentType = res.headers.get("content-type") || "";

  let data;
  if (contentType.includes("application/json")) {
    data = await res.json();
  } else {
    data = await res.text();
  }

  if (!res.ok) {
    const msg = typeof data === "string" ? data : data?.error || "Request failed";
    throw new Error(msg);
  }

  return data;
}

/**
 * Create a new medical case (manual or AI-populated).
 * Expects a plain JSON object.
 */
export function createCase(caseData) {
  return request("/api/cases", {
    method: "POST",
    body: caseData
  });
}

/**
 * Upload a PDF report and ask backend to extract structured fields.
 * Backend endpoint should:
 * - accept multipart/form-data
 * - return JSON with fields matching our form:
 *   {
 *     patientId, name, age, gender,
 *     chiefComplaint,
 *     familyHistory, personalHistory, lifestyle, medications,
 *     colonoscopy, stoolStudies, bloodTests,
 *     vitals, abdominalExam
 *   }
 */
export function extractCaseFromPdf(file) {
  const formData = new FormData();
  formData.append("file", file);

  return request("/api/cases/parse-report", {
    method: "POST",
    body: formData,
    isFormData: true
  });
}

// We’ll add these later when we build dashboard/detail:
export function listCases(params = {}) {
  const q = new URLSearchParams(params).toString();
  return request(`/api/cases${q ? `?${q}` : ""}`);
}

export function getCase(caseId) {
  return request(`/api/cases/${encodeURIComponent(caseId)}`);
}

export function rerunAgents(caseId) {
  return request(`/api/cases/${encodeURIComponent(caseId)}/rerun`, {
    method: "POST"
  });
}
