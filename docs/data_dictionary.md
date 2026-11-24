# Data dictionary

Generated from ovol/schema.sql. SQLite foreign key enforcement is enabled on every application connection.

## audit_events

| Column | Type | Required | PK position | Default |
| --- | --- | --- | --- | --- |
| id | INTEGER | Yes | 1 | - |
| report_id | INTEGER | No | - | - |
| entity | TEXT | Yes | - | - |
| entity_id | INTEGER | No | - | - |
| action | TEXT | Yes | - | - |
| details | TEXT | Yes | - | - |
| created_at | TEXT | Yes | - | CURRENT_TIMESTAMP |

Foreign key: report_id references reports.id; ON DELETE SET NULL.

```sql
CREATE TABLE audit_events (
 id INTEGER PRIMARY KEY, report_id INTEGER REFERENCES reports(id) ON DELETE SET NULL,
 entity TEXT NOT NULL, entity_id INTEGER, action TEXT NOT NULL,
 details TEXT NOT NULL, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
```

## cells

| Column | Type | Required | PK position | Default |
| --- | --- | --- | --- | --- |
| record_id | INTEGER | Yes | 1 | - |
| column_id | INTEGER | Yes | 2 | - |
| value | TEXT | Yes | - | - |

Foreign key: column_id references report_columns.id; ON DELETE CASCADE.

Foreign key: record_id references records.id; ON DELETE CASCADE.

```sql
CREATE TABLE cells (
 record_id INTEGER NOT NULL REFERENCES records(id) ON DELETE CASCADE,
 column_id INTEGER NOT NULL REFERENCES report_columns(id) ON DELETE CASCADE,
 value TEXT NOT NULL, PRIMARY KEY(record_id,column_id)
);
```

## conversions

| Column | Type | Required | PK position | Default |
| --- | --- | --- | --- | --- |
| id | INTEGER | Yes | 1 | - |
| report_id | INTEGER | Yes | - | - |
| label | TEXT | Yes | - | - |
| artifact | BLOB | Yes | - | - |
| input_sha256 | TEXT | Yes | - | - |
| artifact_sha256 | TEXT | Yes | - | - |
| row_count | INTEGER | Yes | - | - |
| created_at | TEXT | Yes | - | CURRENT_TIMESTAMP |

Foreign key: report_id references reports.id; ON DELETE CASCADE.

```sql
CREATE TABLE conversions (
 id INTEGER PRIMARY KEY, report_id INTEGER NOT NULL REFERENCES reports(id) ON DELETE CASCADE,
 label TEXT NOT NULL CHECK(length(label) BETWEEN 1 AND 100), artifact BLOB NOT NULL,
 input_sha256 TEXT NOT NULL, artifact_sha256 TEXT NOT NULL, row_count INTEGER NOT NULL,
 created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
```

## issues

| Column | Type | Required | PK position | Default |
| --- | --- | --- | --- | --- |
| id | INTEGER | Yes | 1 | - |
| report_id | INTEGER | Yes | - | - |
| line_no | INTEGER | Yes | - | - |
| raw_text | TEXT | Yes | - | - |
| message | TEXT | Yes | - | - |
| disposition | TEXT | Yes | - | 'open' |
| resolution | TEXT | Yes | - | '' |

Foreign key: report_id references reports.id; ON DELETE CASCADE.

```sql
CREATE TABLE issues (
 id INTEGER PRIMARY KEY, report_id INTEGER NOT NULL REFERENCES reports(id) ON DELETE CASCADE,
 line_no INTEGER NOT NULL, raw_text TEXT NOT NULL, message TEXT NOT NULL,
 disposition TEXT NOT NULL DEFAULT 'open' CHECK(disposition IN ('open','resolved','excluded')),
 resolution TEXT NOT NULL DEFAULT ''
);
```

## records

| Column | Type | Required | PK position | Default |
| --- | --- | --- | --- | --- |
| id | INTEGER | Yes | 1 | - |
| report_id | INTEGER | Yes | - | - |
| line_no | INTEGER | Yes | - | - |
| raw_text | TEXT | Yes | - | - |
| excluded | INTEGER | Yes | - | 0 |
| reason | TEXT | Yes | - | '' |
| revision | INTEGER | Yes | - | 1 |

Foreign key: report_id references reports.id; ON DELETE CASCADE.

