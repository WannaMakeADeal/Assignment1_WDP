# Project structure and responsibility map

| Path | Purpose |
| --- | --- |
| run.py, START_WINDOWS.bat, start_macos_linux.sh | Local startup |
| ovol/__init__.py | Factory, configuration, CSRF, security headers and error handling |
| ovol/blueprints/reports.py | Adil's proposed report CRUD |
| ovol/blueprints/templates.py | Lance's proposed template CRUD |
| ovol/blueprints/review.py | Ming Kong's proposed record/review CRUD |
| ovol/blueprints/exports.py | Aidan's proposed conversion CRUD |
| ovol/blueprints/common.py | Shared input and object lookup helpers |
| ovol/services/parsers.py | Abstract parser and concrete format adapters, field validation |
| ovol/services/conversion.py | Import/export orchestration and transaction rules |
| ovol/services/workbooks.py | XLSX document construction and safe cell typing |
| ovol/db.py, ovol/schema.sql, ovol/seed.py | Repository, persistence schema and first-run templates |
| ovol/templates, ovol/static | Jinja2 views and local CSS/JavaScript |
| tests | Parser and integrated workflow regression tests |
| samples | Synthetic demo TXT and private supplied client sample/reference |
| evidence | Actual test output, sample comparison and generated example XLSX |
| docs | Requirements, design, HTTP contract, assessment and review records |
| members | Four handovers, portfolio material and honest evidence templates |
| instance | Runtime-only database and key, excluded from ZIP and Git |

Controllers, data/repository logic and views have separate folders. Shared services coordinate business rules without making members' features run as separate applications. One working database supports the complete demonstration.


Design record: ChatGPT/Codex assisted with the draft of this document. The team’s accepted changes, self-check, two peer annotations and tutor decision belong in docs/assessment_records/ai_collaboration.md and each member’s peer_review.md.
