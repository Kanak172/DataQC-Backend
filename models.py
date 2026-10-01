from sqlalchemy import Column, Integer, String, Float, DateTime
from database import Base
import datetime

class DatasetLog(Base):
    __tablename__ = "dataset_logs"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, index=True)
    upload_date = Column(DateTime, default=datetime.datetime.utcnow)
    total_rows = Column(Integer)
    missing_count = Column(Integer)
    duplicate_count = Column(Integer)
    quality_score = Column(Float)
    status = Column(String)  # e.g., "Passed" or "Failed"