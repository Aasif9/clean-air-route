-- Create route_points table to preserve coordinate order
-- This ensures exact reconstruction of routes for debugging and rendering

CREATE TABLE IF NOT EXISTS route_points (
    id SERIAL PRIMARY KEY,
    route_id INTEGER NOT NULL,
    point_order INTEGER NOT NULL,
    lat DECIMAL(10, 6) NOT NULL,
    lng DECIMAL(10, 6) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (route_id) REFERENCES routes(id) ON DELETE CASCADE
);

-- Create index for fast lookups
CREATE INDEX IF NOT EXISTS idx_route_points_route_id ON route_points(route_id);
CREATE INDEX IF NOT EXISTS idx_route_points_order ON route_points(route_id, point_order);

-- Add coordinates JSONB column to routes table for full data storage
ALTER TABLE routes ADD COLUMN IF NOT EXISTS coordinates JSONB;

-- Add comment for documentation
COMMENT ON TABLE route_points IS 'Stores individual coordinate points for each route to preserve exact order';
COMMENT ON COLUMN route_points.point_order IS 'Order of this point in the route sequence (0-based)';
COMMENT ON COLUMN routes.coordinates IS 'Full coordinate array as JSONB for easy access and reconstruction';
