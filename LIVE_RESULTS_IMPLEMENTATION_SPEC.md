# Live Results & Telemetry Implementation Specification

## Audit and data sources

The frontend owns the render/mobility frame counter in `frontend/src/App.tsx` and polls existing backend Module 2–8 endpoints. `SimulationState` already carries the environment/geometry snapshot plus the validated module response objects. No WebSocket/SSE infrastructure or historical-results store existed.

## Canonical frame and storage

`TelemetryFrame` is an observational envelope containing `run_id`, `frame_id`, `simulation_time_s`, wall-clock timestamp, and relational sheet rows. The browser adapts values already present in `SimulationState`; it never recalculates H(0), SNR, BER, localization, allocation, or power. The Express server validates and atomically commits frames to an authoritative in-memory run store. This provides live persistence for the running server; durable database persistence is a future deployment concern.

## Sheets

The workbook exposes Overview, Environment, Optical Channel, Communication, Localization, Subcarriers, Power, Optimization, Validation, Events, and Run Metadata. Each sheet has stable machine-readable export names and explicit units in column labels. Values unavailable from existing module states remain `null`/blank.

## UI and performance

The React tab uses a virtualized-window style table (only the latest filtered 200 rows are rendered), server-backed frame commits, column visibility, sortable headers, filtering, search, sheet selection, pause/follow-latest, row inspection, and resizable columns. Historical endpoint pagination avoids ordinary table endpoints returning unbounded data.

## Export

The server snapshots only committed frames. The client requests that immutable snapshot and writes CSV, JSON, or a self-contained XLSX workbook. Exported values preserve raw numeric precision; display formatting is separate.

## Risks / compatibility

The legacy frontend does not model multiple physical receivers; the relational schema supports device IDs, while the current adapter emits the existing receiver as `D1`. Module polling is asynchronous, so a frame stores the most recently validated module result and never fabricates a missing metric. Telemetry has no simulation-side writes and therefore cannot affect calculations.
