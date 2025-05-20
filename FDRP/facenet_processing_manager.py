import sys
import time
import subprocess
sys.path.append("FDRP-Workers")
from datetime import datetime
from healpers.db_helper import get_cropped_event, update_event_status, update_facenet_time, get_duration_string

print("FaceNet Working......")
print("Looking For cropped events")

def run_embedding_subprocess(input_folder, output_folder):
    try:
        result = subprocess.run(
            [sys.executable, "FDRP-Workers/facenet_subprocess_entry.py", input_folder, output_folder],
            capture_output=True, text=True
        )
        if result.returncode != 0:
            print(f"[ERROR] Subprocess failed with code {result.returncode}")
            print("STDOUT:\n", result.stdout)
            print("STDERR:\n", result.stderr)
        else:
            print("[INFO] Subprocess completed successfully.")
            print("STDOUT:\n", result.stdout)
    except Exception as e:
        print(f"[EXCEPTION] Failed to run subprocess: {e}")

def main_processing_loop(db_path='database.db', check_interval=5):
    while True:
        event_id_result = get_cropped_event(db_path)
        if event_id_result:
            event_id = event_id_result[0][0]
            print(f"Processing event_id: {event_id}")
            input_folder = f"Cropped_Events/event_{event_id}/Cropped_Faces_Align"
            output_folder = f"Cropped_Events/event_{event_id}"
            start_time = datetime.now().isoformat()
            run_embedding_subprocess(input_folder, output_folder)
            end_time = datetime.now().isoformat()
            duration_str = get_duration_string(start_time, end_time)
            update_facenet_time(event_id,duration_str)
            update_event_status(event_id, "emb_ext")
            print("FaceNet Working......")
            print("Looking For cropped events")

        time.sleep(check_interval)

if __name__ == "__main__":
    main_processing_loop()
