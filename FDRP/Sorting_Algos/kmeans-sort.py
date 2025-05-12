import pickle
import numpy as np
from sklearn.cluster import KMeans
from collections import defaultdict
import os
import shutil

# --- Configuration ---
base_dir = '../Cropped_Events/event_1/'
embeddings_file_path = base_dir+'facenet512_embeddings.pkl'
output_album_dir = base_dir+'albums_dbscan'
custom_source_path = base_dir+'/Cropped_Faces_Align'
n_clusters = 9  # <--- SET THE NUMBER OF CLUSTERS (NUMBER OF PEOPLE)

try:
    with open(embeddings_file_path, 'rb') as f:
        embeddings_dict = pickle.load(f)
    print(f"Successfully loaded {len(embeddings_dict)} face embeddings.")
except FileNotFoundError:
    print(f"Error: File not found at {embeddings_file_path}")
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

if num_faces == 0:
    print("No face embeddings found. Exiting.")
    exit()

# Perform K-Means Clustering
kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init='auto') # Added n_init for future compatibility
cluster_labels = kmeans.fit_predict(embedding_vectors)

# Create a dictionary to store face names for each cluster ID
clustered_faces = defaultdict(list)
for i, label in enumerate(cluster_labels):
    clustered_faces[label].append(face_names[i])

print("\nClustered Faces (using K-Means):")
for cluster_id, names in clustered_faces.items():
    print(f"Person ID: {cluster_id}")
    for name in names:
        print(f"- {name}")
    print("-" * 20)

# --- Create Albums based on Clustering ---
if not os.path.exists(output_album_dir):
    os.makedirs(output_album_dir)
    print(f"Created directory: {output_album_dir}")

print("\nOrganizing images into albums based on K-Means clustering...")
for person_id, face_filenames in clustered_faces.items():
    person_album_path = os.path.join(output_album_dir, str(person_id))

    if not os.path.exists(person_album_path):
        os.makedirs(person_album_path)
        print(f"Created album directory for Person ID '{person_id}': {person_album_path}")

    for face_filename in face_filenames:
        source_file_path = os.path.join(custom_source_path, face_filename)
        destination_file_path = os.path.join(person_album_path, os.path.basename(face_filename))

        try:
            shutil.copy2(source_file_path, destination_file_path)
            # print(f"Copied '{os.path.basename(face_filename)}' to '{person_album_path}'")
        except FileNotFoundError:
            print(f"Warning: Source file not found: {source_file_path}")
        except Exception as e:
            print(f"Error copying '{os.path.basename(face_filename)}': {e}")

print("\nImage organization based on K-Means clustering complete!")