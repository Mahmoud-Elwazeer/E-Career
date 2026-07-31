-- Initialize PostgreSQL database with Apache AGE extension

-- Create AGE extension
CREATE EXTENSION IF NOT EXISTS age;

-- Load AGE into shared_preload_libraries
-- Note: In production, add 'age' to shared_preload_libraries in postgresql.conf
-- shared_preload_libraries = 'age'

-- Add ag_catalog to search path
ALTER DATABASE ecareer SET search_path = ag_catalog, "$user", public;

-- Grant permissions
GRANT USAGE ON SCHEMA ag_catalog TO postgres;
