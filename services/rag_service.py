from typing import List, Dict, Any
from .retrieval_service import retrieval_service
from .gemini_client import gemini_client
import logging

logger = logging.getLogger(__name__)

class RAGService:
    def __init__(self):
        pass

    def generate_debug_response(self, project_id: int, error_message: str, 
                              code_snippet: str = None, file_path: str = None, 
                              additional_context: str = None) -> Dict[str, Any]:
        """Generate a debug response using RAG"""
        try:
            # Step 1: Retrieve relevant context
            similar_errors = retrieval_service.retrieve_similar_errors(project_id, error_message)
            documentation = retrieval_service.retrieve_relevant_documentation(project_id, error_message)
            code_suggestions = retrieval_service.get_code_suggestions(project_id, error_message, code_snippet)
            
            # Step 2: Build context for the LLM
            context = self._build_context(
                similar_errors, 
                documentation, 
                code_suggestions,
                code_snippet,
                file_path,
                additional_context
            )
            
            # Step 3: Generate response using Gemini
            prompt = self._build_debug_prompt(error_message, context)
            response = gemini_client.generate(prompt, context)
            
            # Step 4: Calculate confidence (simplified)
            confidence = self._calculate_confidence(similar_errors, response)
            
            return {
                "solution": response,
                "context": {
                    "similar_errors": similar_errors,
                    "documentation": documentation,
                    "code_suggestions": code_suggestions
                },
                "confidence": confidence
            }
            
        except Exception as e:
            logger.error(f"Failed to generate debug response: {e}")
            return {
                "solution": "Sorry, I encountered an error while processing your request.",
                "context": {},
                "confidence": 0.0
            }

    def _build_context(self, similar_errors: List[Dict[str, Any]], 
                      documentation: List[Dict[str, Any]], 
                      code_suggestions: List[str],
                      code_snippet: str = None,
                      file_path: str = None,
                      additional_context: str = None) -> List[str]:
        """Build context for the LLM from retrieved information"""
        context = []
        
        # Add similar errors
        if similar_errors:
            context.append("Similar errors found in project history:")
            for error in similar_errors[:3]:  # Limit to top 3
                context.append(f"- Commit {error['metadata'].get('hash', 'unknown')}: {error['content']}")
        
        # Add documentation
        if documentation:
            context.append("Relevant documentation:")
            for doc in documentation[:2]:  # Limit to top 2
                context.append(f"- {doc['content']}")
        
        # Add code suggestions
        if code_suggestions:
            context.append("General code suggestions:")
            for suggestion in code_suggestions[:3]:  # Limit to top 3
                context.append(f"- {suggestion}")
        
        # Add current code context
        if code_snippet:
            context.append(f"Current code snippet:\n{code_snippet}")
        
        if file_path:
            context.append(f"File path: {file_path}")
            
        if additional_context:
            context.append(f"Additional context: {additional_context}")
            
        return context

    def _build_debug_prompt(self, error_message: str, context: List[str] = None) -> str:
        """Build a prompt for debugging"""
        base_prompt = f"""You are an expert software developer helping to debug an issue.

Error: {error_message}

Please provide a helpful solution to fix this error. Be specific and provide code examples if appropriate.

Consider the following context from the project's history and documentation:
"""
        
        if context:
            context_str = "\n".join(context)
            return f"{base_prompt}\n{context_str}\n\nSolution:"
        else:
            return f"{base_prompt}\n\nSolution:"

    def _calculate_confidence(self, similar_errors: List[Dict[str, Any]], response: str) -> float:
        """Calculate confidence score for the response"""
        if not similar_errors:
            return 0.3  # Low confidence if no similar errors found
        
        # Calculate average similarity of retrieved errors
        avg_similarity = sum(error.get('distance', 0) for error in similar_errors) / len(similar_errors)
        
        # Adjust based on response quality (simplified)
        quality_indicator = 1.0 if any(keyword in response.lower() for keyword in ["fix", "solution", "try", "change"]) else 0.5
        
        return min(0.9, avg_similarity * quality_indicator)

rag_service = RAGService()