import os
from app.utils.helpers import allowed_file
from werkzeug.utils import secure_filename
from flask import current_app
import shutil
UPLOADS_FOLDER = "uploads"  # Root uploads folder


def create_event_folder(event_id):
    """
    Creates the folder structure for a new event:
    - uploads/event_{event_id}/original_images/
    - uploads/event_{event_id}/albums/
    - uploads/event_{event_id}/albums/all_photos/
    """
    event_folder = os.path.join(UPLOADS_FOLDER, f"event_{event_id}")
    original_images_folder = os.path.join(event_folder, "original_images")
    albums_folder = os.path.join(event_folder, "albums")
    all_photos_folder = os.path.join(albums_folder, "all_photos")

    # Create the necessary directories
    os.makedirs(original_images_folder, exist_ok=True)
    os.makedirs(albums_folder, exist_ok=True)  # Create the empty albums folder
    os.makedirs(all_photos_folder, exist_ok=True)  # Create the all_photos folder within albums
    print(f"Created folder structure for event_{event_id}")

    return {
        "event_folder": event_folder,
        "original_images_folder": original_images_folder,
        "albums_folder": albums_folder,
        "all_photos_folder": all_photos_folder,
    }


def save_image_to_event_folder(event_id, image):
    """
    Saves the uploaded image to the 'original_images' folder for the specified event.

    Args:
        event_id (int): The ID of the event to associate the image with.
        image (FileStorage): The uploaded image from the user.

    Returns:
        dict: A response containing the file path, status, or an error message.
    """
    print(f"Processing image: {image.filename}")  # Debugging: File being processed

    if not image or not allowed_file(image.filename):
        print(f"Invalid file or type: {image.filename}")  # Debugging: Invalid file detected
        return {"error": "Invalid file or file type", "status_code": 400}

    try:
        # Debugging: Ensure the upload folder configuration exists
        print(f"Upload folder: {current_app.config['UPLOAD_FOLDER']}")

        # Generate the folder path for original images
        original_images_folder = os.path.join(current_app.config['UPLOAD_FOLDER'], f"event_{event_id}", "original_images")
        os.makedirs(original_images_folder, exist_ok=True)  # Ensure the folder exists
        print(f"Original images folder: {original_images_folder}")

        # Secure the filename to avoid path traversal attacks
        filename = secure_filename(image.filename)
        print(f"Secure filename: {filename}")

        file_path = os.path.join(original_images_folder, filename)
        print(f"File path: {file_path}")

        # Save the image to the folder
        image.save(file_path)
        print(f"Image saved to {file_path}")

        return {"success": True, "image.filename": image.filename, "status_code": 201}

    except Exception as e:
        print(f"Error saving image for event ID {event_id}: {e}")
        return {"error": f"Failed to save image: {str(e)}", "status_code": 500}




def create_symbolic_link(original_path, album_path):
    """
    Creates a symbolic link from the album to the original image.
    """
    try:
        # Remove the link if it already exists and is broken
        if os.path.islink(album_path) and not os.path.exists(album_path):
            os.unlink(album_path)
            print(f"Removed broken symbolic link: {album_path}")

        # Create the symbolic link
        os.symlink(original_path, album_path)
        print(f"Created symbolic link: {album_path} -> {original_path}")
    except FileExistsError:
        print(f"Symbolic link already exists: {album_path}")
    except OSError as e:
        print(f"Error creating symbolic link: {e}")

def add_image_to_album(event_id, album_name, image_filename):
    """
    Adds an image to an album by creating a symbolic link.
    """
    original_images_folder = os.path.join(UPLOADS_FOLDER, f"event_{event_id}", "original_images")
    albums_folder = os.path.join(UPLOADS_FOLDER, f"event_{event_id}", "albums", album_name)

    os.makedirs(albums_folder, exist_ok=True)

    original_image_path = os.path.join(original_images_folder, image_filename)
    album_image_path = os.path.join(albums_folder, image_filename)

    # Ensure the original image exists before creating a link
    if not os.path.exists(original_image_path):
        print(f"Original image does not exist: {original_image_path}")
        return

    create_symbolic_link(original_image_path, album_image_path)
    print(f"Added {image_filename} to album '{album_name}' for event_{event_id}")



