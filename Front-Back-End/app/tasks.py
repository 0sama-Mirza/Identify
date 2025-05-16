# app/tasks.py
import os
import requests
import sqlite3
import traceback # For detailed error logging

# ====> 1. IMPORT allowed_file HELPER <====
from app.utils.helpers import allowed_file
# =======================================

# Function accepts the app instance from the scheduler
def check_and_process_unsorted_events(app_instance):
    """
    Finds and processes *only one* unsorted event per execution.
    Checks file types using allowed_file before processing.
    Relies on the finally block for all cursor and connection closing.
    """
    with app_instance.app_context():
        db_path = app_instance.config['DATABASE']
        fastapi_url = app_instance.config['FASTAPI_UPLOAD_URL']
        uploads_base_dir = app_instance.config['UPLOAD_FOLDER']

        # print("-" * 60)
        # print(f"SCHEDULER TASK: Checking for ONE unsorted event in DB -> {db_path}")

        conn = None
        cursor = None

        try:
            conn = sqlite3.connect(db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute("SELECT id FROM events WHERE status = 'unsorted' ORDER BY id ASC LIMIT 1")
            event_row = cursor.fetchone()

            if not event_row:
                # print("SCHEDULER TASK: No unsorted events found.")
                return # Finally block will close conn/cursor

            event_id = event_row['id']
            print(f"  -> Found unsorted Event ID: {event_id}. Processing this event only.")

            cursor.execute("""
                SELECT image_path 
                FROM event_images 
                WHERE event_id = ? AND status = 'unsorted'
            """, (event_id,))

            image_rows = cursor.fetchall()

            if not image_rows:
                print(f"  -> No images found for Event ID: {event_id}. Marking as 'sorted'.")
                try:
                    cursor.execute("UPDATE events SET status = 'sorted' WHERE id = ?", (event_id,))
                    conn.commit()
                    print(f"SCHEDULER TASK: Committed status update for event {event_id} (no images).")
                except sqlite3.Error as e_update:
                    print(f"SCHEDULER TASK: DB error updating status (no images): {e_update}")
                    conn.rollback()
                return # Finally block will close conn/cursor

            # --- Prepare files ---
            files_to_upload = []
            file_handles = []
            has_valid_files = False
            image_dir = os.path.join(uploads_base_dir, f'event_{event_id}', 'original_images')
            print(f"  -> Base image directory for event: {image_dir}")

            for img_row in image_rows:
                image_filename = img_row['image_path'] # This is just the filename

                if not image_filename:
                    print(f"  -> Warning: Skipping empty filename for event {event_id}.")
                    continue

                # ====> 2. CHECK IF FILE TYPE IS ALLOWED <====
                if not allowed_file(image_filename):
                    print(f"  -> Skipping disallowed file type: {image_filename} (Event {event_id})")
                    continue # Skip to the next image row
                # ============================================

                full_image_path = os.path.join(image_dir, image_filename)
                print(f"  -> Checking allowed file: {full_image_path}") # Updated log

                if os.path.exists(full_image_path):
                    try:
                        file_handle = open(full_image_path, 'rb')
                        file_handles.append(file_handle)
                        content_type = 'application/octet-stream'
                        # Determine content type (using the already validated filename)
                        if image_filename.lower().endswith(('.jpg', '.jpeg')): content_type = 'image/jpeg'
                        elif image_filename.lower().endswith('.png'): content_type = 'image/png'
                        elif image_filename.lower().endswith('.gif'): content_type = 'image/gif'
                        # Add webp if needed by FastAPI endpoint
                        elif image_filename.lower().endswith('.webp'): content_type = 'image/webp'

                        files_to_upload.append(('images', (image_filename, file_handle, content_type)))
                        has_valid_files = True
                    except Exception as e_open:
                         print(f"  -> Error opening file {full_image_path}: {e_open}")
                else:
                    print(f"  -> CRITICAL WARNING: Image file not found: {full_image_path} (Event {event_id}). Skipping.")

            if not has_valid_files:
                print(f"  -> No *accessible and allowed* image files found/prepared for event {event_id}.") # Refined log
                for fh in file_handles: fh.close()
                return # Finally block will close conn/cursor

            # --- Send images ---
            print(f"  -> Attempting to send {len(files_to_upload)} allowed file(s)...")
            api_call_successful = False
            try:
                response = requests.post(
                    fastapi_url,
                    files=files_to_upload,
                    data={"event_id": str(event_id)},  # Send event ID as a form field
                    timeout=180
                )

                if response.status_code == 200:
                    api_call_successful = True
                    try: msg = response.json().get('message', 'OK')
                    except: msg = response.text[:100]
                    print(f"  -> SUCCESS: FastAPI processed images for event {event_id}. Response: {msg}")
                else:
                    print(f"  -> ERROR: FastAPI returned status {response.status_code} for event {event_id}. Response: {response.text}")
            # (Requests exception handling remains the same...)
            except requests.exceptions.Timeout: print(f"  -> ERROR: Request timed out.")
            except requests.exceptions.ConnectionError: print(f"  -> ERROR: Connection error.")
            except requests.exceptions.RequestException as e: print(f"  -> ERROR: Network error: {e}")
            except Exception as e_api: print(f"  -> ERROR during API call: {e_api}")
            finally:
                # Close file handles here
                print(f"  -> Closing {len(file_handles)} file handles...")
                for fh in file_handles:
                    try: fh.close()
                    except Exception as e_close: print(f"    -> Error closing handle: {e_close}")

            # --- Update status ---
            if api_call_successful:
                print(f"SCHEDULER TASK: Updating status to 'processing' for event {event_id}")
                try:
                    cursor.execute("UPDATE events SET status = 'processing' WHERE id = ?", (event_id,))
                    cursor.execute("""
                        UPDATE event_images 
                        SET status = 'processing' 
                        WHERE event_id = ? AND status = 'unsorted'
                    """, (event_id,))
                    conn.commit()
                    print(f"SCHEDULER TASK: Committed status update for event {event_id}.")
                except sqlite3.Error as e_update:
                    print(f"SCHEDULER TASK: DB error updating status: {e_update}")
                    conn.rollback()
            else:
                 print(f"SCHEDULER TASK: API call failed or no valid files sent; status not updated for event {event_id}.")

        # --- Outer Error Handling ---
        except sqlite3.OperationalError as e: print(f"SCHEDULER TASK ERROR: DB operational error: {e}"); traceback.print_exc(); conn and conn.rollback()
        except sqlite3.Error as e: print(f"SCHEDULER TASK ERROR: DB error: {e}"); traceback.print_exc(); conn and conn.rollback()
        except Exception as e: print(f"SCHEDULER TASK ERROR: Unexpected error: {e}"); traceback.print_exc(); conn and conn.rollback()

        # --- Final Cleanup ---
        finally:
            if cursor:
                try: cursor.close()
                except Exception as ce: print(f"Error closing cursor: {ce}")
            if conn:
                try: conn.close(); #print("SCHEDULER TASK: Database connection closed.")
                except Exception as ce: print(f"Error closing connection: {ce}")
            print("-" * 60)
