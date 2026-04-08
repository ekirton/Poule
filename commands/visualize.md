Generate visual diagrams of proof states, proof trees, dependencies, or proof evolution. Writes a self-contained HTML file to `proof-diagram.html` in the project directory. This command is read-only.

## Determine the visualization type

Parse the user's arguments to select a visualization mode:

- **`state`** or **`proof state`** (e.g., `/visualize state`): render the current proof state as a diagram.
- **`tree`** (e.g., `/visualize tree`): render the complete proof tree.
- **`deps <name>`** (e.g., `/visualize deps Nat.add_comm`): render a dependency graph for a declaration.
- **`sequence`** or **`steps`** (e.g., `/visualize sequence`): render step-by-step proof evolution.
- **No arguments**: infer from context — if in a proof session, default to `state`; otherwise ask.

Optional flags:
- `--detail <level>`: `summary`, `standard` (default), or `detailed` — controls how much information each node shows.
- `--depth <n>`: for dependency graphs, maximum depth (default 2, max 5).
- `--max-nodes <n>`: for dependency graphs, cap on total nodes (default 50).
- `--step <n>`: for proof state visualization, show the state at step N instead of the current step.

## Step 1: Ensure prerequisites

### For proof state, tree, or sequence visualizations

A proof session must be open. Check with `list_proof_sessions`.

- If a session is open, use it.
- If no session is open and the user specified a file and proof name, call `open_proof_session` to start one.
- If no session is open and no file was specified, ask the user which proof to visualize.

### For dependency visualizations

No proof session is required. The user must provide a declaration name. If not given, ask for one.

## Step 2: Generate the diagram

### Proof state (`visualize_proof_state`)

1. Call `visualize_proof_state` with the `session_id` and optional `step` and `detail_level`.
2. The tool returns Mermaid diagram text and writes `proof-diagram.html`.

### Proof tree (`visualize_proof_tree`)

1. The proof must be complete (all goals closed). If goals remain, inform the user and suggest using `state` mode instead.
2. Call `visualize_proof_tree` with the `session_id`.
3. The tool returns a tree diagram showing how subgoals were created and resolved.

### Dependencies (`visualize_dependencies`)

1. Call `visualize_dependencies` with the declaration `name`, `max_depth`, and `max_nodes`.
2. The tool returns a graph diagram with visual distinction between theorems, definitions, and axioms.

### Proof sequence (`visualize_proof_sequence`)

1. Call `visualize_proof_sequence` with the `session_id` and optional `detail_level`.
2. The tool returns a series of diagrams showing how the proof state evolves at each tactic step, with diffs highlighted.

## Step 3: Present the result

1. Confirm which diagram was generated.
2. Tell the user: "Open `proof-diagram.html` in your browser to view the diagram. Refresh after each new visualization."
3. Provide a brief text summary of what the diagram shows:
   - For **state**: number of goals, key hypotheses, goal types.
   - For **tree**: depth, number of branches, which tactics created subgoals.
   - For **deps**: number of nodes, any axioms found, key dependency chains.
   - For **sequence**: number of steps, where the proof branches or merges.

## Edge cases

- **No proof session and mode requires one**: Tell the user to open a proof first, or offer to open one if they specify the file and proof name.
- **Proof tree on incomplete proof**: Explain that proof tree requires a complete proof. Suggest `state` or `sequence` instead.
- **Large dependency graph (>50 nodes at requested depth)**: The `max_nodes` parameter caps the output. If the cap is hit, mention that the diagram is truncated and suggest reducing depth or adding a scope filter.
- **Multiple active sessions**: If more than one proof session is open, ask which one to visualize.

## Clean up

Do not close the proof session after visualization — the user likely wants to continue working with it. Only close if you opened a session specifically for this command and the user did not ask for an interactive session.
