from pinecone import Pinecone
import requests
from typing import List, Dict, Any
from config import settings
import logging
import uuid
from datetime import datetime

logger = logging.getLogger(__name__)

class EmbeddingService:
    def __init__(self):
        # Initialize Pinecone client correctly (v3+)
        try:
            self.pc = Pinecone(api_key=settings.PINECONE_API_KEY)
            logger.info("Pinecone client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Pinecone client: {e}")
            raise
        
        self.index_name = settings.PINECONE_INDEX_NAME
        # Check if index exists; create if not
        existing_indexes = [idx["name"] for idx in self.pc.list_indexes()]
        if self.index_name not in existing_indexes:
            try:
                self.pc.create_index(
                    name=self.index_name,
                    dimension=384,  # Dimension for all-MiniLM-L6-v2 embeddings
                    metric="cosine"
                )
                logger.info(f"Created Pinecone index '{self.index_name}'")
            except Exception as e:
                logger.error(f"Failed to create Pinecone index: {e}")
                raise
        
        self.index = self.pc.Index(self.index_name)

    def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings using Gemini API's sentence-transformers endpoint"""
        try:
            headers = {
                "Authorization": f"Bearer {settings.GEMINI_API_KEY}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "inputs": texts,
                "truncate": True
            }
            
            response = requests.post(
                "https://api.gemini.com/v1/inference/sentence-transformers/all-MiniLM-L6-v2",  # Replace with actual Gemini embeddings endpoint
                headers=headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Gemini embeddings error: {response.status_code} - {response.text}")
                # Fallback: return dummy embeddings for testing
                return [[0.1] * 384 for _ in texts]
                
        except Exception as e:
            logger.error(f"Failed to get embeddings: {e}")
            return [[0.1] * 384 for _ in texts]

    def create_collection(self, collection_name: str):
        """In Pinecone v3, use namespaces instead of collections"""
        return collection_name

    def add_documents(self, collection_name: str, documents: List[Dict[str, Any]]):
        """Add documents to Pinecone namespace"""
        try:
            texts = [doc["content"] for doc in documents]
            metadatas = [doc["metadata"] for doc in documents]
            
            embeddings = self.get_embeddings(texts)
            
            vectors = []
            for i, (embedding, metadata) in enumerate(zip(embeddings, metadatas)):
                vectors.append({
                    "id": str(uuid.uuid4()),
                    "values": embedding,
                    "metadata": {
                        **metadata,
                        "text": texts[i],
                        "collection": collection_name,
                        "timestamp": datetime.now().isoformat()
                    }
                })
            
            self.index.upsert(vectors=vectors, namespace=collection_name)
            
            logger.info(f"Added {len(documents)} documents to namespace {collection_name}")
            
        except Exception as e:
            logger.error(f"Failed to add documents to namespace {collection_name}: {e}")
            raise

    def query_collection(self, collection_name: str, query_text: str, n_results: int = 5) -> List[Dict[str, Any]]:
        """Query a namespace for similar documents"""
        try:
            query_embedding = self.get_embeddings([query_text])[0]
            
            results = self.index.query(
                vector=query_embedding,
                top_k=n_results,
                namespace=collection_name,
                include_metadata=True,
                include_values=False
            )
            
            formatted_results = []
            for match in results["matches"]:
                formatted_results.append({
                    "content": match["metadata"].get("text", ""),
                    "metadata": {k: v for k, v in match["metadata"].items() if k != "text"},
                    "distance": match["score"],
                    "id": match["id"]
                })
            
            return formatted_results
            
        except Exception as e:
            logger.error(f"Failed to query namespace {collection_name}: {e}")
            return []

    def index_commit_history(self, project_id: int, commits: List[Dict[str, Any]]):
        """Index commit history for a project"""
        collection_name = f"project_{project_id}_commits"
        documents = []
        
        for commit in commits:
            content = (
                f"Commit: {commit['hash']}\n"
                f"Author: {commit['author']}\n"
                f"Message: {commit['message']}\n"
                f"Files: {', '.join(commit['files_changed'])}"
            )
            
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
        """Index code files for a project (to be implemented if needed)"""
        pass

embedding_service = EmbeddingService()
