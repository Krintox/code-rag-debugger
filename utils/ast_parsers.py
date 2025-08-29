import tree_sitter
from tree_sitter import Language, Parser
from typing import List, Dict, Any, Optional
import os
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

# Tree-sitter language builds
TREE_SITTER_LANGUAGES = {
    'python': 'tree_sitter_languages/build/python.so',
    'javascript': 'tree_sitter_languages/build/javascript.so',
    'typescript': 'tree_sitter_languages/build/typescript.so',
    'java': 'tree_sitter_languages/build/java.so',
    'cpp': 'tree_sitter_languages/build/cpp.so',
    'go': 'tree_sitter_languages/build/go.so',
    'rust': 'tree_sitter_languages/build/rust.so'
}

class ASTParser:
    def __init__(self):
        self.parsers = {}
        self._load_languages()

    def _load_languages(self):
        """Load tree-sitter language parsers"""
        for lang, lib_path in TREE_SITTER_LANGUAGES.items():
            try:
                if os.path.exists(lib_path):
                    language = Language(lib_path, lang)
                    parser = Parser()
                    parser.set_language(language)
                    self.parsers[lang] = parser
                    logger.info(f"Loaded parser for {lang}")
                else:
                    logger.warning(f"Tree-sitter library not found for {lang}: {lib_path}")
            except Exception as e:
                logger.error(f"Failed to load parser for {lang}: {e}")

    def parse_python_symbols(self, file_content: str, file_path: str) -> List[Dict[str, Any]]:
        """Parse Python file and extract symbols"""
        return self._parse_symbols('python', file_content, file_path)

    def parse_javascript_symbols(self, file_content: str, file_path: str) -> List[Dict[str, Any]]:
        """Parse JavaScript file and extract symbols"""
        return self._parse_symbols('javascript', file_content, file_path)

    def parse_typescript_symbols(self, file_content: str, file_path: str) -> List[Dict[str, Any]]:
        """Parse TypeScript file and extract symbols"""
        return self._parse_symbols('typescript', file_content, file_path)

    def parse_java_symbols(self, file_content: str, file_path: str) -> List[Dict[str, Any]]:
        """Parse Java file and extract symbols"""
        return self._parse_symbols('java', file_content, file_path)

    def parse_cpp_symbols(self, file_content: str, file_path: str) -> List[Dict[str, Any]]:
        """Parse C++ file and extract symbols"""
        return self._parse_symbols('cpp', file_content, file_path)

    def parse_go_symbols(self, file_content: str, file_path: str) -> List[Dict[str, Any]]:
        """Parse Go file and extract symbols"""
        return self._parse_symbols('go', file_content, file_path)

    def parse_rust_symbols(self, file_content: str, file_path: str) -> List[Dict[str, Any]]:
        """Parse Rust file and extract symbols"""
        return self._parse_symbols('rust', file_content, file_path)

    def _parse_symbols(self, language: str, file_content: str, file_path: str) -> List[Dict[str, Any]]:
        """Generic symbol parsing method"""
        if language not in self.parsers:
            logger.warning(f"No parser available for {language}")
            return []

        try:
            parser = self.parsers[language]
            tree = parser.parse(bytes(file_content, 'utf8'))
            root_node = tree.root_node

            symbols = []
            
            # Language-specific extraction logic
            if language == 'python':
                symbols = self._extract_python_symbols(root_node, file_content)
            elif language in ['javascript', 'typescript']:
                symbols = self._extract_javascript_symbols(root_node, file_content)
            elif language == 'java':
                symbols = self._extract_java_symbols(root_node, file_content)
            elif language == 'cpp':
                symbols = self._extract_cpp_symbols(root_node, file_content)
            elif language == 'go':
                symbols = self._extract_go_symbols(root_node, file_content)
            elif language == 'rust':
                symbols = self._extract_rust_symbols(root_node, file_content)

            # Add file path and language to each symbol
            for symbol in symbols:
                symbol['file_path'] = file_path
                symbol['language'] = language

            return symbols

        except Exception as e:
            logger.error(f"Failed to parse {language} file {file_path}: {e}")
            return []

    def _extract_python_symbols(self, root_node, file_content: str) -> List[Dict[str, Any]]:
        """Extract symbols from Python code"""
        symbols = []
        
        def traverse(node):
            if node.type in ['function_definition', 'class_definition']:
                # Get symbol name
                name_node = node.child_by_field_name('name')
                if name_node:
                    symbol_name = file_content[name_node.start_byte:name_node.end_byte].decode('utf8')
                    
                    # Get signature/docstring
                    signature = self._get_python_signature(node, file_content)
                    docstring = self._get_python_docstring(node, file_content)
                    
                    symbols.append({
                        'symbol_name': symbol_name,
                        'symbol_type': 'function' if node.type == 'function_definition' else 'class',
                        'start_line': node.start_point[0] + 1,
                        'end_line': node.end_point[0] + 1,
                        'signature': signature,
                        'docstring': docstring,
                        'code_snippet': file_content[node.start_byte:node.end_byte].decode('utf8')
                    })
            
            # Traverse children
            for child in node.children:
                traverse(child)
        
        traverse(root_node)
        return symbols

    def _get_python_signature(self, node, file_content: str) -> str:
        """Extract function/class signature"""
        if node.type == 'function_definition':
            # Get parameters
            parameters_node = node.child_by_field_name('parameters')
            if parameters_node:
                return file_content[parameters_node.start_byte:parameters_node.end_byte].decode('utf8')
        return ""

    def _get_python_docstring(self, node, file_content: str) -> str:
        """Extract docstring from Python node"""
        # Look for string literal immediately after definition
        for child in node.children:
            if child.type == 'expression_statement':
                string_node = child.child_by_field_name('value')
                if string_node and string_node.type == 'string':
                    return file_content[string_node.start_byte:string_node.end_byte].decode('utf8')
        return ""

    def _extract_javascript_symbols(self, root_node, file_content: str) -> List[Dict[str, Any]]:
        """Extract symbols from JavaScript/TypeScript code"""
        symbols = []
        # Implementation for JS/TS symbol extraction
        # This is a simplified version - would need more complex logic
        def traverse(node):
            if node.type in ['function_declaration', 'class_declaration', 'variable_declarator']:
                name_node = node.child_by_field_name('name')
                if name_node:
                    symbol_name = file_content[name_node.start_byte:name_node.end_byte].decode('utf8')
                    symbol_type = self._get_js_symbol_type(node.type)
                    
                    symbols.append({
                        'symbol_name': symbol_name,
                        'symbol_type': symbol_type,
                        'start_line': node.start_point[0] + 1,
                        'end_line': node.end_point[0] + 1,
                        'code_snippet': file_content[node.start_byte:node.end_byte].decode('utf8')
                    })
            
            for child in node.children:
                traverse(child)
        
        traverse(root_node)
        return symbols

    def _get_js_symbol_type(self, node_type: str) -> str:
        """Map JS node type to symbol type"""
        type_map = {
            'function_declaration': 'function',
            'class_declaration': 'class',
            'variable_declarator': 'variable'
        }
        return type_map.get(node_type, 'variable')

    # Similar methods for other languages would be implemented here
    def _extract_java_symbols(self, root_node, file_content: str) -> List[Dict[str, Any]]:
        """Extract symbols from Java code"""
        return []  # Placeholder

    def _extract_cpp_symbols(self, root_node, file_content: str) -> List[Dict[str, Any]]:
        """Extract symbols from C++ code"""
        return []  # Placeholder

    def _extract_go_symbols(self, root_node, file_content: str) -> List[Dict[str, Any]]:
        """Extract symbols from Go code"""
        return []  # Placeholder

    def _extract_rust_symbols(self, root_node, file_content: str) -> List[Dict[str, Any]]:
        """Extract symbols from Rust code"""
        return []  # Placeholder

    def find_enclosing_symbol_by_line(self, symbols: List[Dict[str, Any]], line: int) -> Optional[Dict[str, Any]]:
        """Find the symbol that encloses the given line number"""
        for symbol in symbols:
            if symbol['start_line'] <= line <= symbol['end_line']:
                return symbol
        return None

# Global parser instance
ast_parser = ASTParser()