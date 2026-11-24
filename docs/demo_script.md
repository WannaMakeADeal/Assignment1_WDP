# Integrated demonstration and rehearsal

Use a clean local database on a separate rehearsal copy. Keep the app in one browser session and hand the workstation between presenters. Use synthetic inputs for a public recording. Estimated duration below is a suggested allocation, not an official time limit.

## Adil - approximately 2 minutes

“Ovol finance staff need structured Excel data from text reports. Our application retains the original report and applies a selected layout. I manage the report workflow.” Open Reports, import samples/demo_clean.txt with the Simple delimited TXT template, show the three records, rename the report and download its source. Explain that invalid inputs create no report. Demonstrate deletion on a disposable second report at the end, after the others finish the shared flow.

Explain one code path: reports.new → import_report → get_parser → SQLite records/cells. Show that the source digest rejects identical duplicate imports.

## Lance - approximately 2 minutes

“A reusable template describes how a report becomes columns. Existing reports keep the layout used at import.” Create a template with the four demo columns, retrieve its details, edit its name and delete this disposable template. Explain fixed-width ranges and demonstrate a validation failure using overlapping ranges. Show that the built-in stock parser preserves the tested 12-column layout.

Explain one design decision: template_columns are relational current definitions; each imported report has its own column/configuration snapshot.

## Ming Kong - approximately 2 minutes

Import samples/demo_errors.txt as a different report. Open the invalid BOARD-01 record, compare the original, change “twenty five” to 25 with reason “Verified quantity from source”, and retrieve the corrected record. Create a manual source-linked row, edit it, then delete that disposable duplicate with a reason. Review the unknown comment line and exclude it as a non-data comment. Demonstrate reversible exclusion/restoration on an included record.

Explain why export blocks unresolved issues and invalid included records. Show the audit entry and describe the revision check that prevents a stale form overwriting newer values.

## Aidan - approximately 2 minutes

“The workbook is a stable copy of the reviewed data at export time.” Create a saved export of the reviewed report, open its details, rename it and download it. Show the Data table with numeric quantities, then Metadata, Exclusions, Audit and Provenance. Explain the workbook hash. Delete a disposable export while keeping the report.

As an optional integration proof, save one export, correct a value, download the original export again and show that the original workbook is unchanged. Create a new export for the revised value.

## Group close

Show evidence/sample_validation.json: 1,423 matching source/reference keys, 17,076 compared data cells, no value mismatches after three explicitly reported reference-text normalizations. Show the final test_run.txt and describe its actual test count. Do not equate one automated run time with staff time saved. Real user acceptance and new-format testing remain separate activities.

## Demonstration recovery

If a file already exists, open its existing report or use a fresh rehearsal copy. If an export blocks, read the reported issue and complete the review. If the server stops, rerun the startup script and reopen the browser. If live demonstration fails, show the generated example workbook and automated test evidence, then state which part could not be demonstrated live.
