-- PostgreSQL + PostGIS Schema for Clean Air Route Storage
-- Run this after creating your PostgreSQL database on Render

-- Enable PostGIS extension
CREATE EXTENSION IF NOT EXISTS postgis;

-- Create routes table
CREATE TABLE IF NOT EXISTS routes (
    id SERIAL PRIMARY KEY,
    route_number INTEGER NOT NULL,
    route_type VARCHAR(50) NOT NULL,
    distance_km DECIMAL(10, 2) NOT NULL,
    travel_time_min DECIMAL(10, 2) NOT NULL,
    avg_aqi DECIMAL(5, 2) NOT NULL,
    max_aqi INTEGER NOT NULL,
    min_aqi INTEGER NOT NULL,
    exposure_score DECIMAL(12, 2) NOT NULL,
    sample_points_count INTEGER NOT NULL,
    node_count INTEGER NOT NULL,
    
    -- PostGIS geometry column (LINESTRING for routes)
    geometry GEOMETRY(LINESTRING, 4326) NOT NULL,
    
    -- Metadata
    start_lat DECIMAL(10, 6),
    start_lon DECIMAL(10, 6),
    end_lat DECIMAL(10, 6),
    end_lon DECIMAL(10, 6),
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create spatial index for fast geo queries
CREATE INDEX IF NOT EXISTS idx_routes_geometry ON routes USING GIST (geometry);

-- Create indexes for common queries
CREATE INDEX IF NOT EXISTS idx_routes_avg_aqi ON routes (avg_aqi);
CREATE INDEX IF NOT EXISTS idx_routes_distance ON routes (distance_km);
CREATE INDEX IF NOT EXISTS idx_routes_created_at ON routes (created_at);

-- Create function to auto-update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create trigger to auto-update updated_at
CREATE TRIGGER update_routes_updated_at
    BEFORE UPDATE ON routes
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Create route_batches table to group routes from a single request
CREATE TABLE IF NOT EXISTS route_batches (
    id SERIAL PRIMARY KEY,
    batch_id UUID DEFAULT gen_random_uuid() NOT NULL UNIQUE,
    total_routes INTEGER NOT NULL,
    data_source VARCHAR(100),
    cache_size INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Add foreign key to routes table to link to batch
ALTER TABLE routes ADD COLUMN IF NOT EXISTS batch_id UUID REFERENCES route_batches(batch_id) ON DELETE CASCADE;

-- Create index on batch_id
CREATE INDEX IF NOT EXISTS idx_routes_batch_id ON routes (batch_id);

-- Grant permissions (adjust based on your Render setup)
-- GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO your_user;
-- GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO your_user;
