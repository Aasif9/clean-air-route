-- Create route_batches table
CREATE TABLE IF NOT EXISTS route_batches (
    id SERIAL PRIMARY KEY,
    batch_id TEXT UNIQUE NOT NULL,
    data_source TEXT,
    start_lat FLOAT,
    start_lon FLOAT,
    end_lat FLOAT,
    end_lon FLOAT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Add index on batch_id for faster lookups
CREATE INDEX IF NOT EXISTS idx_route_batches_batch_id ON route_batches(batch_id);

-- Add index on created_at for sorting
CREATE INDEX IF NOT EXISTS idx_route_batches_created_at ON route_batches(created_at);
