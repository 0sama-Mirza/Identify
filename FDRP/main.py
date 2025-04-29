import os
import shutil
from fastapi import FastAPI, File, UploadFile, HTTPException, Form
from fastapi.responses import JSONResponse
from typing import List
from db_helper import insert_event_into_deepface_jobs

# --- Configuration ---
UPLOAD_DIRECTORY = "received_images"
OUTPUT_DIRECTORY = "output_faces"
os.makedirs(UPLOAD_DIRECTORY, exist_ok=True)
os.makedirs(OUTPUT_DIRECTORY, exist_ok=True)

# --- Initialize FastAPI app ---
app = FastAPI(title="Image Upload API")

# --- Global Status ---
app.state.status = "idle"  # Can be "idle" or "processing"

@app.get("/", tags=["Status"])
async def read_root():
    return {"status": "Image Upload API is running"}


@app.get("/status", tags=["Status"])
async def get_status():
    """
    Returns the current processing status of the API.
    """
    return {"status": app.state.status}


@app.post("/upload-images/", tags=["Image Upload"])
async def upload_multiple_images(
    event_id: int = Form(..., description="Event ID this image belongs to"),
    images: List[UploadFile] = File(..., description="Select multiple image files to upload")
):
    if app.state.status == "processing":
        raise HTTPException(status_code=429, detail="Server is busy processing. Try again later.")

    app.state.status = "processing"
    try:
        if not images:
            raise HTTPException(status_code=400, detail="No files were sent.")

        print(f"📥 Received {len(images)} image(s) for event ID: {event_id}")
        saved_files = []
        errors = []

        # Create event-specific subdirectory
        event_folder = os.path.join(UPLOAD_DIRECTORY, f"event_{event_id}")
        os.makedirs(event_folder, exist_ok=True)

        for image in images:
            if not image.filename:
                errors.append({"filename": None, "error": "No filename found."})
                continue

            filename = os.path.basename(image.filename)
            file_path = os.path.join(event_folder, filename)

            # Prevent overwriting if filename already exists
            base, extension = os.path.splitext(filename)
            counter = 1
            while os.path.exists(file_path):
                file_path = os.path.join(event_folder, f"{base}_{counter}{extension}")
                counter += 1

            try:
                with open(file_path, "wb") as f:
                    shutil.copyfileobj(image.file, f)
                saved_files.append(os.path.basename(file_path))
                insert_event_into_deepface_jobs(event_id)
                print(f"✅ Saved: {file_path}")
            except Exception as e:
                print(f"❌ Error saving {filename}: {e}")
                errors.append({"filename": filename, "error": str(e)})
            finally:
                await image.close()

        if not saved_files:
            raise HTTPException(status_code=400, detail="No files saved. Check errors.")

        return JSONResponse(
            status_code=200,
            content={
                "message": f"Uploaded {len(saved_files)} file(s) for event ID {event_id}.",
                "event_id": event_id,
                "saved_filenames": saved_files,
                "upload_errors": errors if errors else "None"
            }
        )

    finally:
        app.state.status = "idle"
