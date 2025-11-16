"""
FastAPI server for MedAuraAI - Medical Diagnostics API
"""
from fastapi import FastAPI, HTTPException, UploadFile, File, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Optional, Dict
from datetime import datetime
import json
import os
import uuid
import io
from concurrent.futures import ThreadPoolExecutor, as_completed
from dotenv import load_dotenv
import pdfplumber
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser

from Utils.Agents import (
    Internist,
    Neurologist,
    Cardiologist,
    Gastroenterologist,
    Psychiatrist,
    MultidisciplinaryTeam,
    TeamSummary,
)

# Load environment variables
load_dotenv(dotenv_path='apikey.env')

app = FastAPI(title="MedAuraAI API", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory storage (replace with database in production)
cases_db: Dict[str, dict] = {}
cases_dir = "cases_data"
os.makedirs(cases_dir, exist_ok=True)

# Pydantic models
class CaseCreate(BaseModel):
    patientId: str
    name: str
    age: Optional[int] = None
    gender: Optional[str] = None
    chiefComplaint: Optional[str] = None
    familyHistory: Optional[str] = None
    personalHistory: Optional[str] = None
    lifestyle: Optional[str] = None
    medications: Optional[str] = None
    colonoscopy: Optional[str] = None
    stoolStudies: Optional[str] = None
    bloodTests: Optional[str] = None
    vitals: Optional[str] = None
    abdominalExam: Optional[str] = None

class CaseResponse(BaseModel):
    id: str
    patientId: str
    name: str
    age: Optional[int]
    gender: Optional[str]
    chiefComplaint: Optional[str]
    status: str
    createdAt: str
    updatedAt: str
    agentResults: Optional[Dict] = None

def build_medical_report(case_data: dict) -> str:
    """Build a medical report string from case data"""
    report_parts = []
    
    if case_data.get("name"):
        report_parts.append(f"Patient: {case_data['name']}")
    if case_data.get("age"):
        report_parts.append(f"Age: {case_data['age']}")
    if case_data.get("gender"):
        report_parts.append(f"Gender: {case_data['gender']}")
    if case_data.get("patientId"):
        report_parts.append(f"Patient ID: {case_data['patientId']}")
    
    report_parts.append("\n--- CHIEF COMPLAINT ---")
    if case_data.get("chiefComplaint"):
        report_parts.append(case_data['chiefComplaint'])
    
    report_parts.append("\n--- MEDICAL HISTORY ---")
    if case_data.get("familyHistory"):
        report_parts.append(f"Family History: {case_data['familyHistory']}")
    if case_data.get("personalHistory"):
        report_parts.append(f"Personal History: {case_data['personalHistory']}")
    if case_data.get("lifestyle"):
        report_parts.append(f"Lifestyle: {case_data['lifestyle']}")
    if case_data.get("medications"):
        report_parts.append(f"Medications: {case_data['medications']}")
    
    report_parts.append("\n--- LABORATORY & EXAMINATION ---")
    if case_data.get("colonoscopy"):
        report_parts.append(f"Colonoscopy: {case_data['colonoscopy']}")
    if case_data.get("stoolStudies"):
        report_parts.append(f"Stool Studies: {case_data['stoolStudies']}")
    if case_data.get("bloodTests"):
        report_parts.append(f"Blood Tests: {case_data['bloodTests']}")
    if case_data.get("vitals"):
        report_parts.append(f"Vitals: {case_data['vitals']}")
    if case_data.get("abdominalExam"):
        report_parts.append(f"Abdominal Exam: {case_data['abdominalExam']}")
    
    return "\n".join(report_parts)

def run_agents_for_case(case_id: str, medical_report: str):
    """Run all AI agents for a case in the background"""
    try:
        case = cases_db.get(case_id)
        if not case:
            return
        
        case["status"] = "Running"
        save_case_to_file(case_id, case)
        
        # Load API keys
        agent_api_keys = {
            "Internist": os.getenv("INTERNIST_API_KEY") or os.getenv("GOOGLE_API_KEY"),
            "Neurologist": os.getenv("NEUROLOGIST_API_KEY") or os.getenv("GOOGLE_API_KEY"),
            "Cardiologist": os.getenv("CARDIOLOGIST_API_KEY") or os.getenv("GOOGLE_API_KEY"),
            "Gastroenterologist": os.getenv("GASTROENTEROLOGIST_API_KEY") or os.getenv("GOOGLE_API_KEY"),
            "Psychiatrist": os.getenv("PSYCHIATRIST_API_KEY") or os.getenv("GOOGLE_API_KEY"),
        }
        
        # Initialize agents
        agents = {
            "Internist": Internist(medical_report, api_key=agent_api_keys["Internist"]),
            "Neurologist": Neurologist(medical_report, api_key=agent_api_keys["Neurologist"]),
            "Cardiologist": Cardiologist(medical_report, api_key=agent_api_keys["Cardiologist"]),
            "Gastroenterologist": Gastroenterologist(medical_report, api_key=agent_api_keys["Gastroenterologist"]),
            "Psychiatrist": Psychiatrist(medical_report, api_key=agent_api_keys["Psychiatrist"])
        }
        
        # Run agents concurrently
        responses = {}
        def get_response(agent_name, agent):
            try:
                print(f"[API] Starting {agent_name} agent...")
                response = agent.run()
                if response is None:
                    print(f"[API] WARNING: {agent_name} returned None - agent may have failed")
                else:
                    print(f"[API] {agent_name} completed successfully")
                return agent_name, response
            except Exception as e:
                print(f"[API] ERROR: {agent_name} failed with exception: {e}")
                import traceback
                traceback.print_exc()
                return agent_name, None
        
        with ThreadPoolExecutor() as executor:
            futures = {executor.submit(get_response, name, agent): name for name, agent in agents.items()}
            for future in as_completed(futures):
                try:
                    agent_name, response = future.result()
                    if response is None:
                        print(f"[API] WARNING: Storing None for {agent_name} - check logs above for errors")
                    responses[agent_name] = response.model_dump() if response else None
                except Exception as e:
                    print(f"[API] ERROR: Failed to get result for agent: {e}")
                    import traceback
                    traceback.print_exc()
        
        # Run multidisciplinary team
        team_api_key = os.getenv("MULTIDISCIPLINARYTEAM_API_KEY") or os.getenv("GOOGLE_API_KEY")
        team_agent = MultidisciplinaryTeam(
            medical_report=medical_report,
            internist_report=json.dumps(responses.get("Internist", {}), indent=2),
            neurologist_report=json.dumps(responses.get("Neurologist", {}), indent=2),
            cardiologist_report=json.dumps(responses.get("Cardiologist", {}), indent=2),
            gastroenterologist_report=json.dumps(responses.get("Gastroenterologist", {}), indent=2),
            psychiatrist_report=json.dumps(responses.get("Psychiatrist", {}), indent=2),
            structured_reports_json=json.dumps(responses, indent=2),
            api_key=team_api_key
        )
        
        team_summary = team_agent.run()
        team_summary_dict = team_summary.model_dump() if team_summary else None
        
        # Generate treatment plan
        treatment_options = None
        if team_summary:
            treatment_options = team_agent.generate_treatment_plan_json(team_summary)
        
        # Update case with results
        case["status"] = "Completed"
        case["agentResults"] = {
            "specialists": responses,
            "teamSummary": team_summary_dict,
            "treatmentOptions": treatment_options
        }
        case["updatedAt"] = datetime.utcnow().isoformat()
        
        save_case_to_file(case_id, case)
        
    except Exception as e:
        case = cases_db.get(case_id)
        if case:
            case["status"] = "Error"
            case["error"] = str(e)
            case["updatedAt"] = datetime.utcnow().isoformat()
            save_case_to_file(case_id, case)
        print(f"Error processing case {case_id}: {e}")

def save_case_to_file(case_id: str, case: dict):
    """Save case to JSON file"""
    file_path = os.path.join(cases_dir, f"{case_id}.json")
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(case, f, indent=2)

def load_case_from_file(case_id: str) -> Optional[dict]:
    """Load case from JSON file"""
    file_path = os.path.join(cases_dir, f"{case_id}.json")
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return None

# Load existing cases on startup
def load_existing_cases():
    """Load all cases from files"""
    if os.path.exists(cases_dir):
        for filename in os.listdir(cases_dir):
            if filename.endswith(".json"):
                case_id = filename[:-5]
                case = load_case_from_file(case_id)
                if case:
                    cases_db[case_id] = case

@app.on_event("startup")
async def startup_event():
    load_existing_cases()
    print(f"Loaded {len(cases_db)} existing cases")

# API Endpoints
@app.get("/")
async def root():
    return {"message": "MedAuraAI API", "version": "1.0.0"}

@app.post("/api/cases", response_model=CaseResponse)
async def create_case(case_data: CaseCreate, background_tasks: BackgroundTasks):
    """Create a new medical case"""
    case_id = str(uuid.uuid4())
    now = datetime.utcnow().isoformat()
    
    case = {
        "id": case_id,
        "patientId": case_data.patientId,
        "name": case_data.name,
        "age": case_data.age,
        "gender": case_data.gender,
        "chiefComplaint": case_data.chiefComplaint,
        "familyHistory": case_data.familyHistory,
        "personalHistory": case_data.personalHistory,
        "lifestyle": case_data.lifestyle,
        "medications": case_data.medications,
        "colonoscopy": case_data.colonoscopy,
        "stoolStudies": case_data.stoolStudies,
        "bloodTests": case_data.bloodTests,
        "vitals": case_data.vitals,
        "abdominalExam": case_data.abdominalExam,
        "status": "Queued",
        "createdAt": now,
        "updatedAt": now,
        "agentResults": None
    }
    
    cases_db[case_id] = case
    save_case_to_file(case_id, case)
    
    # Build medical report and run agents in background
    medical_report = build_medical_report(case)
    background_tasks.add_task(run_agents_for_case, case_id, medical_report)
    
    return CaseResponse(**case)

@app.get("/api/cases")
async def list_cases(status: Optional[str] = None):
    """List all cases, optionally filtered by status"""
    cases = list(cases_db.values())
    
    if status and status.lower() != "all":
        cases = [c for c in cases if c.get("status", "").lower() == status.lower()]
    
    # Sort by creation date (newest first)
    cases.sort(key=lambda x: x.get("createdAt", ""), reverse=True)
    
    return {"items": cases, "total": len(cases)}

@app.get("/api/cases/{case_id}", response_model=CaseResponse)
async def get_case(case_id: str):
    """Get a specific case by ID"""
    case = cases_db.get(case_id)
    if not case:
        # Try loading from file
        case = load_case_from_file(case_id)
        if case:
            cases_db[case_id] = case
        else:
            raise HTTPException(status_code=404, detail="Case not found")
    
    return CaseResponse(**case)

@app.post("/api/cases/{case_id}/rerun")
async def rerun_agents(case_id: str, background_tasks: BackgroundTasks):
    """Rerun AI agents for a case"""
    case = cases_db.get(case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    
    medical_report = build_medical_report(case)
    background_tasks.add_task(run_agents_for_case, case_id, medical_report)
    
    return {"message": "Agents rerun initiated", "case_id": case_id}

def extract_text_from_pdf(pdf_bytes: bytes) -> str:
    """Extract text from PDF bytes"""
    try:
        with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
            text_parts = []
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    text_parts.append(text)
            return "\n\n".join(text_parts)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error reading PDF: {str(e)}")

def parse_medical_report_with_ai(text: str) -> dict:
    """Use AI to extract structured data from medical report text"""
    try:
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise HTTPException(status_code=500, detail="GOOGLE_API_KEY not configured")
        
        llm = ChatGoogleGenerativeAI(
            model="gemini-pro",
            google_api_key=api_key,
            temperature=0.1
        )
        
        parser = JsonOutputParser()
        
        prompt = PromptTemplate(
            template="""You are a medical data extraction specialist. Extract structured information from the following medical report text.

Medical Report Text:
{report_text}

Extract the following fields and return as JSON. If a field is not found in the text, use an empty string or null as appropriate:
- patientId: Patient ID or medical record number
- name: Patient's full name
- age: Patient's age (as integer, or null if not found)
- gender: Patient's gender (Male/Female/Other)
- chiefComplaint: Chief complaint or presenting symptoms
- familyHistory: Family medical history
- personalHistory: Personal medical history or past medical history
- lifestyle: Lifestyle factors (smoking, alcohol, exercise, diet, etc.)
- medications: Current medications
- colonoscopy: Colonoscopy findings (if any)
- stoolStudies: Stool study results (if any)
- bloodTests: Blood test results or lab values
- vitals: Vital signs (BP, HR, BMI, temperature, etc.)
- abdominalExam: Abdominal examination findings (if any)

Return ONLY valid JSON, no additional text or explanation.

{format_instructions}""",
            input_variables=["report_text"],
            partial_variables={"format_instructions": parser.get_format_instructions()}
        )
        
        chain = prompt | llm | parser
        
        result = chain.invoke({"report_text": text})
        
        # Ensure all expected fields are present
        expected_fields = {
            "patientId": "",
            "name": "",
            "age": None,
            "gender": "",
            "chiefComplaint": "",
            "familyHistory": "",
            "personalHistory": "",
            "lifestyle": "",
            "medications": "",
            "colonoscopy": "",
            "stoolStudies": "",
            "bloodTests": "",
            "vitals": "",
            "abdominalExam": ""
        }
        
        # Merge extracted data with defaults
        extracted = {**expected_fields, **result}
        
        # Convert age to int if it's a string number
        if isinstance(extracted.get("age"), str) and extracted["age"].isdigit():
            extracted["age"] = int(extracted["age"])
        elif extracted.get("age") == "":
            extracted["age"] = None
        
        return extracted
        
    except Exception as e:
        print(f"Error parsing with AI: {e}")
        # Fallback: try simple text parsing
        return parse_medical_report_simple(text)

def parse_medical_report_simple(text: str) -> dict:
    """Simple rule-based parsing as fallback"""
    result = {
        "patientId": "",
        "name": "",
        "age": None,
        "gender": "",
        "chiefComplaint": "",
        "familyHistory": "",
        "personalHistory": "",
        "lifestyle": "",
        "medications": "",
        "colonoscopy": "",
        "stoolStudies": "",
        "bloodTests": "",
        "vitals": "",
        "abdominalExam": ""
    }
    
    lines = text.split('\n')
    text_lower = text.lower()
    
    # Extract patient ID
    for line in lines:
        if 'patient id' in line.lower() or 'patientid' in line.lower():
            parts = line.split(':')
            if len(parts) > 1:
                result["patientId"] = parts[1].strip()
    
    # Extract name
    for line in lines:
        if line.lower().startswith('name:'):
            result["name"] = line.split(':', 1)[1].strip()
    
    # Extract age
    for line in lines:
        if line.lower().startswith('age:'):
            age_str = line.split(':', 1)[1].strip()
            try:
                result["age"] = int(age_str)
            except:
                pass
    
    # Extract gender
    for line in lines:
        if line.lower().startswith('gender:'):
            result["gender"] = line.split(':', 1)[1].strip()
    
    # Extract chief complaint
    if 'chief complaint' in text_lower:
        start_idx = text_lower.find('chief complaint')
        end_idx = text_lower.find('medical history', start_idx)
        if end_idx == -1:
            end_idx = text_lower.find('recent lab', start_idx)
        if end_idx == -1:
            end_idx = len(text)
        complaint_text = text[start_idx:end_idx].split(':', 1)
        if len(complaint_text) > 1:
            result["chiefComplaint"] = complaint_text[1].strip()
    
    # Extract family history
    if 'family history' in text_lower:
        start_idx = text_lower.find('family history')
        end_idx = text_lower.find('personal', start_idx)
        if end_idx == -1:
            end_idx = text_lower.find('lifestyle', start_idx)
        if end_idx == -1:
            end_idx = len(text)
        history_text = text[start_idx:end_idx].split(':', 1)
        if len(history_text) > 1:
            result["familyHistory"] = history_text[1].strip()
    
    # Extract personal history
    if 'personal' in text_lower and 'history' in text_lower:
        start_idx = text_lower.find('personal')
        end_idx = text_lower.find('lifestyle', start_idx)
        if end_idx == -1:
            end_idx = text_lower.find('medications', start_idx)
        if end_idx == -1:
            end_idx = len(text)
        history_text = text[start_idx:end_idx].split(':', 1)
        if len(history_text) > 1:
            result["personalHistory"] = history_text[1].strip()
    
    # Extract lifestyle
    if 'lifestyle' in text_lower:
        start_idx = text_lower.find('lifestyle')
        end_idx = text_lower.find('medications', start_idx)
        if end_idx == -1:
            end_idx = len(text)
        lifestyle_text = text[start_idx:end_idx].split(':', 1)
        if len(lifestyle_text) > 1:
            result["lifestyle"] = lifestyle_text[1].strip()
    
    # Extract medications
    if 'medications' in text_lower or 'medication' in text_lower:
        start_idx = text_lower.find('medication')
        end_idx = text_lower.find('recent lab', start_idx)
        if end_idx == -1:
            end_idx = text_lower.find('physical examination', start_idx)
        if end_idx == -1:
            end_idx = len(text)
        med_text = text[start_idx:end_idx].split(':', 1)
        if len(med_text) > 1:
            result["medications"] = med_text[1].strip()
    
    # Extract colonoscopy
    if 'colonoscopy' in text_lower:
        for line in lines:
            if 'colonoscopy' in line.lower():
                parts = line.split(':', 1)
                if len(parts) > 1:
                    result["colonoscopy"] = parts[1].strip()
    
    # Extract stool studies
    if 'stool' in text_lower:
        for line in lines:
            if 'stool' in line.lower():
                parts = line.split(':', 1)
                if len(parts) > 1:
                    result["stoolStudies"] = parts[1].strip()
    
    # Extract blood tests
    if 'blood' in text_lower or 'lab' in text_lower:
        start_idx = text_lower.find('blood') if 'blood' in text_lower else text_lower.find('lab')
        end_idx = text_lower.find('physical examination', start_idx)
        if end_idx == -1:
            end_idx = len(text)
        lab_section = text[start_idx:end_idx]
        result["bloodTests"] = lab_section.strip()
    
    # Extract vitals
    if 'vital' in text_lower:
        for line in lines:
            if 'vital' in line.lower():
                parts = line.split(':', 1)
                if len(parts) > 1:
                    result["vitals"] = parts[1].strip()
    
    # Extract abdominal exam
    if 'abdominal' in text_lower:
        for line in lines:
            if 'abdominal' in line.lower():
                parts = line.split(':', 1)
                if len(parts) > 1:
                    result["abdominalExam"] = parts[1].strip()
    
    return result

@app.post("/api/cases/parse-report")
async def parse_report(file: UploadFile = File(...)):
    """Parse PDF report and extract structured data using AI"""
    if not file.filename or not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")
    
    try:
        # Read PDF file
        pdf_bytes = await file.read()
        
        if len(pdf_bytes) == 0:
            raise HTTPException(status_code=400, detail="PDF file is empty")
        
        # Extract text from PDF
        report_text = extract_text_from_pdf(pdf_bytes)
        
        if not report_text or len(report_text.strip()) < 50:
            raise HTTPException(
                status_code=400, 
                detail="Could not extract sufficient text from PDF. The PDF may be scanned or corrupted."
            )
        
        # Parse with AI
        extracted_data = parse_medical_report_with_ai(report_text)
        
        return extracted_data
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error parsing PDF: {e}")
        raise HTTPException(
            status_code=500, 
            detail=f"Error processing PDF: {str(e)}"
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

