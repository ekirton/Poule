You are executing the `/run-e2e` command. This command runs end-to-end tests by executing user prompts from `test/e2e/test_*.md` files against the Poule MCP tools, recording results in `test/e2e/results.md`, and updating `examples/README.md` to list only passing prompts.

## Determine scope

The user may provide a scope argument after `/run-e2e`:
- A specific test file name or pattern (e.g., `test_navigation.md`, `navigation`): run only that test file.
- No argument: run all `test/e2e/test_*.md` files.

Use `Glob` with the pattern `test/e2e/test_*.md` to collect the list of test files.

## Run tests and collect results

Before running any tests, read `test/e2e/results.md` and `examples/README.md` to understand their current structure and content.

Accumulate all test results in memory as you go. For each result, store: the section name, the prompt number (e.g., 1.1), the prompt text, the result (PASS/FAIL), and the one-line reason.

For each test file in scope, read the file and extract every prompt (text inside ``` fenced code blocks).

For each prompt:

1. **Slash commands.** If the prompt starts with `/` (e.g., `/explain-error`, `/formalize`), invoke it using the `Skill` tool with the skill name and any arguments. Then evaluate the result the same way as any other prompt.

2. **Direct prompts.** For all other prompts, call the appropriate Poule MCP tools as a user would. Use your judgment to select tools — the prompt text describes what the user wants, not which tool to call. For prompts that require a proof session, open one, execute the steps, then close it when done.

3. **Evaluate the result:**
   - **PASS** — tool returned relevant, non-empty results that answer the question.
   - **FAIL** — tool returned an error, empty results, or clearly unrelated results.

4. **Record a one-line reason** summarizing what happened: which tool was called, what it returned, and why it passes or fails. Be specific — name the tool, mention result counts, cite key identifiers found.

Number prompts sequentially within each section (e.g., 1.1, 1.2, ... for Discovery and Search; 2.1, 2.2, ... for Errors).

## Write results.md in one shot

Once all tests have been executed and results collected, generate the **complete** `test/e2e/results.md` file content and write it using the `Write` tool in a single call. Do NOT use the `Edit` tool to update rows one at a time.

The generated file must include:

1. The header with the "Tested:" line (today's date and the extent of the retest, e.g., "full retest of all prompts" or "retested navigation and debugging sections only").
2. The summary total line (e.g., "**Summary: 60 PASS, 19 FAIL, 10 SKIP (89 total)**").
3. The per-section summary table with PASS/FAIL/SKIP counts.
4. Each section with its full results table (columns: `#`, `Prompt`, `Result`, `Reason`).
5. A "Remaining Issues" section:
   - For a **full retest**: write issues only for current FAIL results. Start fresh — do not carry over old issues.
   - For a **partial retest**: preserve existing issues for sections not retested. Delete issues whose referenced tests now pass. Add new issues for new FAIL results.

For a partial retest (only some sections re-run): preserve the existing results rows for sections not in scope, and replace only the sections that were retested.

## Write examples/README.md in one shot

Generate the **complete** `examples/README.md` file content and write it using the `Write` tool in a single call. Do NOT use the `Edit` tool to add/remove prompts one at a time.

Synchronize it with the test results:
- **Include** all passing prompts under the appropriate section and subsection heading.
- **Exclude** all failing prompts.
- Slash command prompts follow the same PASS/FAIL rules as other prompts.
- Preserve the existing section structure, introductory text, and subsection headings from the file you read at the start.

## Example data

Example Coq files in `examples/` provide project context for prompts that reference specific files: `algebra.v` (my_lemma, ring_morph, axiom comparisons), `typeclasses.v` (Proper instances, setoid rewriting, typeclass resolution), `dependent.v` (convoy pattern, dependent types), `automation.v` (auto vs eauto, hint databases, custom Ltac), `flocq.v` (bpow/simpl debugging).

## Cleanup

Close all open proof sessions before finishing. Use `list_proof_sessions` to check, then `close_proof_session` for each.

## Output

When done, print a summary:
- Date and scope of the test run
- Total PASS / FAIL / SKIP counts
- List of any newly failing prompts (regressions)
- List of any newly passing prompts (fixes)
- Confirmation that `results.md` and `examples/README.md` have been updated
