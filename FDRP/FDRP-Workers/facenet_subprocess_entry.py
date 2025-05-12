import sys
import os
sys.path.append(".")  # To import facenet_worker
from facenet_worker import extract_face_embeddings

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python facenet_subprocess_entry.py <input_folder> <output_folder>")
        sys.exit(1)

    input_folder = sys.argv[1]
    output_folder = sys.argv[2]

    try:
        extract_face_embeddings(input_folder, output_folder)
        print("[INFO] Face embeddings extracted successfully.")
        sys.exit(0)
    except Exception as e:
        print(f"[ERROR] Failed to extract embeddings: {e}")
        sys.exit(2)
