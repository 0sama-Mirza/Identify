import os
from app.utils.file_utils import create_symbolic_link, save_image_to_event_folder
from app.db.dbhelper import get_db_connection
from datetime import datetime
UPLOADS_FOLDER = "uploads"


def add_images_to_event_db(event_id, images):
    """
    Saves uploaded images to the 'original_images' folder and adds their records to the event_images table.

    Args:
        event_id (int): The ID of the event to associate the images with.
        images (list of FileStorage): A list of uploaded images.

    Returns:
        dict: A success or error response, with a 'status_code' key.
    """
    print(f"\n=== Debug: Received images for event ID {event_id}: {images} ===\n")

    if not images or len(images) == 0:
        print(f"No images to add for event ID {event_id}")
        return {"success": True, "message": "No images provided", "status_code": 200}

    print(f"Processing {len(images)} images for event ID: {event_id}")

    saved_image_paths = []  # Collect paths of successfully saved images

    # Step 1: Save images to the file system
    for image in images:
        try:
            print(f"Saving image: {image.filename} for event ID {event_id}")
            save_response = save_image_to_event_folder(event_id, image)
            if "error" in save_response:
                print(f"Error saving image: {save_response['error']}")
                return {"error": f"Failed to save image: {save_response['error']}", "status_code": 500}
            saved_image_paths.append(save_response.get("file_path"))
            print(f"Image successfully saved: {save_response.get('file_path')}")
        except Exception as e:
            print(f"Unexpected error while saving image '{image.filename}': {e}")
            return {"error": f"Failed to save image: {str(e)}", "status_code": 500}

    print("\n=== Debug: All images successfully saved ===\n")
    print(f"Saved image paths: {saved_image_paths}")

    # Step 2: Add image paths to the database
    try:
        uploaded_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')  # Current timestamp

        with get_db_connection() as conn:
            cur = conn.cursor()
            image_query = '''
            INSERT INTO event_images (event_id, image_path, uploaded_at)
            VALUES (?, ?, ?);
            '''
            for file_path in saved_image_paths:
                try:
                    cur.execute(image_query, (event_id, file_path, uploaded_at))
                    print(f"Image record added to database: {file_path}")
                except Exception as e:
                    print(f"Error adding image record for path '{file_path}' to database: {e}")
                    return {"error": f"Failed to add image '{file_path}' to database: {str(e)}", "status_code": 500}

            conn.commit()  # Commit the transaction
            print(f"All image records for event ID {event_id} added successfully.")

        return {"success": True, "message": "All images saved and database updated successfully", "status_code": 201}

    except Exception as e:
        print(f"Unexpected database error for event ID {event_id}: {e}")
        return {"error": f"Database error: {str(e)}", "status_code": 500}




def link_image_to_album(event_id, album_id, filename):
    """
    Creates a symbolic link for an image in an album.
    """
    try:
        # Determine the paths for the original image and the album link
        original_image_folder = os.path.join(UPLOADS_FOLDER, f"event_{event_id}", "original_images")
        album_folder = os.path.join(UPLOADS_FOLDER, f"event_{event_id}", "albums", str(album_id))
        
        original_image_path = os.path.join(original_image_folder, filename)
        album_image_path = os.path.join(album_folder, filename)

        # Create the symbolic link
        create_symbolic_link(original_image_path, album_image_path)
        return {"success": True, "message": f"Image linked to album {album_id}"}, 200
    except Exception as e:
        return {"error": str(e)}, 500


def delete_image(event_id, filename):
    """
    Deletes an image from the 'original_images' folder and removes associated symbolic links.
    """
    try:
        # Delete the original image
        original_image_path = os.path.join(UPLOADS_FOLDER, f"event_{event_id}", "original_images", filename)
        if os.path.exists(original_image_path):
            os.remove(original_image_path)

        # Remove any symbolic links pointing to this image
        album_folder = os.path.join(UPLOADS_FOLDER, f"event_{event_id}", "albums")
        for root, dirs, files in os.walk(album_folder):
            if filename in files:
                symbolic_link_path = os.path.join(root, filename)
                os.unlink(symbolic_link_path)

        return {"success": True, "message": f"Image '{filename}' deleted successfully"}, 200
    except Exception as e:
        return {"error": str(e)}, 500
