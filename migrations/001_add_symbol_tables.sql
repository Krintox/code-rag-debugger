-- Migration to add symbol and reference tables
CREATE TABLE symbols (
    id SERIAL PRIMARY KEY,
    project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    symbol_name VARCHAR(512) NOT NULL,
    symbol_type VARCHAR(50) NOT NULL CHECK (symbol_type IN ('function', 'class', 'method', 'constant', 'variable', 'module', 'import')),
    language VARCHAR(50) NOT NULL,
    file_path VARCHAR(1024) NOT NULL,
    start_line INTEGER NOT NULL,
    end_line INTEGER NOT NULL,
    signature TEXT,
    docstring TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    commit_hash VARCHAR(64),
    token_count_estimate INTEGER DEFAULT 0,
    usage_count INTEGER DEFAULT 0,
    centrality_score FLOAT DEFAULT 0.0,
    metadata JSONB DEFAULT '{}'::jsonb,
    UNIQUE(project_id, file_path, symbol_name, start_line)
);

CREATE INDEX idx_symbols_project_id ON symbols(project_id);
CREATE INDEX idx_symbols_file_path ON symbols(file_path);
CREATE INDEX idx_symbols_symbol_name ON symbols(symbol_name);
CREATE INDEX idx_symbols_symbol_type ON symbols(symbol_type);
CREATE INDEX idx_symbols_language ON symbols(language);

CREATE TABLE symbol_chunks (
    id SERIAL PRIMARY KEY,
    symbol_id INTEGER NOT NULL REFERENCES symbols(id) ON DELETE CASCADE,
    chunk_index INTEGER NOT NULL,
    content TEXT NOT NULL,
    start_line INTEGER NOT NULL,
    end_line INTEGER NOT NULL,
    embedding_vector_id VARCHAR(256),
    token_count INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(symbol_id, chunk_index)
);

CREATE INDEX idx_symbol_chunks_symbol_id ON symbol_chunks(symbol_id);

CREATE TABLE references (
    id SERIAL PRIMARY KEY,
    from_symbol_id INTEGER NOT NULL REFERENCES symbols(id) ON DELETE CASCADE,
    to_symbol_id INTEGER NOT NULL REFERENCES symbols(id) ON DELETE CASCADE,
    reference_type VARCHAR(50) NOT NULL CHECK (reference_type IN ('call', 'import', 'inheritance', 'usage', 'implementation')),
    file_path VARCHAR(1024) NOT NULL,
    line INTEGER NOT NULL,
    context_snippet TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(from_symbol_id, to_symbol_id, reference_type, file_path, line)
);

CREATE INDEX idx_references_from_symbol ON references(from_symbol_id);
CREATE INDEX idx_references_to_symbol ON references(to_symbol_id);
CREATE INDEX idx_references_reference_type ON references(reference_type);

CREATE TABLE symbol_embeddings_metadata (
    id SERIAL PRIMARY KEY,
    symbol_id INTEGER NOT NULL REFERENCES symbols(id) ON DELETE CASCADE,
    pinecone_id VARCHAR(256) NOT NULL,
    namespace VARCHAR(256) NOT NULL,
    embedding_dim INTEGER NOT NULL,
    last_upserted_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(symbol_id, namespace)
);

CREATE INDEX idx_symbol_embeddings_symbol ON symbol_embeddings_metadata(symbol_id);
CREATE INDEX idx_symbol_embeddings_pinecone ON symbol_embeddings_metadata(pinecone_id);

CREATE TABLE indexing_jobs (
    id SERIAL PRIMARY KEY,
    project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    status VARCHAR(50) NOT NULL CHECK (status IN ('pending', 'processing', 'completed', 'failed')),
    started_at TIMESTAMP WITH TIME ZONE,
    finished_at TIMESTAMP WITH TIME ZONE,
    stats JSONB DEFAULT '{}'::jsonb,
    last_error TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_indexing_jobs_project ON indexing_jobs(project_id);
CREATE INDEX idx_indexing_jobs_status ON indexing_jobs(status);