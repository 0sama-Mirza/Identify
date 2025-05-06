import pickle
import numpy as np
import os
import shutil
from sklearn.metrics.pairwise import cosine_similarity
from collections import defaultdict

file_path = '../Cropped_Events/event_1/facenet_embeddings.pkl'
threshold = 0.5  # Adjust this threshold as needed

try:
    with open(file_path, 'rb') as f:
        embeddings_dict = pickle.load(f)
    print(f"Successfully loaded {len(embeddings_dict)} face embeddings.")
except FileNotFoundError:
    print(f"Error: File not found at {file_path}")
    embeddings_dict = {}
except pickle.UnpicklingError:
    print("Error: The file does not contain a valid pickled dictionary.")
    embeddings_dict = {}
except Exception as e:
    print(f"An unexpected error occurred: {e}")
    embeddings_dict = {}

if not embeddings_dict:
    exit()

face_names = list(embeddings_dict.keys())
embedding_vectors = np.array(list(embeddings_dict.values()))
num_faces = len(face_names)

# Initialize a list to store the cluster ID for each face (-1 means not yet assigned)
face_clusters = [-1] * num_faces
next_cluster_id = 0

print("\nClustering faces...")
for i in range(num_faces):
    if face_clusters[i] == -1:  # If this face hasn't been assigned to a cluster yet
        face_clusters[i] = next_cluster_id  # Assign a new cluster ID
        for j in range(i + 1, num_faces):
            if face_clusters[j] == -1:  # If the other face hasn't been assigned
                similarity = cosine_similarity(embedding_vectors[i].reshape(1, -1), embedding_vectors[j].reshape(1, -1))[0][0]
                if similarity > threshold:
                    face_clusters[j] = next_cluster_id  # Assign the same cluster ID
        next_cluster_id += 1

# Create a dictionary to store the face names for each cluster ID
clustered_faces = defaultdict(list)
for i, cluster_id in enumerate(face_clusters):
    clustered_faces[cluster_id].append(face_names[i])

print("\nFace IDs and corresponding image names:")
for cluster_id, names in clustered_faces.items():
    print(f"Person ID: {cluster_id}")
    for name in names:
        print(f"- {name}")
    print("-" * 20)

print("==================Cluster================")
print(clustered_faces)



output_album_dir = 'Cropped_Events/event_1/albums'
custom_source_path = 'Cropped_Events/event_1/Cropped_Faces_Align'

# Create the main albums directory if it doesn't exist
if not os.path.exists(output_album_dir):
    os.makedirs(output_album_dir)
    print(f"Created directory: {output_album_dir}")

print("\nOrganizing images into albums...")
for person_id, face_filenames in clustered_faces.items():
    person_album_path = os.path.join(output_album_dir, str(person_id))

    # Create the person's album directory if it doesn't exist
    if not os.path.exists(person_album_path):
        os.makedirs(person_album_path)
        print(f"Created album directory for Person ID '{person_id}': {person_album_path}")

    for face_filename in face_filenames:
        source_file_path = os.path.join(custom_source_path, face_filename)  # <--- USE CUSTOM PATH HERE
        destination_file_path = os.path.join(person_album_path, os.path.basename(face_filename))

        try:
            shutil.copy2(source_file_path, destination_file_path)
            # print(f"Copied '{os.path.basename(face_filename)}' to '{person_album_path}'")
        except FileNotFoundError:
            print(f"Warning: Source file not found: {source_file_path}")
        except Exception as e:
            print(f"Error copying '{os.path.basename(face_filename)}': {e}")

print("\nImage organization complete!")

