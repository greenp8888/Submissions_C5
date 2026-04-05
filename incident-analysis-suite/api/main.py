from fastapi import Depends, FastAPI, File, Header, HTTPException, UploadFile

from incident_suite.models.schemas import AnalyzeIncidentRequest, AnalyzeIncidentResponse
from incident_suite.service import analyze_incident
from incident_suite.utils.settings import get_settings

app = FastAPI(title="Incident Analysis Suite")


def enforce_auth(authorization: str | None = Header(default=None)) -> None:
    settings = get_settings()
    if settings.auth_mode.lower() != "api_key" or not settings.incident_api_key:
        return
    expected = f"Bearer {settings.incident_api_key}"
    if authorization != expected:
        raise HTTPException(status_code=401, detail="Invalid or missing API key.")


@app.get("/health")
def healthcheck() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/incidents/analyze", response_model=AnalyzeIncidentResponse)
async def analyze_incident_route(
    payload: AnalyzeIncidentRequest,
    _: None = Depends(enforce_auth),
) -> AnalyzeIncidentResponse:
    return analyze_incident(payload)


@app.post("/incidents/analyze-file", response_model=AnalyzeIncidentResponse)
async def analyze_incident_file(
    file: UploadFile = File(...),
    _: None = Depends(enforce_auth),
) -> AnalyzeIncidentResponse:
    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")
    return analyze_incident(AnalyzeIncidentRequest(raw_logs=content.decode("utf-8", errors="ignore"), source=file.filename or "upload"))
