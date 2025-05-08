# retinaface_worker.py

print("Setting Up The Environment. Please Wait...")
print("importing os, cv2, RetinaFace, tensorflow...")
import os
import cv2
from retinaface import RetinaFace
import tensorflow as tf

# Enable GPU memory growth to avoid memory allocation errors
gpus = tf.config.experimental.list_physical_devices('GPU')
if gpus:
    try:
        for gpu in gpus:
            tf.config.experimental.set_memory_growth(gpu, True)
    except RuntimeError as e:
        print(e)

def extract_faces(input_folder, output_folder):
    print("\n\t\t\tYo YO Yo Yo Yo\n")
    # Output folders for faces detected and no face
    faces_detected_folder = os.path.join(output_folder, 'Face')
    no_face_folder = os.path.join(output_folder, 'No-Face')
    cropped_faces_align_folder = os.path.join(output_folder, 'Cropped_Faces_Align')
    cropped_faces_folder = os.path.join(output_folder, 'Cropped_Faces')

    os.makedirs(faces_detected_folder, exist_ok=True)
    os.makedirs(no_face_folder, exist_ok=True)
    os.makedirs(cropped_faces_folder, exist_ok=True)
    os.makedirs(cropped_faces_align_folder, exist_ok=True)

    Total_Faces = 0
    Total_NoFaces = 0
    Face_Array = []
    No_Face_Array = []

    def display_statistics(total_faces, total_no_faces):
        stats_output = (
            "+----------------------------+\n"
            "|     Face Detection Stats    |\n"
            "+----------------------------+\n"
            "| Images with Faces   | {:5}  |\n".format(total_faces) +
            "| Images without Face | {:5}  |\n".format(total_no_faces) +
            "+----------------------------+\n"
            "| Total Images        | {:5}  |\n".format(total_faces + total_no_faces) +
            "+----------------------------+\n"
        )
        print(stats_output)
        with open("Small_Results.txt", "w") as file:
            file.write(stats_output)

    print("Setting Up GPU. Please Wait...")

    def save_cropped_faces_old(image_name, faces, img_resized):
        face_id = 0
        for key, face_info in faces.items():
            facial_area = face_info['facial_area']
            x1, y1, x2, y2 = facial_area
            cropped_face = img_resized[y1:y2, x1:x2]
            cropped_face_name = f"{image_name}_face_{face_id}.jpg"
            cv2.imwrite(os.path.join(cropped_faces_folder, cropped_face_name), cropped_face)
            face_id += 1

    def save_cropped_faces(image_name, img_resized):
        try:
            with tf.device('/GPU:0'):
                faces = RetinaFace.extract_faces(img_path=img_resized, align=True)
                num_faces_detected = len(faces)
                print(f"Number of faces detected in the image '{image_name}': {num_faces_detected}")
                if num_faces_detected == 0:
                    print(f"No faces detected in the image: {image_name}")
                    return
                face_id = 0
                for face in faces:
                    if face is None or face.size == 0:
                        print(f"Warning: Face {face_id} is empty and will be skipped.")
                        continue
                    print(f"Extracted face {face_id} with shape: {face.shape}")
                    cropped_face_name = f"{image_name}_face_{face_id}.jpg"
                    if not os.path.exists(cropped_faces_align_folder):
                        os.makedirs(cropped_faces_align_folder)
                    success = cv2.imwrite(os.path.join(cropped_faces_align_folder, cropped_face_name), face[:,:,::-1])
                    if not success:
                        print(f"Failed to save face {face_id} for image {image_name}")
                    else:
                        print(f"Successfully saved face {face_id} as {cropped_face_name}")
                    face_id += 1
        except tf.errors.ResourceExhaustedError:
            print("Falling back to CPU for face extraction due to GPU OOM.")
            with tf.device('/CPU:0'):
                faces = RetinaFace.extract_faces(img_path=img_resized, align=True)
                num_faces_detected = len(faces)
                print(f"(CPU) Number of faces detected in the image '{image_name}': {num_faces_detected}")
                if num_faces_detected == 0:
                    print(f"(CPU) No faces detected in the image: {image_name}")
                    return
                face_id = 0
                for face in faces:
                    if face is None or face.size == 0:
                        print(f"(CPU) Warning: Face {face_id} is empty and will be skipped.")
                        continue
                    print(f"(CPU) Extracted face {face_id} with shape: {face.shape}")
                    cropped_face_name = f"{image_name}_face_{face_id}.jpg"
                    if not os.path.exists(cropped_faces_align_folder):
                        os.makedirs(cropped_faces_align_folder)
                    success = cv2.imwrite(os.path.join(cropped_faces_align_folder, cropped_face_name), face[:,:,::-1])
                    if not success:
                        print(f"(CPU) Failed to save face {face_id} for image {image_name}")
                    else:
                        print(f"(CPU) Successfully saved face {face_id} as {cropped_face_name}")
                    face_id += 1

    def resize_image_if_needed(img, max_width=1920, max_height=1080):
        height, width = img.shape[:2]
        if height > max_height or width > max_width:
            scaling_factor = min(max_width / width, max_height / height)
            new_size = (int(width * scaling_factor), int(height * scaling_factor))
            img_resized = cv2.resize(img, new_size)
            return img_resized
        else:
            return img

    def detect_faces_retinaface(image_path):
        img = cv2.imread(image_path)
        if img is None:
            print(f"Warning: Unable to load image at {image_path}. Skipping...")
            return None, None, []
        img_resized = resize_image_if_needed(img)
        try:
            with tf.device('/GPU:0'):
                faces = RetinaFace.detect_faces(img_resized)
        except tf.errors.ResourceExhaustedError:
            print("Falling back to CPU for face detection due to GPU OOM.")
            with tf.device('/CPU:0'):
                faces = RetinaFace.detect_faces(img_resized)
        if faces == {}:
            return img_resized, img_resized, []
        img_resized_for_cropping = img_resized.copy()
        for key, face_info in faces.items():
            facial_area = face_info['facial_area']
            x1, y1, x2, y2 = facial_area
            cv2.rectangle(img_resized, (x1, y1), (x2, y2), (0, 255, 0), 2)
        return img_resized, img_resized_for_cropping, faces

    # --- Process all images in the input folder ---
    if not os.listdir(input_folder):
        print("Error: Input folder is empty!")
        return

    for image_name in os.listdir(input_folder):
        image_path = os.path.join(input_folder, image_name)
        annotated_img, img_resized_for_cropping, faces = detect_faces_retinaface(image_path)
        if annotated_img is None:
            continue
        if len(faces) == 0:
            print(image_name, "No Face")
            cv2.imwrite(os.path.join(no_face_folder, image_name), annotated_img)
            No_Face_Array.append(image_name)
            Total_NoFaces += 1
        else:
            print(image_name, "Face Found")
            cv2.imwrite(os.path.join(faces_detected_folder, image_name), annotated_img)
            save_cropped_faces_old(image_name, faces, img_resized_for_cropping)
            save_cropped_faces(image_name, img_resized_for_cropping)
            Face_Array.append(image_name)
            Total_Faces += 1
        # --- ✅ Remove the original image after processing ---
        try:
            os.remove(image_path)
            print(f"Removed original: {image_name}")
        except Exception as e:
            print(f"Failed to delete {image_name}: {e}")

    print("Images Have Been Successfully Filtered Out.")
    display_statistics(Total_Faces, Total_NoFaces)

    # with open("small_faces_detected_list.txt", "w") as f:
    #     f.write("\n".join(Face_Array))
    # with open("small_no_faces_detected_list.txt", "w") as f:
    #     f.write("\n".join(No_Face_Array))
    return
