# import pickle
# import sys
# import matplotlib.pyplot as plt
# import numpy as np
# from collections import defaultdict
# from sklearn.manifold import TSNE
# from sklearn.decomposition import PCA


# pkl_files = [
#     "Cropped_Events/event_10/facenet512_embeddings.pkl",
#     "Cropped_Events/event_10/clustered_faces.pkl"
# ]

# def peek_pkl(filepath):
#     """Safely view contents of a .pkl file"""
#     with open(filepath, 'rb') as f:
#         data = pickle.load(f)
    
#     print(f"\n=== Contents of {filepath} ===")
#     print(f"Dictionary with {len(data)} items:")
#     print(f"Data type: {type(data)}")
#     # print("====RAW===\n",data)
#     if isinstance(data, dict):
#         print("\nDictionary Structure:")
#         for key, value in list(data.items())[:3]:  # Show first 3 items
#             print(f"Key: {key} | Value type: {type(value)}")
#             if isinstance(value, np.ndarray):
#                 print(f"  Array shape: {value.shape}")
    
#     elif isinstance(data, np.ndarray):
#         print(f"Array shape: {data.shape}")
#         print("First 3 rows:")
#         print(data[:3])
    
#     else:
#         print("Sample data:", str(data)[:200] + ("..." if len(str(data)) > 200 else ""))

# # Usage
# peek_pkl(pkl_files[0]) 
# peek_pkl(pkl_files[1])


# # --- Load Pickle Files ---
# with open(pkl_files[0], "rb") as f:
#     embeddings_dict = pickle.load(f)

# with open(pkl_files[1], "rb") as f:
#     clustered_faces = pickle.load(f)

# # --- Prepare Data for Visualization ---
# embeddings = []
# labels = []

# for cluster_id, face_files in clustered_faces.items():
#     for face_file in face_files:
#         if face_file in embeddings_dict:
#             embeddings.append(embeddings_dict[face_file])
#             labels.append(cluster_id)

# embeddings = np.array(embeddings)
# labels = np.array(labels)

# # --- Dimensionality Reduction ---
# # Use PCA first (for speed), then t-SNE
# pca = PCA(n_components=10)  # or 15, or even just 2 to skip t-SNE
# pca_result = pca.fit_transform(embeddings)

# tsne = TSNE(n_components=2, perplexity=15, random_state=42)
# reduced = tsne.fit_transform(pca_result)

# # --- Plot ---
# plt.figure(figsize=(10, 8))
# unique_labels = sorted(set(labels))
# for label in unique_labels:
#     idxs = labels == label
#     plt.scatter(reduced[idxs, 0], reduced[idxs, 1], label=f'Cluster {label}', alpha=0.7)

# plt.legend()
# plt.title("FaceNet Embedding Clusters (t-SNE 2D)")
# plt.xlabel("Component 1")
# plt.ylabel("Component 2")
# plt.grid(True)
# plt.tight_layout()

# # Save the figure
# plt.savefig("embedding_clusters.png", dpi=300)

# # Optionally show it (if your environment supports it)
# plt.show()


import pickle
import sys
import numpy

event_path = f"Cropped_Events/event_11"
print(f"{event_path}/clustered_faces.pkl")
with open(f"{event_path}/clustered_faces.pkl", "rb") as f:
    clustered_faces = pickle.load(f)