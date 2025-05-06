import pickle
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.cluster import AgglomerativeClustering
from collections import defaultdict
import os
import shutil

# --- Configuration ---
embeddings_file_path = '../Cropped_Events/event_1/facenet_embeddings.pkl'
output_album_dir = '../Cropped_Events/event_1/albums_clustered'
custom_source_path = '../Cropped_Events/event_1/Cropped_Faces_Align'
similarity_threshold = 0.1  # Adjust this threshold to control clustering

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

# Calculate the pairwise cosine similarity matrix
similarity_matrix = cosine_similarity(embedding_vectors)

# Convert similarity to distance (1 - similarity) for clustering
distance_matrix = 1 - similarity_matrix

# Perform Agglomerative Clustering
n_clusters = None  # We will use a distance threshold instead of a fixed number of clusters
cluster = AgglomerativeClustering(
    n_clusters=n_clusters,
    linkage='average',      # You can experiment with 'ward', 'complete', 'single'
    distance_threshold=1 - similarity_threshold  # The distance threshold for merging clusters
)
cluster_labels = cluster.fit_predict(distance_matrix)

# Create a dictionary to store face names for each cluster ID
clustered_faces = defaultdict(list)
for i, label in enumerate(cluster_labels):
    clustered_faces[label].append(face_names[i])

print("\nClustered Faces (using Agglomerative Clustering):")
for cluster_id, names in clustered_faces.items():
    print(f"Person ID: {cluster_id}")
    for name in names:
        print(f"- {name}")
    print("-" * 20)

# --- Create Albums based on Clustering ---
if not os.path.exists(output_album_dir):
    os.makedirs(output_album_dir)
    print(f"Created directory: {output_album_dir}")

print("\nOrganizing images into albums based on clustering...")
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

print("\nImage organization based on clustering complete!")