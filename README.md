# Ovol ReportBridge

PS 9g / SCCCI ID 28. A local Python Flask application that converts Ovol's Pronto ERP TXT reports into structured Excel workbooks. Start with `../00_START_HERE.txt` or the instructions below.

## Run on Windows

1. Install Python 3.12 or newer from python.org and enable the Python launcher.
2. Extract the ZIP completely. Double-click `START_WINDOWS.bat`.
3. Open http://127.0.0.1:5000 in a browser on the same computer. Keep the terminal open.
4. Choose **Import a TXT report**. Use `samples/demo_clean.txt` with **Simple delimited TXT**, or the supplied stock sample with **Ovol Stock Valuation - Sep 2026**.
5. Review records, then create and download an Excel export.

Manual setup:

```powershell
py -3 -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe run.py
```

macOS/Linux: `sh start_macos_linux.sh`. This installs dependencies on the first run and starts a loopback-only Waitress server. The application itself needs no external API, paid service or internet connection after installation. Python packages must be available for installation.

## Four integrated features

| Proposed owner | Feature | Create | Retrieve | Update | Delete |
| --- | --- | --- | --- | --- | --- |
| Adil | Reports | Upload source and parse | List, details, original download | Rename | Delete report and dependent data |
| Lance | Mapping templates | Add layout | List and schema details | Change name/layout/columns | Delete while retaining imported snapshots |
| Ming Kong | Reviewed records | Recover or add a source-linked record | Values beside original source | Correct values with reason | Delete with audit, or exclude reversibly |
| Aidan | Excel conversions | Create validated snapshot | Details and download | Rename saved export | Delete export while retaining source |

Each member's folder contains a guide, code map, presentation practice, portfolio template and contribution/review records.

## What works

- Complete parsing of the supplied September 2026 stock valuation report, including page breaks, multiple item groups, multi-line descriptions and both warehouses.
- Reusable delimited and fixed-width mappings for other simple TXT layouts. The built-in stock layout uses its tested schema.
- Required-field and numeric validation. Unknown lines require an explicit decision. Invalid included rows block export.
- Source bytes and source SHA-256 retained, correction audit history, optimistic edit revisions and consistent export transactions.
- Typed numeric Excel cells, one record per row, an Excel table and source-line provenance. Workbook sheets: Data, Provenance, Metadata, Exclusions, Audit.
- Saved Excel snapshots keep their original bytes after later edits. Untrusted text cells are explicitly written as strings.
- SQLite persistence, CSRF-protected forms, Jinja2 autoescaping, request limits, security headers, host validation and loopback binding.

## Verify

```powershell
.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.venv\Scripts\python.exe -m pytest --cov=ovol --cov-report=term-missing
.venv\Scripts\python.exe validate_sample.py
```

Use `.venv/bin/python` on macOS/Linux. The included evidence records the actual checks run while constructing this baseline. `validate_sample.py` checks the generated workbook, not just the parser's in-memory output.

## Assessment and review status

The application and documents are ready for team testing and rehearsal. Each member should go through their guide, run their assigned feature and practise explaining the code. Complete the two peer reviews and tutor design review before submission.

The assessment checklist is in docs/rubric_traceability.md. Required process records are kept in docs/assessment_records/ai_collaboration.md and docs/review_gate.md. Each personal folder includes editable portfolio documents and a contribution log.

## Boundaries

This POC targets a trusted local workstation. It has no individual login, role-based permissions, network deployment, encryption-at-rest or scheduled processing. Audit events identify the workspace, not the human operator. Do not expose it to a network without a separate access-control and deployment design. The built-in parser is verified against one supplied stock report; other complex reports require their own tested parser. PDF extraction is outside the confirmed TXT POC.

Company samples and example outputs are included for private team assessment use. Keep them out of public GitHub repositories, public portfolios and LinkedIn posts. Portfolio templates use descriptive text and should use synthetic demonstration screenshots. Do not publish until each member has reviewed the content.

Working data lives in `instance/ovol.sqlite3`, created on first launch. Stop the server before copying the entire `instance` directory for backup. Retained audit details may contain corrected values. A report deletion removes related source data, rows and exports, but preserves audit events. See `docs/operations.md` for backup, restore and retention instructions.
