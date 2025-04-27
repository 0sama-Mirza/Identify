from db_helper import get_unsorted_event, update_event_status
from retinaface_worker.py import process_images

def main_processing_loop(db_path='database.db'):
    event_id_result = get_unsorted_event(db_path)  # Get unsorted event IDs
    if event_id:
        event_id = event_id_result[0]
        print(f"Processing event_id: {event_id}")

        input_folder = f"received_images/event_{event_id}"  # Construct input folder path
        output_folder = f"Cropped_Events/event_{event_id}"  # Construct output folder path

        process_images(input_folder, output_folder)  # Run face detection
        update_event_status(event_id,"cropped")
    else:
        print("No unsorted events found.")

if __name__ == "__main__":
    main_processing_loop()