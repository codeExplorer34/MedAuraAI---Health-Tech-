from langchain_core.prompts import PromptTemplate
from langchain_ollama import ChatOllama
import os
import json
import re
from typing import List, Optional, Dict
import time
from threading import Lock
from pydantic import BaseModel, Field, ValidationError
from typing import Literal


class EvidenceItem(BaseModel):
    summary: str
    quote: str
    confidence: float = Field(ge=0, le=100)


class ContradictionItem(BaseModel):
    description: str
    related_specialist: Optional[str] = None
    impact: Literal["low", "medium", "high"]


class SpecialistReport(BaseModel):
    specialist: str
    primary_assessment: str
    overall_confidence: float = Field(ge=0, le=100)
    key_findings: List[EvidenceItem] = Field(default_factory=list)
    contradictions: List[ContradictionItem] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)


class SupportItem(BaseModel):
    specialist: str
    confidence: float = Field(ge=0, le=100)
    evidence: str


class TeamDiagnosisContradiction(BaseModel):
    description: str
    specialist: Optional[str] = None
    impact: Literal["low", "medium", "high"]


class DiagnosisItem(BaseModel):
    rank: int = Field(ge=1, le=3)
    condition: str
    confidence: float = Field(ge=0, le=100)
    primary_reason: str
    specialist_support: List[SupportItem] = Field(default_factory=list)
    contradictions: List[TeamDiagnosisContradiction] = Field(default_factory=list)
    next_steps: List[str] = Field(default_factory=list)


class TeamSummary(BaseModel):
    overall_confidence: float = Field(ge=0, le=100)
    diagnoses: List[DiagnosisItem]
    consensus_highlights: List[str] = Field(default_factory=list)
    disagreement_notes: List[str] = Field(default_factory=list)
    specialist_confidence: Dict[str, float] = Field(default_factory=dict)

# Simple rate limiting (default: 7 seconds between calls, configurable via env variable)
_RATE_LIMIT_LOCK = Lock()
_LAST_CALL_TIME = 0.0
_CALL_INTERVAL_SECONDS = float(os.getenv("LLM_CALL_INTERVAL_SECONDS", "7"))


def enforce_rate_limit():
    """Ensure at most 1 call every _CALL_INTERVAL_SECONDS globally."""
    global _LAST_CALL_TIME
    with _RATE_LIMIT_LOCK:
        now = time.time()
        wait_time = _CALL_INTERVAL_SECONDS - (now - _LAST_CALL_TIME)
        if wait_time > 0:
            time.sleep(wait_time)
        _LAST_CALL_TIME = time.time()


# Try to import Google Gemini (optional - only if package is installed)
try:
    from langchain_google_genai import ChatGoogleGenerativeAI
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False

