import pickle
import numpy as np
import os
import shutil
from sklearn.metrics.pairwise import cosine_similarity
from collections import defaultdict

def cluster_faces_first_match(base_directory, threshold=0.575):
    """
    Clusters face embeddings by assigning each unclustered face to the
    first existing cluster it exceeds the similarity threshold with.

    Args:
        base_directory (str): Base directory containing
                               'facenet512_embeddings.pkl' and 'Cropped_Faces_Align'.
        threshold (float, optional): Similarity threshold for clustering.
                                     Defaults to 0.575.

    Returns:
        dict: A dictionary where keys are cluster IDs (integers) and
              values are lists of face names. Returns an empty dict on error.
    """
    file_path = os.path.join(base_directory, 'facenet512_embeddings.pkl')
    output_album_dir = os.path.join(base_directory, 'albums')
    custom_source_path = os.path.join(base_directory, 'Cropped_Faces_Align')

    try:
        with open(file_path, 'rb') as f:
            embeddings_dict = pickle.load(f)
        print(f"Successfully loaded {len(embeddings_dict)} face embeddings.")
    except FileNotFoundError:
        print(f"Error: File not found at {file_path}")
        return {}
    except pickle.UnpicklingError:
        print("Error: The file does not contain a valid pickled dictionary.")
        return {}
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return {}

    if not embeddings_dict:
        print("No face embeddings loaded.")
        return {}

    face_names = list(embeddings_dict.keys())
    embedding_vectors = np.array(list(embeddings_dict.values()))
    num_faces = len(face_names)

    if num_faces == 0:
        print("No face embeddings found.")
        return {}

    face_clusters = [-1] * num_faces
    next_cluster_id = 0

    print("\nInitial clustering of faces (first match above threshold)...")
    for i in range(num_faces):
        if face_clusters[i] == -1:
            face_clusters[i] = next_cluster_id
            for j in range(i + 1, num_faces):
                if face_clusters[j] == -1:
                    similarity = cosine_similarity(embedding_vectors[i].reshape(1, -1), embedding_vectors[j].reshape(1, -1))[0][0]
                    if similarity > threshold:
                        face_clusters[j] = next_cluster_id
            next_cluster_id += 1

    clustered_faces = defaultdict(list)
    for i, cluster_id in enumerate(face_clusters):
        clustered_faces[cluster_id].append(face_names[i])
    return dict(clustered_faces)


def refine_clusters_by_highest_similarity(initial_clusters, base_directory, threshold=0.575):
    """Refines clusters by reassigning each face to the cluster with which
    it has the highest similarity.

    Args:
        initial_clusters (dict):  A dictionary representing the initial clusters,
                                  where keys are cluster IDs and values are lists of face names.
        base_directory (str):  Base directory.
        threshold (float): The similarity threshold.

    Returns:
        dict: A dictionary representing the refined clusters.  Empty dict on error.
    """

    file_path = os.path.join(base_directory, 'facenet512_embeddings.pkl')
    try:
        with open(file_path, 'rb') as f:
            embeddings_dict = pickle.load(f)
    except Exception as e:
        print(f"Error loading embeddings: {e}")
        return {}

    face_names = list(embeddings_dict.keys())
    embedding_vectors = np.array(list(embeddings_dict.values()))
    num_faces = len(face_names)
    if num_faces == 0:
        return {}

    # Invert the initial_clusters dictionary for efficient lookup
    face_to_cluster = {}
    for cluster_id, names in initial_clusters.items():
        for name in names:
            face_to_cluster[name] = cluster_id

    new_clusters = defaultdict(list)
    cluster_changed = False  # Flag to track if any changes occurred

    print("\nRefining clusters based on highest similarity...")
    for i, face_name in enumerate(face_names):
        best_cluster = face_to_cluster[face_name]  # Start with original cluster
        highest_similarity = -1

        for cluster_id, cluster_faces in initial_clusters.items():
            if cluster_id == face_to_cluster[face_name]:
                continue  # Skip comparison with current cluster

            for cluster_face_name in cluster_faces:
                cluster_face_index = face_names.index(cluster_face_name)
                similarity = cosine_similarity(
                    embedding_vectors[i].reshape(1, -1),
                    embedding_vectors[cluster_face_index].reshape(1, -1)
                )[0][0]
                if similarity > highest_similarity:
                    highest_similarity = similarity
                    best_cluster = cluster_id

        if highest_similarity > threshold and best_cluster != face_to_cluster[face_name]:
            cluster_changed = True
            new_clusters[best_cluster].append(face_name)
            print(f"Reassigned {face_name} from cluster {face_to_cluster[face_name]} to {best_cluster}")
        else:
            new_clusters[face_to_cluster[face_name]].append(face_name)  # Keep in original

    if not cluster_changed:
        print("No cluster reassignment occurred during refinement.")
    return dict(new_clusters)

def create_albums_from_clusters(clusters, base_directory):
    """Creates album directories and copies face images based on cluster assignments.

    Args:
        clusters (dict): A dictionary representing the clusters.
        base_directory (str):  Base directory.
    """
    output_album_dir = os.path.join(base_directory, 'albums')
    custom_source_path = os.path.join(base_directory, 'Cropped_Faces_Align')

    # Create the main albums directory if it doesn't exist
    if not os.path.exists(output_album_dir):
        os.makedirs(output_album_dir)
        print(f"Created directory: {output_album_dir}")

    print("\nOrganizing images into albums...")
    for person_id, face_filenames in clusters.items():
        person_album_path = os.path.join(output_album_dir, str(person_id))

        # Create the person's album directory if it doesn't exist
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
    print("\nImage organization complete!")



if __name__ == '__main__':
    base_directory = '../Cropped_Events/event_1/'
    initial_clusters = cluster_faces_first_match(base_directory)

    if initial_clusters:
        print("\nInitial Clusters:")
        print(initial_clusters)
        create_albums_from_clusters(initial_clusters, base_directory)
        # refined_clusters = refine_clusters_by_highest_similarity(initial_clusters, base_directory)
        # if refined_clusters:
        #     print("\nRefined Clusters:")
        #     print(refined_clusters)
        #     create_albums_from_clusters(refined_clusters, base_directory)
        # else:
        #     print("Cluster refinement failed.")
        #     create_albums_from_clusters(initial_clusters, base_directory) #create albums even if refinement fails
    else:
        print("Initial clustering failed.")
