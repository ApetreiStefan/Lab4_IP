CREATE TABLE IF NOT EXISTS ai_records (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL,
    record_type VARCHAR(50) NOT NULL, -- 'pop_quiz', 'final_test', 'explanation'
    subject_tag VARCHAR(100),         -- ex: 'Matematica', 'Istorie - Lectia 2'
    difficulty VARCHAR(20),           -- 'easy', 'medium', 'hard'
    context_text TEXT,                
    content JSONB NOT NULL,           
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 2.4. Cache (rămâne neschimbat, pentru viteză)
CREATE TABLE IF NOT EXISTS ai_cache (
    content_hash VARCHAR(64) PRIMARY KEY,
    cached_response JSONB NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Indexare pentru performanță (Căutare rapidă în istoric)
CREATE INDEX idx_user_id ON ai_records(user_id);
CREATE INDEX idx_record_type ON ai_records(record_type);
