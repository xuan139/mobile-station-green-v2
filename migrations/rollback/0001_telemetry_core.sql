BEGIN;
DROP TABLE IF EXISTS telemetry_history CASCADE;
DROP TABLE IF EXISTS telemetry_current CASCADE;
DROP TABLE IF EXISTS station_runtime_status CASCADE;
DROP TABLE IF EXISTS raw_message CASCADE;
DROP FUNCTION IF EXISTS set_updated_at_now() CASCADE;
DELETE FROM schema_migration WHERE version = '0001_telemetry_core';
COMMIT;
