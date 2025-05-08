import os
from deepface import DeepFace

matched_images = []
matched_set = set()
model_name = "Facenet512"
folder_path = '../Cropped_Events/event_1/Cropped_Faces_Align'

image_files = sorted([os.path.join(folder_path, f) for f in os.listdir(folder_path) if os.path.isfile(os.path.join(folder_path, f))])
image_files

for i in range(len(image_files)):
    if image_files[i] in matched_set:
        continue
    current_matches = []
    for j in range(1,len(image_files)):
        if image_files[j] in matched_set:
            continue
        try:
            obj = DeepFace.verify(img1_path=image_files[i], img2_path=image_files[j], model_name=model_name, enforce_detection=False)
            if obj['verified']:
                print(f"({i},{j}): Found Match")
                current_matches.append(image_files[j])
                matched_set.add(image_files[j])
        except ValueError as e:
            print(f"Face could not be detected in {image_files[j]}. Skipping this image.")
        except Exception as e:
            print(f"An error occurred while comparing images: {e}")

    if current_matches:
        matched_images.append([image_files[i]] + current_matches)
        matched_set.add(image_files[i])
print("Matched images:", matched_images)



base_dir = '../Cropped_Events/event_1/Custom_Results'

os.makedirs(base_dir, exist_ok=True)
for index, group in enumerate(matched_images):
    folder_name = os.path.join(base_dir, str(index))
    os.makedirs(folder_name, exist_ok=True)

    text_file_path = os.path.join(folder_name, "image_paths.txt")

    with open(text_file_path, "w") as text_file:
        for image_path in group:
            text_file.write(image_path + "\n")

print(f"Folders and text files created in {base_dir}.")