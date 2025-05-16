import os
import shutil

def delete_folders_in_event_folder(event_id):
    """
    Deletes all folders within the Cropped_Events/event_{event_id} directory,
    but skips folders named 'Cropped_Faces_Align' and any that start with 'albums_'.
    Leaves files intact.
    """
    event_folder_path = f"Cropped_Events/event_{event_id}"

    if not os.path.exists(event_folder_path):
        print(f"Error: Folder '{event_folder_path}' not found.")
        return

    items = os.listdir(event_folder_path)

    for item in items:
        item_path = os.path.join(event_folder_path, item)
        if os.path.isdir(item_path):
            # ❌ Skip if the folder is Cropped_Faces_Align or starts with albums_
            if item == "Cropped_Faces_Align" or item.startswith("albums_"):
                print(f"Skipping protected folder: {item_path}")
                continue

            try:
                shutil.rmtree(item_path)
                print(f"Deleted folder: {item_path}")
            except Exception as e:
                print(f"Error deleting folder {item_path}: {e}")
        else:
            print(f"Skipping file: {item_path}")


def clean_user_data(user_id, base_dir="user_data"):
    user_path = os.path.join(base_dir, str(user_id))

    if not os.path.exists(user_path):
        print(f"[Error] Path does not exist: {user_path}")
        return

    for item in os.listdir(user_path):
        item_path = os.path.join(user_path, item)

        if os.path.isdir(item_path):
            # Special handling for Cropped_Faces_Align
            if item == "Cropped_Faces_Align":
                print(f"Processing: {item_path}")
                for sub_item in os.listdir(item_path):
                    sub_item_path = os.path.join(item_path, sub_item)
                    if os.path.isfile(sub_item_path):
                        dest_path = os.path.join(user_path, sub_item)
                        shutil.move(sub_item_path, dest_path)
                        print(f"Moved: {sub_item_path} → {dest_path}")
                shutil.rmtree(item_path)
                print(f"Deleted folder: {item_path}")
            else:
                # Delete any other folders
                shutil.rmtree(item_path)
                print(f"Deleted folder: {item_path}")

    print(f"[Done] Cleaned up {user_path}")

if __name__ == '__main__':
    # Example usage: Delete folders in 'Cropped_Events/event_1'
    event_id_to_delete = 1
    delete_folders_in_event_folder(event_id_to_delete)
