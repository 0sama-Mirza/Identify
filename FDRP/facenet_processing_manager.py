import time
from db_helper import get_cropped_event, update_event_status
from facenet_worker import extract_face_embeddings
def main_processing_loop(db_path='database.db', check_interval=5):
    while True:  # Infinite loop to keep checking for new events
        event_id_result = get_cropped_event(db_path)  # Get unsorted event IDs
        print("event_id_result: ", event_id_result)
        if event_id_result:
            event_id = event_id_result[0][0]
            print(f"Processing event_id: {event_id}")
            input_folder = f"Cropped_Events/event_{event_id}/Cropped_Faces_Align"  # Construct input folder path
            output_folder = f"Cropped_Events/event_{event_id}"  # Construct output folder path
            extract_face_embeddings(input_folder, output_folder)  # Run face detection
            update_event_status(event_id, "emb_ext")
        else:
            print("No unsorted events found.")
        time.sleep(check_interval)  # Wait for the specified interval before checking again
if __name__ == "__main__":
    main_processing_loop()