from typing import List, Dict, Any
import numpy as np
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class ReferenceRanking:
    def __init__(self):
        # Default ranking weights
        self.default_weights = {
            'semantic_similarity': 0.6,
            'proximity': 0.2,
            'recency': 0.1,
            'usage': 0.08,
            'test_boost': 0.02
        }
        
        # Lambda for recency decay
        self.recency_lambda = 0.1  # ~10 day half-life

    def rank_references(self, reference_candidates: List[Dict[str, Any]], 
                       error_embedding: List[float] = None,
                       params: Dict[str, float] = None) -> List[Dict[str, Any]]:
        """Rank reference candidates using multiple factors"""
        if not reference_candidates:
            return []
        
        weights = params or self.default_weights
        
        ranked_candidates = []
        for candidate in reference_candidates:
            score = self._calculate_score(candidate, error_embedding, weights)
            ranked_candidates.append({
                **candidate,
                'ranking_score': score
            })
        
        # Sort by score descending
        ranked_candidates.sort(key=lambda x: x['ranking_score'], reverse=True)
        return ranked_candidates

    def _calculate_score(self, candidate: Dict[str, Any], 
                        error_embedding: List[float], 
                        weights: Dict[str, float]) -> float:
        """Calculate composite ranking score"""
        scores = {
            'semantic_similarity': self._semantic_similarity_score(candidate, error_embedding),
            'proximity': self._proximity_score(candidate),
            'recency': self._recency_score(candidate),
            'usage': self._usage_score(candidate),
            'test_boost': self._test_boost_score(candidate)
        }
        
        # Weighted sum
        total_score = 0.0
        for factor, weight in weights.items():
            total_score += scores[factor] * weight
        
        return total_score

    def _semantic_similarity_score(self, candidate: Dict[str, Any], 
                                 error_embedding: List[float]) -> float:
        """Calculate semantic similarity score"""
        if not error_embedding or 'embedding' not in candidate:
            return 0.5  # Neutral score if no embedding available
        
        try:
            # Cosine similarity between error and candidate embeddings
            candidate_embedding = candidate['embedding']
            if not candidate_embedding or len(candidate_embedding) != len(error_embedding):
                return 0.5
                
            dot_product = np.dot(error_embedding, candidate_embedding)
            norm_a = np.linalg.norm(error_embedding)
            norm_b = np.linalg.norm(candidate_embedding)
            
            if norm_a == 0 or norm_b == 0:
                return 0.0
                
            return float(dot_product / (norm_a * norm_b))
            
        except Exception as e:
            logger.error(f"Failed to calculate semantic similarity: {e}")
            return 0.5

    def _proximity_score(self, candidate: Dict[str, Any]) -> float:
        """Calculate proximity score based on call distance"""
        call_distance = candidate.get('call_distance', 2)  # Default to max distance
        return 1.0 / (1.0 + call_distance)  # Inverse relationship

    def _recency_score(self, candidate: Dict[str, Any]) -> float:
        """Calculate recency score based on last modification"""
        last_modified = candidate.get('last_modified')
        if not last_modified:
            return 0.5
            
        try:
            if isinstance(last_modified, str):
                last_modified = datetime.fromisoformat(last_modified.replace('Z', '+00:00'))
            
            days_since_modification = (datetime.now() - last_modified).days
            return float(np.exp(-self.recency_lambda * days_since_modification))
            
        except Exception as e:
            logger.error(f"Failed to calculate recency score: {e}")
            return 0.5

    def _usage_score(self, candidate: Dict[str, Any]) -> float:
        """Calculate usage score based on usage count"""
        usage_count = candidate.get('usage_count', 0)
        return float(np.log(1 + usage_count) / 10.0)  # Log scaling, capped

    def _test_boost_score(self, candidate: Dict[str, Any]) -> float:
        """Calculate test boost score if candidate is a test"""
        file_path = candidate.get('file_path', '')
        is_test = any(test_indicator in file_path.lower() 
                     for test_indicator in ['test', 'spec', 'testing'])
        return 1.2 if is_test else 1.0

    def update_weights_from_feedback(self, positive_examples: List[Dict[str, Any]],
                                   negative_examples: List[Dict[str, Any]]):
        """Update ranking weights based on user feedback"""
        # Simple reinforcement learning approach
        # This would be implemented based on collected feedback data
        pass

# Global ranking instance
reference_ranking = ReferenceRanking()