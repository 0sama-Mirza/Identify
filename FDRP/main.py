import os
import shutil
from fastapi import FastAPI, File, UploadFile, HTTPException, Form
from fastapi.responses import JSONResponse
from typing import List
from fastapi.middleware.cors import CORSMiddleware
from healpers.db_helper import insert_event_into_deepface_jobs, update_event_status, init_deepface_jobs_table
from match_face import find_best_match
import base64

# --- Configuration ---
UPLOAD_DIRECTORY = "received_images"
OUTPUT_DIRECTORY = "user_data"
os.makedirs(UPLOAD_DIRECTORY, exist_ok=True)
os.makedirs(OUTPUT_DIRECTORY, exist_ok=True)
init_deepface_jobs_table()
# --- Initialize FastAPI app ---
app = FastAPI(title="Image Upload API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5000", "http://127.0.0.1:5000"],  # Match this with your Flask frontend origin
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
        update_event_status(event_id, "unsorted")


@app.post("/match-face/")
async def match_face_endpoint(
    file: UploadFile,
    user_id: int = Form(...),
    event_id: int = Form(...)
):
    # Step 1: Create user directory
    user_folder = f"user_data/{user_id}"
    # --- Step 1: Create or Clear User Directory ---
    try:
        os.makedirs(user_folder, exist_ok=True)  # Create if it doesn't exist

        # Clear existing files and directories
        for item in os.listdir(user_folder):
            item_path = os.path.join(user_folder, item)
            if os.path.isfile(item_path) or os.path.islink(item_path):
                os.remove(item_path)  # Remove files and symbolic links
            elif os.path.isdir(item_path):
                shutil.rmtree(item_path)  # Remove directories and their contents
        print(f"Successfully cleared contents of: {user_folder}")  # Debugging
    except Exception as e:
        print(f"Error during directory cleanup: {e}")
        traceback.print_exc()  # Log the full traceback
        return JSONResponse(
            status_code=500, content={"error": f"Error clearing user directory: {e}"}
        )

    # Step 2: Save the uploaded image with a custom name: u-ID<user_id>-selfie.jpg
    image_filename = f"u-ID{user_id}-selfie.jpg"
    image_path = os.path.join(user_folder, image_filename)
    with open(image_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Step 3: Run matching
    try:
        cluster_id, best_match_filename, similarity = find_best_match(user_id, event_id)
        if cluster_id is None:
            raise ValueError("No matching cluster found.")
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JSONResponse(status_code=500, content={"error": str(e)})


    # Step 4: Read and encode the matched image
    matched_image_path = f"Cropped_Events/event_{event_id}/Cropped_Faces_Align/{best_match_filename}"
    try:
        with open(matched_image_path, "rb") as image_file:
            encoded_image = base64.b64encode(image_file.read()).decode("utf-8")
    except FileNotFoundError:
        return JSONResponse(status_code=404, content={"error": "Matched image file not found."})


    # Step 5: Return result with Base64 image
    return {
        "matched_cluster": int(cluster_id),
        "matched_image": best_match_filename,
        "similarity_score": round(float(similarity), 4),
        "image_base64": encoded_image  # <-- base64 string here
    }