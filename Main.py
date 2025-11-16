# Importing the needed modules 
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor, as_completed
from Utils.Agents import (
    Internist,
    Neurologist,
    Cardiologist,
    Gastroenterologist,
    Psychiatrist,
    MultidisciplinaryTeam,
    TeamSummary,
)
import json, os, re
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

# Loading API key from a dotenv file.
load_dotenv(dotenv_path='apikey.env')

# Available reports:
# - "Medical Report - Anna Thompson - Irritable Bowel Syndrome.txt"
# - "Medical Report - Charles Baker - Prostate Cancer (Suspicion).txt"
# - "Medical Report - James Carter - Insomnia.txt"
# - "Medical Report - Kevin Adams - Diabetic Neuropathy.txt"
# - "Medical Report - Laura Garcia - Rheumatoid Arthritis.txt"
# - "Medical Report - Maria Silva - Polycystic Ovary Syndrome.txt"
# - "Medical Report - Olivia White - Recurrent Tonsillitis.txt"
# - "Medical Report - Robert Miller - COPD.txt"
# - "Medical Rerort - Michael Johnson - Panic Attack Disorder.txt"
MEDICAL_REPORT_FILE = "Medical Report - Charles Baker - Prostate Cancer (Suspicion).txt"

# Read the medical report
with open(os.path.join("Medical Reports", MEDICAL_REPORT_FILE), "r", encoding="utf-8") as file:
    medical_report = file.read()

# Load API keys for each agent from environment variables
# Format: INTERNIST_API_KEY, NEUROLOGIST_API_KEY, etc.
# Falls back to GOOGLE_API_KEY if agent-specific key not found
agent_api_keys = {
    "Internist": os.getenv("INTERNIST_API_KEY") or os.getenv("GOOGLE_API_KEY"),
    "Neurologist": os.getenv("NEUROLOGIST_API_KEY") or os.getenv("GOOGLE_API_KEY"),
    "Cardiologist": os.getenv("CARDIOLOGIST_API_KEY") or os.getenv("GOOGLE_API_KEY"),
    "Gastroenterologist": os.getenv("GASTROENTEROLOGIST_API_KEY") or os.getenv("GOOGLE_API_KEY"),
    "Psychiatrist": os.getenv("PSYCHIATRIST_API_KEY") or os.getenv("GOOGLE_API_KEY"),
}

agents = {
    "Internist": Internist(medical_report, api_key=agent_api_keys["Internist"]),
    "Neurologist": Neurologist(medical_report, api_key=agent_api_keys["Neurologist"]),
    "Cardiologist": Cardiologist(medical_report, api_key=agent_api_keys["Cardiologist"]),
    "Gastroenterologist": Gastroenterologist(medical_report, api_key=agent_api_keys["Gastroenterologist"]),
    "Psychiatrist": Psychiatrist(medical_report, api_key=agent_api_keys["Psychiatrist"])
}

# Function to run each agent and get their response
def get_response(agent_name, agent):
    response = agent.run()
    return agent_name, response

# Run the agents concurrently and collect responses
responses = {}
with ThreadPoolExecutor() as executor:
    futures = {executor.submit(get_response, name, agent): name for name, agent in agents.items()}
    
    for future in as_completed(futures):
        agent_name, response = future.result()
        responses[agent_name] = response

# Validate specialist outputs
missing_specialists = [name for name, result in responses.items() if result is None]
if missing_specialists:
    raise RuntimeError(f"Failed to obtain structured output from: {', '.join(missing_specialists)}")

# Prepare JSON payloads for the multidisciplinary agent
structured_reports_json = json.dumps({k: v.model_dump() for k, v in responses.items()}, indent=2)

# Load API key for MultidisciplinaryTeam (falls back to GOOGLE_API_KEY if not specified)
team_api_key = os.getenv("MULTIDISCIPLINARYTEAM_API_KEY") or os.getenv("GOOGLE_API_KEY")

team_agent = MultidisciplinaryTeam(
    medical_report=medical_report,
    internist_report=responses["Internist"].model_dump_json(indent=2),
    neurologist_report=responses["Neurologist"].model_dump_json(indent=2),
    cardiologist_report=responses["Cardiologist"].model_dump_json(indent=2),
    gastroenterologist_report=responses["Gastroenterologist"].model_dump_json(indent=2),
    psychiatrist_report=responses["Psychiatrist"].model_dump_json(indent=2),
    structured_reports_json=structured_reports_json,
    api_key=team_api_key
)

# Run the MultidisciplinaryTeam agent to generate the final diagnosis
team_summary = team_agent.run()
if team_summary is None:
    raise RuntimeError("Multidisciplinary team failed to produce a structured summary.")
json_output_path = "results/final_diagnosis.json"

# Ensure the directory exists
os.makedirs(os.path.dirname(json_output_path), exist_ok=True)

# Write the structured summary to disk
with open(json_output_path, "w", encoding="utf-8") as json_file:
    json_file.write(team_summary.model_dump_json(indent=2))

# Ensure subdirectories exist for detailed outputs
treatments_dir = os.path.join("results", "treatment")
os.makedirs(treatments_dir, exist_ok=True)

# Generate treatment recommendations (each option saved separately)
def render_treatment_text(option):
    if not option:
        return "Treatment recommendation unavailable."
    lines = []
    lines.append("💊 Treatment Options")
    lines.append("")
    lines.append(f"Option {option.get('option_number', '?')}({option.get('match_percentage', 0)}% match)")
    lines.append(option.get("primary_name", ""))
    lines.append(option.get("overview", ""))
    lines.append("Therapy Modality Label")
    lines.append(option.get("modality", ""))
    lines.append("Success_Rate_1%")
    lines.append(f"{option.get('success_rate', 0)}% Success Rate")
    lines.append("⏱ Duration")
    lines.append(option.get("duration", ""))
    lines.append("🏥 Recovery Time")
    lines.append(option.get("recovery_time", ""))
    lines.append("💰 Cost Estimate")
    lines.append(option.get("cost_estimate", ""))
    lines.append("⚠")
    lines.append("Potential Side Effects")
    for se in option.get("side_effects", [])[:10]:
        lines.append(f"• {se}")
    lines.append("✅")
    lines.append("Recommended For")
    for rec in option.get("recommended_for", [])[:10]:
        lines.append(f"✓ {rec}")
    lines.append("📋")
    lines.append("Procedure Steps")
    for idx, step in enumerate(option.get("procedure_steps", [])[:5], start=1):
        lines.append(str(idx))
        lines.append(step)
    lines.append("💡")
    lines.append("Personalized Notes")
    for note in option.get("notes", [])[:10]:
        lines.append(f"• {note}")
    return "\n".join(lines).strip()

# Also generate structured treatment JSON and save per-option
treatment_options_json = team_agent.generate_treatment_plan_json(team_summary)
if treatment_options_json and isinstance(treatment_options_json, list):
    for idx, option in enumerate(treatment_options_json[:3], start=1):
        json_path = os.path.join(treatments_dir, f"treatment{idx}.json")
        with open(json_path, "w", encoding="utf-8") as jf:
            jf.write(json.dumps(option, indent=2))

print(f"Structured team summary saved to {json_output_path}")
print("Structured treatment options saved to results/treatment/treatment1.json, treatment2.json, treatment3.json")