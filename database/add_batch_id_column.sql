-- Add batch_id column to routes table
ALTER TABLE routes ADD COLUMN IF NOT EXISTS batch_id TEXT;

-- Add index on batch_id for faster lookups
CREATE INDEX IF NOT EXISTS idx_routes_batch_id ON routes(batch_id);
