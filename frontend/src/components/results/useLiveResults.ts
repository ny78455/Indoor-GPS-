import { useEffect, useRef, useState } from "react";
import type { SimulationState } from "../../types";
import { buildTelemetryFrame, type LiveResultsState, type ResultRow, type SheetName } from "./types";

const RUN_ID = "live";
const MAX_LOCAL_ROWS = 5000;

export function useLiveResults(state: SimulationState): LiveResultsState {
  const [telemetry, setTelemetry] = useState<LiveResultsState>({ runId: RUN_ID, latestFrame: 0, rows: {}, pendingFrames: 0, commitError: null });
  const committedFrame = useRef(-1);

  useEffect(() => {
    if (state.frameIndex <= 0 || committedFrame.current === state.frameIndex) return;
    committedFrame.current = state.frameIndex;
    const frame = buildTelemetryFrame(state, RUN_ID);
    setTelemetry((previous) => ({
      ...previous,
      latestFrame: frame.frame_id,
      pendingFrames: previous.pendingFrames + 1,
      rows: { ...previous.rows, ...Object.fromEntries(Object.entries(frame.sheets).map(([sheet, additions]) => {
        const existing = previous.rows[sheet as SheetName] ?? [];
        return [sheet, [...existing, ...(additions ?? [])].slice(-MAX_LOCAL_ROWS)];
      })) },
    }));
    fetch(`/api/results/${RUN_ID}/frame`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(frame) })
      .then((response) => response.ok ? response.json() : response.json().then((body) => Promise.reject(new Error(body.error ?? "Telemetry commit failed"))))
      .then(() => setTelemetry((previous) => ({ ...previous, pendingFrames: Math.max(0, previous.pendingFrames - 1), commitError: null })))
      .catch((error: Error) => setTelemetry((previous) => ({ ...previous, pendingFrames: Math.max(0, previous.pendingFrames - 1), commitError: error.message })));
  }, [state.frameIndex]); // Frame ID, rather than render FPS, defines a telemetry commit.

  return telemetry;
}