class Agent:
    def __init__(self, medical_report=None, role=None, extra_info=None, api_key=None):
        self.medical_report = medical_report
        self.role = role
        self.extra_info = extra_info
        # Initialize the prompt based on role and other info
        self.prompt_template = self.create_prompt_template()
        self.schema_model = self._resolve_schema_model()
        # Initialize the model - using free Gemini model
        # Use provided api_key, or fall back to role-specific env var, or default GOOGLE_API_KEY
        if api_key is None:
            # Try role-specific API key first (e.g., INTERNIST_API_KEY, NEUROLOGIST_API_KEY)
            role_env_key = f"{self.role.upper()}_API_KEY" if self.role else None
            google_api_key = os.getenv(role_env_key) if role_env_key else None
            # Fall back to default if role-specific key not found
            if not google_api_key:
                google_api_key = os.getenv("GOOGLE_API_KEY")
        else:
            google_api_key = api_key
        if GEMINI_AVAILABLE and google_api_key:
            # Using gemini-2.5-flash (stable, free tier, fast)
            # Alternative free models: gemini-2.0-flash-lite,
            # "models/gemini-flash-latest" (latest flash), "models/gemini-pro-latest" (latest pro)
            self.model = ChatGoogleGenerativeAI(
                temperature=0, 
                model="models/gemini-2.5-flash",
                google_api_key=google_api_key
            )
        else:
            # Fallback to Ollama if Gemini not available
            self.model = ChatOllama(temperature=0, model="llama3.1")
        self.last_raw_response = None
        self.last_structured_response = None

    def _resolve_schema_model(self):
        if self.role == "MultidisciplinaryTeam":
            return TeamSummary
        return SpecialistReport

    def _extract_json(self, text):
        if isinstance(text, list):
            text = " ".join([json.dumps(t) if isinstance(t, (dict, list)) else str(t) for t in text])
        elif isinstance(text, dict):
            text = json.dumps(text)
        elif isinstance(text, str):
            text = text.strip()
        else:
            text = str(text)
        
        if not text:
            raise ValueError(f"[{self.role}] No content to parse!")

        # First, try to extract JSON from markdown code blocks (```json ... ``` or ``` ... ```)
        markdown_pattern = r'```(?:json)?\s*\n?(.*?)\n?```'
        markdown_match = re.search(markdown_pattern, text, flags=re.S | re.I)
        if markdown_match:
            text = markdown_match.group(1).strip()
        
        # Now try to find JSON object in the text
        match = re.search(r'\{.*\}', text, flags=re.S)
        if match:
            candidate = match.group(0)
            try:
                json.loads(candidate)
                return candidate
            except json.JSONDecodeError:
                pass  # fallback to using full text below

        return text

    def _parse_response(self, raw_text):
        if raw_text is None or (isinstance(raw_text, str) and not raw_text.strip()):
            raise ValueError(f"[{self.role}] Empty response received!")

        json_text = self._extract_json(raw_text)

        if not json_text.strip():
            raise ValueError(f"[{self.role}] Extracted JSON is empty!")

        try:
            data = json.loads(json_text)
        except json.JSONDecodeError as e:
            raise ValueError(f"[{self.role}] Failed to decode JSON: {e}\nRaw text: {repr(json_text)}") from e

        try:
            # Validate with your schema model
            return self.schema_model.model_validate(data)
        except ValidationError as err:
            raise ValueError(f"[{self.role}] Structured output validation failed: {err}") from err

    def create_prompt_template(self):
        if self.role == "MultidisciplinaryTeam":
            templates = """
You are the multidisciplinary synthesis team responsible for converting structured specialist insights into a prioritized differential diagnosis.

INPUT DATA (validated JSON strings):
- Internist Report: {internist_report}
- Neurologist Report: {neurologist_report}
- Cardiologist Report: {cardiologist_report}
- Gastroenterologist Report: {gastroenterologist_report}
- Psychiatrist Report: {psychiatrist_report}
- Structured Specialist Bundle: {structured_specialist_reports}
- Patient Chief Complaint and Symptoms: {chief_complaint}

OUTPUT REQUIREMENTS:
Return ONLY valid JSON matching this schema exactly:
{
  "overall_confidence": 0-100,
  "diagnoses": [
    {
      "rank": 1,
      "condition": "string",
      "confidence": 0-100,
      "primary_reason": "string",
      "specialist_support": [
        {
          "specialist": "string",
          "confidence": 0-100,
          "evidence": "string"
        }
      ],
      "contradictions": [
        {
          "description": "string",
          "specialist": "string",
          "impact": "low" | "medium" | "high"
        }
      ],
      "next_steps": [
        "string"
      ]
    },
    {
      "rank": 2,
      "condition": "string",
      "confidence": 0-100,
      "primary_reason": "string",
      "specialist_support": [
        {
          "specialist": "string",
          "confidence": 0-100,
          "evidence": "string"
        }
      ],
      "contradictions": [
        {
          "description": "string",
          "specialist": "string",
          "impact": "low" | "medium" | "high"
        }
      ],
      "next_steps": [
        "string"
      ]
    },
    {
      "rank": 3,
      "condition": "string",
      "confidence": 0-100,
      "primary_reason": "string",
      "specialist_support": [
        {
          "specialist": "string",
          "confidence": 0-100,
          "evidence": "string"
        }
      ],
      "contradictions": [
        {
          "description": "string",
          "specialist": "string",
          "impact": "low" | "medium" | "high"
        }
      ],
      "next_steps": [
        "string"
      ]
    }
  ],
  "consensus_highlights": [
    "string"
  ],
  "disagreement_notes": [
    "string"
  ],
  "specialist_confidence": {
    "Internist": 0-100,
    "Neurologist": 0-100,
    "Cardiologist": 0-100,
    "Gastroenterologist": 0-100,
    "Psychiatrist": 0-100
  }
}

CONSTRAINTS:
- Provide EXACTLY three diagnoses ranked 1-3 (rank 1 = highest confidence).
- Confidence values must be realistic and grounded in the supplied reports.
- Each specialist_support entry must map to a supplied specialist (no new specialists).
- Contradictions should capture conflicts or gaps, referencing the relevant specialist.
- next_steps should list concrete clinical actions for that diagnosis.
- consensus_highlights summarize areas of agreement; disagreement_notes capture unresolved conflicts.
- Return nothing except the JSON object.
"""
        else:
            templates = {
                "Internist": """
You are the Internist synthesizing systemic medical findings.

INSTRUCTIONS:
- Focus strictly on systemic diseases, medication interactions, and whole-body implications.
- Reference only evidence from the report using short quotes (5-15 words).
- Identify contradictions or gaps relevant to systemic assessment.

OUTPUT (return ONLY JSON matching this schema):
{
  "specialist": "Internist",
  "primary_assessment": "string",
  "overall_confidence": 0-100,
  "key_findings": [
    {
      "summary": "string",
      "quote": "string",
      "confidence": 0-100
    }
  ],
  "contradictions": [
    {
      "description": "string",
      "related_specialist": "string or null",
      "impact": "low" | "medium" | "high"
    }
  ],
  "recommendations": [
    "string"
  ]
}

RULES:
- Provide 2-4 key_findings with confidence scores.
- Recommendations should be actionable systemic next steps.
- Include arrays even if empty (use []).
- Return only the JSON object (no prose or explanations).

Medical Report: {medical_report}
""",
                "Neurologist": """
You are the Neurologist evaluating the patient's neurological status.

INSTRUCTIONS:
- Cover brain, spine, nerve, and neuromuscular issues only.
- Use short quotes (5-15 words) from the report as evidence.
- Highlight contradictions or missing data relevant to neurology.

OUTPUT (return ONLY JSON matching this schema):
{
  "specialist": "Neurologist",
  "primary_assessment": "string",
  "overall_confidence": 0-100,
  "key_findings": [
    {
      "summary": "string",
      "quote": "string",
      "confidence": 0-100
    }
  ],
  "contradictions": [
    {
      "description": "string",
      "related_specialist": "string or null",
      "impact": "low" | "medium" | "high"
    }
  ],
  "recommendations": [
    "string"
  ]
}

RULES:
- Provide 2-4 key_findings with confidence scores.
- Recommendations must be neurologically focused.
- Arrays must be present even if empty.
- Return only the JSON object.

Medical Report: {medical_report}
""",
                "Cardiologist": """
You are the Cardiologist focusing on cardiovascular findings.

INSTRUCTIONS:
- Discuss heart structure, rhythm, perfusion, and cardiovascular risk only.
- Include short quotes (5-15 words) from the report to support each finding.
- Flag contradictions or missing information affecting cardiac interpretation.

OUTPUT (return ONLY JSON matching this schema):
{
  "specialist": "Cardiologist",
  "primary_assessment": "string",
  "overall_confidence": 0-100,
  "key_findings": [
    {
      "summary": "string",
      "quote": "string",
      "confidence": 0-100
    }
  ],
  "contradictions": [
    {
      "description": "string",
      "related_specialist": "string or null",
      "impact": "low" | "medium" | "high"
    }
  ],
  "recommendations": [
    "string"
  ]
}

RULES:
- Provide 2-4 key_findings with confidence scores.
- Recommendations must address cardiac management or follow-up.
- Arrays must be present even if empty.
- Return only the JSON object.

Medical Report: {medical_report}
""",
                "Gastroenterologist": """
You are the Gastroenterologist assessing gastrointestinal and hepatobiliary findings.

INSTRUCTIONS:
- Focus on GI tract, liver, pancreas, and related systems only.
- Support each finding with short quotes (5-15 words) from the report.
- Document contradictions or gaps impacting GI interpretation.

OUTPUT (return ONLY JSON matching this schema):
{
  "specialist": "Gastroenterologist",
  "primary_assessment": "string",
  "overall_confidence": 0-100,
  "key_findings": [
    {
      "summary": "string",
      "quote": "string",
      "confidence": 0-100
    }
  ],
  "contradictions": [
    {
      "description": "string",
      "related_specialist": "string or null",
      "impact": "low" | "medium" | "high"
    }
  ],
  "recommendations": [
    "string"
  ]
}

RULES:
- Provide 2-4 key_findings with confidence scores.
- Recommendations must be GI-focused actions.
- Arrays must be present even if empty.
- Return only the JSON object.

Medical Report: {medical_report}
""",
                "Psychiatrist": """
You are the Psychiatrist evaluating mental health findings.

INSTRUCTIONS:
- Focus on mood, anxiety, cognition, behavior, and psychopharmacology effects.
- Use short quotes (5-15 words) from the report to support findings.
- Capture contradictions or missing information relevant to psychiatric assessment.

OUTPUT (return ONLY JSON matching this schema):
{
  "specialist": "Psychiatrist",
  "primary_assessment": "string",
  "overall_confidence": 0-100,
  "key_findings": [
    {
      "summary": "string",
      "quote": "string",
      "confidence": 0-100
    }
  ],
  "contradictions": [
    {
      "description": "string",
      "related_specialist": "string or null",
      "impact": "low" | "medium" | "high"
    }
  ],
  "recommendations": [
    "string"
  ]
}

RULES:
- Provide 2-4 key_findings with confidence scores.
- Recommendations must be psychiatric next steps.
- Arrays must be present even if empty.
- Return only the JSON object.

Medical Report: {medical_report}
"""
            }
            templates = templates[self.role]
        # Convert placeholders to Jinja2 to avoid Python .format conflicts with JSON braces
        templates = templates.replace("{medical_report}", "{{ medical_report }}") \
            .replace("{internist_report}", "{{ internist_report }}") \
            .replace("{neurologist_report}", "{{ neurologist_report }}") \
            .replace("{cardiologist_report}", "{{ cardiologist_report }}") \
            .replace("{gastroenterologist_report}", "{{ gastroenterologist_report }}") \
            .replace("{psychiatrist_report}", "{{ psychiatrist_report }}") \
            .replace("{structured_specialist_reports}", "{{ structured_specialist_reports }}") \
            .replace("{chief_complaint}", "{{ chief_complaint }}") \
            .replace("{diagnoses}", "{{ diagnoses }}") \
            .replace("{team_confidence}", "{{ team_confidence }}")
        # Determine expected input variables
        if self.role == "MultidisciplinaryTeam":
            input_vars = [
                "internist_report",
                "neurologist_report",
                "cardiologist_report",
                "gastroenterologist_report",
                "psychiatrist_report",
                "structured_specialist_reports",
                "chief_complaint",
            ]
        else:
            input_vars = ["medical_report"]
        return PromptTemplate(template=templates, input_variables=input_vars, template_format="jinja2")
    
    def run(self):
        print(f"{self.role} is running...")
        if self.role == "MultidisciplinaryTeam":
            # For MultidisciplinaryTeam, format with extra_info values
            prompt = self.prompt_template.format(
                internist_report=self.extra_info.get('internist_report', ''),
                neurologist_report=self.extra_info.get('neurologist_report', ''),
                cardiologist_report=self.extra_info.get('cardiologist_report', ''),
                gastroenterologist_report=self.extra_info.get('gastroenterologist_report', ''),
                psychiatrist_report=self.extra_info.get('psychiatrist_report', ''),
                chief_complaint=self.extra_info.get('chief_complaint', ''),
                structured_specialist_reports=self.extra_info.get('structured_reports_json', '')
            )
        else:
            # For individual agents, format with medical_report
            prompt = self.prompt_template.format(medical_report=self.medical_report)
        try:
            enforce_rate_limit()
            response = self.model.invoke(prompt)
            raw_text = response.content if hasattr(response, "content") else str(response)
            self.last_raw_response = raw_text
            structured = self._parse_response(raw_text)
            self.last_structured_response = structured
            return structured
        except Exception as e:
            print(f"Error occurred in {self.role}:", e)
            import traceback
            traceback.print_exc()
            return None

