Change control: If templates affecting this surface change, update this file in the same PR.

# Components and Required Selectors

The following UI components must retain these `data-testid` hooks for tests and monitoring.

| Component | Location | Selector |
|-----------|----------|----------|
| Post card | Feed lists and post stubs | `data-testid="post-card"` |
| Sidebar CTA block | Right sidebar | `data-testid="sidebar-cta"` |
| Submit Post form | `/submit` page | `data-testid="submit-form"` |

These selectors are exercised by the `smoke_ui_contract` management command.
