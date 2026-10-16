-- PostgreSQL Initialization for India Leads Platform
-- Enable pg_trgm for fuzzy similarity matching on business names and addresses
CREATE EXTENSION IF NOT EXISTS pg_trgm;
CREATE EXTENSION IF NOT EXISTS btree_gist;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

