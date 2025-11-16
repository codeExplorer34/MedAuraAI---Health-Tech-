// File: src/components/CaseIntakeWizard.jsx
import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { createCase, extractCaseFromPdf } from "../api/api";
import './CaseIntakeWizard.css';

const initialForm = {
  patientId: "",
  name: "",
  age: "",
  gender: "",
  chiefComplaint: "",
  familyHistory: "",
  personalHistory: "",
  lifestyle: "",
  medications: "",
  colonoscopy: "",
  stoolStudies: "",
  bloodTests: "",
  vitals: "",
  abdominalExam: "",
  attachedFiles: []
};

export default function CaseIntakeWizard() {
  const [step, setStep] = useState(1);
  const [form, setForm] = useState(initialForm);
  const [errors, setErrors] = useState({});
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isParsingPdf, setIsParsingPdf] = useState(false);
  const [submitted, setSubmitted] = useState(false);

  const navigate = useNavigate();

  const updateField = (field, value) => {
    setForm(prev => ({ ...prev, [field]: value }));
    setErrors(prev => ({ ...prev, [field]: undefined }));
  };

  const validateStep = () => {
    const e = {};

    if (step === 1) {
      if (!form.patientId.trim()) e.patientId = "Patient ID is required";
      if (!form.name.trim()) e.name = "Name is required";
      if (!form.age) e.age = "Age is required";
      if (!form.gender) e.gender = "Gender is required";
    } else if (step === 2) {
      if (!form.chiefComplaint.trim()) {
        e.chiefComplaint = "Chief complaint is required";
      }
    }

    setErrors(e);
    return Object.keys(e).length === 0;
  };

  const handleNext = () => {
    if (!validateStep()) return;
    setStep(s => s + 1);
  };

  const handleBack = () => {
    setStep(s => Math.max(1, s - 1));
  };

  // ---------- PDF upload for auto-fill ----------
  const handlePdfSelect = async (event) => {
    const file = event.target.files?.[0];
    if (!file) return;

    // Validate file size (max 10MB)
    if (file.size > 10 * 1024 * 1024) {
      alert("PDF file is too large. Maximum size is 10MB.");
      event.target.value = "";
      return;
    }

    setIsParsingPdf(true);
    try {
      const data = await extractCaseFromPdf(file);
      
      // Check if we got any meaningful data
      const hasData = data.patientId || data.name || data.chiefComplaint;
      
      if (!hasData) {
        alert("The PDF was processed but no patient data was found. Please enter the information manually.");
      } else {
        // Map backend response into our form fields
        setForm(prev => ({
          ...prev,
          patientId: data.patientId || prev.patientId,
          name: data.name || prev.name,
          age: data.age || prev.age,
          gender: data.gender || prev.gender,
          chiefComplaint: data.chiefComplaint || prev.chiefComplaint,
          familyHistory: data.familyHistory || prev.familyHistory,
          personalHistory: data.personalHistory || prev.personalHistory,
          lifestyle: data.lifestyle || prev.lifestyle,
          medications: data.medications || prev.medications,
          colonoscopy: data.colonoscopy || prev.colonoscopy,
          stoolStudies: data.stoolStudies || prev.stoolStudies,
          bloodTests: data.bloodTests || prev.bloodTests,
          vitals: data.vitals || prev.vitals,
          abdominalExam: data.abdominalExam || prev.abdominalExam,
          attachedFiles: [file, ...(prev.attachedFiles || [])]
        }));
      }
    } catch (err) {
      console.error("Error parsing PDF:", err);
      const errorMsg = err.message || "Could not extract data from the PDF.";
      alert(`${errorMsg}\n\nYou can still fill in the information manually.`);
    } finally {
      setIsParsingPdf(false);
      // reset input so same file can be picked again if needed
      event.target.value = "";
    }
  };

  const handleExtraFileSelect = (e) => {
    const files = Array.from(e.target.files || []);
    setForm(prev => ({
      ...prev,
      attachedFiles: [...(prev.attachedFiles || []), ...files]
    }));
  };

  const handleSubmit = async () => {
    if (!validateStep()) return;

    setIsSubmitting(true);
    setSubmitted(false);

    try {
      const payload = {
        patientId: form.patientId.trim(),
        name: form.name.trim(),
        age: Number(form.age) || null,
        gender: form.gender,
        chiefComplaint: form.chiefComplaint.trim(),
        familyHistory: form.familyHistory.trim(),
        personalHistory: form.personalHistory.trim(),
        lifestyle: form.lifestyle.trim(),
        medications: form.medications.trim(),
        colonoscopy: form.colonoscopy.trim(),
        stoolStudies: form.stoolStudies.trim(),
        bloodTests: form.bloodTests.trim(),
        vitals: form.vitals.trim(),
        abdominalExam: form.abdominalExam.trim()
        // note: attachedFiles would usually go via a separate upload endpoint
      };

      // For now, call backend createCase (JSON only).
      // Later we can also send files via /upload endpoint.
      const created = await createCase(payload);
      console.log("Created case:", created);

      setSubmitted(true);
      // If backend returns id, navigate to detail:
      if (created?.id) {
        navigate(`/cases/${created.id}`);
      } else {
        // Otherwise reset and stay
        setForm(initialForm);
        setStep(1);
      }
    } catch (err) {
      console.error("Error submitting case:", err);
      alert("Something went wrong while submitting the case.");
    } finally {
      setIsSubmitting(false);
    }
  };

  // ---------- UI ----------
  return (
    <section className="hero-card">
      <h2 className="title">New Case</h2>
      <p className="subtitle">
        You can either upload a PDF report to auto-fill details, or enter them manually.
      </p>

      {/* Step indicator */}
      <div className="wizard-steps">
        <div className={`wizard-step ${step === 1 ? "wizard-step-active" : ""}`}>
          <span className="wizard-step-number">1</span>
          <span className="wizard-step-label">Patient</span>
        </div>
        <div className={`wizard-step ${step === 2 ? "wizard-step-active" : ""}`}>
          <span className="wizard-step-number">2</span>
          <span className="wizard-step-label">History</span>
        </div>
        <div className={`wizard-step ${step === 3 ? "wizard-step-active" : ""}`}>
          <span className="wizard-step-number">3</span>
          <span className="wizard-step-label">Labs & Exam</span>
        </div>
      </div>

      {submitted && (
        <div className="alert-success">
          Case created successfully. If an ID was returned, you should be redirected
          to the case detail page.
        </div>
      )}

      {/* ---------- STEP 1: Patient + PDF upload ---------- */}
      {step === 1 && (
        <div className="wizard-section">
          <div className="form-field" style={{ marginBottom: '32px' }}>
            <label>Upload report PDF (auto-fill)</label>
            <div className="pdf-drop">
              <p className="pdf-drop-title">
                Drag & drop PDF here or click to browse
              </p>
              <p className="field-hint" style={{ marginTop: '8px', marginBottom: '0' }}>
                The AI will extract patient info, complaint, history, labs, and exam details.
              </p>
              <input
                type="file"
                accept="application/pdf"
                onChange={handlePdfSelect}
              />
            </div>
            {isParsingPdf && (
              <div style={{ marginTop: '16px', textAlign: 'center', padding: '16px', background: 'rgba(14, 165, 233, 0.1)', borderRadius: '12px', border: '1px solid rgba(14, 165, 233, 0.3)' }}>
                <div style={{ fontSize: '1.5rem', marginBottom: '8px' }}>⏳</div>
                <p className="field-hint" style={{ color: '#0ea5e9', fontWeight: '500', margin: 0 }}>
                  Analyzing PDF with AI...
                </p>
                <p className="field-hint" style={{ color: '#94a3b8', fontSize: '0.85rem', marginTop: '4px', marginBottom: 0 }}>
                  Extracting patient information from the report
                </p>
              </div>
            )}
          </div>

          <div className="form-grid">
            <div className="form-field">
              <label htmlFor="patientId">Patient ID</label>
              <input
                id="patientId"
                type="text"
                value={form.patientId}
                onChange={e => updateField("patientId", e.target.value)}
              />
              {errors.patientId && (
                <p className="field-error">{errors.patientId}</p>
              )}
            </div>

            <div className="form-field">
              <label htmlFor="name">Patient name</label>
              <input
                id="name"
                type="text"
                value={form.name}
                onChange={e => updateField("name", e.target.value)}
              />
              {errors.name && (
                <p className="field-error">{errors.name}</p>
              )}
            </div>
          </div>

          <div className="form-grid">
            <div className="form-field">
              <label htmlFor="age">Age</label>
              <input
                id="age"
                type="number"
                min="0"
                value={form.age}
                onChange={e => updateField("age", e.target.value)}
              />
              {errors.age && <p className="field-error">{errors.age}</p>}
            </div>

            <div className="form-field">
              <label htmlFor="gender">Gender</label>
              <select
                id="gender"
                value={form.gender}
                onChange={e => updateField("gender", e.target.value)}
              >
                <option value="">Select</option>
                <option value="Female">Female</option>
                <option value="Male">Male</option>
                <option value="Other">Other / Prefer not to say</option>
              </select>
              {errors.gender && (
                <p className="field-error">{errors.gender}</p>
              )}
            </div>
          </div>
        </div>
      )}

      {/* ---------- STEP 2: Complaint & history ---------- */}
      {step === 2 && (
        <div className="wizard-section">
          <div className="form-field">
            <label htmlFor="chiefComplaint">Chief complaint</label>
            <textarea
              id="chiefComplaint"
              rows={3}
              placeholder="Abdominal bloating, irregular bowel movements, cramping abdominal pain for 6 months..."
              value={form.chiefComplaint}
              onChange={e => updateField("chiefComplaint", e.target.value)}
            />
            {errors.chiefComplaint && (
              <p className="field-error">{errors.chiefComplaint}</p>
            )}
          </div>

          <div className="form-field">
            <label htmlFor="familyHistory">Family history</label>
            <textarea
              id="familyHistory"
              rows={2}
              value={form.familyHistory}
              onChange={e => updateField("familyHistory", e.target.value)}
            />
          </div>

          <div className="form-field">
            <label htmlFor="personalHistory">Personal medical history</label>
            <textarea
              id="personalHistory"
              rows={2}
              value={form.personalHistory}
              onChange={e => updateField("personalHistory", e.target.value)}
            />
          </div>

          <div className="form-field">
            <label htmlFor="lifestyle">Lifestyle factors</label>
            <textarea
              id="lifestyle"
              rows={2}
              value={form.lifestyle}
              onChange={e => updateField("lifestyle", e.target.value)}
            />
          </div>

          <div className="form-field">
            <label htmlFor="medications">Medications</label>
            <textarea
              id="medications"
              rows={2}
              value={form.medications}
              onChange={e => updateField("medications", e.target.value)}
            />
          </div>
        </div>
      )}

      {/* ---------- STEP 3: Labs & exam ---------- */}
      {step === 3 && (
        <div className="wizard-section">
          <div className="form-field">
            <label htmlFor="colonoscopy">Colonoscopy</label>
            <textarea
              id="colonoscopy"
              rows={2}
              value={form.colonoscopy}
              onChange={e => updateField("colonoscopy", e.target.value)}
            />
          </div>

          <div className="form-field">
            <label htmlFor="stoolStudies">Stool studies</label>
            <textarea
              id="stoolStudies"
              rows={2}
              value={form.stoolStudies}
              onChange={e => updateField("stoolStudies", e.target.value)}
            />
          </div>

          <div className="form-field">
            <label htmlFor="bloodTests">Blood tests</label>
            <textarea
              id="bloodTests"
              rows={2}
              value={form.bloodTests}
              onChange={e => updateField("bloodTests", e.target.value)}
            />
          </div>

          <div className="form-field">
            <label htmlFor="vitals">Vitals</label>
            <textarea
              id="vitals"
              rows={2}
              value={form.vitals}
              onChange={e => updateField("vitals", e.target.value)}
            />
          </div>

          <div className="form-field">
            <label htmlFor="abdominalExam">Abdominal exam</label>
            <textarea
              id="abdominalExam"
              rows={2}
              value={form.abdominalExam}
              onChange={e => updateField("abdominalExam", e.target.value)}
            />
          </div>

          <div className="form-field">
            <label htmlFor="extraFiles">Attach extra files (optional)</label>
            <input
              id="extraFiles"
              type="file"
              multiple
              onChange={handleExtraFileSelect}
            />
            {form.attachedFiles?.length ? (
              <p className="field-hint">
                {form.attachedFiles.length} file(s) attached.
              </p>
            ) : (
              <p className="field-hint">
                You can attach additional images or lab reports here.
              </p>
            )}
          </div>
        </div>
      )}

      {/* Navigation buttons */}
      <div className="wizard-actions">
        <button
          className="btn btn-outline"
          type="button"
          onClick={() => (step === 1 ? navigate("/cases") : handleBack())}
        >
          {step === 1 ? "Cancel" : "Back"}
        </button>

        {step < 3 && (
          <button className="btn" type="button" onClick={handleNext}>
            Next
          </button>
        )}

        {step === 3 && (
          <button
            className="btn"
            type="button"
            onClick={handleSubmit}
            disabled={isSubmitting}
          >
            {isSubmitting ? "Submitting…" : "Submit Case"}
          </button>
        )}
      </div>
    </section>
  );
}

