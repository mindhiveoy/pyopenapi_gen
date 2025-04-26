# Task Board – pyopenapi_gen

Legend: ⬜ To Do | 🔄 In‑Progress | ⛔ Blocked | ✅ Done

---

## 0. Foundation & Tooling
| Status | Task |
|--------|------|
| ✅ | Research parser libraries & choose openapi‑spec‑validator + openapi‑core |
| ✅ | Project scaffolding (`src/pyopenapi_gen/`, `tests/`) |
| ✅ | Implement ImportCollector utility for consistent imports management |

## 1. Internal IR Layer
| Status | Task |
|--------|------|
| ✅ | Define IR dataclasses (`IRSpec`, `IRSchema`, `IROperation`, ...) |
| ✅ | Write unit tests for dataclass validation & linking |
| ✅ | Implement spec→IR loader (basic paths, schemas) |

## 2. Parsing, Validation & Warnings
| Status | Task |
|--------|------|
| ✅ | Integrate openapi‑spec‑validator into loader |
| ✅ | Implement WarningCollector with remediation hints |
| ✅ | Create test fixtures for malformed specs |
| ✅ | Support multipart/form‑data request bodies in IR loader |
| ✅ | Recognize binary/streaming response schemas in IR loader |

## 3. Model Emitter Slice
| Status | Task |
|--------|------|
| ✅ | Extract NameSanitizer helper and integrate into model emitter templates |
| ✅ | Design Jinja2 templates for dataclass models |
| ✅ | Generate one model per schema into `models/` |
| ✅ | Black‑format emitted code |
| ✅ | Snapshot tests for generated models |
| ✅ | Enhance model emitter to handle arrays, enums, and complex types |
| ✅ | Integrate ImportCollector for consistent imports in generated models |
| ✅ | Introduce Formatter helper to run Black on emitted model files |
| ✅ | Write unit tests for model file name sanitization and formatting |
| ✅ | Implement TemplateRenderer helper for models emitter and update model templates to use it |

## 4. Endpoint & Tag Emitter Slice
| Status | Task |
|--------|------|
| ✅ | Generate per‑tag classes & per‑operation modules |
| ✅ | Implement lazy‑loading via `__getattr__` stubs |
| ✅ | Snapshot tests + runtime import tests |
| ✅ | Emit file‑upload parameters (multipart/form‑data) in endpoint methods |
| ✅ | Emit streaming methods for binary/stream responses |
| ✅ | Use ImportCollector for consistent imports in endpoint modules |
| ✅ | Implement NameSanitizer helper to convert spec tag/schema names into valid Python file and module names |
| ✅ | Implement ParamSubstitutor helper for URL rendering |
| ✅ | Implement KwargsBuilder helper for assembling request kwargs |
| ✅ | Refactor endpoint templates to use NameSanitizer, ParamSubstitutor, KwargsBuilder |
| ✅ | Add unit tests for endpoint file naming and URL rendering |
| ✅ | Implement TemplateRenderer helper for endpoints emitter and update endpoint templates to use it |

## 5. Client Core Slice
| Status | Task |
|--------|------|
| ✅ | Implement `ClientConfig` and base async client using httpx |
| ✅ | Pluggable `HttpTransport` protocol & default httpx transport |
| ✅ | Pagination helper base + auto‑detection logic |
| ✅ | Configuration env‑var & TOML layering |
| ✅ | Use ImportCollector for client-related modules |
| ✅ | Extract ConfigLoader helper for layered config logic |
| ✅ | Add unit tests for default transport and config layering |
| ✅ | Integrate Formatter helper for client core modules |

## 6. Authentication Plugins
| Status | Task |
|--------|------|
| ✅ | Implement `BaseAuth` protocol |
| ✅ | BearerAuth plugin |
| ✅ | HeadersAuth plugin |
| ✅ | Unit tests & composition tests |

## 7. Exception Hierarchy
| Status | Task |
|--------|------|
| ✅ | Design `HTTPError` base + 4XX / 5XX subclasses |
| ✅ | Generate spec‑specific exception aliases |

## 8. CLI & UX
| Status | Task |
|--------|------|
| ✅ | Implement Typer‑based CLI: `gen`, `docs` commands |
| ✅ | Support `--name`, `--auth`, `--docs`, `--telemetry`, `--force` flags |
| ✅ | Diff detection & exit codes |
| ✅ | Refactor backup and diff logic into FileManager helper |
| ✅ | Add unit tests for CLI FileManager backup & diff functionality |

## 9. Documentation Site
| Status | Task |
|--------|------|
| ✅ | MkDocs configuration + theme |
| ✅ | Docs emitter to generate markdown pages |
| ✅ | GH Pages publish workflow |
| ✅ | Implement TemplateRenderer helper for docs emitter and add unit tests for docs templates |

## 10. Telemetry & Metrics
| Status | Task |
|--------|------|
| ✅ | Implement opt‑in telemetry client |
| ✅ | CLI flag & env‑var wiring |
| ✅ | Unit tests (ensure no network when disabled) |

## 11. End‑to‑End Demo & Examples
| Status | Task |
|--------|------|
| ✅ | Petstore spec integration test (generate + run) |
| ✅ | Example usage snippets for README |

## 12. CI & Deployment (Final Phase)
| Status | Task |
|--------|------|
| ✅ | Setup GitHub Actions CI (Py 3.10‑3.12, macOS & Ubuntu) |
| ✅ | Add pre‑commit hooks (black, ruff, mypy) |
| ✅ | GH Pages publish workflow |

## 13. Release & Distribution
| Status | Task |
|--------|------|
| ⬜ | Finalize PyPI packaging and publish v1.0.0 |
| ⬜ | Write and test Homebrew formula for CLI |
| ⬜ | Complete release checklist and tag v1.0.0 |

# Future work

## 14. Sync Client Generation
| Status | Task |
|--------|------|
| ⬜ | Design and implement sync client architecture |
| ⬜ | Add sync emitters and templates |
| ⬜ | Write tests for sync client generation |

## 15. Plugin Ecosystem Expansion
| Status | Task |
|--------|------|
| ⬜ | Add Pydantic/attrs model emitters as plugins |
| ⬜ | Implement spec adapter plugin interface |
| ⬜ | Add more built-in and plugin-based paginators |

## 16. Performance & Scalability
| Status | Task |
|--------|------|
| ⬜ | Profile and optimize for large OpenAPI specs |
| ⬜ | Investigate and implement parallel code generation |

## 17. Advanced OpenAPI Features
| Status | Task |
|--------|------|
| ⬜ | Add support for callbacks, webhooks, and links |
| ⬜ | Implement OpenAPI 2.x and 3.0 adapters |
| ⬜ | Allow user-defined error class mapping |

## 18. Community & Documentation
| Status | Task |
|--------|------|
| ⬜ | Expand usage and plugin authoring docs |
| ⬜ | Add more real-world example projects |
| ⬜ | Set up Discussions, issue/PR templates, code of conduct |

## 19. Ongoing Maintenance
| Status | Task |
|--------|------|
| ⬜ | Add more CI test scenarios for edge cases |
| ⬜ | Monitor and update dependencies |
| ⬜ | Collect user feedback and iterate features |

> **Process Note**: Update status as work progresses. A slice may only advance to the next when all tasks in the current slice are `DONE` and coverage thresholds are met. 