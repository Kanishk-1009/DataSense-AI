from io import BytesIO

import pandas as pd
from fastapi import FastAPI, File, HTTPException, UploadFile

from backend.core.profiler import profile_dataset
from backend.core.validator import validate_csv


app = FastAPI(
    title="Smart Dataset Understanding Agent",
    version="0.1.0"
)


@app.get("/")
def root():
    return {
        "message": "Smart Dataset Understanding Agent API",
        "status": "running"
    }


@app.get("/health")
def health():
    return {
        "status": "healthy"
    }


@app.post("/upload")
async def upload_dataset(file: UploadFile = File(...)):

    validate_csv(file)

    try:
        contents = await file.read()

        if not contents:
            raise HTTPException(
                status_code=400,
                detail="Uploaded CSV is empty."
            )

        df = pd.read_csv(BytesIO(contents))

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Unable to read CSV: {str(e)}"
        )

    if df.empty:
        raise HTTPException(
            status_code=400,
            detail="Dataset contains no rows."
        )

    return profile_dataset(df)