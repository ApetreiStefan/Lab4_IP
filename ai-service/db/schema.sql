-- 1. Istoricul generărilor (extins cu coloana de dificultate)
CREATE TABLE IF NOT EXISTS ai_records (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(100) NOT NULL,
    record_type VARCHAR(50) NOT NULL, -- 'pop_quiz', 'final_test', 'explanation'
    subject_tag VARCHAR(100),         -- ex: 'Matematica', 'Istorie - Lectia 2'
    difficulty VARCHAR(20),           -- 'easy', 'medium', 'hard'
    context_text TEXT,                
    content JSONB NOT NULL,           
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 2. Tabela de Nivel/Profil Elev (Aici știm cât de bun e elevul)
CREATE TABLE IF NOT EXISTS student_profiles (
    user_id VARCHAR(100) PRIMARY KEY,
    current_level INTEGER DEFAULT 1,     -- Nivelul (1, 2, 3...)
    preferred_difficulty VARCHAR(20) DEFAULT 'medium',
    total_quizzes_taken INTEGER DEFAULT 0,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 3. Tabela de Stăpânire a Subiectelor (Topic Mastery)
-- Aici salvăm unde are dificultăți pentru a genera explicații extra
CREATE TABLE IF NOT EXISTS student_mastery (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(100) REFERENCES student_profiles(user_id) ON DELETE CASCADE,
    topic_name VARCHAR(100) NOT NULL,    -- ex: 'Fractii', 'Revolutia Franceza'
    mastery_score FLOAT DEFAULT 0.0,     -- Scor de la 0 la 1 (0.2 = slab, 0.9 = expert)
    wrong_answers_count INTEGER DEFAULT 0,
    last_practiced TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, topic_name)
);

-- 4. Cache (rămâne neschimbat, pentru viteză)
CREATE TABLE IF NOT EXISTS ai_cache (
    content_hash VARCHAR(64) PRIMARY KEY,
    cached_response JSONB NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Indexare pentru performanță (Căutare rapidă în istoric)
CREATE INDEX idx_user_mastery ON student_mastery(user_id, topic_name);
CREATE INDEX idx_user_id ON ai_records(user_id);
CREATE INDEX idx_record_type ON ai_records(record_type);