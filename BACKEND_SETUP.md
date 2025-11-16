# Backend API Server Setup

## Quick Start

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Set up API keys:**
   - Make sure your `apikey.env` file has the required API keys:
     ```
     GOOGLE_API_KEY=your_key_here
     # Optional: Agent-specific keys
     INTERNIST_API_KEY=your_key_here
     NEUROLOGIST_API_KEY=your_key_here
     # ... etc
     ```

3. **Run the server:**
   ```bash
   python api_server.py
   ```
   
   Or using uvicorn directly:
   ```bash
   uvicorn api_server:app --reload --host 0.0.0.0 --port 8000
   ```

4. **API will be available at:**
   - http://localhost:8000
   - API docs: http://localhost:8000/docs (Swagger UI)
   - Alternative docs: http://localhost:8000/redoc

## API Endpoints

- `POST /api/cases` - Create a new case
- `GET /api/cases` - List all cases (supports ?status= filter)
- `GET /api/cases/{case_id}` - Get case details
- `POST /api/cases/{case_id}/rerun` - Rerun AI agents
- `POST /api/cases/parse-report` - Parse PDF report (placeholder)

## Notes

- Cases are stored in `cases_data/` directory as JSON files
- AI agents run in the background when a case is created
- Case status: Queued → Running → Completed (or Error)

