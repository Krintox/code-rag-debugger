import subprocess
import json
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

class LSPClient:
    def __init__(self):
        self.servers = {}
        self.processes = {}

    def start_lsp_server(self, language: str, project_root: str) -> bool:
        """Start an LSP server for the given language"""
        servers = {
            'python': ['pylsp'],
            'javascript': ['typescript-language-server', '--stdio'],
            'typescript': ['typescript-language-server', '--stdio'],
            'java': ['java', '-jar', 'path/to/eclipse.jdt.ls.jar'],
            'cpp': ['clangd'],
            'go': ['gopls'],
            'rust': ['rust-analyzer']
        }
        
        if language not in servers:
            logger.warning(f"No LSP server configured for {language}")
            return False
        
        try:
            cmd = servers[language]
            process = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=project_root,
                text=True,
                bufsize=1
            )
            
            self.processes[language] = process
            self.servers[language] = {
                'project_root': project_root,
                'initialized': False
            }
            
            # Initialize LSP server
            self._initialize_server(language)
            return True
            
        except Exception as e:
            logger.error(f"Failed to start LSP server for {language}: {e}")
            return False

    def _initialize_server(self, language: str):
        """Initialize LSP server with handshake"""
        if language not in self.processes:
            return
        
        try:
            init_msg = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "processId": self.processes[language].pid,
                    "rootUri": f"file://{self.servers[language]['project_root']}",
                    "capabilities": {}
                }
            }
            
            self._send_message(language, init_msg)
            response = self._receive_message(language)
            
            if response and 'result' in response:
                self.servers[language]['initialized'] = True
                logger.info(f"LSP server for {language} initialized successfully")
                
                # Send initialized notification
                initialized_msg = {
                    "jsonrpc": "2.0",
                    "method": "initialized",
                    "params": {}
                }
                self._send_message(language, initialized_msg)
                
        except Exception as e:
            logger.error(f"Failed to initialize LSP server for {language}: {e}")

    def find_references_via_lsp(self, project_root: str, file_path: str, line: int, column: int) -> List[Dict[str, Any]]:
        """Find references using LSP"""
        language = self._detect_language(file_path)
        if not language or language not in self.processes:
            logger.warning(f"No LSP server available for {file_path}")
            return []
        
        if not self.servers[language]['initialized']:
            if not self.start_lsp_server(language, project_root):
                return []
        
        try:
            # Open the document first
            with open(Path(project_root) / file_path, 'r') as f:
                content = f.read()
            
            open_msg = {
                "jsonrpc": "2.0",
                "method": "textDocument/didOpen",
                "params": {
                    "textDocument": {
                        "uri": f"file://{Path(project_root) / file_path}",
                        "languageId": language,
                        "version": 1,
                        "text": content
                    }
                }
            }
            self._send_message(language, open_msg)
            
            # Find references
            ref_msg = {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "textDocument/references",
                "params": {
                    "textDocument": {
                        "uri": f"file://{Path(project_root) / file_path}"
                    },
                    "position": {
                        "line": line - 1,
                        "character": column - 1
                    },
                    "context": {
                        "includeDeclaration": True
                    }
                }
            }
            
            self._send_message(language, ref_msg)
            response = self._receive_message(language)
            
            references = []
            if response and 'result' in response:
                for ref in response['result']:
                    references.append({
                        'file_path': ref['uri'].replace('file://', ''),
                        'line': ref['range']['start']['line'] + 1,
                        'column': ref['range']['start']['character'] + 1
                    })
            
            return references
            
        except Exception as e:
            logger.error(f"Failed to find references via LSP: {e}")
            return []

    def _send_message(self, language: str, message: dict):
        """Send message to LSP server"""
        if language not in self.processes:
            return
        
        content = json.dumps(message)
        length = len(content)
        header = f"Content-Length: {length}\r\n\r\n"
        
        self.processes[language].stdin.write(header + content)
        self.processes[language].stdin.flush()

    def _receive_message(self, language: str) -> Optional[dict]:
        """Receive message from LSP server"""
        if language not in self.processes:
            return None
        
        # Read content length
        line = self.processes[language].stdout.readline().strip()
        if not line.startswith('Content-Length:'):
            return None
        
        length = int(line.split(':')[1].strip())
        
        # Read empty line
        self.processes[language].stdout.readline()
        
        # Read content
        content = self.processes[language].stdout.read(length)
        return json.loads(content)

    def _detect_language(self, file_path: str) -> Optional[str]:
        """Detect language from file extension"""
        ext_map = {
            '.py': 'python',
            '.js': 'javascript',
            '.ts': 'typescript',
            '.java': 'java',
            '.cpp': 'cpp', '.cc': 'cpp', '.cxx': 'cpp', '.h': 'cpp', '.hpp': 'cpp',
            '.go': 'go',
            '.rs': 'rust'
        }
        
        ext = Path(file_path).suffix.lower()
        return ext_map.get(ext)

    def shutdown(self):
        """Shutdown all LSP servers"""
        for language, process in self.processes.items():
            try:
                # Send shutdown message
                shutdown_msg = {
                    "jsonrpc": "2.0",
                    "id": 999,
                    "method": "shutdown"
                }
                self._send_message(language, shutdown_msg)
                
                # Wait for exit
                process.terminate()
                process.wait(timeout=5)
            except:
                process.kill()
        
        self.processes = {}
        self.servers = {}

# Global LSP client instance
lsp_client = LSPClient()