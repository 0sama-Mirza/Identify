import time
import requests
from healpers.db_helper import get_embeding_extracted_event, update_event_status, delete_sorted_event
from Sorting_Algos.HDBSCAN import cluster_faces_hdbscan
from healpers.folder_healper import delete_folders_in_event_folder
import os
print("HDBSCAN Working......")
print("Looking For emb_ext events")
def main_processing_loop(db_path='database.db', check_interval=5):
    while True:  # Infinite loop to keep checking for new events
        event_id_result = get_embeding_extracted_event(db_path)  # Get unsorted event IDs
        if event_id_result:
            # print("event_id_result: ", event_id_result)
            event_id = event_id_result[0][0]
            print(f"Processing event_id: {event_id}")
            input_folder = f"Cropped_Events/event_{event_id}"
            clustered_data = cluster_faces_hdbscan(input_folder)  # Assuming this returns the clustered data
            if clustered_data:
                print("Clustered Data:", clustered_data)
                processed_data = {}
                for key, value in clustered_data.items():
                    processed_data[str(key)] = value

                no_face_path = os.path.join(input_folder, "no_faces.txt")
                if os.path.exists(no_face_path):
                    with open(no_face_path, "r") as f:
                        no_face_files = [line.strip() for line in f if line.strip()]
                    processed_data["No Face"] = no_face_files
                print("\n=================processed_data=================\n",processed_data)

                # Include the event_id in the payload
                payload = {
                    'event_id': event_id,
                    'albums': processed_data
                }
                print("=====================payload Data=====================:\n", payload)
                try:
                    headers = {'Content-Type': 'application/json'}
                    response = requests.post("http://127.0.0.1:5000/albums/process_album_data", headers=headers, json=payload)
                    response.raise_for_status()
                    print("Data sent to Flask endpoint successfully.")
                    print("Response:", response.json())
                    update_event_status(event_id, "sorted")
                    delete_sorted_event(event_id)
                    delete_folders_in_event_folder(event_id)
                except requests.exceptions.RequestException as e:
                    print(f"Error sending data to Flask endpoint: {e}")
                    print("HDBSCAN Working......")
                    print("Looking For emb_ext events")
            else:
                print("HDBSCAN returned no cluster data.")
                update_event_status(event_id, "failed_sorting") # Or some other appropriate status
        # else:
        #     print("HDBSCAN: No emb_ext events found.")
        time.sleep(check_interval)  # Wait for the specified interval before checking again
if __name__ == "__main__":
    main_processing_loop()