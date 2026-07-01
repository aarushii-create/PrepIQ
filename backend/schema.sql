-- ============================================================
-- Interview Prep System — MySQL Schema
-- (Converted from PostgreSQL. Run with: mysql -u root -p < schema.sql)
-- ============================================================

CREATE DATABASE IF NOT EXISTS interview_prep
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

USE interview_prep;

-- ------------------------------------------------------------
-- Analyses table
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS analyses (
    id VARCHAR(36) PRIMARY KEY,
    resume_text LONGTEXT NOT NULL,
    jd_text LONGTEXT NOT NULL,
    match_score FLOAT NOT NULL,
    matched_skills JSON,
    missing_skills JSON,
    recommended_topics JSON,
    interview_questions JSON,
    study_plan JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ------------------------------------------------------------
-- Skills database (source of truth for ml_engine's FAISS index)
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS skills (
    id VARCHAR(36) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    category VARCHAR(50),
    difficulty VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uq_skills_name (name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ------------------------------------------------------------
-- Interview questions
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS interview_questions (
    id VARCHAR(36) PRIMARY KEY,
    question TEXT NOT NULL,
    skill VARCHAR(100),
    difficulty VARCHAR(20),
    topic VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ------------------------------------------------------------
-- Learning resources
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS learning_resources (
    id VARCHAR(36) PRIMARY KEY,
    topic VARCHAR(100),
    title VARCHAR(255),
    url VARCHAR(500),
    resource_type VARCHAR(50),   -- 'video', 'article', 'course'
    priority VARCHAR(20) DEFAULT 'medium',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ------------------------------------------------------------
-- Indexes for performance
-- (MySQL does not support `CREATE INDEX IF NOT EXISTS`,
--  so these will error harmlessly if already present on re-run —
--  drop them first if you need a clean re-apply.)
-- ------------------------------------------------------------
CREATE INDEX idx_analyses_created_at ON analyses(created_at);
CREATE INDEX idx_skills_category ON skills(category);
CREATE INDEX idx_questions_skill ON interview_questions(skill);
CREATE INDEX idx_resources_topic ON learning_resources(topic);

-- ------------------------------------------------------------
-- Sample data
-- Note: prefer running `python seed_data.py` instead — it's idempotent
-- (safe to re-run) and keeps Python and SQL seed data in one place.
-- These INSERTs are kept here for a quick manual bootstrap if needed.
-- ------------------------------------------------------------
INSERT INTO skills (id, name, category, difficulty) VALUES
('s1', 'Python', 'Programming', 'easy'),
('s2', 'JavaScript', 'Programming', 'easy'),
('s3', 'React', 'Frontend', 'medium'),
('s4', 'Node.js', 'Backend', 'medium'),
('s5', 'SQL', 'Database', 'medium'),
('s6', 'AWS', 'Cloud', 'hard'),
('s7', 'Docker', 'DevOps', 'medium'),
('s8', 'System Design', 'System Design', 'hard'),
('s9', 'Microservices', 'Architecture', 'hard'),
('s10', 'Machine Learning', 'ML', 'hard')
ON DUPLICATE KEY UPDATE category = VALUES(category), difficulty = VALUES(difficulty);

INSERT INTO interview_questions (id, question, skill, difficulty, topic) VALUES
('q1', 'Design a URL Shortener', 'System Design', 'medium', 'System Design'),
('q2', 'Design TinyURL', 'System Design', 'medium', 'System Design'),
('q3', 'What is EC2?', 'AWS', 'easy', 'AWS'),
('q4', 'Explain S3 buckets', 'AWS', 'easy', 'AWS'),
('q5', 'Design a chat application', 'System Design', 'hard', 'System Design'),
('q6', 'What is a microservice?', 'Microservices', 'medium', 'Architecture'),
('q7', 'Docker vs Virtual Machine', 'Docker', 'medium', 'DevOps')
ON DUPLICATE KEY UPDATE question = VALUES(question);

INSERT INTO learning_resources (id, topic, title, url, resource_type, priority) VALUES
('r1', 'AWS', 'AWS Official Documentation', 'https://docs.aws.amazon.com', 'article', 'high'),
('r2', 'AWS', 'A Cloud Guru AWS Course', 'https://acloudguru.com', 'course', 'high'),
('r3', 'System Design', 'Grokking the System Design Interview', 'https://educative.io', 'course', 'high'),
('r4', 'Docker', 'Docker Official Docs', 'https://docs.docker.com', 'article', 'medium'),
('r5', 'Machine Learning', 'Andrew Ng ML Course', 'https://coursera.org', 'course', 'medium')
ON DUPLICATE KEY UPDATE title = VALUES(title);
