# risk/nlp_service.py

import numpy as np
from sentence_transformers import SentenceTransformer
from typing import List

class NLPEmbeddingService:
    """
    Utility class to load a Sentence Transformer model and generate 
    L2-normalized embeddings for GRC text data (Policies, Risks, Requirements).
    """

    # Using a model optimized for high-quality sentence embeddings, suitable
    # for similarity calculations (e.g., auto-mapping regulations).
    MODEL_NAME = 'all-MiniLM-L6-v2' 
    MODEL = None
    
    @classmethod
    def initialize_model(cls) -> SentenceTransformer:
        """Loads the model into memory (lazy loading and singleton pattern)."""
        if cls.MODEL is None:
            print(f"Loading SentenceTransformer model: {cls.MODEL_NAME}...")
            # Loads the model from Hugging Face/disk
            cls.MODEL = SentenceTransformer(cls.MODEL_NAME)
            # Set model to evaluation mode (important for production efficiency)
            cls.MODEL.eval()
            print("BERT-based model loaded successfully.")
        return cls.MODEL

    @classmethod
    def get_embedding(cls, text: str) -> List[float]:
        """
        Generates a vector embedding for the input text and applies L2 normalization.
        
        Args:
            text: The GRC text (e.g., Risk description or Policy title).
            
        Returns:
            A list of floats representing the L2-normalized embedding vector.
        """
        if not text:
            # Returns an empty vector if input is empty
            return []

        model = cls.initialize_model()
        
        # 1. Encode text to get embedding (returns a numpy array)
        embedding: np.ndarray = model.encode(text, convert_to_tensor=False)
        
        # 2. Apply L2 Normalization
        # L2 normalization ensures all vectors lie on a unit sphere, making 
        # cosine similarity calculation direct and accurate.
        norm = np.linalg.norm(embedding)
        if norm > 0:
            embedding = embedding / norm

        # 3. Convert to a list of floats for easy JSON/PostgreSQL/Neo4j storage
        return embedding.tolist()

    @classmethod
    def get_dimension(cls) -> int:
        """Returns the fixed dimension of the embedding vector (384 for this model)."""
        model = cls.initialize_model()
        return model.get_sentence_embedding_dimension()


# Example Usage (for testing/demonstration)
if __name__ == '__main__':
    # Initializing model takes a moment on first call
    print(f"Model dimension: {NLPEmbeddingService.get_dimension()}")
    
    policy_text = "The Information Security Policy requires MFA for all remote access to critical systems."
    requirement_text = "PENCOM ICT guidelines mandate multi-factor authentication for remote access."

    policy_vector = NLPEmbeddingService.get_embedding(policy_text)
    requirement_vector = NLPEmbeddingService.get_embedding(requirement_text)

    print(f"\nPolicy Vector (first 5 elements): {policy_vector[:5]}")
    print(f"Requirement Vector (first 5 elements): {requirement_vector[:5]}")
    
    # Calculate Cosine Similarity to demonstrate effectiveness
    if policy_vector and requirement_vector:
        similarity = np.dot(policy_vector, requirement_vector)
        print(f"\nCosine Similarity: {similarity:.4f} (Closer to 1.0 means highly related)")