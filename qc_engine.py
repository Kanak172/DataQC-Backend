import pandas as pd
import os

def analyze_dataset(file_path: str):
    df = pd.read_csv(file_path)
    
    total_rows = len(df)
    missing_count = int(df.isnull().sum().sum())
    duplicate_count = int(df.duplicated().sum())
    
    total_cells = df.size
    quality_score = max(0, round(((total_cells - missing_count) / total_cells) * 100, 2)) if total_cells > 0 else 0
    
    return {
        "total_rows": total_rows,
        "missing_count": missing_count,
        "duplicate_count": duplicate_count,
        "quality_score": quality_score,
        "status": "Passed" if quality_score >= 80 else "Failed"
    }

def detect_dataset_issues(file_path: str):
    df = pd.read_csv(file_path)
    
    missing_by_column = {col: int(count) for col, count in df.isnull().sum().to_dict().items()}
    duplicate_rows = [int(i) for i in df[df.duplicated()].index.tolist()]
    data_types = {str(col): str(dtype) for col, dtype in df.dtypes.items()}
    
    total_missing = sum(missing_by_column.values())
    has_issues = bool(total_missing > 0 or len(duplicate_rows) > 0)
    
    return {
        "filename": os.path.basename(file_path),
        "total_columns": int(len(df.columns)),
        "columns": [str(col) for col in df.columns],
        "data_types": data_types,
        "missing_by_column": missing_by_column,
        "duplicate_row_indices": duplicate_rows,
        "has_issues": has_issues
    }

def generate_recommendations(file_path: str):
    df = pd.read_csv(file_path)
    duplicate_count = int(df.duplicated().sum())
    missing_cols = df.columns[df.isnull().any()].tolist()
    
    recs = []
    if duplicate_count > 0:
        recs.append(f"Found {duplicate_count} duplicate rows. Recommendation: Drop duplicates to prevent model bias.")
    
    if missing_cols:
        recs.append(f"Columns with missing values: {', '.join(missing_cols)}. Recommendation: Impute with median/mode or drop affected rows if missing data is minimal.")
        
    if not recs:
        recs.append("Dataset is clean and healthy! No critical data quality issues found.")
        
    return {
        "filename": os.path.basename(file_path),
        "overall_health": "Needs Attention" if recs and "Recommendation" in recs[0] else "Healthy",
        "recommendations": recs
    }

def process_user_approval(file_path: str, action: str, fill_strategy: str = "drop"):
    df = pd.read_csv(file_path)
    initial_rows = int(len(df))
    
    if action == "approve":
        df = df.drop_duplicates()
        
        if fill_strategy == "drop":
            df = df.dropna()
        elif fill_strategy == "fill_mean":
            numeric_cols = df.select_dtypes(include=['number']).columns
            df[numeric_cols] = df[numeric_cols].fillna(df[numeric_cols].mean())
            
        cleaned_file_path = f"uploads/cleaned_{os.path.basename(file_path)}"
        df.to_csv(cleaned_file_path, index=False)
        
        return {
            "status": "Approved",
            "action_taken": "Dataset cleaned based on approved rules",
            "rows_before": initial_rows,
            "rows_after": int(len(df)),
            "cleaned_file": os.path.basename(cleaned_file_path)
        }
    else:
        return {
            "status": "Rejected",
            "action_taken": "No changes applied to dataset",
            "rows_before": initial_rows,
            "rows_after": initial_rows,
            "cleaned_file": None
        }