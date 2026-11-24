# Wireframe and prototype review

This file supplies screen intent and evaluation prompts. It does not claim that a student has completed a prototype review or that a client has tested it.

| Screen | Main user goal | Primary action | Error/alternate state | Evaluation question |
| --- | --- | --- | --- | --- |
| Report list | Find the source to convert | Import a TXT report | Empty list | Can a first-time user find the import action? |
| Import | Choose source and layout | Import & review | Bad file, duplicate or empty file | Is the stock template choice clear? |
| Report details | Identify required corrections | Review record / create export | Invalid field or unknown source line | Is it clear why export is blocked? |
| Record review | Compare extracted values with source | Correct record | Excluded or invalid record | Can the reviewer see the source and value together? |
| Correction form | Fix an error accurately | Save reviewed record | Stale revision or invalid number | Does the form explain how to recover? |
| Source exception | Recover data or explain exclusion | Recover as record | Already reviewed issue | Could a user accidentally discard a real record? |
| Template editor | Define meaningful output fields | Save template | Duplicate/overlapping columns | Does a staff member understand zero-based ranges? |
| Export details | Obtain a stable Excel file | Download Excel | Report changed after snapshot | Is the saved snapshot behaviour clear? |

Use case → screen trace: UC01 covers list/import/details, UC02 covers template list/editor/detail, UC03 covers record/source review and UC04 covers export form/detail. The working local prototype is the Jinja2 application in ovol/templates. Screens adapt to narrow windows in app.css. Keyboard focus, labels, table headings and skip navigation are included.

## Three practical review tasks

1. A peer imports demo_clean.txt without instructions. Record where they hesitate and whether they choose the correct template.
2. A peer imports demo_errors.txt, corrects “twenty five” to 25, and excludes the non-data comment with a reason. Record any confusion.
3. A peer exports, changes a record and downloads the earlier export again. Ask them to explain which version they received.

For each task, record participant, date, observed issue, actual change and retest result. Do not invent observations. The built-in stock mapping avoids exposing range editing to everyday users. A future friendlier custom-layout builder can replace the CSV definition editor after observing real staff difficulty.


Design record: ChatGPT/Codex assisted with the draft of this document. The team’s accepted changes, self-check, two peer annotations and tutor decision belong in docs/assessment_records/ai_collaboration.md and each member’s peer_review.md.

## Report detail prototype comparison
| State observed in the data | Earlier primary action | Revised action and outcome |
| --- | --- | --- |
| Bad quantity on a later page | Create Excel export | Review first invalid record opens the affected row directly. |
| Unknown source line only | Create Excel export | Review first unknown line opens the decision form. |
| All records excluded | Create Excel export; status read Ready | Add a reviewed record and an empty-selection explanation. |
| Valid included rows, clean source | Create Excel export | Export opens normally. |

Reproduce with the sample files or run the two report-action tests. For the assessed peer walkthrough, ask the reviewer to reach the issue without telling them its line number. Record their actual route and any hesitation.
