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
                              additional_context: str = None,
                              use_reference_pack: bool = True) -> Dict[str, Any]:
        """Generate a debug response using RAG, optionally with reference packs"""
        try:
            if use_reference_pack and code_snippet and file_path:
                # Try to use reference pack for more precise context
                try:
                    from services.reference_service import reference_service
                    
                    # Resolve snippet to symbol and build reference pack
                    symbol_id = reference_service.resolve_snippet_to_symbol(
                        project_id, file_path, code_snippet
                    )
                    
                    if symbol_id:
                        reference_pack = reference_service.build_reference_pack(symbol_id)
                        context = self._build_context_from_reference_pack(
                            reference_pack, error_message, code_snippet, additional_context
                        )
                    else:
                        # Fallback to traditional retrieval
                        context = self._build_context_traditional(
                            project_id, error_message, code_snippet, file_path, additional_context
                        )
                except Exception as e:
                    logger.warning(f"Reference pack failed, falling back: {e}")
                    context = self._build_context_traditional(
                        project_id, error_message, code_snippet, file_path, additional_context
                    )
            else:
                # Use traditional retrieval
                context = self._build_context_traditional(
                    project_id, error_message, code_snippet, file_path, additional_context
                )
            
            # Generate response using Gemini
            prompt = self._build_debug_prompt(error_message, context)
            response = gemini_client.generate(prompt, context)
            
            # Calculate confidence
            confidence = self._calculate_confidence(context, response)
            
            return {
                "solution": response,
                "context": {
                    "similar_errors": context.get('similar_errors', []),
                    "documentation": context.get('documentation', []),
                    "code_suggestions": context.get('code_suggestions', [])
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

    def _build_context_from_reference_pack(self, reference_pack, error_message: str,
                                         code_snippet: str = None, additional_context: str = None) -> Dict[str, Any]:
        """Build context from reference pack"""
        context = {}
        
        # Add reference pack information
        context['reference_pack'] = {
            'symbol_name': reference_pack.symbol.symbol_name,
            'symbol_type': reference_pack.symbol.symbol_type,
            'file_path': reference_pack.symbol.file_path,
            'lines': f"{reference_pack.symbol.start_line}-{reference_pack.symbol.end_line}",
            'definition': reference_pack.definition,
            'references': reference_pack.references,
            'callers': reference_pack.callers,
            'callees': reference_pack.callees,
            'imports': reference_pack.imports,
            'tests': reference_pack.tests,
            'historical_fixes': reference_pack.historical_fixes,
            'token_count': reference_pack.token_count,
            'reasoning': reference_pack.reasoning
        }
        
        # Add current error context
        context['error'] = error_message
        if code_snippet:
            context['code_snippet'] = code_snippet
        if additional_context:
            context['additional_context'] = additional_context
        
        return context

    def _build_context_traditional(self, project_id: int, error_message: str,
                                 code_snippet: str = None, file_path: str = None,
                                 additional_context: str = None) -> Dict[str, Any]:
        """Traditional context building (existing implementation)"""
        similar_errors = retrieval_service.retrieve_similar_errors(project_id, error_message)
        documentation = retrieval_service.retrieve_relevant_documentation(project_id, error_message)
        code_suggestions = retrieval_service.get_code_suggestions(project_id, error_message, code_snippet)
        
        context = {
            'similar_errors': similar_errors,
            'documentation': documentation,
            'code_suggestions': code_suggestions
        }
        
        if code_snippet:
            context['code_snippet'] = code_snippet
        if file_path:
            context['file_path'] = file_path
        if additional_context:
            context['additional_context'] = additional_context
            
        return context

    def _build_debug_prompt(self, error_message: str, context: Dict[str, Any]) -> str:
        """Build a prompt for debugging"""
        base_prompt = f"""You are an expert software developer helping to debug an issue.

Error: {error_message}

Please provide a helpful solution to fix this error. Be specific and provide code examples if appropriate.

Consider the following context from the project's history and documentation:
"""
        
        if 'reference_pack' in context:
            # Use reference pack context
            ref_pack = context['reference_pack']
            context_str = f"""
Symbol: {ref_pack['symbol_name']} ({ref_pack['symbol_type']})
File: {ref_pack['file_path']}:{ref_pack['lines']}

Definition:
{ref_pack['definition']}

References found:
{ref_pack['reasoning']}

Additional context:
"""
            if 'code_snippet' in context:
                context_str += f"\nCurrent code snippet:\n{context['code_snippet']}"
            if 'additional_context' in context:
                context_str += f"\nAdditional context: {context['additional_context']}"
                
            return f"{base_prompt}\n{context_str}\n\nSolution:"
            
        else:
            # Use traditional context
            context_parts = []
            
            if 'similar_errors' in context and context['similar_errors']:
                context_parts.append("Similar errors found in project history:")
                for error in context['similar_errors'][:3]:
                    context_parts.append(f"- {error.get('content', '')[:100]}...")
            
            if 'documentation' in context and context['documentation']:
                context_parts.append("Relevant documentation:")
                for doc in context['documentation'][:2]:
                    context_parts.append(f"- {doc.get('content', '')[:100]}...")
            
            if 'code_suggestions' in context and context['code_suggestions']:
                context_parts.append("General code suggestions:")
                for suggestion in context['code_suggestions'][:3]:
                    context_parts.append(f"- {suggestion}")
            
            if 'code_snippet' in context:
                context_parts.append(f"Current code snippet:\n{context['code_snippet']}")
            
            if 'file_path' in context:
                context_parts.append(f"File path: {context['file_path']}")
                
            if 'additional_context' in context:
                context_parts.append(f"Additional context: {context['additional_context']}")
            
            context_str = "\n".join(context_parts)
            return f"{base_prompt}\n{context_str}\n\nSolution:"

    def _calculate_confidence(self, context: Dict[str, Any], response: str) -> float:
        """Calculate confidence score for the response"""
        if 'reference_pack' in context:
            # Higher confidence when using reference packs
            return 0.8
            
        # Traditional confidence calculation
        similar_errors = context.get('similar_errors', [])
        if not similar_errors:
            return 0.3  # Low confidence if no similar errors found
        
        # Calculate average similarity of retrieved errors
        avg_similarity = sum(error.get('distance', 0) for error in similar_errors) / len(similar_errors)
        
        # Adjust based on response quality (simplified)
        quality_indicator = 1.0 if any(keyword in response.lower() for keyword in ["fix", "solution", "try", "change"]) else 0.5
        
        return min(0.9, avg_similarity * quality_indicator)

rag_service = RAGService()