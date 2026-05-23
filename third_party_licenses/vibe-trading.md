# HKUDS/Vibe-Trading Snapshot Notice

- Upstream repository: `https://github.com/HKUDS/Vibe-Trading`
- Vendored path: `vendor/vibe-trading/`
- Snapshot commit: `a74bca22c1a415c5cd4e6bda6d01e77c7e1746e9`
- Snapshot date observed in this workspace analysis: `2026-05-22`
- License: MIT, see `vendor/vibe-trading/LICENSE`
- Upstream notice file: `vendor/vibe-trading/NOTICE`

This workspace vendors the upstream project as an isolated source snapshot.
Project-specific integration code lives under `trading_core/`; upstream source
under `vendor/vibe-trading/` should remain unmodified so future manual syncs can
be audited cleanly.

The Vibe-Trading Alpha Zoo and related subdirectories are retained as part of
the upstream snapshot. Before redistributing derived factor datasets or reports,
review the corresponding upstream files and any embedded third-party notices.
