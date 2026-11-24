PRAGMA foreign_keys = ON;
CREATE TABLE IF NOT EXISTS templates (
 id INTEGER PRIMARY KEY, name TEXT NOT NULL UNIQUE CHECK(length(name) BETWEEN 1 AND 80),
 kind TEXT NOT NULL CHECK(kind IN ('stock','delimited','fixed')),
 delimiter TEXT NOT NULL DEFAULT ',', created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS template_columns (
 id INTEGER PRIMARY KEY, template_id INTEGER NOT NULL REFERENCES templates(id) ON DELETE CASCADE,
 position INTEGER NOT NULL CHECK(position>=0), name TEXT NOT NULL,
 data_type TEXT NOT NULL CHECK(data_type IN ('text','decimal')),
 start_pos INTEGER, end_pos INTEGER, required INTEGER NOT NULL CHECK(required IN (0,1)),
 UNIQUE(template_id, position), UNIQUE(template_id, name)
);
CREATE TABLE IF NOT EXISTS reports (
 id INTEGER PRIMARY KEY, template_id INTEGER REFERENCES templates(id) ON DELETE SET NULL,
 name TEXT NOT NULL CHECK(length(name) BETWEEN 1 AND 100), filename TEXT NOT NULL,
 sha256 TEXT NOT NULL, raw_text TEXT NOT NULL, raw_bytes BLOB NOT NULL, template_snapshot TEXT NOT NULL,
 created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS report_columns (
 id INTEGER PRIMARY KEY, report_id INTEGER NOT NULL REFERENCES reports(id) ON DELETE CASCADE,
 position INTEGER NOT NULL, name TEXT NOT NULL, data_type TEXT NOT NULL,
 required INTEGER NOT NULL, UNIQUE(report_id,position), UNIQUE(report_id,name)
);
CREATE TABLE IF NOT EXISTS records (
 id INTEGER PRIMARY KEY, report_id INTEGER NOT NULL REFERENCES reports(id) ON DELETE CASCADE,
 line_no INTEGER NOT NULL CHECK(line_no>0), raw_text TEXT NOT NULL,
 excluded INTEGER NOT NULL DEFAULT 0 CHECK(excluded IN (0,1)), reason TEXT NOT NULL DEFAULT '',
 revision INTEGER NOT NULL DEFAULT 1
);
CREATE TABLE IF NOT EXISTS cells (
 record_id INTEGER NOT NULL REFERENCES records(id) ON DELETE CASCADE,
 column_id INTEGER NOT NULL REFERENCES report_columns(id) ON DELETE CASCADE,
 value TEXT NOT NULL, PRIMARY KEY(record_id,column_id)
);
CREATE TABLE IF NOT EXISTS issues (
 id INTEGER PRIMARY KEY, report_id INTEGER NOT NULL REFERENCES reports(id) ON DELETE CASCADE,
 line_no INTEGER NOT NULL, raw_text TEXT NOT NULL, message TEXT NOT NULL,
 disposition TEXT NOT NULL DEFAULT 'open' CHECK(disposition IN ('open','resolved','excluded')),
 resolution TEXT NOT NULL DEFAULT ''
);
CREATE TABLE IF NOT EXISTS conversions (
 id INTEGER PRIMARY KEY, report_id INTEGER NOT NULL REFERENCES reports(id) ON DELETE CASCADE,
 label TEXT NOT NULL CHECK(length(label) BETWEEN 1 AND 100), artifact BLOB NOT NULL,
 input_sha256 TEXT NOT NULL, artifact_sha256 TEXT NOT NULL, row_count INTEGER NOT NULL,
 created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS audit_events (
 id INTEGER PRIMARY KEY, report_id INTEGER REFERENCES reports(id) ON DELETE SET NULL,
 entity TEXT NOT NULL, entity_id INTEGER, action TEXT NOT NULL,
 details TEXT NOT NULL, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS records_by_report ON records(report_id,line_no);
CREATE INDEX IF NOT EXISTS issues_by_report ON issues(report_id,disposition);
