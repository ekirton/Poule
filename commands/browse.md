Explore Coq modules, libraries, typeclasses, and dependency structure interactively. This command is read-only — it helps you navigate and understand the available mathematical infrastructure.

## Determine the browse mode

Parse the user's arguments:

- **A module name or prefix** (e.g., `Coq.Arith`, `mathcomp.ssralg`): show module contents and structure.
- **`typeclasses`** or **`tc`** (e.g., `/browse typeclasses`): list registered typeclasses.
- **`instances <typeclass>`** (e.g., `/browse instances Decidable`): list instances of a typeclass.
- **`deps <name>`** (e.g., `/browse deps Nat.add_comm`): show what a declaration depends on.
- **`impact <name>`** (e.g., `/browse impact Nat.add_comm`): show what depends on a declaration.
- **`cycles`**: detect circular dependencies in the project.
- **No arguments**: show a top-level overview of available libraries and modules.

Optional flags:
- `--depth <n>`: for dependency browsing, maximum traversal depth (default 2).
- `--scope <prefix>`: restrict dependency results to a module prefix (e.g., `--scope Coq.Arith`).

## Step 1: Top-level overview (no arguments)

1. Call `list_modules` with no prefix to get the top-level module hierarchy.
2. Call `module_summary` to get aggregate dependency statistics.
3. Present a concise overview:
   - Available library families (Stdlib, MathComp, std++, etc.) with approximate declaration counts.
   - Top-level modules with brief descriptions of what they contain.
   - Suggest browsing into a specific module for details.

## Step 2: Module browsing

1. Call `list_modules` with the user's prefix to list submodules and declarations.
2. Call `module_summary` for dependency statistics scoped to that module.
3. Present:
   - **Submodules** — listed with brief descriptions if available.
   - **Key declarations** — notable lemmas, definitions, and typeclasses in the module.
   - **Dependencies** — which other modules this one depends on (fan-out) and which depend on it (fan-in).
   - **Navigation hints** — suggest related modules or deeper submodules to explore.

## Step 3: Typeclass browsing

### List all typeclasses

1. A proof session is required. If none is open, ask the user for a file to open a session on, or open one on a representative project file.
2. Call `list_typeclasses` with the session ID.
3. Present typeclasses grouped by library/module, with brief descriptions.

### List instances of a typeclass

1. Call `list_instances` with the typeclass name and session ID.
2. Present instances grouped by the type they instantiate, with the instance name and defining module.

## Step 4: Dependency browsing

### Transitive closure (what does X depend on?)

1. Call `transitive_closure` with the declaration name, optional `max_depth`, and optional `scope_filter`.
2. Present:
   - Total dependency count at the requested depth.
   - Dependencies grouped by module.
   - Any axiom dependencies highlighted.
   - Suggest using `/visualize deps <name>` for a graphical view.

### Impact analysis (what depends on X?)

1. Call `impact_analysis` with the declaration name, optional `max_depth`, and optional `scope_filter`.
2. Present:
   - Total dependent count — the blast radius of changing this declaration.
   - Dependents grouped by module.
   - Highlight heavily-depended-upon declarations as stability risks.

### Cycle detection

1. Call `detect_cycles` with no arguments.
2. If no cycles found, report "No circular dependencies detected."
3. If cycles found, present each cycle as a chain of declaration names, grouped by module. Suggest which dependency to break to resolve each cycle.

## Step 5: Interactive navigation

After presenting results, offer to:
- Drill deeper into a submodule (`/browse <submodule>`).
- Look up a specific declaration (`get_lemma`).
- Visualize dependencies (`/visualize deps <name>`).
- Show instances of a typeclass found during browsing.

## Edge cases

- **Unknown module prefix**: If `list_modules` returns no results, suggest similar prefixes or list the top-level modules available.
- **Typeclass not found**: Report the error and suggest using `/browse typeclasses` to see available typeclasses.
- **Very large modules (>500 declarations)**: Summarize rather than listing every declaration. Group by kind (lemmas, definitions, instances) and show counts.
- **Deep dependency chains (depth >3)**: Warn that results may be large and suggest starting at depth 1-2.
- **No proof session for typeclass queries**: Typeclass queries require a live Coq session. Offer to open one on the user's project root or a specific file.

## Clean up

If a proof session was opened specifically for this command (typeclass browsing), close it when finished. Do not close sessions the user opened before invoking this command.
