from fastapi import FastAPI, UploadFile, File, Depends
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
import shutil
import os
import asyncio

from database import Base, engine, SessionLocal
from models import DatasetLog
from qc_engine import analyze_dataset, detect_dataset_issues, generate_recommendations, process_user_approval

# Create database tables automatically
Base.metadata.create_all(bind=engine)

app = FastAPI()

# Enable CORS so frontend UI can send requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
# Upload and process endpoint
@app.post("/upload")
async def upload_file(file: UploadFile = File(...), db: Session = Depends(get_db)):
    os.makedirs("uploads", exist_ok=True)
    file_location = f"uploads/{file.filename}"
    
    # Save file asynchronously
    with open(file_location, "wb") as f:
        shutil.copyfileobj(file.file, f)
        
    # Run CPU-bound analysis in background thread pool to prevent blocking
    qc_results = await asyncio.to_thread(analyze_dataset, file_location)
    
    # Save results to database
    log = DatasetLog(
        filename=file.filename,
        total_rows=qc_results["total_rows"],
        missing_count=qc_results["missing_count"],
        duplicate_count=qc_results["duplicate_count"],
        quality_score=qc_results["quality_score"],
        status=qc_results["status"]
    )
    db.add(log)
    db.commit()
    
    return {"message": "Processing successful", "data": qc_results}
# Get reports endpoint for dashboard UI
@app.get("/reports")
def get_reports(db: Session = Depends(get_db)):
    return db.query(DatasetLog).all()

@app.post("/detect-issues")
def detect_issues(file: UploadFile = File(...)):
    os.makedirs("uploads", exist_ok=True)
    file_location = f"uploads/{file.filename}"
    
    # Save uploaded file locally
    with open(file_location, "wb") as f:
        shutil.copyfileobj(file.file, f)
        
    # Analyze issues and return JSON to frontend
    issue_report = detect_dataset_issues(file_location)
    return {"message": "Issue detection complete", "data": issue_report}

@app.post("/explain-recommend")
def explain_recommend(file: UploadFile = File(...)):
    os.makedirs("uploads", exist_ok=True)
    file_location = f"uploads/{file.filename}"
    
    with open(file_location, "wb") as f:
        shutil.copyfileobj(file.file, f)
        
    report = generate_recommendations(file_location)
    return {"message": "Explanation and recommendations generated", "data": report}

@app.post("/approve-actions")
def approve_actions(filename: str, action: str = "approve", fill_strategy: str = "drop"):
    file_location = f"uploads/{filename}"
    if not os.path.exists(file_location):
        return {"error": "File not found"}
        
    result = process_user_approval(file_location, action, fill_strategy)
    return {"message": "Approval processed successfully", "data": result}

@app.get("/download-cleaned")
def download_cleaned_file(filename: str):
    file_location = f"uploads/{filename}"
    if not os.path.exists(file_location):
        return {"error": "Cleaned file not found"}
        
    return FileResponse(
        path=file_location,
        filename=filename,
        media_type="text/csv"
    )
    
@app.get("/")
def read_root():
    return {"message": "DataQC Backend API is live!"}