import os
import shutil
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
from typing import List
from retinaface_worker import process_images  # Import your face recognition logic

# --- Configuration ---
UPLOAD_DIRECTORY = "received_images"
OUTPUT_DIRECTORY = "output_faces"
os.makedirs(UPLOAD_DIRECTORY, exist_ok=True)
os.makedirs(OUTPUT_DIRECTORY, exist_ok=True)

# --- Initialize FastAPI app ---
app = FastAPI(title="Image Upload API")

# --- Global Status ---
app.state.status = "idle"  # "idle" or "processing"

@app.get("/status", tags=["Status"])
async def get_status():
    """
    Returns the current processing status of the API.
    """
    return {"status": app.state.status}

@app.post("/upload-images/", tags=["Image Upload"])
async def upload_multiple_images(images: List[UploadFile] = File(..., description="Select multiple image files to upload")):
    """
    Endpoint to receive and save multiple image files.
    Then triggers the facial recognition process.
    """
    if app.state.status == "processing":
        raise HTTPException(status_code=429, detail="Server is busy processing. Try again later.")

    app.state.status = "processing"
    try:
        if not images:
            raise HTTPException(status_code=400, detail="No files were sent.")

        saved_files = []
        errors = []

        for image in images:
            if not image.filename:
                errors.append({"filename": None, "error": "No filename found."})
                continue

            filename = os.path.basename(image.filename)
            file_path = os.path.join(UPLOAD_DIRECTORY, filename)

            base, extension = os.path.splitext(filename)
            counter = 1
            while os.path.exists(file_path):
                file_path = os.path.join(UPLOAD_DIRECTORY, f"{base}_{counter}{extension}")
                counter += 1

            try:
                with open(file_path, "wb") as f:
                    shutil.copyfileobj(image.file, f)
                saved_files.append(os.path.basename(file_path))
                print(f"Saved: {file_path}")
            except Exception as e:
                print(f"Error saving {filename}: {e}")
                errors.append({"filename": filename, "error": str(e)})
            finally:
                await image.close()

        if not saved_files:
            raise HTTPException(status_code=400, detail="No files saved. Check errors.")

        # --- Run facial recognition ---
        try:
            process_images(UPLOAD_DIRECTORY, OUTPUT_DIRECTORY)
            print("Facial recognition completed.")
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Processing failed: {e}")

        return JSONResponse(
            status_code=200,
            content={
                "message": f"Uploaded and processed {len(saved_files)} files.",
                "saved_filenames": saved_files,
                "upload_errors": errors if errors else "None"
            }
        )

    finally:
        app.state.status = "idle"

@app.get("/", tags=["Status"])
async def read_root():
    return {"status": "Image Upload API is running"}
