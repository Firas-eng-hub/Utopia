-- Hosted schema v1. Applied once, atomically, by deploy/bootstrap.py.

-- UtopiaHire Database Schema
-- This creates all tables needed for Resume Reviewer feature

-- Users table: Store user information
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    region VARCHAR(100),  -- e.g., "Tunisia", "Nigeria", "Egypt"
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Resumes table: Store uploaded resumes
CREATE TABLE IF NOT EXISTS resumes (
        id SERIAL PRIMARY KEY,
        user_id INTEGER NOT NULL,
        filename VARCHAR(255) NOT NULL,
        file_path TEXT NOT NULL,
        file_size INTEGER NOT NULL,
        file_type VARCHAR(10) NOT NULL,
        parsed_text TEXT,
        parsed_data JSONB,
        word_count INTEGER DEFAULT 0,
        uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        last_analyzed TIMESTAMP,
        last_score FLOAT,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    );

-- Analysis results table: Store AI analysis of resumes
CREATE TABLE IF NOT EXISTS analyses (
    id SERIAL PRIMARY KEY,
    resume_id INTEGER REFERENCES resumes(id) ON DELETE CASCADE,
    ats_score INTEGER CHECK (ats_score >= 0 AND ats_score <= 100),
    formatting_score INTEGER CHECK (formatting_score >= 0 AND formatting_score <= 100),
    keyword_score INTEGER CHECK (keyword_score >= 0 AND keyword_score <= 100),
    overall_score INTEGER CHECK (overall_score >= 0 AND overall_score <= 100),
    suggestions JSONB,  -- Array of improvement suggestions
    strengths JSONB,    -- What's good in the resume
    weaknesses JSONB,   -- What needs improvement
    missing_sections JSONB,  -- Sections that should be added
    model_used VARCHAR(100),  -- AI model name (e.g., 'llama3.2')
    analysis_time_seconds FLOAT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Improved resumes table: Store AI-enhanced versions
CREATE TABLE IF NOT EXISTS improved_resumes (
    id SERIAL PRIMARY KEY,
    resume_id INTEGER REFERENCES resumes(id) ON DELETE CASCADE,
    analysis_id INTEGER REFERENCES analyses(id) ON DELETE CASCADE,
    enhanced_text TEXT NOT NULL,
    enhanced_data JSONB,  -- Structured improved data
    changes_made JSONB,   -- List of specific changes
    improvement_percentage FLOAT,
    version INTEGER DEFAULT 1,  -- Allow multiple versions
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Skills database: Common skills to match against
CREATE TABLE IF NOT EXISTS skills_database (
    id SERIAL PRIMARY KEY,
    skill_name VARCHAR(255) UNIQUE NOT NULL,
    category VARCHAR(100),  -- e.g., 'Technical', 'Soft Skills', 'Language'
    popularity INTEGER DEFAULT 0,  -- How often it appears in job postings
    region VARCHAR(100),  -- Region-specific skills
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Job keywords: Common keywords from job descriptions
CREATE TABLE IF NOT EXISTS job_keywords (
    id SERIAL PRIMARY KEY,
    keyword VARCHAR(255) NOT NULL,
    job_role VARCHAR(100),  -- e.g., 'Software Engineer', 'Data Scientist'
    frequency INTEGER DEFAULT 0,
    region VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_resumes_user_id ON resumes(user_id);
CREATE INDEX IF NOT EXISTS idx_analyses_resume_id ON analyses(resume_id);
CREATE INDEX IF NOT EXISTS idx_improved_resumes_resume_id ON improved_resumes(resume_id);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_skills_category ON skills_database(category);
CREATE INDEX IF NOT EXISTS idx_job_keywords_role ON job_keywords(job_role);

-- Insert some sample skills for MENA/Sub-Saharan Africa region
INSERT INTO skills_database (skill_name, category, popularity, region) VALUES
    ('Python', 'Technical', 95, 'Global'),
    ('JavaScript', 'Technical', 90, 'Global'),
    ('SQL', 'Technical', 85, 'Global'),
    ('Data Analysis', 'Technical', 80, 'Global'),
    ('Communication', 'Soft Skills', 95, 'Global'),
    ('Teamwork', 'Soft Skills', 90, 'Global'),
    ('Problem Solving', 'Soft Skills', 92, 'Global'),
    ('Arabic', 'Language', 85, 'MENA'),
    ('French', 'Language', 80, 'Sub-Saharan Africa'),
    ('English', 'Language', 95, 'Global')
ON CONFLICT (skill_name) DO NOTHING;

-- Insert sample job keywords
INSERT INTO job_keywords (keyword, job_role, frequency, region) VALUES
    ('experience', 'Software Engineer', 95, 'Global'),
    ('develop', 'Software Engineer', 90, 'Global'),
    ('design', 'Software Engineer', 85, 'Global'),
    ('team', 'Software Engineer', 88, 'Global'),
    ('agile', 'Software Engineer', 75, 'Global'),
    ('bachelor', 'All', 80, 'Global'),
    ('master', 'All', 70, 'Global')
ON CONFLICT DO NOTHING;

-- Create a function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create trigger for users table
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

COMMENT ON TABLE users IS 'Stores user account information';
COMMENT ON TABLE resumes IS 'Stores uploaded resume files and extracted data';
COMMENT ON TABLE analyses IS 'Stores AI analysis results for each resume';
COMMENT ON TABLE improved_resumes IS 'Stores AI-enhanced versions of resumes';
COMMENT ON TABLE skills_database IS 'Database of common skills for matching';
COMMENT ON TABLE job_keywords IS 'Common keywords from job descriptions';

ALTER TABLE users ADD COLUMN IF NOT EXISTS password_hash VARCHAR(255);
ALTER TABLE users ADD COLUMN IF NOT EXISTS accepted_privacy_policy BOOLEAN DEFAULT FALSE;
ALTER TABLE users ADD COLUMN IF NOT EXISTS privacy_policy_accepted_at TIMESTAMP;

CREATE TABLE IF NOT EXISTS jobs (
        id SERIAL PRIMARY KEY,
        job_id VARCHAR(255) UNIQUE NOT NULL,
        title VARCHAR(500) NOT NULL,
        company VARCHAR(500) NOT NULL,
        location TEXT NOT NULL,
        region VARCHAR(100),
        job_type VARCHAR(50) DEFAULT 'Full-time',
        experience_level VARCHAR(50),
        description TEXT,
        required_skills JSONB DEFAULT '[]'::jsonb,
        preferred_skills JSONB DEFAULT '[]'::jsonb,
        salary_range JSONB,
        posted_date VARCHAR(50),
        remote BOOLEAN DEFAULT false,
        url TEXT NOT NULL,
        source VARCHAR(100),
        fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

CREATE INDEX IF NOT EXISTS idx_jobs_job_id ON jobs(job_id);

CREATE INDEX IF NOT EXISTS idx_jobs_title ON jobs(title);

CREATE INDEX IF NOT EXISTS idx_jobs_company ON jobs(company);

CREATE INDEX IF NOT EXISTS idx_jobs_location ON jobs(location);

CREATE INDEX IF NOT EXISTS idx_jobs_region ON jobs(region);

CREATE INDEX IF NOT EXISTS idx_jobs_job_type ON jobs(job_type);

CREATE INDEX IF NOT EXISTS idx_jobs_experience_level ON jobs(experience_level);

CREATE INDEX IF NOT EXISTS idx_jobs_remote ON jobs(remote);

CREATE INDEX IF NOT EXISTS idx_jobs_fetched_at ON jobs(fetched_at DESC);

CREATE INDEX IF NOT EXISTS idx_jobs_required_skills ON jobs USING GIN(required_skills);

CREATE INDEX IF NOT EXISTS idx_jobs_posted_date ON jobs(posted_date DESC);

CREATE TABLE IF NOT EXISTS saved_jobs (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    job_id VARCHAR(255) NOT NULL REFERENCES jobs(job_id) ON DELETE CASCADE,
    notes TEXT,
    status VARCHAR(50) DEFAULT 'saved',
    saved_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, job_id)
);

-- Interview Question Bank Schema and Sample Data
-- This creates the question bank and populates it with interview questions

-- Create question bank table
CREATE TABLE IF NOT EXISTS interview_question_bank (
    id SERIAL PRIMARY KEY,
    question_text TEXT NOT NULL,
    question_type VARCHAR(50) NOT NULL, -- 'technical', 'behavioral', 'situational'
    category VARCHAR(100), -- 'programming', 'system_design', 'leadership', etc.
    difficulty_level VARCHAR(20) NOT NULL, -- 'junior', 'mid', 'senior'
    job_roles TEXT[], -- Array of applicable job roles
    key_points JSONB, -- Expected key points in answer
    sample_answer TEXT,
    tags TEXT[],
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create index for faster queries
CREATE INDEX IF NOT EXISTS idx_question_type ON interview_question_bank(question_type);
CREATE INDEX IF NOT EXISTS idx_difficulty_level ON interview_question_bank(difficulty_level);
CREATE INDEX IF NOT EXISTS idx_job_roles ON interview_question_bank USING GIN(job_roles);

-- Insert Technical Questions for Software Engineers

-- Junior Level Technical
INSERT INTO interview_question_bank (question_text, question_type, category, difficulty_level, job_roles, key_points, tags) VALUES
('Explain the difference between var, let, and const in JavaScript.', 'technical', 'programming', 'junior',
 ARRAY['Software Engineer', 'Frontend Developer', 'Full Stack Developer'],
 '{"must_mention": ["var is function-scoped", "let is block-scoped", "const is immutable"], "bonus_points": ["hoisting", "temporal dead zone"]}',
 ARRAY['javascript', 'variables', 'fundamentals']),

('What is the difference between == and === in JavaScript?', 'technical', 'programming', 'junior',
 ARRAY['Software Engineer', 'Frontend Developer', 'Full Stack Developer'],
 '{"must_mention": ["== type coercion", "=== strict equality", "checks type and value"], "bonus_points": ["performance", "best practices"]}',
 ARRAY['javascript', 'operators', 'comparison']),

('What is a REST API and how does it work?', 'technical', 'web_development', 'junior',
 ARRAY['Software Engineer', 'Backend Developer', 'Full Stack Developer'],
 '{"must_mention": ["HTTP methods", "stateless", "resources", "endpoints"], "bonus_points": ["CRUD operations", "status codes"]}',
 ARRAY['api', 'rest', 'http']),

('Explain what Git is and why version control is important.', 'technical', 'tools', 'junior',
 ARRAY['Software Engineer', 'DevOps Engineer', 'Full Stack Developer'],
 '{"must_mention": ["version control", "collaboration", "history tracking", "branching"], "bonus_points": ["git commands", "workflow"]}',
 ARRAY['git', 'version-control', 'collaboration']),

('What is the difference between SQL and NoSQL databases?', 'technical', 'database', 'junior',
 ARRAY['Software Engineer', 'Backend Developer', 'Database Administrator'],
 '{"must_mention": ["relational vs non-relational", "schema", "use cases"], "bonus_points": ["examples", "scalability"]}',
 ARRAY['database', 'sql', 'nosql']);

-- Mid Level Technical
INSERT INTO interview_question_bank (question_text, question_type, category, difficulty_level, job_roles, key_points, tags) VALUES
('Explain how React hooks work and give examples of useState and useEffect.', 'technical', 'frontend', 'mid',
 ARRAY['Software Engineer', 'Frontend Developer', 'Full Stack Developer'],
 '{"must_mention": ["state management", "side effects", "lifecycle", "examples"], "bonus_points": ["custom hooks", "dependency array", "performance"]}',
 ARRAY['react', 'hooks', 'frontend']),

('What are microservices and what are their advantages and disadvantages?', 'technical', 'architecture', 'mid',
 ARRAY['Software Engineer', 'Backend Developer', 'Solutions Architect'],
 '{"must_mention": ["independent services", "scalability", "complexity"], "bonus_points": ["vs monolith", "communication patterns", "deployment"]}',
 ARRAY['architecture', 'microservices', 'design']),

('Explain the CAP theorem and its implications for distributed systems.', 'technical', 'distributed_systems', 'mid',
 ARRAY['Software Engineer', 'Backend Developer', 'Solutions Architect'],
 '{"must_mention": ["Consistency", "Availability", "Partition tolerance", "tradeoffs"], "bonus_points": ["real-world examples", "eventual consistency"]}',
 ARRAY['distributed-systems', 'theory', 'architecture']),

('How would you optimize a slow database query?', 'technical', 'performance', 'mid',
 ARRAY['Software Engineer', 'Backend Developer', 'Database Administrator'],
 '{"must_mention": ["indexes", "query analysis", "execution plan"], "bonus_points": ["caching", "denormalization", "query rewriting"]}',
 ARRAY['database', 'optimization', 'performance']),

('Explain dependency injection and why it is useful.', 'technical', 'design_patterns', 'mid',
 ARRAY['Software Engineer', 'Backend Developer'],
 '{"must_mention": ["decoupling", "testability", "flexibility"], "bonus_points": ["inversion of control", "examples", "frameworks"]}',
 ARRAY['design-patterns', 'dependency-injection', 'architecture']);

-- Senior Level Technical
INSERT INTO interview_question_bank (question_text, question_type, category, difficulty_level, job_roles, key_points, tags) VALUES
('Design a system like Twitter that can handle millions of users. Discuss scalability, data storage, and real-time updates.', 'technical', 'system_design', 'senior',
 ARRAY['Software Engineer', 'Solutions Architect', 'Tech Lead'],
 '{"must_mention": ["load balancing", "caching", "database sharding", "message queue", "CDN"], "bonus_points": ["fan-out strategy", "timeline generation", "search"]}',
 ARRAY['system-design', 'scalability', 'architecture']),

('How would you design a rate limiter for an API? Discuss algorithms and implementation.', 'technical', 'system_design', 'senior',
 ARRAY['Software Engineer', 'Backend Developer', 'Solutions Architect'],
 '{"must_mention": ["token bucket", "sliding window", "distributed systems"], "bonus_points": ["redis", "performance", "edge cases"]}',
 ARRAY['system-design', 'rate-limiting', 'algorithms']),

('Explain event-driven architecture and when you would use it.', 'technical', 'architecture', 'senior',
 ARRAY['Software Engineer', 'Solutions Architect', 'Backend Developer'],
 '{"must_mention": ["events", "publishers", "subscribers", "asynchronous"], "bonus_points": ["event sourcing", "CQRS", "message brokers"]}',
 ARRAY['architecture', 'event-driven', 'design-patterns']);

-- Behavioral Questions

-- Junior Level Behavioral
INSERT INTO interview_question_bank (question_text, question_type, category, difficulty_level, job_roles, key_points, tags) VALUES
('Tell me about a time you had to learn a new technology quickly.', 'behavioral', 'learning', 'junior',
 ARRAY['Software Engineer', 'Frontend Developer', 'Backend Developer'],
 '{"must_mention": ["situation", "learning approach", "outcome"], "bonus_points": ["resources used", "challenges", "application"]}',
 ARRAY['learning', 'adaptability', 'growth']),

('Describe a challenging bug you fixed. How did you approach it?', 'behavioral', 'problem_solving', 'junior',
 ARRAY['Software Engineer', 'Full Stack Developer'],
 '{"must_mention": ["problem", "debugging process", "solution", "result"], "bonus_points": ["tools used", "learnings", "prevention"]}',
 ARRAY['debugging', 'problem-solving', 'technical']),

('Tell me about a time you worked on a team project.', 'behavioral', 'teamwork', 'junior',
 ARRAY['Software Engineer', 'Frontend Developer', 'Backend Developer'],
 '{"must_mention": ["role", "collaboration", "outcome"], "bonus_points": ["challenges", "communication", "contribution"]}',
 ARRAY['teamwork', 'collaboration', 'communication']);

-- Mid Level Behavioral
INSERT INTO interview_question_bank (question_text, question_type, category, difficulty_level, job_roles, key_points, tags) VALUES
('Describe a time when you had to make a technical decision with incomplete information.', 'behavioral', 'decision_making', 'mid',
 ARRAY['Software Engineer', 'Tech Lead', 'Solutions Architect'],
 '{"must_mention": ["situation", "analysis", "decision", "outcome"], "bonus_points": ["tradeoffs", "stakeholders", "lessons learned"]}',
 ARRAY['decision-making', 'critical-thinking', 'leadership']),

('Tell me about a time you disagreed with a team member about a technical approach. How did you handle it?', 'behavioral', 'conflict_resolution', 'mid',
 ARRAY['Software Engineer', 'Tech Lead', 'Senior Developer'],
 '{"must_mention": ["disagreement", "communication", "resolution", "outcome"], "bonus_points": ["respect", "data-driven", "compromise"]}',
 ARRAY['conflict-resolution', 'communication', 'teamwork']),

('Describe a project where you had to balance technical debt with new features.', 'behavioral', 'prioritization', 'mid',
 ARRAY['Software Engineer', 'Tech Lead', 'Engineering Manager'],
 '{"must_mention": ["situation", "prioritization", "approach", "result"], "bonus_points": ["stakeholder management", "metrics", "tradeoffs"]}',
 ARRAY['prioritization', 'technical-debt', 'management']);

-- Senior Level Behavioral
INSERT INTO interview_question_bank (question_text, question_type, category, difficulty_level, job_roles, key_points, tags) VALUES
('Tell me about a time you led a technical initiative that had significant business impact.', 'behavioral', 'leadership', 'senior',
 ARRAY['Tech Lead', 'Engineering Manager', 'Solutions Architect'],
 '{"must_mention": ["initiative", "leadership", "business impact", "outcome"], "bonus_points": ["metrics", "team management", "challenges"]}',
 ARRAY['leadership', 'impact', 'business']),

('Describe how you mentored junior developers and helped them grow.', 'behavioral', 'mentorship', 'senior',
 ARRAY['Senior Developer', 'Tech Lead', 'Engineering Manager'],
 '{"must_mention": ["approach", "specific examples", "growth", "impact"], "bonus_points": ["feedback", "teaching methods", "long-term results"]}',
 ARRAY['mentorship', 'leadership', 'team-development']),

('Tell me about a time you had to make a critical architecture decision under pressure.', 'behavioral', 'leadership', 'senior',
 ARRAY['Solutions Architect', 'Tech Lead', 'Engineering Manager'],
 '{"must_mention": ["situation", "analysis", "decision", "execution", "outcome"], "bonus_points": ["stakeholder communication", "risk management", "lessons"]}',
 ARRAY['architecture', 'decision-making', 'leadership']);

-- Data Science / ML Questions
INSERT INTO interview_question_bank (question_text, question_type, category, difficulty_level, job_roles, key_points, tags) VALUES
('Explain the bias-variance tradeoff in machine learning.', 'technical', 'machine_learning', 'mid',
 ARRAY['Data Scientist', 'ML Engineer', 'AI Engineer'],
 '{"must_mention": ["bias", "variance", "overfitting", "underfitting"], "bonus_points": ["model complexity", "examples", "solutions"]}',
 ARRAY['machine-learning', 'theory', 'modeling']),

('How would you approach building a recommendation system?', 'technical', 'machine_learning', 'senior',
 ARRAY['Data Scientist', 'ML Engineer', 'Senior Software Engineer'],
 '{"must_mention": ["collaborative filtering", "content-based", "data collection", "evaluation"], "bonus_points": ["cold start", "scalability", "real-time"]}',
 ARRAY['recommendation-systems', 'machine-learning', 'system-design']);

-- DevOps Questions
INSERT INTO interview_question_bank (question_text, question_type, category, difficulty_level, job_roles, key_points, tags) VALUES
('Explain what CI/CD is and why it is important.', 'technical', 'devops', 'mid',
 ARRAY['DevOps Engineer', 'Software Engineer', 'Site Reliability Engineer'],
 '{"must_mention": ["continuous integration", "continuous deployment", "automation", "testing"], "bonus_points": ["tools", "pipeline", "benefits"]}',
 ARRAY['cicd', 'devops', 'automation']),

('How would you design a monitoring and alerting system for a production application?', 'technical', 'infrastructure', 'senior',
 ARRAY['DevOps Engineer', 'Site Reliability Engineer', 'Solutions Architect'],
 '{"must_mention": ["metrics", "logs", "traces", "alerting", "dashboards"], "bonus_points": ["tools", "incident response", "SLOs"]}',
 ARRAY['monitoring', 'observability', 'infrastructure']);

-- Product Manager Questions
INSERT INTO interview_question_bank (question_text, question_type, category, difficulty_level, job_roles, key_points, tags) VALUES
('How would you prioritize features for a product roadmap?', 'behavioral', 'product_management', 'mid',
 ARRAY['Product Manager', 'Technical Product Manager'],
 '{"must_mention": ["criteria", "stakeholders", "data", "framework"], "bonus_points": ["RICE", "trade-offs", "communication"]}',
 ARRAY['product-management', 'prioritization', 'strategy']),

('Tell me about a time you launched a feature that failed. What did you learn?', 'behavioral', 'learning', 'mid',
 ARRAY['Product Manager', 'Technical Product Manager', 'Engineering Manager'],
 '{"must_mention": ["feature", "failure", "analysis", "learnings"], "bonus_points": ["metrics", "recovery", "prevention"]}',
 ARRAY['product-management', 'failure', 'learning']);

-- Update timestamp trigger
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_interview_question_bank_updated_at BEFORE UPDATE
    ON interview_question_bank FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Verify insertion
SELECT
    difficulty_level,
    question_type,
    COUNT(*) as count
FROM interview_question_bank
GROUP BY difficulty_level, question_type
ORDER BY difficulty_level, question_type;

CREATE TABLE IF NOT EXISTS interview_sessions (
        id SERIAL PRIMARY KEY,
        user_id INTEGER NOT NULL,
        resume_id INTEGER,
        session_type VARCHAR(50) NOT NULL,
        job_role VARCHAR(200) NOT NULL,
        difficulty_level VARCHAR(20) NOT NULL,
        total_questions INTEGER NOT NULL,
        questions_answered INTEGER DEFAULT 0,
        status VARCHAR(20) DEFAULT 'in_progress',
        average_score FLOAT,
        duration_seconds INTEGER,
        started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        completed_at TIMESTAMP,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
        FOREIGN KEY (resume_id) REFERENCES resumes(id) ON DELETE SET NULL
    );

CREATE TABLE IF NOT EXISTS interview_questions (
        id SERIAL PRIMARY KEY,
        session_id INTEGER NOT NULL,
        question_id INTEGER NOT NULL,
        question_order INTEGER NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (session_id) REFERENCES interview_sessions(id) ON DELETE CASCADE,
        FOREIGN KEY (question_id) REFERENCES interview_question_bank(id) ON DELETE CASCADE
    );

CREATE TABLE IF NOT EXISTS interview_answers (
        id SERIAL PRIMARY KEY,
        interview_question_id INTEGER NOT NULL,
        session_id INTEGER NOT NULL,
        user_answer TEXT NOT NULL,
        time_taken_seconds INTEGER NOT NULL,
        relevance_score FLOAT NOT NULL,
        completeness_score FLOAT NOT NULL,
        clarity_score FLOAT NOT NULL,
        technical_accuracy_score FLOAT NOT NULL,
        communication_score FLOAT NOT NULL,
        overall_score FLOAT NOT NULL,
        strengths TEXT,
        weaknesses TEXT,
        missing_points TEXT,
        suggestions TEXT,
        ai_feedback TEXT,
        word_count INTEGER,
        sentiment VARCHAR(50),
        answer_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (interview_question_id) REFERENCES interview_questions(id) ON DELETE CASCADE,
        FOREIGN KEY (session_id) REFERENCES interview_sessions(id) ON DELETE CASCADE
    );

CREATE TABLE IF NOT EXISTS interview_feedback (
        id SERIAL PRIMARY KEY,
        session_id INTEGER NOT NULL UNIQUE,
        overall_performance VARCHAR(50) NOT NULL,
        technical_rating INTEGER CHECK (technical_rating >= 1 AND technical_rating <= 5),
        communication_rating INTEGER CHECK (communication_rating >= 1 AND communication_rating <= 5),
        confidence_rating INTEGER CHECK (confidence_rating >= 1 AND confidence_rating <= 5),
        key_strengths TEXT,
        areas_to_improve TEXT,
        recommended_resources TEXT,
        preparation_tips TEXT,
        practice_recommendations TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (session_id) REFERENCES interview_sessions(id) ON DELETE CASCADE
    );

CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON interview_sessions(user_id);

CREATE INDEX IF NOT EXISTS idx_sessions_status ON interview_sessions(status);

CREATE INDEX IF NOT EXISTS idx_sessions_started_at ON interview_sessions(started_at DESC);

CREATE INDEX IF NOT EXISTS idx_questions_session_id ON interview_questions(session_id);

CREATE INDEX IF NOT EXISTS idx_answers_session_id ON interview_answers(session_id);

CREATE INDEX IF NOT EXISTS idx_question_bank_job_roles ON interview_question_bank USING GIN(job_roles);

CREATE TABLE IF NOT EXISTS footprint_scans (
        id SERIAL PRIMARY KEY,
        user_id INTEGER NOT NULL,

        -- Scan metadata
        scan_type VARCHAR(50) DEFAULT 'full',
        platforms_scanned TEXT[] DEFAULT '{}',

        -- GitHub data (stored as JSONB for flexibility)
        github_username VARCHAR(200),
        github_data JSONB,
        github_score INTEGER,

        -- StackOverflow data
        stackoverflow_user_id INTEGER,
        stackoverflow_name VARCHAR(200),
        stackoverflow_data JSONB,
        stackoverflow_score INTEGER,

        -- LinkedIn data (future expansion)
        linkedin_url TEXT,
        linkedin_data JSONB,

        -- Overall scores
        overall_visibility_score INTEGER CHECK (overall_visibility_score >= 0 AND overall_visibility_score <= 100),
        professional_score INTEGER CHECK (professional_score >= 0 AND professional_score <= 100),

        -- Dimension scores
        visibility_score INTEGER DEFAULT 0 CHECK (visibility_score >= 0 AND visibility_score <= 100),
        activity_score INTEGER DEFAULT 0 CHECK (activity_score >= 0 AND activity_score <= 100),
        impact_score INTEGER DEFAULT 0 CHECK (impact_score >= 0 AND impact_score <= 100),
        expertise_score INTEGER DEFAULT 0 CHECK (expertise_score >= 0 AND expertise_score <= 100),

        -- Privacy analysis
        privacy_report JSONB,
        privacy_risk_level VARCHAR(50),

        -- Recommendations
        recommendations JSONB,
        career_insights JSONB,

        -- Timestamps
        scanned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    );

CREATE INDEX IF NOT EXISTS idx_footprint_user_id ON footprint_scans(user_id);

CREATE INDEX IF NOT EXISTS idx_footprint_scanned_at ON footprint_scans(scanned_at DESC);

CREATE INDEX IF NOT EXISTS idx_footprint_github_username ON footprint_scans(github_username);

CREATE INDEX IF NOT EXISTS idx_footprint_stackoverflow_id ON footprint_scans(stackoverflow_user_id);

CREATE INDEX IF NOT EXISTS idx_footprint_visibility ON footprint_scans(overall_visibility_score DESC);

CREATE INDEX IF NOT EXISTS idx_footprint_platforms ON footprint_scans USING GIN(platforms_scanned);

CREATE INDEX IF NOT EXISTS idx_resumes_user_id ON resumes(user_id);
    CREATE INDEX IF NOT EXISTS idx_resumes_uploaded_at ON resumes(uploaded_at DESC);
    CREATE INDEX IF NOT EXISTS idx_resumes_last_score ON resumes(last_score);
