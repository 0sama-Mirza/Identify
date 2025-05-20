import pickle
import numpy as np
import hdbscan
from collections import defaultdict
import os
import shutil
from sklearn.metrics.pairwise import cosine_distances, cosine_similarity

def cluster_faces_hdbscan(base_directory, min_cluster_size=3, min_samples=None, similarity_threshold=0.6):
    embeddings_file_path = os.path.join(base_directory, 'facenet512_embeddings.pkl')
    output_album_dir = os.path.join(base_directory, 'albums_dbscan')
    custom_source_path = os.path.join(base_directory, 'Cropped_Faces_Align')

    try:
        with open(embeddings_file_path, 'rb') as f:
            embeddings_dict = pickle.load(f)
        print(f"Successfully loaded {len(embeddings_dict)} face embeddings from '{embeddings_file_path}'.")
    except FileNotFoundError:
        print(f"Error: File not found at {embeddings_file_path}")
        return
    except pickle.UnpicklingError:
        print("Error: The file does not contain a valid pickled dictionary.")
        return
    except Exception as e:
        print(f"An unexpected error occurred while loading embeddings: {e}")
        return

    if not embeddings_dict:
        print("No face embeddings loaded. Exiting clustering.")
        return

    face_names = list(embeddings_dict.keys())
    embedding_vectors = np.array(list(embeddings_dict.values()))
    num_faces = len(face_names)

    if num_faces == 0:
        print("No face embeddings found. Exiting clustering.")
        return

    # Step 1: Compute cosine distance matrix
    distance_matrix = cosine_distances(embedding_vectors)

    # Step 2: Run HDBSCAN with loosened selection epsilon
    clusterer = hdbscan.HDBSCAN(
        min_cluster_size=min_cluster_size,
        min_samples=min_samples,
        metric='precomputed',
        cluster_selection_epsilon=0.1  # Loosen cluster merging threshold
    )
    cluster_labels = clusterer.fit_predict(distance_matrix)

    # Step 3: Group faces by cluster label
    clustered_faces = defaultdict(list)
    label_to_indices = defaultdict(list)
    for i, label in enumerate(cluster_labels):
        clustered_faces[label].append(face_names[i])
        label_to_indices[label].append(i)

    # Step 4: Compute centroids for merging similar clusters
    centroids = {}
    for label, indices in label_to_indices.items():
        if label == -1:
            continue  # Skip noise
        vectors = embedding_vectors[indices]
        centroids[label] = np.mean(vectors, axis=0)

    labels = list(centroids.keys())
    merged = {}
    for i in range(len(labels)):
        for j in range(i + 1, len(labels)):
            sim = cosine_similarity([centroids[labels[i]]], [centroids[labels[j]]])[0][0]
            if sim >= similarity_threshold:
                merged.setdefault(labels[i], set()).add(labels[j])
                merged.setdefault(labels[j], set()).add(labels[i])

    # Union-find to flatten merged groups
    def find(label, parent):
        while parent[label] != label:
            label = parent[label]
        return label

    parent = {label: label for label in labels}
    for label, neighbors in merged.items():
        for neighbor in neighbors:
            parent1 = find(label, parent)
            parent2 = find(neighbor, parent)
            if parent1 != parent2:
                parent[parent2] = parent1

    label_mapping = {}
    for label in labels:
        root = find(label, parent)
        label_mapping[label] = root

    # Step 5: Remap clusters with merged labels
    final_clustered_faces = defaultdict(list)
    for i, label in enumerate(cluster_labels):
        new_label = label_mapping.get(label, label)
        final_clustered_faces[new_label].append(face_names[i])

    print("\nClustered Faces (merged by centroid similarity):")
    for cluster_id, names in final_clustered_faces.items():
        print(f"Person ID: {cluster_id}")
        for name in names:
            print(f"- {name}")
        print("-" * 20)

    # Save to pickle
    clustered_faces_path = os.path.join(base_directory, 'clustered_faces.pkl')
    try:
        with open(clustered_faces_path, 'wb') as f:
            pickle.dump(final_clustered_faces, f)
        print(f"\nClustered faces saved to '{clustered_faces_path}'")
    except Exception as e:
        print(f"Failed to save clustered_faces.pkl: {e}")

    # Create albums
    if not os.path.exists(output_album_dir):
        os.makedirs(output_album_dir)
        print(f"Created directory: {output_album_dir}")

    print("\nOrganizing images into albums based on merged clustering...")
    for person_id, face_filenames in final_clustered_faces.items():
        person_album_path = os.path.join(output_album_dir, str(person_id))

        if not os.path.exists(person_album_path):
            os.makedirs(person_album_path)
            print(f"Created album directory for Person ID '{person_id}': {person_album_path}")

        for face_filename in face_filenames:
            source_file_path = os.path.join(custom_source_path, face_filename)
            destination_file_path = os.path.join(person_album_path, os.path.basename(face_filename))

            try:
                shutil.copy2(source_file_path, destination_file_path)
            except FileNotFoundError:
                print(f"Warning: Source file not found: {source_file_path}")
            except Exception as e:
                print(f"Error copying '{os.path.basename(face_filename)}': {e}")

    print("\nImage organization based on merged HDBSCAN clustering complete!")
    return final_clustered_faces
