import sys
import time
from db_helper import get_embeding_extracted_event, update_event_status, delete_sorted_event
sys.path.append("Sorting-Algos")
from HDBSCAN import cluster_faces_hdbscan
def main_processing_loop(db_path='database.db', check_interval=5):
    while True:  # Infinite loop to keep checking for new events
        event_id_result = get_embeding_extracted_event(db_path)  # Get unsorted event IDs
        print("event_id_result: ", event_id_result)
        if event_id_result:
            event_id = event_id_result[0][0]
            print(f"Processing event_id: {event_id}")
            input_folder = f"Cropped_Events/event_{event_id}"
            cluster_faces_hdbscan(input_folder)
            update_event_status(event_id, "sorted")
            delete_sorted_event(event_id)
        else:
            print("HDBSCAN: No unsorted events found.")
        time.sleep(check_interval)  # Wait for the specified interval before checking again
if __name__ == "__main__":
    main_processing_loop()