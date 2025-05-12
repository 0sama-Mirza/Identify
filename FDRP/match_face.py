import pickle
import sys
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
import subprocess
import logging
from pathlib import Path
from typing import Tuple, Optional, Dict, List, Union
import argparse
from healpers.folder_healper import clean_user_data

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_subprocess(script_name: str, input_path: str, output_path: str, timeout: int = 300) -> bool:
    """Generic subprocess runner with enhanced error handling"""
    try:
        script_path = Path(f"FDRP-Workers/{script_name}").resolve()
        if not script_path.exists():
            logger.error(f"Script not found: {script_path}")
            return False

        logger.info(f"Starting {script_name} on {input_path}")
        result = subprocess.run(
            [sys.executable, str(script_path), input_path, output_path],
            check=True,
            timeout=timeout,
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace'
        )
        
        logger.debug(f"Subprocess output:\n{result.stdout[:500]}")  # Truncate long outputs
        return True
        
    except subprocess.CalledProcessError as e:
        logger.error(f"{script_name} failed with code {e.returncode}:\nError: {e.stderr[:500]}")
    except subprocess.TimeoutExpired:
        logger.error(f"{script_name} timed out after {timeout} seconds")
    except Exception as e:
        logger.error(f"Unexpected error in {script_name}: {str(e)}", exc_info=True)
    return False

def load_embeddings(file_path: str) -> Optional[Dict[str, np.ndarray]]:
    """Safely load embeddings with validation"""
    try:
        with open(file_path, "rb") as f:
            embeddings = pickle.load(f)
            if not embeddings or not isinstance(embeddings, dict):
                logger.error(f"Invalid embeddings format in {file_path}")
                return None
            return embeddings
    except Exception as e:
        logger.error(f"Failed to load embeddings from {file_path}: {str(e)}", exc_info=True)
        return None

def find_best_match(user_id: str, event_id: str) -> Union[Tuple[None, None, None], Tuple[int, str, float]]:
    """Enhanced face matching pipeline with complete error handling"""
    user_path = Path(f"user_data/{user_id}")
    facenet_user_path = user_path / "Cropped_Faces_Align"
    event_path = Path(f"Cropped_Events/event_{event_id}")
    
    # Validate paths
    if not user_path.exists():
        logger.error(f"User path not found: {user_path}")
        return None, None, None
    if not event_path.exists():
        logger.error(f"Event path not found: {event_path}")
        return None, None, None

    # Pipeline execution
    steps = [
        ("retinaface_subprocess_entry.py", "Face detection"),
        ("facenet_subprocess_entry.py", "Embedding extraction")
    ]
    
    # Run RetinaFace 
    if not run_subprocess(steps[0][0], str(user_path), str(user_path)):
        return None, None, None
    # Run FaceNet
    if not run_subprocess(steps[1][0], str(facenet_user_path), str(user_path)):
        return None, None, None
    
    try:
        clean_user_data(user_id)
    except Exception as e:
        logger.error(f"Cleanup failed: {str(e)}", exc_info=True)
        return None, None, None

    # Load and validate embeddings
    user_embeddings = load_embeddings(f"{user_path}/facenet512_embeddings.pkl")
    event_embeddings = load_embeddings(f"{event_path}/facenet512_embeddings.pkl")
    
    if not user_embeddings or not event_embeddings:
        return None, None, None

    # Get primary user embedding
    try:
        my_embed = next(iter(user_embeddings.values()))
    except StopIteration:
        logger.error("No valid user embeddings found")
        return None, None, None

    # Find best match
    best_score = -1
    best_match = None
    
    for filename, embed in event_embeddings.items():
        try:
            score = cosine_similarity([my_embed], [embed])[0][0]
            if score > best_score:
                best_score = score
                best_match = filename
        except Exception as e:
            logger.warning(f"Error comparing with {filename}: {str(e)}")
            continue

    if best_match is None:
        logger.error("No valid matches found")
        return None, None, None

    # Check clustered faces
    try:
        with open(f"{event_path}/clustered_faces.pkl", "rb") as f:
            clustered_faces = pickle.load(f)
        
        for cluster_id, face_list in clustered_faces.items():
            if best_match in face_list:
                logger.info(f"Matched Cluster {cluster_id} with similarity {best_score:.4f}")
                return cluster_id, best_match, best_score
                
    except Exception as e:
        logger.error(f"Failed to process clusters: {str(e)}", exc_info=True)

    logger.warning("Match not found in any cluster")
    return None, best_match, best_score

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Face matching system")
    parser.add_argument("--user_id", required=True, help="User ID")
    parser.add_argument("--event_id", required=True, help="Event ID")
    
    args = parser.parse_args()
    
    result = find_best_match(args.user_id, args.event_id)
    
    if result[0] is not None:
        cluster_id, filename, score = result
        print(f"\nMATCH FOUND\nCluster: {cluster_id}\nFile: {filename}\nScore: {score:.4f}")
    else:
        print("\nNO MATCH FOUND")
        if result[1]:  # If we have a filename despite no cluster
            print(f"Best candidate: {result[1]} (Score: {result[2]:.4f})")