```sql
CREATE TABLE records (
 id INTEGER PRIMARY KEY, report_id INTEGER NOT NULL REFERENCES reports(id) ON DELETE CASCADE,
 line_no INTEGER NOT NULL CHECK(line_no>0), raw_text TEXT NOT NULL,
 excluded INTEGER NOT NULL DEFAULT 0 CHECK(excluded IN (0,1)), reason TEXT NOT NULL DEFAULT '',
 revision INTEGER NOT NULL DEFAULT 1
);
```

## report_columns

| Column | Type | Required | PK position | Default |
| --- | --- | --- | --- | --- |
| id | INTEGER | Yes | 1 | - |
| report_id | INTEGER | Yes | - | - |
| position | INTEGER | Yes | - | - |
| name | TEXT | Yes | - | - |
| data_type | TEXT | Yes | - | - |
| required | INTEGER | Yes | - | - |

Foreign key: report_id references reports.id; ON DELETE CASCADE.

```sql
CREATE TABLE report_columns (
 id INTEGER PRIMARY KEY, report_id INTEGER NOT NULL REFERENCES reports(id) ON DELETE CASCADE,
 position INTEGER NOT NULL, name TEXT NOT NULL, data_type TEXT NOT NULL,
 required INTEGER NOT NULL, UNIQUE(report_id,position), UNIQUE(report_id,name)
);
```

## reports

| Column | Type | Required | PK position | Default |
| --- | --- | --- | --- | --- |
| id | INTEGER | Yes | 1 | - |
| template_id | INTEGER | No | - | - |
| name | TEXT | Yes | - | - |
| filename | TEXT | Yes | - | - |
| sha256 | TEXT | Yes | - | - |
| raw_text | TEXT | Yes | - | - |
| raw_bytes | BLOB | Yes | - | - |
| template_snapshot | TEXT | Yes | - | - |
| created_at | TEXT | Yes | - | CURRENT_TIMESTAMP |

Foreign key: template_id references templates.id; ON DELETE SET NULL.

```sql
CREATE TABLE reports (
 id INTEGER PRIMARY KEY, template_id INTEGER REFERENCES templates(id) ON DELETE SET NULL,
 name TEXT NOT NULL CHECK(length(name) BETWEEN 1 AND 100), filename TEXT NOT NULL,
 sha256 TEXT NOT NULL, raw_text TEXT NOT NULL, raw_bytes BLOB NOT NULL, template_snapshot TEXT NOT NULL,
 created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
```

## template_columns

| Column | Type | Required | PK position | Default |
| --- | --- | --- | --- | --- |
| id | INTEGER | Yes | 1 | - |
| template_id | INTEGER | Yes | - | - |
| position | INTEGER | Yes | - | - |
| name | TEXT | Yes | - | - |
| data_type | TEXT | Yes | - | - |
| start_pos | INTEGER | No | - | - |
| end_pos | INTEGER | No | - | - |
| required | INTEGER | Yes | - | - |

Foreign key: template_id references templates.id; ON DELETE CASCADE.

```sql
CREATE TABLE template_columns (
 id INTEGER PRIMARY KEY, template_id INTEGER NOT NULL REFERENCES templates(id) ON DELETE CASCADE,
 position INTEGER NOT NULL CHECK(position>=0), name TEXT NOT NULL,
 data_type TEXT NOT NULL CHECK(data_type IN ('text','decimal')),
 start_pos INTEGER, end_pos INTEGER, required INTEGER NOT NULL CHECK(required IN (0,1)),
 UNIQUE(template_id, position), UNIQUE(template_id, name)
);
```

## templates

| Column | Type | Required | PK position | Default |
| --- | --- | --- | --- | --- |
| id | INTEGER | Yes | 1 | - |
| name | TEXT | Yes | - | - |
| kind | TEXT | Yes | - | - |
| delimiter | TEXT | Yes | - | ',' |
| created_at | TEXT | Yes | - | CURRENT_TIMESTAMP |

```sql
CREATE TABLE templates (
 id INTEGER PRIMARY KEY, name TEXT NOT NULL UNIQUE CHECK(length(name) BETWEEN 1 AND 80),
 kind TEXT NOT NULL CHECK(kind IN ('stock','delimited','fixed')),
 delimiter TEXT NOT NULL DEFAULT ',', created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
```


Design record: ChatGPT/Codex assisted with the draft of this document. The team’s accepted changes, self-check, two peer annotations and tutor decision belong in docs/assessment_records/ai_collaboration.md and each member’s peer_review.md.
