# Test Writing Guidelines

## Source of Authority

Tests are derived from specification documents (`specification/`). The specification is authoritative for all behavioral expectations, formulas, contracts, and edge cases. When writing a test, consult the relevant specification — not intuition or general expectations about how a function "should" behave.

Authority chain: `specification/*.md` → `doc/architecture/` → `doc/architecture/data-models/`

## Upstream Authority Is Immutable

Specification documents (`specification/`), architecture documents (`doc/architecture/`), and data model documents (`doc/architecture/data-models/`) **must not be modified** when writing tests. Tests encode the specification contracts using TDD — they are derived from the spec, not the other way around.

- If a specification appears ambiguous or incorrect, file feedback in `specification/feedback/` — do not change the spec. Follow the feedback standards defined in `specification/feedback/CLAUDE.md`.
- If an architecture or data model document conflicts with a specification, file feedback in `doc/architecture/feedback/`. Follow the feedback standards defined in `doc/architecture/feedback/CLAUDE.md`.
- If a test cannot be written to match the spec, the issue belongs in feedback, not in a spec edit.

## Numeric Bounds Must Be Formula-Derived

When a specification defines a formula, all test bounds and expected values **must be computed from that formula** — never estimated by intuition.

- **Compute the expected value** by substituting the test input into the spec formula before choosing an assertion bound.
- **Show the derivation** in a comment next to the assertion so reviewers can verify it.
- **Do not use "round number" bounds** (e.g., `< 1.01`) unless the formula confirms they hold at the chosen input.

Example — wrong:
```python
# "Should be very close to 1.0 for large freq"
assert symbol_weight(1_000_000) < 1.01  # intuition, not derived
```

Example — correct:
```python
# 1.0 + 2.0 / log2(1_000_001) ≈ 1.1003
assert symbol_weight(1_000_000) < 1.2
```

## Mock Discipline

Every `Mock()` or `patch()` requires a corresponding **contract test** that exercises the real implementation against the same interface. Skipping via pytest marker (e.g., `@pytest.mark.requires_coq`) is acceptable when external tools are needed; omitting the test is not.

```python
# Good: consumer test mocks the backend
def test_pipeline_calls_backend():
    backend = Mock()
    backend.list_declarations.return_value = [("A", "Lemma", {})]
    ...

# Good: contract test verifies real backend satisfies the same interface
@pytest.mark.requires_coq
def test_coq_lsp_backend_list_declarations():
    backend = CoqLspBackend(...)
    decls = backend.list_declarations(Path("test_fixture.vo"))
    assert isinstance(decls, list)
    assert all(len(d) == 3 for d in decls)

# Bad: consumer test exists but no contract test for the real implementation
```

Before declaring a task phase complete, verify every `Mock()`/`patch()` has a corresponding contract test. If not, the phase is incomplete.

### Mock Return Values Must Use Real Types

Mock `return_value` must use the actual type the real implementation returns (e.g., dataclass, not `dict`). This exercises serialization and attribute-access paths in the consumer.

## Test File Feedback

When a test appears to conflict with its specification, file feedback in `test/feedback/<test-file-name>.md` describing the discrepancy. Do not silently adjust the test or the implementation. Follow the feedback standards defined in `test/feedback/CLAUDE.md`.
