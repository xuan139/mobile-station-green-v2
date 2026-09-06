INSERT_RAW_MESSAGE = """
INSERT INTO raw_message (
  message_id, station_id, station_name, device_id, protocol_type, protocol_version,
  group_name, message_type, sequence, collected_at, received_at, payload_json,
  ingest_status, parse_status, parse_error
) VALUES (
  %(message_id)s, %(station_id)s, %(station_name)s, %(device_id)s,
  %(protocol_type)s, %(protocol_version)s, %(group_name)s, %(message_type)s,
  %(sequence)s, %(collected_at)s::timestamptz, %(received_at)s::timestamptz,
  %(payload_json)s, %(ingest_status)s, %(parse_status)s, %(parse_error)s
)
ON CONFLICT DO NOTHING
RETURNING message_id;
"""

SELECT_RUNTIME = """
SELECT status, last_heartbeat_at, backlog_count
FROM station_runtime_status
WHERE station_id = %s;
"""

UPSERT_RUNTIME = """
INSERT INTO station_runtime_status (
  station_id, station_name, status, last_seen_at, last_heartbeat_at,
  last_message_id, last_sequence, last_uplink_ip, backlog_count, parser_lag_seconds
) VALUES (
  %(station_id)s, %(station_name)s, %(status)s, %(last_seen_at)s::timestamptz,
  %(last_heartbeat_at)s::timestamptz, %(last_message_id)s, %(last_sequence)s,
  %(last_uplink_ip)s, %(backlog_count)s, %(parser_lag_seconds)s
)
ON CONFLICT (station_id) DO UPDATE SET
  station_name = EXCLUDED.station_name,
  status = CASE WHEN EXCLUDED.last_seen_at >= station_runtime_status.last_seen_at
    THEN EXCLUDED.status ELSE station_runtime_status.status END,
  last_seen_at = GREATEST(station_runtime_status.last_seen_at, EXCLUDED.last_seen_at),
  last_heartbeat_at = CASE
    WHEN station_runtime_status.last_heartbeat_at IS NULL THEN EXCLUDED.last_heartbeat_at
    WHEN EXCLUDED.last_heartbeat_at IS NULL THEN station_runtime_status.last_heartbeat_at
    ELSE GREATEST(station_runtime_status.last_heartbeat_at, EXCLUDED.last_heartbeat_at) END,
  last_message_id = CASE WHEN EXCLUDED.last_seen_at >= station_runtime_status.last_seen_at
    THEN EXCLUDED.last_message_id ELSE station_runtime_status.last_message_id END,
  last_sequence = GREATEST(station_runtime_status.last_sequence, EXCLUDED.last_sequence),
  last_uplink_ip = CASE WHEN EXCLUDED.last_seen_at >= station_runtime_status.last_seen_at
    THEN EXCLUDED.last_uplink_ip ELSE station_runtime_status.last_uplink_ip END,
  backlog_count = CASE WHEN EXCLUDED.last_seen_at >= station_runtime_status.last_seen_at
    THEN EXCLUDED.backlog_count ELSE station_runtime_status.backlog_count END,
  parser_lag_seconds = CASE WHEN EXCLUDED.last_seen_at >= station_runtime_status.last_seen_at
    THEN EXCLUDED.parser_lag_seconds ELSE station_runtime_status.parser_lag_seconds END;
"""

INSERT_HISTORY = """
INSERT INTO telemetry_history (
  station_id, source_type, source_id, metric_key, metric_value_double,
  metric_value_text, unit, quality, collected_at, source_message_id
) VALUES (%s, %s, %s, %s, %s, %s, NULL, 'good', %s::timestamptz, %s);
"""

UPSERT_CURRENT = """
INSERT INTO telemetry_current (
  station_id, source_type, source_id, metric_key, metric_value_double,
  metric_value_text, unit, quality, collected_at, source_message_id
) VALUES (%s, %s, %s, %s, %s, %s, NULL, 'good', %s::timestamptz, %s)
ON CONFLICT (station_id, source_type, source_id, metric_key) DO UPDATE SET
  metric_value_double = EXCLUDED.metric_value_double,
  metric_value_text = EXCLUDED.metric_value_text,
  unit = EXCLUDED.unit,
  quality = EXCLUDED.quality,
  collected_at = EXCLUDED.collected_at,
  source_message_id = EXCLUDED.source_message_id
WHERE EXCLUDED.collected_at >= telemetry_current.collected_at;
"""
