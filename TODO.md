# ScriptRunner Syntax Redesign TODO

## Phase 1: Documentation and Examples
- [x] Rewrite `docs/syntax_manual.md` with new uniform command structure, expanded commands, enhanced expressions, scoped variables, advanced events, and improved modularity.
- [x] Update `scripts/main.yaml` to demonstrate new syntax features (e.g., loops, expressions, error handling).

## Phase 2: Parser Updates
- [x] Modify `src/domain/parser/parser.py` to validate new structures (e.g., scoped variables, parameterized events, namespaced includes).
- [x] Add semantic validation for expressions and types.

## Phase 3: Runtime Enhancements
- [x] Refactor `src/domain/runtime/core_command_executor.py` to handle uniform YAML commands only.
- [x] Extend `src/domain/runtime/interfaces.py` with new interfaces (e.g., `ILoopExecutor`, `IAsyncExecutor`).
- [x] Update `src/domain/runtime/script_action_executor.py` to remove legacy string-based actions.
- [x] Add new executor classes for loops, async, and input handling.

## Phase 4: Utilities and Validation
- [ ] Create `src/utils/expression_engine.py` for advanced expression evaluation (functions, array ops).
- [ ] Enhance `src/utils/syntax_checker.py` for type hints and assertions.

## Phase 5: Testing and Migration
- [ ] Add unit tests in `tests/` for new features.
- [ ] Create a migration script to convert old syntax to new.
- [ ] Test with complex examples (interactive game with loops, async, and events).

## Phase 6: Finalization
- [ ] Update README.md and other docs with migration guide.
- [ ] Ensure backward compatibility where possible.
