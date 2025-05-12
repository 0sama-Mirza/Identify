import sys
from retinaface_worker import extract_faces

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python retinaface_subprocess_entry.py <input_folder> <output_folder>")
        sys.exit(1)

    input_folder = sys.argv[1]
    output_folder = sys.argv[2]

    extract_faces(input_folder, output_folder)
