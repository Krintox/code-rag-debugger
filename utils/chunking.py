from typing import List, Dict, Any
import re

def chunk_commits(commits: List[Dict[str, Any]], max_chunk_size: int = 1000) -> List[Dict[str, Any]]:
    """Chunk commits into smaller pieces for embedding"""
    chunks = []
    
    for commit in commits:
        content = f"Commit: {commit['hash']}\nAuthor: {commit['author']}\nMessage: {commit['message']}\nFiles: {', '.join(commit['files_changed'])}"
        
        # If content is too long, split it
        if len(content) > max_chunk_size:
            # Split by lines and create smaller chunks
            lines = content.split('\n')
            current_chunk = []
            current_size = 0
            
            for line in lines:
                if current_size + len(line) + 1 > max_chunk_size and current_chunk:
                    chunks.append({
                        "content": '\n'.join(current_chunk),
                        "metadata": {
                            "type": "commit",
                            "hash": commit["hash"],
                            "author": commit["author"],
                            "timestamp": commit["timestamp"].isoformat(),
                            "chunk_type": "partial"
                        }
                    })
                    current_chunk = []
                    current_size = 0
                
                current_chunk.append(line)
                current_size += len(line) + 1
            
            if current_chunk:
                chunks.append({
                    "content": '\n'.join(current_chunk),
                    "metadata": {
                        "type": "commit",
                        "hash": commit["hash"],
                        "author": commit["author"],
                        "timestamp": commit["timestamp"].isoformat(),
                        "chunk_type": "partial"
                    }
                })
        else:
            chunks.append({
                "content": content,
                "metadata": {
                    "type": "commit",
                    "hash": commit["hash"],
                    "author": commit["author"],
                    "timestamp": commit["timestamp"].isoformat(),
                    "chunk_type": "full"
                }
            })
    
    return chunks

def chunk_text(text: str, metadata: Dict[str, Any], max_chunk_size: int = 1000) -> List[Dict[str, Any]]:
    """Chunk text into smaller pieces for embedding"""
    chunks = []
    
    # Split by paragraphs or sentences
    paragraphs = re.split(r'\n\s*\n', text)
    
    current_chunk = []
    current_size = 0
    
    for paragraph in paragraphs:
        if current_size + len(paragraph) + 2 > max_chunk_size and current_chunk:
            chunks.append({
                "content": '\n\n'.join(current_chunk),
                "metadata": {**metadata, "chunk_type": "partial"}
            })
            current_chunk = []
            current_size = 0
        
        current_chunk.append(paragraph)
        current_size += len(paragraph) + 2
    
    if current_chunk:
        chunks.append({
            "content": '\n\n'.join(current_chunk),
            "metadata": {**metadata, "chunk_type": "full"}
        })
    
    return chunks