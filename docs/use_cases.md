# Use cases and user journeys

## UC01 - Import and manage a source report (Adil)

Actor: finance staff member using the local workstation. Trigger: a Pronto TXT report needs analysis. Preconditions: the local app is running and a matching mapping template exists. Success: an immutable source and parsed records are stored together.

1. Staff choose Import a TXT report, enter a meaningful name, choose the layout and select the file.
2. The server checks extension, size, encoding and exact-file duplication.
3. The selected parser returns records, known layout exclusions and unrecognised source lines.
4. One database transaction creates the report, its column snapshot, records, cells, issues and audit event.
5. Staff view the report, rename it, download the exact original bytes, or confirm deletion.

Alternatives: bad extension, empty/binary file, invalid template or duplicate digest produces an explanation and creates no report. A structurally unknown line remains visible for review. A report with no included records cannot export. Deletion cascades to rows and exports while retaining audit history.

Journey: “I have a text report” → choose file/layout → inspect extracted records → continue to review. Screen trace: reports.html, report_form.html, report_detail.html, confirm.html. Data trace: reports, report_columns, records, cells, issues and audit_events.

## UC02 - Maintain a mapping template (Lance)

Actor: staff member familiar with a report layout. Preconditions: its field boundaries or delimiter are known. Success: future imports use the saved mapping.

1. Open Mapping templates and choose New template.
2. Choose the built-in stock parser, delimited TXT or fixed-width TXT.
3. For custom layouts, define each heading, data type, required flag and field range where applicable.
4. Validate names, ordering, ranges and supported types before saving parent and column rows atomically.
5. Read the schema details, edit the layout, or confirm deletion.

Alternatives: repeated names, invalid delimiter, malformed CSV definitions or overlapping ranges return errors without replacing the current configuration. The stock parser retains its built-in schema. Updating or deleting a template never reparses existing reports: imported reports retain snapshots.

Journey: identify layout → define columns → check schema → reuse on next import. Screen trace: templates.html, template_form.html, template_detail.html. Data trace: templates and template_columns, with immutable snapshots in reports/report_columns.

## UC03 - Review and correct records (Ming Kong)

Actor: finance reviewer. Preconditions: a source has been imported. Success: included records contain valid fields and unknown source lines have explicit decisions.

1. Open a record beside the original source text.
2. Correct a field and provide a reason. The server validates all values and checks the submitted revision before updating cells.
3. Alternatively, exclude a record with a reason, restore it, or delete it with an audit entry retaining its prior values.
4. Review each unrecognised line. Recover it as a validated, source-linked record or explicitly exclude it as non-data.
5. Return to the report and confirm there are no invalid included records or open source exceptions.

Alternatives: a missing required field or bad decimal leaves saved values unchanged. A stale edit returns HTTP 409. A reviewed source issue cannot be recovered or excluded again. Manual record creation requires a source line that exists in the uploaded file.

Journey: “This value looks wrong” → compare source → correct with reason → verify saved values/audit. Screen trace: record_detail.html, record_form.html, issue.html and confirm.html. Data trace: records, cells, issues and audit_events.

## UC04 - Save and manage Excel exports (Aidan)

Actor: finance staff member. Preconditions: the report has at least one included row, no invalid included values and no open source exceptions. Success: a saved XLSX snapshot is available for analysis.

1. Choose Create Excel export and enter a useful label.
2. The service locks a consistent database transaction, revalidates included rows and computes a reviewed-data fingerprint.
3. The workbook writer creates typed Data cells, source-line provenance, metadata, exclusions and an audit sheet.
4. Store workbook bytes and SHA-256, then show a download link.
5. Staff may rename or delete the saved export. Download always returns its stored bytes.

Alternatives: validation failures block export without creating a conversion. Changes made after export require a new snapshot. Deleting a saved export retains the source report and its reviewed records.

Journey: “My rows are ready” → name export → download → analyse in Excel. Screen trace: export_form.html, export_detail.html and report_detail.html. Data trace: conversions with reports and audit_events.

## Business needs and acceptance

| Need | Evidence / reasoning | Acceptance criterion |
| --- | --- | --- |
| Reduce repetitive conversion | Client reports about 10 hours/month spent converting | Repeatable upload-to-XLSX workflow; record real staff timings in UAT |
| Keep columns aligned | Client describes tedious column separation/rework | All 1,423 sample records and numeric values match the supplied reference |
| Start analysis in Excel | Client requests one record per row and meaningful headings | Data sheet has named columns, numeric cells and no subtotal rows |
| Retain user control | Client favours practical local on-demand processing | Local file selection, explicit review and a user-triggered export |
| Handle variable layouts | Client says standard layouts are fixed but analytical reports can vary | Reusable simple mappings; unfamiliar complex formats fail visibly and require new tests |

Sources: Project 28 in the SCCCI problem statements, the Ovol meeting summary and G-ID28 client clarification. Business benefits are intended outcomes, not established savings.


Design record: ChatGPT/Codex assisted with the draft of this document. The team’s accepted changes, self-check, two peer annotations and tutor decision belong in docs/assessment_records/ai_collaboration.md and each member’s peer_review.md.
