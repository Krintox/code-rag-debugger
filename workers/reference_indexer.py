import logging
from typing import List, Dict, Any, Optional
from pathlib import Path
import time
from datetime import datetime

from models import crud
from utils.ast_parsers import ast_parser
from utils.file_processing import find_code_files, read_code_files
from services.embedding_service import embedding_service
from services.git_service import git_service

logger = logging.getLogger(__name__)

class ReferenceIndexer:
    def __init__(self):
        self.batch_size = 50

    def index_project_symbols(self, project_id: int, changed_files: List[str] = None, 
                            commit_hash: str = None, force_full_reindex: bool = False):
        """Index symbols for a project"""
        try:
            # Create indexing job record
            job_id = self._create_indexing_job(project_id, "processing")
            
            project = crud.project.get(project_id)
            if not project:
                raise ValueError(f"Project {project_id} not found")
            
            repo_path = f"./repositories/{project['name']}"
            
            if force_full_reindex or not changed_files:
                # Full reindex - get all code files
                code_files = find_code_files(repo_path)
            else:
                # Incremental index - only process changed files
                code_files = [f for f in changed_files if self._is_code_file(f)]
            
            stats = {
                'total_files': len(code_files),
                'files_processed': 0,
                'symbols_found': 0,
                'references_found': 0,
                'errors': 0
            }
            
            # Process files in batches
            for i in range(0, len(code_files), self.batch_size):
                batch_files = code_files[i:i + self.batch_size]
                self._process_file_batch(project_id, repo_path, batch_files, stats, commit_hash)
                
                # Update job progress
                self._update_indexing_job(job_id, {
                    'status': 'processing',
                    'stats': stats,
                    'progress': f"{min(i + self.batch_size, len(code_files))}/{len(code_files)}"
                })
            
            # Mark job as completed
            self._update_indexing_job(job_id, {
                'status': 'completed',
                'stats': stats,
                'finished_at': datetime.now().isoformat()
            })
            
            logger.info(f"Indexing completed for project {project_id}: {stats}")
            
        except Exception as e:
            logger.error(f"Indexing failed for project {project_id}: {e}")
            self._update_indexing_job(job_id, {
                'status': 'failed',
                'last_error': str(e),
                'finished_at': datetime.now().isoformat()
            })
            raise

    def _process_file_batch(self, project_id: int, repo_path: str, file_paths: List[str],
                          stats: Dict[str, Any], commit_hash: str = None):
        """Process a batch of files"""
        file_contents = read_code_files(repo_path, file_paths)
        
        for file_path, content in file_contents.items():
            try:
                self._process_single_file(project_id, repo_path, file_path, content, stats, commit_hash)
                stats['files_processed'] += 1
            except Exception as e:
                logger.error(f"Failed to process file {file_path}: {e}")
                stats['errors'] += 1

    def _process_single_file(self, project_id: int, repo_path: str, file_path: str,
                           content: str, stats: Dict[str, Any], commit_hash: str = None):
        """Process a single file and extract symbols"""
        language = self._detect_language(file_path)
        if language == 'unknown':
            return
        
        # Parse symbols from file
        symbols = ast_parser.parse_python_symbols(content, file_path)
        if not symbols:
            return
        
        for symbol_data in symbols:
            # Create or update symbol record
            symbol_data['project_id'] = project_id
            symbol_data['commit_hash'] = commit_hash
            symbol_data['token_count_estimate'] = self._estimate_tokens(symbol_data.get('code_snippet', ''))
            
            symbol_id = self._upsert_symbol(symbol_data)
            if symbol_id:
                stats['symbols_found'] += 1
                
                # Extract and index symbol chunks
                self._index_symbol_chunks(symbol_id, symbol_data, content)
                
                # Extract references within this file
                references = self._extract_references(symbol_id, content, file_path, symbols)
                stats['references_found'] += len(references)
                
                # TODO: Cross-file reference resolution would go here

    def _upsert_symbol(self, symbol_data: Dict[str, Any]) -> Optional[int]:
        """Upsert a symbol record"""
        try:
            # Check if symbol already exists
            existing = crud.symbol.get_by_unique(
                symbol_data['project_id'],
                symbol_data['file_path'],
                symbol_data['symbol_name'],
                symbol_data['start_line']
            )
            
            if existing:
                # Update existing symbol
                symbol_data['id'] = existing['id']
                updated = crud.symbol.update(symbol_data['id'], symbol_data)
                return updated['id'] if updated else None
            else:
                # Create new symbol
                created = crud.symbol.create(symbol_data)
                return created['id'] if created else None
                
        except Exception as e:
            logger.error(f"Failed to upsert symbol {symbol_data['symbol_name']}: {e}")
            return None

    def _index_symbol_chunks(self, symbol_id: int, symbol_data: Dict[str, Any], file_content: str):
        """Index symbol chunks for embedding"""
        try:
            # For now, create a single chunk for the whole symbol
            chunk_data = {
                'symbol_id': symbol_id,
                'chunk_index': 0,
                'content': symbol_data.get('code_snippet', ''),
                'start_line': symbol_data['start_line'],
                'end_line': symbol_data['end_line'],
                'token_count': symbol_data['token_count_estimate']
            }
            
            # Create chunk record
            chunk_id = crud.symbol_chunk.create(chunk_data)
            if not chunk_id:
                return
                
            # Generate embedding and upsert to Pinecone
            embedding = embedding_service.get_embeddings([chunk_data['content']])[0]
            if embedding:
                namespace = f"project_{symbol_data['project_id']}_symbols"
                metadata = {
                    'symbol_id': symbol_id,
                    'chunk_id': chunk_id,
                    'file_path': symbol_data['file_path'],
                    'language': symbol_data['language'],
                    'start_line': symbol_data['start_line'],
                    'end_line': symbol_data['end_line'],
                    'symbol_type': symbol_data['symbol_type'],
                    'symbol_name': symbol_data['symbol_name'],
                    'commit_hash': symbol_data.get('commit_hash')
                }
                
                embedding_service.upsert_symbol_embedding(
                    namespace, chunk_id, embedding, metadata
                )
                
                # Store embedding metadata
                crud.symbol_embedding.create({
                    'symbol_id': symbol_id,
                    'pinecone_id': str(chunk_id),
                    'namespace': namespace,
                    'embedding_dim': len(embedding)
                })
                
        except Exception as e:
            logger.error(f"Failed to index symbol chunks: {e}")

    def _extract_references(self, symbol_id: int, content: str, file_path: str,
                          all_symbols: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Extract references within the same file"""
        references = []
        symbol_name = next((s['symbol_name'] for s in all_symbols if s.get('id') == symbol_id), None)
        if not symbol_name:
            return references
        
        # Simple regex-based reference extraction
        # This would be enhanced with proper AST analysis
        lines = content.split('\n')
        for line_num, line in enumerate(lines, 1):
            if symbol_name in line and not line.strip().startswith('def ') and not line.strip().startswith('class '):
                # Found a potential reference
                ref_data = {
                    'from_symbol_id': symbol_id,
                    'to_symbol_id': symbol_id,  # Self-reference for now
                    'reference_type': 'usage',
                    'file_path': file_path,
                    'line': line_num,
                    'context_snippet': line.strip()
                }
                
                try:
                    crud.reference.create(ref_data)
                    references.append(ref_data)
                except Exception as e:
                    logger.error(f"Failed to create reference: {e}")
        
        return references

    def _create_indexing_job(self, project_id: int, status: str) -> int:
        """Create a new indexing job record"""
        job_data = {
            'project_id': project_id,
            'status': status,
            'started_at': datetime.now().isoformat(),
            'stats': {}
        }
        
        job = crud.indexing_job.create(job_data)
        return job['id'] if job else None

    def _update_indexing_job(self, job_id: int, updates: Dict[str, Any]):
        """Update an indexing job record"""
        try:
            crud.indexing_job.update(job_id, updates)
        except Exception as e:
            logger.error(f"Failed to update indexing job {job_id}: {e}")

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
        
        ext = Path(file_path).suffix.lower()
        return ext_map.get(ext, 'unknown')

    def _is_code_file(self, file_path: str) -> bool:
        """Check if a file is a code file"""
        code_extensions = {'.py', '.js', '.jsx', '.ts', '.tsx', '.java', '.cpp', '.cc', '.cxx', '.h', '.hpp', '.go', '.rs'}
        return Path(file_path).suffix.lower() in code_extensions

    def _estimate_tokens(self, text: str) -> int:
        """Estimate token count"""
        return len(text.split())  # Simple word count approximation

# Global indexer instance
reference_indexer = ReferenceIndexer()