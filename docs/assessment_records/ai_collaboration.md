# Collaboration and refinement record

Tool: OpenAI ChatGPT/Codex. Scope: requirements and source analysis, design, Python/Flask implementation, verification, documentation, handover and presentation preparation. The supplied code and documents include generated material. Individual student review and contributions remain to be recorded.

## Verified refinements
The implementation handles leading decimal points in the supplied report, preserves original bytes, isolates three known reference-description artefacts, blocks exports with unresolved issues, checks stale revisions and retains saved workbook bytes after later edits. The current regression run passes 49 cases with 91% statement coverage. The reference comparison covers 1,423 rows and 17,076 cells with no mismatches after the stated reference-only normalisation.

## Design lab records to complete
The guidebook requires use-case and design artefacts, prompt-and-refinement records, student evaluation, two annotated peer reviews and tutor approval. Keep the actual lab prompts, generated drafts, student revisions and reasons for accepting or rejecting each change in the repository. The included technical artefacts and automated checks do not establish that these personal review steps have happened.

For each record, identify the use case, exact prompt, retained output, specific student amendment, test result, reviewers and dated tutor decision. Record actual feedback and decisions. Do not mark unperformed reviews or approvals complete.

## Report review refinement in the supplied reference
The earlier report screen offered “Create Excel export” even when a rejected field needed attention. A report with no included records also showed “Ready to export”. A reviewer could have to search every page to find the problem.

The revised primary action opens the first invalid record across the entire report; otherwise it opens the first unresolved source line. A clean report offers export. An empty selection offers a reviewed record entry. The export service still validates every request.

Tests in tests/test_workflow.py place a bad record in position 51, then follow the separate unknown-line, clean and all-excluded states. All 49 regression cases pass. This is a documented tool-assisted change to the reference. Member evaluation and dated peer annotations remain open.
