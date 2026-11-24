# HTTP interface specification

This implementation uses server-rendered HTML and standard browser form submissions. It does not claim a JSON REST API. GET retrieves pages/downloads. POST submits creates, updates or confirmed deletes. A GET confirmation page never deletes data.

All state-changing requests require csrf_token in the form body or X-CSRF-Token in the header, matching the current session. Successful mutations redirect with HTTP 302. HTML validation errors redisplay the form with feedback (200). Missing CSRF returns 400, missing IDs return 404, stale review revisions/decisions return 409, and request-size violations return 413. GET/POST forms use application/x-www-form-urlencoded except source upload, which uses multipart/form-data. The source and Excel download endpoints return attachments.

## Implemented routes

| Path | Methods | Handler |
| --- | --- | --- |
| `/` | GET | reports.home |
| `/exports/<int:conversion_id>` | GET | exports.detail |
| `/exports/<int:conversion_id>/delete` | GET,POST | exports.delete |
| `/exports/<int:conversion_id>/download` | GET | exports.download |
| `/exports/<int:conversion_id>/edit` | GET,POST | exports.edit |
| `/issues/<int:issue_id>/review` | GET,POST | review.issue_review |
| `/records/<int:record_id>` | GET | review.detail |
| `/records/<int:record_id>/delete` | GET,POST | review.delete |
| `/records/<int:record_id>/edit` | GET,POST | review.form |
| `/records/<int:record_id>/exclude` | GET,POST | review.exclude |
| `/reports/<int:report_id>` | GET | reports.detail |
| `/reports/<int:report_id>/audit` | GET | reports.history |
| `/reports/<int:report_id>/delete` | GET,POST | reports.delete |
| `/reports/<int:report_id>/edit` | GET,POST | reports.edit |
| `/reports/<int:report_id>/exports/new` | GET,POST | exports.new |
| `/reports/<int:report_id>/records/new` | GET,POST | review.form |
| `/reports/<int:report_id>/source` | GET | reports.source |
| `/reports/new` | GET,POST | reports.new |
| `/static/<path:filename>` | GET | static |
| `/templates` | GET | templates.index |
| `/templates/<int:template_id>` | GET | templates.detail |
| `/templates/<int:template_id>/delete` | GET,POST | templates.delete |
| `/templates/<int:template_id>/edit` | GET,POST | templates.form |
| `/templates/new` | GET,POST | templates.form |

## Request fields

| Operation | Required inputs | Validation / response |
| --- | --- | --- |
| Report create | name, template_id, file | 1-100 name characters; existing template; .txt ≤5 MB; UTF-8/CP1252; distinct SHA-256 |
| Report update | name | Rename only; original source and schema remain |
| Template create/update | name, kind, delimiter, columns | Unique name ≤80; stock/delimited/fixed; one-character delimiter or TAB; CSV column definitions |
| Record create | c_COLUMN_ID for each column, line_no, reason; optional issue_id | Existing source line, valid required/numeric values, reason ≤500 |
| Record update | c_COLUMN_ID fields, revision, reason | Same column validation; optimistic revision match |
| Record exclude/restore/delete | reason | Required reason ≤500; decision written to audit |
| Issue exclusion | reason | Issue must still be open; decision written to audit |
| Export create/update | label | 1-100 characters; create revalidates the included dataset |
| Report/template/export delete | csrf_token | Confirmation screen describes cascading effects |

## Example native-form interaction

1. GET /reports/new to obtain a page and session token.
2. POST /reports/new with multipart fields name=September, template_id=1, file=<TXT bytes>, csrf_token=<session token>.
3. On success, follow Location: /reports/{id}.
4. GET /reports/{id}/exports/new and POST label plus token.
5. Follow the redirect to /exports/{id}; its /download endpoint returns XLSX bytes.

## Response contracts

Report details display report metadata, up to 50 records per page, validity/exclusion state, source exceptions and saved exports. Template details display ordered columns and types. Record detail displays every value alongside original source. Export details display label, row count, creation time and stored digests. User-controlled text is HTML-escaped. Invalid data is never inserted into an export merely because client-side validation is bypassed.

## Versioning and integration

The interface is a local POC without external consumers. A future JSON API should use separately versioned endpoints with explicit JSON schemas, authentication and authorization. Keep this current contract aligned with route code rather than documenting unimplemented REST verbs.

Design record: ChatGPT/Codex assisted with the draft of this document. The team’s accepted changes, self-check, two peer annotations and tutor decision belong in docs/assessment_records/ai_collaboration.md and each member’s peer_review.md.
