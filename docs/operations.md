# Operations and user manual

## Import and review

Choose a report name that explains its period and purpose. For the supplied September 2026 stock TXT, select the Ovol stock template. Use simple mappings only for layouts whose delimiter or exact field ranges you understand. The app accepts .txt files up to 5 MB, decodes UTF-8 (including BOM) or Windows-1252, and rejects binary/UTF-16 data.

The report page shows up to 50 records per page. Use Next/Previous to navigate. A record page places fields beside its immutable original source. Correct fields using a reason. An included invalid record must be corrected or excluded. Unknown source lines must be recovered into a record or explicitly excluded as non-data. Excluded rows remain available and appear in the workbook's Exclusions sheet.

Use Delete record only for a deliberate removal; the audit retains its original text/values and reason. Exclude is preferable when the record should be transparently listed among export exclusions. Restoring an excluded record makes it subject to validation again.

## Templates

Each custom column definition is one CSV line: Name,type,required,start,end. Use type text or decimal and required 0/1. Leave positions blank for a delimited layout. For fixed width, use ordered zero-based half-open ranges: a range 0,16 includes characters 0 through 15. Select TAB by typing TAB in the delimiter field. Built-in stock column definitions are fixed by the tested parser.

Changing a mapping affects future imports. Existing reports keep their own schema and configuration. To process the same file differently, export/back up the existing work, then delete that report and reimport the original with the correct mapping. The duplicate-file rule intentionally prevents ambiguous copies within the working list.

## Exports

Create Excel export after review. Its Data sheet contains one included record per row and real numeric values. Provenance rows correspond to Data rows and record their source lines. Metadata records digests and the original mapping configuration. Exclusions records explicit source/record omissions. Audit records actions before export creation. The snapshot's creation event is available in the app's audit history because it occurs after workbook construction.

Download retrieves the saved bytes. Rename changes only the local export label. To include newer record corrections, create a new export. Deleting an export retains the source and records. Deleting a source report removes all its related records and saved exports, so download/back up necessary files first.

## Backup and restore

1. Stop the app with Ctrl+C. Ensure all processes using this project copy have stopped.
2. Copy the complete instance directory to a secure backup location. It contains ovol.sqlite3 and the local session key.
3. Restore by stopping the app and replacing the instance directory with the chosen backup. Keep a copy of the pre-restore directory until you verify the result.
4. Restart and verify the report list, a source download and a saved export. Sessions may need a page refresh if the key changed.

Do not copy an actively changing SQLite file as a reliable backup. Use operating-system access controls for this trusted local workstation. Source records and audit details are not encrypted by this application.

## Retention

Report deletion retains audit events, which can include prior values. To remove all local POC data, stop the app and remove the instance directory from that project copy, following the team's retention requirements and backup policy. The next launch creates an empty database with the two starter templates. This is a complete reset, so do not do it on the presentation or working copy without preserving needed files.

The supplied Ovol samples and generated example workbook also contain company data. Keep those files private and apply the same retention decisions to backups and copied ZIPs. Public portfolios should use demo_clean.txt, demo_errors.txt and invented values only.

## Known limitations

The stock parser is validated against the supplied September 2026 report, not every Pronto format. PDF/OCR, scheduled ingestion, collaborative accounts, ERP write-back, cloud hosting and multi-line quoted CSV are outside this implementation. A browser visual run was blocked by the execution environment; automated route/render and workflow tests ran through Flask's test client. Teammates must perform the supplied desktop/narrow-window usability checklist on their presentation machine.