def add_all_images_to_album(event_id, album_name="all_photos"):
    """
    Adds all images from the original_images folder to a specified album by creating symbolic links.
    """
    original_images_folder = os.path.join(UPLOADS_FOLDER, f"event_{event_id}", "original_images")

    # Check if the original_images folder exists
    if not os.path.exists(original_images_folder):
        print(f"Original images folder does not exist for event_{event_id}: {original_images_folder}")
        return

    # Iterate over all files in the original_images folder
    for image_filename in os.listdir(original_images_folder):
        # Ensure it's a file (and not a directory or other)
        original_image_path = os.path.join(original_images_folder, image_filename)
        if os.path.isfile(original_image_path):
            add_image_to_album(event_id, album_name, image_filename)

    print(f"All images added to album '{album_name}' for event_{event_id}")



def create_album_folder(event_id, album_name):
    """
    Creates a folder for a specific album within an event's album directory.

    :param event_id: The ID of the event to which the album belongs.
    :param album_name: The name of the album for which the folder will be created.
    :return: A dictionary indicating success or error.
    """
    print("\n\n\t\t\t\t# create_album_folder running for file handling\n\n")
    try:
        # Base directory for event albums
        base_path = f"uploads/event_{event_id}/albums/"
        
        # Ensure the base directory exists
        if not os.path.exists(base_path):
            return {"error": f"Base path '{base_path}' does not exist. Create the event first."}
        
        # Path for the new album
        album_path = os.path.join(base_path, album_name)

        # Check if the album folder already exists
        if os.path.exists(album_path):
            # Do nothing if the folder already exists
            return {"success": f"Folder for album '{album_name}' already exists at '{album_path}'"}
        
        # Create the album folder
        os.makedirs(album_path)
        return {"success": f"Folder for album '{album_name}' created successfully at '{album_path}'"}
    
    except Exception as e:
        return {"error": f"An error occurred while creating the album folder: {str(e)}"}

def delete_event_folder(event_id):
    """
    Deletes the folder associated with the event.

    Args:
        event_id (int): The ID of the event whose folder is to be deleted.

    Returns:
        dict: Success or error response.
    """
    try:
        # Construct the event folder path
        event_folder = os.path.join(
            os.getcwd(), "uploads", f"event_{event_id}"  # Fixed the folder structure
        )
        print(f"[DEBUG] Event folder path resolved: {event_folder}")

        # Check if the folder exists
        if not os.path.exists(event_folder):
            print(f"[ERROR] Folder {event_folder} does not exist.")
            return {"error": "Event folder not found"}

        # Delete the folder
        shutil.rmtree(event_folder)
        print(f"[INFO] Successfully deleted folder: {event_folder}")
        return {"success": True, "message": f"Folder for Event ID {event_id} deleted successfully"}

    except Exception as e:
        print(f"[ERROR] Error deleting folder for Event ID {event_id}: {e}")
        return {"error": f"Failed to delete folder: {str(e)}"}


def delete_album(event_id, album_name):
    """
    Deletes an album folder and its symbolic links.
    """
    album_path = os.path.join(UPLOADS_FOLDER, f"event_{event_id}", "albums", album_name)

    if os.path.exists(album_path):
        # Remove the album folder itself
        os.rmdir(album_path)
        print(f"Deleted album '{album_name}' for event_{event_id}")
    else:
        print(f"Album '{album_name}' does not exist for event_{event_id}")



def delete_image_files(event_id, image_paths):
    """
    Deletes the actual image files from the filesystem.

    Parameters:
    - event_id (int): The event ID associated with the images.
    - image_paths (list): List of relative image file paths to delete.

    Deletes files from:
    - uploads/event_<event_id>/original_images/
    - uploads/event_<event_id>/albums/all_photos/
    """
    for image_path in image_paths:
        # Construct full paths to both directories
        original_image_path = os.path.join(
            'uploads', f'event_{event_id}', 'original_images', image_path
        )
        all_photos_image_path = os.path.join(
            'uploads', f'event_{event_id}', 'albums', 'all_photos', image_path
        )

        # Delete files if they exist
        for path in [original_image_path, all_photos_image_path]:
            try:
                if os.path.exists(path):
                    os.remove(path)
                    print(f"Deleted: {path}")
            except Exception as e:
                print(f"Error deleting file {path}: {e}")