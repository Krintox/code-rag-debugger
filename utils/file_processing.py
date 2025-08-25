import os
from pathlib import Path
from typing import List, Dict, Any
import logging
import re

logger = logging.getLogger(__name__)

def find_code_files(directory: str, extensions: List[str] = None) -> List[str]:
    """
    Find all code files in a directory with the given extensions.
    
    Args:
        directory: The directory to search in
        extensions: List of file extensions to include (e.g., ['.py', '.js', '.java'])
    
    Returns:
        List of file paths relative to the directory
    """
    if extensions is None:
        extensions = ['.py', '.js', '.ts', '.java', '.cpp', '.c', '.h', '.hpp', '.go', '.rs', '.rb', '.php']
    
    code_files = []
    directory_path = Path(directory)
    
    try:
        for extension in extensions:
            for file_path in directory_path.rglob(f"*{extension}"):
                if file_path.is_file():
                    # Get relative path
                    relative_path = file_path.relative_to(directory_path)
                    code_files.append(str(relative_path))
    except Exception as e:
        logger.error(f"Error finding code files in {directory}: {e}")
    
    return code_files

def read_code_files(directory: str, file_paths: List[str]) -> Dict[str, str]:
    """
    Read the content of multiple code files.
    
    Args:
        directory: The base directory
        file_paths: List of relative file paths
    
    Returns:
        Dictionary mapping file paths to their content
    """
    contents = {}
    directory_path = Path(directory)
    
    for file_path in file_paths:
        try:
            full_path = directory_path / file_path
            if full_path.exists() and full_path.is_file():
                with open(full_path, 'r', encoding='utf-8') as f:
                    contents[str(file_path)] = f.read()
        except UnicodeDecodeError:
            logger.warning(f"Could not read file {file_path} (encoding issue)")
        except Exception as e:
            logger.error(f"Error reading file {file_path}: {e}")
    
    return contents

def extract_code_metadata(file_path: str, content: str) -> Dict[str, Any]:
    """
    Extract metadata from code file content.
    
    Args:
        file_path: The file path
        content: The file content
    
    Returns:
        Dictionary with extracted metadata
    """
    metadata = {
        "file_path": file_path,
        "file_extension": os.path.splitext(file_path)[1],
        "lines_of_code": len(content.splitlines()),
        "size_bytes": len(content.encode('utf-8')),
        "imports": [],
        "functions": [],
        "classes": []
    }
    
    # Extract imports (simple regex-based approach)
    import_patterns = {
        '.py': r'^(?:from\s+(\S+)\s+)?import\s+([^\n#]+)',
        '.js': r'^(?:import\s+[^\']+from\s+)?[\'"]([^\'"]+)[\'"]',  # Fixed: escaped single quote
        '.java': r'^import\s+([^;]+);'
    }
    
    extension = metadata["file_extension"]
    if extension in import_patterns:
        matches = re.findall(import_patterns[extension], content, re.MULTILINE)
        if matches:
            if extension == '.py':
                # For Python, matches are tuples (from_module, import_target)
                metadata["imports"] = [f"{frm} {imp}" if frm else imp for frm, imp in matches if imp]
            else:
                metadata["imports"] = [match[0] if isinstance(match, tuple) else match for match in matches]
    
    # Extract function definitions
    function_patterns = {
        '.py': r'^def\s+(\w+)\s*\([^)]*\)\s*:',
        '.js': r'^(?:function\s+(\w+)\s*\([^)]*\)|const\s+(\w+)\s*=\s*\([^)]*\)\s*=>|let\s+(\w+)\s*=\s*\([^)]*\)\s*=>)',
        '.java': r'^(?:public|private|protected)\s+[^{]+\s+(\w+)\s*\([^)]*\)\s*\{'
    }
    
    if extension in function_patterns:
        matches = re.findall(function_patterns[extension], content, re.MULTILINE)
        if matches:
            # Flatten tuples and filter empty strings
            flat_matches = []
            for match in matches:
                if isinstance(match, tuple):
                    flat_matches.extend([m for m in match if m])
                elif match:
                    flat_matches.append(match)
            metadata["functions"] = flat_matches
    
    # Extract class definitions
    class_patterns = {
        '.py': r'^class\s+(\w+)',
        '.js': r'^class\s+(\w+)',
        '.java': r'^class\s+(\w+)'
    }
    
    if extension in class_patterns:
        matches = re.findall(class_patterns[extension], content, re.MULTILINE)
        metadata["classes"] = matches
    
    return metadata

def get_file_tree(directory: str, max_depth: int = 3) -> Dict[str, Any]:
    """
    Generate a file tree structure for the directory.
    
    Args:
        directory: The directory to scan
        max_depth: Maximum depth to traverse
    
    Returns:
        Nested dictionary representing the file tree
    """
    def build_tree(path: Path, current_depth: int = 0) -> Dict[str, Any]:
        if current_depth > max_depth:
            return {}
        
        if path.is_file():
            return {
                "name": path.name,
                "type": "file",
                "size": path.stat().st_size,
                "modified": path.stat().st_mtime
            }
        elif path.is_dir():
            tree = {
                "name": path.name,
                "type": "directory",
                "children": {}
            }
            try:
                for item in path.iterdir():
                    if item.name.startswith('.'):
                        continue  # Skip hidden files/directories
                    tree["children"][item.name] = build_tree(item, current_depth + 1)
            except PermissionError:
                logger.warning(f"Permission denied accessing {path}")
            return tree
        return {}
    
    return build_tree(Path(directory))