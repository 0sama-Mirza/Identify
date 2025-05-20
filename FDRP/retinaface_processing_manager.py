import sys
import time
import subprocess
sys.path.append("FDRP-Workers")
from datetime import datetime
from healpers.db_helper import get_unsorted_event, update_event_status, update_retinaface_time, get_duration_string

print("RetinaFace Working......")
print("Looking For unsorted events")

def run_face_extraction_subprocess(input_folder, output_folder):
    try:
        result = subprocess.run(
            [sys.executable, "FDRP-Workers/retinaface_subprocess_entry.py", input_folder, output_folder],
            capture_output=True, text=True
        )

        # ✅ Bonus Tip: Check exit code
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
        event_id_result = get_unsorted_event(db_path)
        if event_id_result:
            event_id = event_id_result[0][0]
            print(f"Processing event_id: {event_id}")
            input_folder = f"received_images/event_{event_id}"
            output_folder = f"Cropped_Events/event_{event_id}"

            # Run extraction in separate subprocess to fully free GPU memory after
            start_time = datetime.now().isoformat()
            run_face_extraction_subprocess(input_folder, output_folder)

            update_event_status(event_id, "cropped")
            end_time = datetime.now().isoformat()
            duration_str = get_duration_string(start_time, end_time)
            update_retinaface_time(event_id,duration_str)
            print("RetinaFace Working......")
            print("Looking For unsorted events")

        time.sleep(check_interval)

if __name__ == "__main__":
    main_processing_loop()
