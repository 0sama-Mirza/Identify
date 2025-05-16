import pickle
import numpy as np
import hdbscan
from collections import defaultdict
import os
import shutil
from sklearn.metrics.pairwise import cosine_distances

def cluster_faces_hdbscan(base_directory, min_cluster_size=3, min_samples=None):
    """
    Clusters face embeddings using HDBSCAN with precomputed cosine distances
    and organizes the corresponding face images into albums.

    Args:
        base_directory (str): The base directory containing the
                                'facenet512_embeddings.pkl' file and the
                                'Cropped_Faces_Align' subdirectory.
        min_cluster_size (int): The minimum size of clusters for HDBSCAN.
        min_samples (int, optional): Controls the robustness of clustering to noise.
                                     If None, it defaults to the minimum cluster size.
    """
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

    # Calculate the pairwise cosine distance matrix
    distance_matrix = cosine_distances(embedding_vectors)

    # Perform HDBSCAN Clustering with precomputed distances
    clusterer = hdbscan.HDBSCAN(min_cluster_size=min_cluster_size, min_samples=min_samples, metric='precomputed')
    cluster_labels = clusterer.fit_predict(distance_matrix)

    # Create a dictionary to store face names for each cluster ID
    clustered_faces = defaultdict(list)
    for i, label in enumerate(cluster_labels):
        clustered_faces[label].append(face_names[i])

    print("\nClustered Faces (using HDBSCAN with precomputed cosine distances):")
    for cluster_id, names in clustered_faces.items():
        print(f"Person ID: {cluster_id}")
        for name in names:
            print(f"- {name}")
        print("-" * 20)

    print(clustered_faces)
    
    # Save clustered_faces dictionary to a .pkl file
    clustered_faces_path = os.path.join(base_directory, 'clustered_faces.pkl')
    try:
        with open(clustered_faces_path, 'wb') as f:
            pickle.dump(clustered_faces, f)
        print(f"\nClustered faces saved to '{clustered_faces_path}'")
    except Exception as e:
        print(f"Failed to save clustered_faces.pkl: {e}")

    # --- Create Albums based on Clustering ---
    if not os.path.exists(output_album_dir):
        os.makedirs(output_album_dir)
        print(f"Created directory: {output_album_dir}")

    print("\nOrganizing images into albums based on HDBSCAN clustering...")
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
    return clustered_faces
    print("\nImage organization based on HDBSCAN clustering complete!")