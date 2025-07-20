from typing import List, Dict, Any, Optional, Tuple
import numpy as np
from sentence_transformers import SentenceTransformer
import torch
from sklearn.metrics.pairwise import cosine_similarity
import json
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class EmbeddingService:
    """Service for creating and managing vector embeddings for semantic search"""
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """
        Initialize the embedding service with a sentence transformer model.
        
        Args:
            model_name: Name of the sentence transformer model to use
        """
        self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
        logger.info(f"Loading embedding model {model_name} on {self.device}")
        self.model = SentenceTransformer(model_name, device=self.device)
        self.embedding_dimension = self.model.get_sentence_embedding_dimension()
        
    def create_embedding(self, text: str) -> List[float]:
        """
        Create an embedding vector for a given text.
        
        Args:
            text: The text to embed
            
        Returns:
            List of floats representing the embedding vector
        """
        if not text or not text.strip():
            return [0.0] * self.embedding_dimension
            
        # Create embedding
        embedding = self.model.encode(text, convert_to_numpy=True)
        return embedding.tolist()
    
    def create_batch_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Create embeddings for multiple texts at once.
        
        Args:
            texts: List of texts to embed
            
        Returns:
            List of embedding vectors
        """
        if not texts:
            return []
            
        # Filter out empty texts
        valid_texts = [text for text in texts if text and text.strip()]
        if not valid_texts:
            return [[0.0] * self.embedding_dimension] * len(texts)
            
        # Create embeddings
        embeddings = self.model.encode(valid_texts, convert_to_numpy=True)
        
        # Map back to original indices
        result = []
        valid_idx = 0
        for text in texts:
            if text and text.strip():
                result.append(embeddings[valid_idx].tolist())
                valid_idx += 1
            else:
                result.append([0.0] * self.embedding_dimension)
                
        return result
    
    def create_memory_embedding(self, memory_content: str, metadata: Dict[str, Any]) -> List[float]:
        """
        Create an enhanced embedding for a memory by combining content and metadata.
        
        Args:
            memory_content: The main memory content
            metadata: Additional metadata to include in the embedding
            
        Returns:
            Enhanced embedding vector
        """
        # Build enhanced text representation
        enhanced_text_parts = [memory_content]
        
        # Add entities to enhance semantic understanding
        if metadata.get("entities"):
            for entity in metadata["entities"]:
                if entity["type"] in ["person", "place", "activity"]:
                    enhanced_text_parts.append(f'{entity["type"]}: {entity["value"]}')
        
        # Add emotions for emotional context
        if metadata.get("emotions"):
            enhanced_text_parts.append(f'emotions: {", ".join(metadata["emotions"])}')
        
        # Add time context if available
        if metadata.get("time_info") and metadata["time_info"].get("has_time"):
            time_str = metadata["time_info"].get("original", "")
            if time_str:
                enhanced_text_parts.append(f'time: {time_str}')
        
        # Combine all parts
        enhanced_text = " | ".join(enhanced_text_parts)
        
        return self.create_embedding(enhanced_text)
    
    def calculate_similarity(self, embedding1: List[float], embedding2: List[float]) -> float:
        """
        Calculate cosine similarity between two embeddings.
        
        Args:
            embedding1: First embedding vector
            embedding2: Second embedding vector
            
        Returns:
            Similarity score between 0 and 1
        """
        if not embedding1 or not embedding2:
            return 0.0
            
        # Convert to numpy arrays
        vec1 = np.array(embedding1).reshape(1, -1)
        vec2 = np.array(embedding2).reshape(1, -1)
        
        # Calculate cosine similarity
        similarity = cosine_similarity(vec1, vec2)[0][0]
        
        # Ensure similarity is between 0 and 1
        return max(0.0, min(1.0, float(similarity)))
    
    def find_similar_embeddings(
        self,
        query_embedding: List[float],
        embeddings: List[Tuple[str, List[float]]],
        threshold: float = 0.5,
        top_k: Optional[int] = None
    ) -> List[Tuple[str, float]]:
        """
        Find embeddings similar to a query embedding.
        
        Args:
            query_embedding: The query embedding vector
            embeddings: List of (id, embedding) tuples to search
            threshold: Minimum similarity threshold
            top_k: Return only top K results
            
        Returns:
            List of (id, similarity_score) tuples sorted by similarity
        """
        if not query_embedding or not embeddings:
            return []
        
        # Calculate similarities
        similarities = []
        query_vec = np.array(query_embedding).reshape(1, -1)
        
        for id, embedding in embeddings:
            if embedding:
                emb_vec = np.array(embedding).reshape(1, -1)
                similarity = cosine_similarity(query_vec, emb_vec)[0][0]
                
                if similarity >= threshold:
                    similarities.append((id, float(similarity)))
        
        # Sort by similarity score
        similarities.sort(key=lambda x: x[1], reverse=True)
        
        # Return top K if specified
        if top_k:
            return similarities[:top_k]
        
        return similarities
    
    def create_query_embedding(self, query: str, context: Optional[Dict[str, Any]] = None) -> List[float]:
        """
        Create an embedding for a search query with optional context enhancement.
        
        Args:
            query: The search query
            context: Optional context to enhance the query
            
        Returns:
            Query embedding vector
        """
        enhanced_query = query
        
        if context:
            # Add temporal context
            if context.get("time_range"):
                enhanced_query += f" time: {context['time_range']}"
            
            # Add type context
            if context.get("memory_type"):
                enhanced_query += f" type: {context['memory_type']}"
            
            # Add entity context
            if context.get("entities"):
                for entity in context["entities"]:
                    enhanced_query += f" {entity['type']}: {entity['value']}"
        
        return self.create_embedding(enhanced_query)
    
    def update_memory_relationships(
        self,
        memory_id: str,
        memory_embedding: List[float],
        all_embeddings: List[Tuple[str, List[float]]],
        threshold: float = 0.7
    ) -> List[Tuple[str, float]]:
        """
        Find related memories based on embedding similarity.
        
        Args:
            memory_id: ID of the memory to find relationships for
            memory_embedding: Embedding of the memory
            all_embeddings: All other memory embeddings
            threshold: Similarity threshold for relationships
            
        Returns:
            List of (related_memory_id, strength) tuples
        """
        # Filter out the memory itself
        other_embeddings = [(id, emb) for id, emb in all_embeddings if id != memory_id]
        
        # Find similar memories
        relationships = self.find_similar_embeddings(
            memory_embedding,
            other_embeddings,
            threshold=threshold,
            top_k=10  # Limit to 10 strongest relationships
        )
        
        return relationships
    
    def cluster_embeddings(
        self,
        embeddings: List[Tuple[str, List[float]]],
        n_clusters: int = 5
    ) -> Dict[int, List[str]]:
        """
        Cluster embeddings to find memory groups.
        
        Args:
            embeddings: List of (id, embedding) tuples
            n_clusters: Number of clusters to create
            
        Returns:
            Dictionary mapping cluster_id to list of memory_ids
        """
        if not embeddings or len(embeddings) < n_clusters:
            return {0: [id for id, _ in embeddings]}
        
        from sklearn.cluster import KMeans
        
        # Extract embedding vectors
        ids = [id for id, _ in embeddings]
        vectors = np.array([emb for _, emb in embeddings])
        
        # Perform clustering
        kmeans = KMeans(n_clusters=n_clusters, random_state=42)
        cluster_labels = kmeans.fit_predict(vectors)
        
        # Group by cluster
        clusters = {}
        for idx, cluster_id in enumerate(cluster_labels):
            if cluster_id not in clusters:
                clusters[cluster_id] = []
            clusters[cluster_id].append(ids[idx])
        
        return clusters