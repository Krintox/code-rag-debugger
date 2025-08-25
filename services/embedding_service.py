import chromadb
from chromadb.config import Settings
from chromadb.utils import embedding_functions
from typing import List, Dict, Any
from config import settings
import logging
import uuid

logger = logging.getLogger(__name__)


class EmbeddingService:
    def __init__(self):
        # Initialize ChromaDB client
        self.chroma_client = chromadb.PersistentClient(
            path=settings.CHROMA_DB_PATH,
            settings=Settings(anonymized_telemetry=False)
        )
        
        # Use ChromaDB's default embedding function
        self.embedding_function = embedding_functions.DefaultEmbeddingFunction()

    def create_collection(self, collection_name: str):
        """Create a new collection in ChromaDB"""
        try:
            return self.chroma_client.get_or_create_collection(
                name=collection_name,
                embedding_function=self.embedding_function,
                metadata={"hnsw:space": "cosine"}
            )
        except Exception as e:
            logger.error(f"Failed to create collection {collection_name}: {e}")
            raise

    def add_documents(self, collection_name: str, documents: List[Dict[str, Any]]):
        """Add documents to a collection with embeddings"""
        try:
            collection = self.create_collection(collection_name)
            
            # Extract texts and metadata
            texts = [doc["content"] for doc in documents]
            metadatas = [doc["metadata"] for doc in documents]
            ids = [str(uuid.uuid4()) for _ in documents]
            
            # Add to collection (ChromaDB will handle embeddings automatically)
            collection.add(
                documents=texts,
                metadatas=metadatas,
                ids=ids
            )
            
            logger.info(f"Added {len(documents)} documents to collection {collection_name}")
            
        except Exception as e:
            logger.error(f"Failed to add documents to collection {collection_name}: {e}")
            raise

    def query_collection(self, collection_name: str, query_text: str, n_results: int = 5) -> List[Dict[str, Any]]:
        """Query a collection for similar documents"""
        try:
            collection = self.create_collection(collection_name)
            
            # Query the collection
            results = collection.query(
                query_texts=[query_text],
                n_results=n_results
            )
            
            # Format results
            formatted_results = []
            for i in range(len(results["documents"][0])):
                formatted_results.append({
                    "content": results["documents"][0][i],
                    "metadata": results["metadatas"][0][i],
                    "distance": results["distances"][0][i] if results["distances"] else 0
                })
            
            return formatted_results
            
        except Exception as e:
            logger.error(f"Failed to query collection {collection_name}: {e}")
            return []

    def index_commit_history(self, project_id: int, commits: List[Dict[str, Any]]):
        """Index commit history for a project"""
        collection_name = f"project_{project_id}_commits"
        documents = []
        
        for commit in commits:
            # Create a document for each commit
            content = f"Commit: {commit['hash']}\nAuthor: {commit['author']}\nMessage: {commit['message']}\nFiles: {', '.join(commit['files_changed'])}"
            
            documents.append({
                "content": content,
                "metadata": {
                    "type": "commit",
                    "hash": commit["hash"],
                    "author": commit["author"],
                    "timestamp": commit["timestamp"].isoformat(),
                    "project_id": project_id
                }
            })
        
        self.add_documents(collection_name, documents)

    def index_code_files(self, project_id: int, repo_path: str, file_patterns: List[str] = None):
        """Index code files for a project"""
        # This would be implemented to parse and index code files
        # For simplicity, we're not implementing the full file traversal here
        pass

embedding_service = EmbeddingService()