import sys
import time
import requests
from db_helper import get_embeding_extracted_event, update_event_status, delete_sorted_event
sys.path.append("Sorting-Algos")
from HDBSCAN import cluster_faces_hdbscan
print("HDBSCAN Working......")
print("Looking For emb_ext events")
def main_processing_loop(db_path='database.db', check_interval=5):
    while True:  # Infinite loop to keep checking for new events
        event_id_result = get_embeding_extracted_event(db_path)  # Get unsorted event IDs
        if event_id_result:
            print("event_id_result: ", event_id_result)
            event_id = event_id_result[0][0]
            print(f"Processing event_id: {event_id}")
            input_folder = f"Cropped_Events/event_{event_id}"
            clustered_data = cluster_faces_hdbscan(input_folder)  # Assuming this returns the clustered data
            if clustered_data:
                print("Clustered Data:", clustered_data)
                processed_data = {}
                for key, value in clustered_data.items():
                    processed_data[str(key)] = value

                # Include the event_id in the payload
                payload = {
                    'event_id': event_id,
                    'albums': processed_data
                }

                try:
                    headers = {'Content-Type': 'application/json'}
                    response = requests.post("http://127.0.0.1:5000/albums/process_album_data", headers=headers, json=payload)
                    response.raise_for_status()
                    print("Data sent to Flask endpoint successfully.")
                    print("Response:", response.json())
                    update_event_status(event_id, "sorted")
                    delete_sorted_event(event_id)
                except requests.exceptions.RequestException as e:
                    print(f"Error sending data to Flask endpoint: {e}")
            else:
                print("HDBSCAN returned no cluster data.")
                update_event_status(event_id, "failed_sorting") # Or some other appropriate status
        # else:
        #     print("HDBSCAN: No emb_ext events found.")
        time.sleep(check_interval)  # Wait for the specified interval before checking again
if __name__ == "__main__":
    main_processing_loop()import sys
import time
import requests
from db_helper import get_embeding_extracted_event, update_event_status, delete_sorted_event
sys.path.append("Sorting-Algos")
from HDBSCAN import cluster_faces_hdbscan
print("HDBSCAN Working......")
print("Looking For emb_ext events")
def main_processing_loop(db_path='database.db', check_interval=5):
    while True:  # Infinite loop to keep checking for new events
        event_id_result = get_embeding_extracted_event(db_path)  # Get unsorted event IDs
        if event_id_result:
            print("event_id_result: ", event_id_result)
            event_id = event_id_result[0][0]
            print(f"Processing event_id: {event_id}")
            input_folder = f"Cropped_Events/event_{event_id}"
            clustered_data = cluster_faces_hdbscan(input_folder)  # Assuming this returns the clustered data
            if clustered_data:
                print("Clustered Data:", clustered_data)
                processed_data = {}
                for key, value in clustered_data.items():
                    processed_data[str(key)] = value

                # Include the event_id in the payload
                payload = {
                    'event_id': event_id,
                    'albums': processed_data
                }

                try:
                    headers = {'Content-Type': 'application/json'}
                    response = requests.post("http://127.0.0.1:5000/albums/process_album_data", headers=headers, json=payload)
                    response.raise_for_status()
                    print("Data sent to Flask endpoint successfully.")
                    print("Response:", response.json())
                    update_event_status(event_id, "sorted")
                    delete_sorted_event(event_id)
                except requests.exceptions.RequestException as e:
                    print(f"Error sending data to Flask endpoint: {e}")
            else:
                print("HDBSCAN returned no cluster data.")
                update_event_status(event_id, "failed_sorting") # Or some other appropriate status
        # else:
        #     print("HDBSCAN: No emb_ext events found.")
        time.sleep(check_interval)  # Wait for the specified interval before checking again
if __name__ == "__main__":
    main_processing_loop()