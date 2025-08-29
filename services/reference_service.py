from typing import List, Dict, Any, Optional
import logging
from models import crud
from models.symbol import Symbol, Reference, ReferencePack
from utils.ast_parsers import ast_parser
from utils.lsp_client import lsp_client
from services.embedding_service import embedding_service
from services.retrieval_service import retrieval_service
import re

logger = logging.getLogger(__name__)

class ReferenceService:
    def __init__(self):
        pass

    def find_enclosing_symbol(self, project_id: int, file_path: str, 
                            start_line: Optional[int] = None, 
                            end_line: Optional[int] = None,
                            snippet_text: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Find the symbol that encloses the given line range or snippet"""
        try:
            # Try to get from database first
            if start_line is not None:
                symbols = crud.symbol.get_by_file_and_line(project_id, file_path, start_line, end_line)
                if symbols:
                    return symbols[0]
            
            # If not found in DB or no line info, use AST parsing
            repo_path = self._get_repo_path(project_id)
            if not repo_path:
                return None
                
            file_content = self._read_file_content(repo_path, file_path)
            if not file_content:
                return None
                
            # Parse symbols from file
            language = self._detect_language(file_path)
            symbols = self._parse_symbols(language, file_content, file_path)
            
            if start_line is not None:
                # Find by line range
                return ast_parser.find_enclosing_symbol_by_line(symbols, start_line)
            elif snippet_text:
                # Find by semantic similarity
                return self.semantic_find_symbols(project_id, snippet_text, file_path, top_k=1)[0]
                
        except Exception as e:
            logger.error(f"Failed to find enclosing symbol: {e}")
            return None

    def semantic_find_symbols(self, project_id: int, query_snippet: str, 
                             file_path: Optional[str] = None, top_k: int = 10) -> List[Dict[str, Any]]:
        """Find symbols semantically similar to the query snippet"""
        try:
            # Query Pinecone for similar symbols
            namespace = f"project_{project_id}_symbols"
            results = embedding_service.query_collection(namespace, query_snippet, top_k)
            
            symbols = []
            for result in results:
                symbol_id = result['metadata'].get('symbol_id')
                if symbol_id:
                    symbol = crud.symbol.get(symbol_id)
                    if symbol:
                        symbols.append({
                            'symbol': symbol,
                            'similarity': 1 - result['distance'],
                            'metadata': result['metadata']
                        })
            
            # Filter by file path if specified
            if file_path:
                symbols = [s for s in symbols if s['symbol']['file_path'] == file_path]
                
            return sorted(symbols, key=lambda x: x['similarity'], reverse=True)[:top_k]
            
        except Exception as e:
            logger.error(f"Failed to semantically find symbols: {e}")
            return []

    def get_symbol_references(self, symbol_id: int, max_depth: int = 1, 
                            max_references: int = 50) -> List[Dict[str, Any]]:
        """Get references for a symbol with graph traversal"""
        try:
            symbol = crud.symbol.get(symbol_id)
            if not symbol:
                return []
                
            references = []
            visited = set()
            
            def traverse(current_symbol_id, depth):
                if depth > max_depth or len(references) >= max_references:
                    return
                    
                if current_symbol_id in visited:
                    return
                    
                visited.add(current_symbol_id)
                
                # Get direct references
                direct_refs = crud.reference.get_by_symbol(current_symbol_id)
                for ref in direct_refs:
                    references.append({
                        'reference': ref,
                        'depth': depth,
                        'symbol': crud.symbol.get(ref['to_symbol_id'])
                    })
                    
                    # Recursively traverse if within depth limit
                    if depth < max_depth:
                        traverse(ref['to_symbol_id'], depth + 1)
            
            traverse(symbol_id, 0)
            return references
            
        except Exception as e:
            logger.error(f"Failed to get symbol references: {e}")
            return []

    def build_reference_pack(self, symbol_id: int, token_budget: int = 4000,
                           ranking_params: Optional[Dict[str, float]] = None) -> ReferencePack:
        """Build a compact context package for debugging"""
        try:
            symbol = crud.symbol.get(symbol_id)
            if not symbol:
                raise ValueError(f"Symbol {symbol_id} not found")
                
            # Get symbol definition
            definition = self._get_symbol_definition(symbol)
            
            # Get references
            references = self.get_symbol_references(symbol_id, max_depth=2)
            
            # Get historical fixes
            historical_fixes = self._get_historical_fixes(symbol['project_id'], symbol['symbol_name'])
            
            # Rank and select snippets within token budget
            selected_snippets = self._rank_and_select_snippets(
                definition, references, historical_fixes, token_budget, ranking_params
            )
            
            return ReferencePack(
                symbol=symbol,
                definition=selected_snippets['definition'],
                references=selected_snippets['references'],
                callers=selected_snippets['callers'],
                callees=selected_snippets['callees'],
                imports=selected_snippets['imports'],
                tests=selected_snippets['tests'],
                historical_fixes=selected_snippets['historical_fixes'],
                token_count=selected_snippets['total_tokens'],
                reasoning=selected_snippets['reasoning']
            )
            
        except Exception as e:
            logger.error(f"Failed to build reference pack: {e}")
            raise

    def resolve_snippet_to_symbol(self, project_id: int, file_path: str, 
                                snippet_text: str, line_range: Optional[tuple] = None) -> Optional[int]:
        """Resolve a code snippet to a specific symbol"""
        try:
            # First try line-based resolution
            if line_range:
                start_line, end_line = line_range
                symbol = self.find_enclosing_symbol(project_id, file_path, start_line, end_line)
                if symbol:
                    return symbol['id']
            
            # Fallback to semantic search
            results = self.semantic_find_symbols(project_id, snippet_text, file_path, top_k=1)
            if results:
                return results[0]['symbol']['id']
                
            return None
            
        except Exception as e:
            logger.error(f"Failed to resolve snippet to symbol: {e}")
            return None

    def _get_symbol_definition(self, symbol: Dict[str, Any]) -> Dict[str, Any]:
        """Get the full definition of a symbol"""
        repo_path = self._get_repo_path(symbol['project_id'])
        file_content = self._read_file_content(repo_path, symbol['file_path'])
        
        if file_content and symbol['start_line'] and symbol['end_line']:
            lines = file_content.split('\n')
            definition = '\n'.join(lines[symbol['start_line']-1:symbol['end_line']])
            
            return {
                'content': definition,
                'file_path': symbol['file_path'],
                'start_line': symbol['start_line'],
                'end_line': symbol['end_line'],
                'token_count': self._estimate_tokens(definition)
            }
        
        return {'content': '', 'token_count': 0}

    def _get_historical_fixes(self, project_id: int, symbol_name: str) -> List[Dict[str, Any]]:
        """Get historical fixes related to this symbol"""
        # Use retrieval service to find similar errors/fixes
        error_query = f"fix {symbol_name} error bug"
        similar_errors = retrieval_service.retrieve_similar_errors(project_id, error_query, n_results=5)
        
        fixes = []
        for error in similar_errors:
            fixes.append({
                'commit_hash': error['metadata'].get('hash'),
                'message': error['content'],
                'similarity': error.get('similarity', 0.0)
            })
        
        return fixes

    def _rank_and_select_snippets(self, definition: Dict[str, Any], references: List[Dict[str, Any]],
                                historical_fixes: List[Dict[str, Any]], token_budget: int,
                                ranking_params: Optional[Dict[str, float]]) -> Dict[str, Any]:
        """Rank and select snippets within token budget"""
        # Implementation of ranking algorithm
        # This would use the scoring formula mentioned in the architecture
        selected = {
            'definition': definition,
            'references': [],
            'callers': [],
            'callees': [],
            'imports': [],
            'tests': [],
            'historical_fixes': [],
            'total_tokens': definition['token_count'],
            'reasoning': 'Prioritized definition and direct references'
        }
        
        # Simple greedy selection for now
        # TODO: Implement proper ranking algorithm
        for ref in references:
            ref_content = self._get_reference_content(ref)
            token_count = self._estimate_tokens(ref_content)
            
            if selected['total_tokens'] + token_count <= token_budget:
                selected['references'].append({
                    'content': ref_content,
                    'reference_type': ref['reference']['reference_type'],
                    'token_count': token_count
                })
                selected['total_tokens'] += token_count
        
        return selected

    def _get_reference_content(self, reference: Dict[str, Any]) -> str:
        """Get content for a reference"""
        repo_path = self._get_repo_path(reference['symbol']['project_id'])
        file_content = self._read_file_content(repo_path, reference['reference']['file_path'])
        
        if file_content:
            lines = file_content.split('\n')
            # Get context around the reference line
            start_line = max(0, reference['reference']['line'] - 5)
            end_line = min(len(lines), reference['reference']['line'] + 5)
            return '\n'.join(lines[start_line:end_line])
        
        return ""

    def _estimate_tokens(self, text: str) -> int:
        """Estimate token count using simple approximation"""
        return len(text.split())  # 1 token ≈ 1 word

    def _get_repo_path(self, project_id: int) -> Optional[str]:
        """Get repository path for a project"""
        project = crud.project.get(project_id)
        if project:
            return f"./repositories/{project['name']}"
        return None

    def _read_file_content(self, repo_path: str, file_path: str) -> Optional[str]:
        """Read file content from repository"""
        try:
            full_path = f"{repo_path}/{file_path}"
            with open(full_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            logger.error(f"Failed to read file {file_path}: {e}")
            return None

    def _detect_language(self, file_path: str) -> str:
        """Detect programming language from file extension"""
        ext_map = {
            '.py': 'python',
            '.js': 'javascript', '.jsx': 'javascript',
            '.ts': 'typescript', '.tsx': 'typescript',
            '.java': 'java',
            '.cpp': 'cpp', '.cc': 'cpp', '.cxx': 'cpp', '.h': 'cpp', '.hpp': 'cpp',
            '.go': 'go',
            '.rs': 'rust'
        }
        
        ext = '.' + file_path.split('.')[-1].lower()
        return ext_map.get(ext, 'unknown')

    def _parse_symbols(self, language: str, file_content: str, file_path: str) -> List[Dict[str, Any]]:
        """Parse symbols from file content using appropriate parser"""
        if language == 'python':
            return ast_parser.parse_python_symbols(file_content, file_path)
        elif language in ['javascript', 'typescript']:
            return ast_parser.parse_javascript_symbols(file_content, file_path)
        elif language == 'java':
            return ast_parser.parse_java_symbols(file_content, file_path)
        elif language == 'cpp':
            return ast_parser.parse_cpp_symbols(file_content, file_path)
        elif language == 'go':
            return ast_parser.parse_go_symbols(file_content, file_path)
        elif language == 'rust':
            return ast_parser.parse_rust_symbols(file_content, file_path)
        else:
            return []

# Global reference service instance
reference_service = ReferenceService()