-- Database initialization script for COE API
-- This will create all required tables with proper structure

-- Create domains table
CREATE TABLE IF NOT EXISTS domains (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create blogs table
CREATE TABLE IF NOT EXISTS blogs (
    id SERIAL PRIMARY KEY,
    title VARCHAR(200) NOT NULL,
    content TEXT NOT NULL,
    author_name VARCHAR(100) NOT NULL,
    domain_id INTEGER REFERENCES domains(id) ON DELETE SET NULL,
    status VARCHAR(20) DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP
);

-- Create events table
CREATE TABLE IF NOT EXISTS events (
    id SERIAL PRIMARY KEY,
    title VARCHAR(200) NOT NULL,
    description TEXT,
    event_date DATE NOT NULL,
    event_type VARCHAR(50),
    domain_id INTEGER REFERENCES domains(id) ON DELETE SET NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create event_registrations table
CREATE TABLE IF NOT EXISTS event_registrations (
    id SERIAL PRIMARY KEY,
    event_id INTEGER REFERENCES events(id) ON DELETE CASCADE,
    user_name VARCHAR(100) NOT NULL,
    email VARCHAR(100) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insert some sample domains
INSERT INTO domains (name, description) VALUES 
('AI', 'Artificial Intelligence'),
('ML', 'Machine Learning'),
('Blockchain', 'Blockchain Technology'),
('IoT', 'Internet of Things'),
('Web Development', 'Full Stack Web Development')
ON CONFLICT (name) DO NOTHING;

-- Show created tables
\dt