# Define specialized agent classes
class Internist(Agent):
    def __init__(self, medical_report, api_key=None):
        super().__init__(medical_report, "Internist", api_key=api_key)

class Neurologist(Agent):
    def __init__(self, medical_report, api_key=None):
        super().__init__(medical_report, "Neurologist", api_key=api_key)

class Cardiologist(Agent):
    def __init__(self, medical_report, api_key=None):
        super().__init__(medical_report, "Cardiologist", api_key=api_key)

class Gastroenterologist(Agent):
    def __init__(self, medical_report, api_key=None):
        super().__init__(medical_report, "Gastroenterologist", api_key=api_key)

class Psychiatrist(Agent):
    def __init__(self, medical_report, api_key=None):
        super().__init__(medical_report, "Psychiatrist", api_key=api_key)

class MultidisciplinaryTeam(Agent):
    def __init__(self, medical_report, internist_report, neurologist_report, cardiologist_report, gastroenterologist_report, psychiatrist_report, structured_reports_json="", api_key=None):
        extra_info = {
            "internist_report": internist_report,
            "neurologist_report": neurologist_report,
            "cardiologist_report": cardiologist_report,
            "gastroenterologist_report": gastroenterologist_report,
            "psychiatrist_report": psychiatrist_report,
            "chief_complaint": medical_report,
            "structured_reports_json": structured_reports_json
        }
        super().__init__(medical_report=medical_report, role="MultidisciplinaryTeam", extra_info=extra_info, api_key=api_key)
        self.treatment_prompt_template = PromptTemplate(template="""
You are the multidisciplinary specialist team finalizing comprehensive treatment recommendations.

CLINICAL CONTEXT:
- Working Diagnoses: {{ diagnoses }}
- Internist Report: {{ internist_report }}
- Neurologist Report: {{ neurologist_report }}
- Cardiologist Report: {{ cardiologist_report }}
- Gastroenterologist Report: {{ gastroenterologist_report }}
- Psychiatrist Report: {{ psychiatrist_report }}
- Patient History & Symptoms: {{ chief_complaint }}
- Specialist Confidence Snapshot: {{ team_confidence }}
- Structured Specialist Bundle: {{ structured_specialist_reports }}

GOAL:
Produce exactly three treatment options that balance efficacy, risk, recovery, and patient fit. Each option must be evidence-based and internally consistent with the clinical findings.

CRITICAL FORMAT RULES (NO deviations):
💊 Treatment Options

Option 1([match_percentage_1]% match)
[Primary Treatment Name]
[One-sentence overview tailored to the patient]
[Therapy Modality Label]
[Success_Rate_1]% Success Rate
⏱ Duration
[Duration Estimate]
🏥 Recovery Time
[Recovery Timeline]
💰 Cost Estimate
[Cost Range]
⚠
Potential Side Effects
• [Side effect 1]
• [Side effect 2]
• [Side effect 3]
✅
Recommended For
✓ [Ideal patient profile 1]
✓ [Ideal patient profile 2]
✓ [Ideal patient profile 3]
📋
Procedure Steps
1
[Step 1]
2
[Step 2]
3
[Step 3]
4
[Step 4]
5
[Step 5]
💡
Personalized Notes
• [Note 1]
• [Note 2]
• [Note 3]

Option 2([match_percentage_2]% match)
[Repeat the exact structure above for the second option]

Option 3([match_percentage_3]% match)
[Repeat the exact structure above for the third option]

ADDITIONAL RULES:
- Match percentages must reflect comparative suitability (e.g., 60-95%), decreasing from most to least preferred unless clinical nuance dictates otherwise.
- Success rates, durations, costs, and side effects must align with realistic medical data.
- Ensure modality labels (e.g., "Pharmacologic Regimen", "Surgical + Radiation") clearly communicate the treatment category.
- Tailor personalized notes to the patient’s presentation and the multidisciplinary findings—do not provide generic statements.
- Maintain strict adherence to the line order and spacing shown (blank line between major sections, none within).
""", input_variables=[
            "diagnoses",
            "internist_report",
            "neurologist_report",
            "cardiologist_report",
            "gastroenterologist_report",
            "psychiatrist_report",
            "chief_complaint",
            "team_confidence",
            "structured_specialist_reports",
        ], template_format="jinja2")
        # JSON schema prompt for structured treatment options
        treatment_json_template = """
You are the multidisciplinary team producing structured treatment recommendations.

INPUT SUMMARY:
- Working Diagnoses: {{ diagnoses }}
- Specialist Confidence Snapshot: {{ team_confidence }}
- Structured Specialist Bundle: {{ structured_specialist_reports }}

OUTPUT REQUIREMENTS:
Return ONLY valid JSON matching this schema exactly:
{
  "options": [
    {
      "option_number": 1,
      "match_percentage": 0-100,
      "primary_name": "string",
      "overview": "string",
      "modality": "string",
      "success_rate": 0-100,
      "duration": "string",
      "recovery_time": "string",
      "cost_estimate": "string",
      "side_effects": ["string"],
      "recommended_for": ["string"],
      "procedure_steps": ["string"],
      "notes": ["string"]
    },
    {
      "option_number": 2,
      "match_percentage": 0-100,
      "primary_name": "string",
      "overview": "string",
      "modality": "string",
      "success_rate": 0-100,
      "duration": "string",
      "recovery_time": "string",
      "cost_estimate": "string",
      "side_effects": ["string"],
      "recommended_for": ["string"],
      "procedure_steps": ["string"],
      "notes": ["string"]
    },
    {
      "option_number": 3,
      "match_percentage": 0-100,
      "primary_name": "string",
      "overview": "string",
      "modality": "string",
      "success_rate": 0-100,
      "duration": "string",
      "recovery_time": "string",
      "cost_estimate": "string",
      "side_effects": ["string"],
      "recommended_for": ["string"],
      "procedure_steps": ["string"],
      "notes": ["string"]
    }
  ]
}

CONSTRAINTS:
- Provide exactly three options with descending match_percentage unless clinical nuance dictates otherwise.
- Ensure fields are concise and clinically realistic.
- Return only JSON.
"""
        self.treatment_json_prompt_template = PromptTemplate(
            template=treatment_json_template,
            input_variables=[
                "diagnoses",
                "team_confidence",
                "structured_specialist_reports",
            ],
            template_format="jinja2",
        )

    def generate_treatment_plan(self, diagnoses_summary):
        try:
            if isinstance(diagnoses_summary, TeamSummary):
                diagnoses_payload = diagnoses_summary.model_dump_json(indent=2)
                team_confidence = json.dumps(diagnoses_summary.specialist_confidence, indent=2)
            elif isinstance(diagnoses_summary, str):
                diagnoses_payload = diagnoses_summary
                team_confidence = "Unavailable"
            else:
                diagnoses_payload = json.dumps(diagnoses_summary, indent=2)
                team_confidence = "Unavailable"
            prompt = self.treatment_prompt_template.format(
                diagnoses=diagnoses_payload,
                internist_report=self.extra_info.get("internist_report", ""),
                neurologist_report=self.extra_info.get("neurologist_report", ""),
                cardiologist_report=self.extra_info.get("cardiologist_report", ""),
                gastroenterologist_report=self.extra_info.get("gastroenterologist_report", ""),
                psychiatrist_report=self.extra_info.get("psychiatrist_report", ""),
                chief_complaint=self.extra_info.get("chief_complaint", ""),
                team_confidence=team_confidence,
                structured_specialist_reports=self.extra_info.get("structured_reports_json", "")
            )
            enforce_rate_limit()
            response = self.model.invoke(prompt)
            return response.content
        except Exception as e:
            print("Error occurred while generating treatment plan:", e)
            import traceback
            traceback.print_exc()
            return None

    def generate_treatment_plan_json(self, diagnoses_summary):
        try:
            if isinstance(diagnoses_summary, TeamSummary):
                diagnoses_payload = diagnoses_summary.model_dump_json(indent=2)
                team_confidence = json.dumps(diagnoses_summary.specialist_confidence, indent=2)
            elif isinstance(diagnoses_summary, str):
                diagnoses_payload = diagnoses_summary
                team_confidence = "Unavailable"
            else:
                diagnoses_payload = json.dumps(diagnoses_summary, indent=2)
                team_confidence = "Unavailable"
            prompt = self.treatment_json_prompt_template.format(
                diagnoses=diagnoses_payload,
                team_confidence=team_confidence,
                structured_specialist_reports=self.extra_info.get("structured_reports_json", ""),
            )
            enforce_rate_limit()
            response = self.model.invoke(prompt)
            raw_text = response.content if hasattr(response, "content") else str(response)
            # Try to extract and validate JSON list of options
            json_text = self._extract_json(raw_text)
            data = json.loads(json_text)
            if not isinstance(data, dict) or "options" not in data or not isinstance(data["options"], list):
                raise ValueError("Treatment JSON does not contain 'options' array.")
            return data["options"]
        except Exception as e:
            print("Error occurred while generating structured treatment JSON:", e)
            import traceback
            traceback.print_exc()
            return None