import faiss
import numpy as np
import pickle
import os
from tqdm import tqdm

class FAISSProcessor:
    def __init__(self, n_clusters=100):
        self.index = None
        self.dimension = 512  # FaceNet embedding size
        self.n_clusters = n_clusters
        self.faiss_params = {
            'nprobe': 10,       # Number of clusters to search (speed/accuracy tradeoff)
            'use_float16': True  # Store embeddings in 16-bit format (half memory)
        }

    def build_index(self, embeddings_path, output_folder):
        """Convert .pkl embeddings to FAISS index"""
        try:
            with open(embeddings_path, 'rb') as f:
                embeddings_dict = pickle.load(f)
            
            if not embeddings_dict:  # Add this check
                raise ValueError("Empty embeddings dictionary")
        
            # Convert to array
            all_embeddings = []
            self.group_map = []
            for group, embs in embeddings_dict.items():
                all_embeddings.extend(embs)
                self.group_map.extend([group]*len(embs))
            
            embeddings_array = np.array(all_embeddings).astype('float32')
            
            # Build optimized index
            quantizer = faiss.IndexFlatL2(self.dimension)
            self.index = faiss.IndexIVFFlat(quantizer, self.dimension, self.n_clusters)
            self.index.train(embeddings_array)
            self.index.add(embeddings_array)
            
            # Save artifacts
            os.makedirs(output_folder, exist_ok=True)
            faiss.write_index(self.index, f"{output_folder}/faiss_index.bin")
            np.save(f"{output_folder}/group_map.npy", self.group_map)
            return True
        except Exception as e:
            print(f"FAISS build failed: {str(e)}")
            return False  # Always return bool

    def search_embedding(self, query_embedding, top_k=5):
        """Production-grade search with validation"""
        # Validate index state
        if self.index is None:
            raise RuntimeError("FAISS index not initialized")
        
        # Validate input shape
        query = np.array(query_embedding, dtype='float32')
        if query.shape != (1, self.dimension):
            raise ValueError(f"Embedding must be shape (1, 512), got {query.shape}")
        
        # Configure search precision
        self.index.nprobe = self.faiss_params['nprobe']  # Controls search depth
        
        # Execute search
        distances, indices = self.index.search(query, top_k)
        
        # Format results safely
        return [
            (self.group_map[i], float(1/(1+d)))  # Convert to Python native float
            for i, d in zip(indices[0], distances[0])
            if i != -1  # Skip invalid indices
        ]