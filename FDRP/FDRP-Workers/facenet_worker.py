import os
import pickle
from deepface import DeepFace
# from tqdm import tqdm # tqdm might not be ideal for a background process log
import logging
import time # For the main loop example
import tensorflow as tf

# Configure logging (do this once at the start of your manager script)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(process)d - %(levelname)s - %(message)s')

# Define allowed extensions globally or pass them if needed
ALLOWED_EXTENSIONS = ('.jpg', '.jpeg', '.png', '.bmp', '.gif', '.tiff')
DEFAULT_MODEL = 'Facenet512' # Using Facenet as requested
GPU = "yes"
def extract_face_embeddings(cropped_faces_dir, embeddings_output_dir, gpu=GPU, model_name=DEFAULT_MODEL):
    """
    Extracts face embeddings from images in cropped_faces_dir using a specified DeepFace model
    and saves them to a pickle file named '<model_name>_embeddings.pkl' in embeddings_output_dir.

    Args:
        cropped_faces_dir (str): Path to the directory containing pre-cropped and aligned face images.
        embeddings_output_dir (str): Path to the directory where the embeddings pickle file will be saved.
                                     This directory will be created if it doesn't exist.
        model_name (str): The DeepFace model to use for generating embeddings (default: 'Facenet').

    Returns:
        str | None: The full path to the saved embeddings pickle file if successful, otherwise None.
                    Returns None if input directory is invalid, no images are found,
                    no embeddings could be extracted, or saving fails.
    """
    if (gpu == "no"):
        os.environ['CUDA_VISIBLE_DEVICES'] = '-1'
        print("Using CPU")
    else:
        # Enable GPU memory growth to avoid memory allocation errors
        gpus = tf.config.experimental.list_physical_devices('GPU')
        if gpus:
            try:
                for gpu in gpus:
                    tf.config.experimental.set_memory_growth(gpu, True)
                    print("Using GPU")
            except RuntimeError as e:
                print(e)

    logging.info(f"Starting embedding extraction for: '{cropped_faces_dir}'")
    logging.info(f"Using model: '{model_name}'. Output directory: '{embeddings_output_dir}'")

    # --- Input Validation ---
    if not os.path.isdir(cropped_faces_dir):
        logging.error(f"Input directory for cropped faces '{cropped_faces_dir}' not found or is not a directory.")
        return None # Indicate failure

    # --- Ensure Output Directory Exists ---
    try:
        os.makedirs(embeddings_output_dir, exist_ok=True)
        # logging.info(f"Ensured embeddings output directory exists: '{embeddings_output_dir}'") # Less verbose
    except OSError as e:
        logging.error(f"Could not create or access embeddings output directory '{embeddings_output_dir}': {e}")
        return None # Indicate failure

    # --- Define Output File Path (inside the output directory) ---
    output_file_name = f"{model_name.lower()}_embeddings.pkl"
    output_file_path = os.path.join(embeddings_output_dir, output_file_name)
    logging.info(f"Embeddings will be saved to: '{output_file_path}'")

    embeddings_dict = {} # Dictionary to store {filename: embedding}

    # --- List Image Files ---
    try:
        all_files = os.listdir(cropped_faces_dir)
        image_files = [f for f in all_files if f.lower().endswith(ALLOWED_EXTENSIONS)]
        if not image_files:
            logging.warning(f"No image files with extensions {ALLOWED_EXTENSIONS} found in '{cropped_faces_dir}'.")
            return None # No images to process
        logging.info(f"Found {len(image_files)} potential image files in '{cropped_faces_dir}'.")
    except OSError as e:
        logging.error(f"Error accessing cropped faces directory '{cropped_faces_dir}': {e}")
        return None

    # --- Process Each Image ---
    processed_count = 0
    for filename in image_files:
        img_path = os.path.join(cropped_faces_dir, filename)

        if not os.path.isfile(img_path): # Double check it's a file
            logging.warning(f"Skipping '{filename}' as it's not a file (likely a subdirectory).")
            continue

        try:
            # --- Extract the embedding using DeepFace.represent ---
            embedding_objs = DeepFace.represent(
                img_path=img_path,
                model_name=model_name,
                enforce_detection=False, # Crucial: Images are already cropped faces
                detector_backend='skip'  # Explicitly skip detection backend
            )

            # DeepFace.represent returns a list containing a dictionary [{ 'embedding': [...] }]
            if embedding_objs and isinstance(embedding_objs, list) and len(embedding_objs) > 0 \
               and 'embedding' in embedding_objs[0] and isinstance(embedding_objs[0]['embedding'], list):
                embedding = embedding_objs[0]['embedding']
                embeddings_dict[filename] = embedding
                processed_count += 1
            else:
                logging.warning(f"Could not extract a valid embedding for '{filename}' from '{cropped_faces_dir}'. DeepFace.represent result format unexpected: {embedding_objs}")

        except ValueError as ve:
            logging.error(f"Skipping '{filename}' from '{cropped_faces_dir}' due to ValueError (often image format/corruption): {ve}")
        except AttributeError as ae:
             logging.error(f"Skipping '{filename}' from '{cropped_faces_dir}' due to AttributeError (backend issue?): {ae}")
        except Exception as e:
            logging.error(f"Skipping '{filename}' from '{cropped_faces_dir}' due to unexpected error: {type(e).__name__} - {e}")
            # For deep debugging:
            # import traceback
            # logging.error(traceback.format_exc())

    logging.info(f"Attempted processing {len(image_files)} files. Successfully extracted embeddings for {processed_count} files.")

    # --- Save Embeddings ---
    if embeddings_dict:  # Only proceed if we have new embeddings
        try:
            # Load existing embeddings if the file exists
            existing_embeddings = {}
            if os.path.exists(output_file_path):
                with open(output_file_path, 'rb') as f:
                    existing_embeddings = pickle.load(f)
                logging.info(f"Loaded {len(existing_embeddings)} existing embeddings from '{output_file_path}'")

            # Merge old + new embeddings (new ones overwrite old if filenames clash)
            merged_embeddings = {**existing_embeddings, **embeddings_dict}
            
            # Save the merged result
            with open(output_file_path, 'wb') as f:
                pickle.dump(merged_embeddings, f)
            
            logging.info(f"Saved {len(merged_embeddings)} embeddings ({len(embeddings_dict)} new) to '{output_file_path}'")
            return output_file_path

        except (IOError, pickle.PickleError) as e:  # Combines both IO and pickle errors
            logging.error(f"Failed to save embeddings to '{output_file_path}': {e}")
            return None
    else:
        logging.warning(f"No new embeddings extracted. Existing file '{output_file_path}' was not modified.")
        return None