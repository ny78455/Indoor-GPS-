import type { SimulationState } from "../../types";

export type SheetName = "overview" | "environment" | "optical_channel" | "communication" | "localization" | "subcarriers" | "power" | "optimization" | "validation" | "events" | "run_metadata";

export type ResultValue = string | number | boolean | null;
export type ResultRow = Record<string, ResultValue>;

export interface TelemetryFrame {
  telemetry_schema_version: "1.0.0";
  run_id: string;
  frame_id: number;
  simulation_time_s: number;
  wall_clock_timestamp: string;
  sheets: Partial<Record<SheetName, ResultRow[]>>;
}

export interface ResultsSnapshot {
  run_id: string;
  frame_id: number;
  rows: Partial<Record<SheetName, ResultRow[]>>;
  metadata?: ResultRow;
}

export interface LiveResultsState {
  runId: string;
  latestFrame: number;
  rows: Partial<Record<SheetName, ResultRow[]>>;
  pendingFrames: number;
  commitError: string | null;
}

const value = (candidate: unknown): ResultValue => typeof candidate === "number" && Number.isFinite(candidate) ? candidate : typeof candidate === "string" || typeof candidate === "boolean" ? candidate : null;
const recordValue = (record: Record<string, number> | undefined, id: string | number): ResultValue => value(record?.[String(id)]);

/** Maps existing validated state into rows. It intentionally contains no physics equations. */
export function buildTelemetryFrame(state: SimulationState, runId: string): TelemetryFrame {
  const frameId = state.frameIndex;
  const time = state.currentTime;
  const physics = state.physicsMetrics;
  const communication = state.commMetrics;
  const localization = state.localizationMetrics;
  const adaptive = state.adaptiveMetrics;
  const power = state.powerMetrics;
  const joint = state.jointMetrics;
  const userIds = Object.keys(communication?.rate_per_user_mbps ?? adaptive?.achievable_rates_bps ?? { "1": 0 });
  const deviceIds = userIds.length ? userIds : ["1"];
  const physicsSnrs = physics?.snrs ?? {};
  const bestLed = Object.entries(physicsSnrs).sort((a, b) => b[1] - a[1])[0]?.[0] ?? null;
  const common = { run_id: runId, frame_id: frameId, simulation_time_s: time };
  const [rxX, rxY, rxZ] = state.receiver.position;
  const overview = deviceIds.map((id) => ({
    ...common, device_id: `D${id}`, rx_x_m: rxX, rx_y_m: rxY, rx_z_m: rxZ,
    velocity_x_mps: state.receiver.velocity[0], velocity_y_mps: state.receiver.velocity[1], velocity_z_mps: state.receiver.velocity[2],
    los_led_count: Object.values(state.losMatrix).filter(Boolean).length, best_led_id: bestLed,
    best_channel_gain: bestLed ? recordValue(physics?.los_gains, bestLed) : null,
    received_optical_power_w: bestLed ? recordValue(physics?.received_powers, bestLed) : null,
    snr_db: bestLed ? recordValue(physicsSnrs, bestLed) : null,
    modulation_order: null, allocated_subcarriers: value(adaptive?.diagnostics.allocated_subcarrier_count),
    ber: recordValue(communication?.ber_per_user, id), data_rate_mbps: recordValue(communication?.rate_per_user_mbps, id),
    localization_x_m: value(localization?.estimated_position[0]), localization_y_m: value(localization?.estimated_position[1]), localization_z_m: value(localization?.estimated_position[2]),
    localization_error_m: value(localization?.errors.instantaneous_m ?? joint?.localization_error_m),
    communication_power_w: value(joint?.comm_power_w), localization_power_w: value(joint?.loc_power_w), total_power_w: value(joint?.total_power_w ?? power?.power_allocation.total_power_budget_w),
    sum_rate_mbps: value(communication?.sum_rate_mbps ?? (joint?.sum_rate_bps ? joint.sum_rate_bps / 1e6 : adaptive?.sum_rate_bps ? adaptive.sum_rate_bps / 1e6 : null)),
    qos_status: value(joint?.constraint_status.overall_feasible ?? adaptive?.qos_status),
    localization_status: value(localization?.quality.status), overall_status: value(joint?.constraint_status.overall_feasible),
  }));
  const environment = deviceIds.map((id) => ({ ...common, device_id: `D${id}`, x_m: rxX, y_m: rxY, z_m: rxZ, velocity_x_mps: state.receiver.velocity[0], velocity_y_mps: state.receiver.velocity[1], velocity_z_mps: state.receiver.velocity[2], mobility_model: state.mobility.type, room_width_m: state.room.width, room_length_m: state.room.length, room_height_m: state.room.height, obstacle_count: state.obstacles.length, visible_leds: Object.values(state.visibilityMatrix).filter(Boolean).length }));
  const opticalChannel = state.leds.map((led) => ({ ...common, device_id: "D1", led_id: `L${led.id}`, led_x_m: led.position[0], led_y_m: led.position[1], led_z_m: led.position[2], receiver_x_m: rxX, receiver_y_m: rxY, receiver_z_m: rxZ, distance_m: value(state.distances[led.id]), irradiance_angle_deg: value(state.irradianceAngles[led.id]), incidence_angle_deg: value(state.incidentAngles[led.id]), los_status: value(state.losMatrix[led.id]), los_dc_gain_h0: recordValue(physics?.los_gains, led.id), nlos_gain: recordValue(physics?.nlos_gains, led.id), total_channel_gain: bestLed === String(led.id) ? recordValue(physics?.los_gains, led.id) : null, received_optical_power_w: recordValue(physics?.received_powers, led.id), photodiode_current_a: recordValue(physics?.electrical_currents, led.id), snr_db: recordValue(physics?.snrs, led.id) }));
  const communicationRows = deviceIds.map((id) => ({ ...common, device_id: `D${id}`, signal_group: "communication", modulation_order_m: null, allocated_carrier_count: value(adaptive?.diagnostics.allocated_subcarrier_count), snr_db: bestLed ? recordValue(physicsSnrs, bestLed) : null, analytical_ber: value(power?.predicted_ber?.[id]), empirical_ber: recordValue(communication?.ber_per_user, id), bit_errors: value(communication?.metadata.bit_errors), bits_transmitted: null, evm_pct: recordValue(communication?.evm_per_user_pct, id), papr_db: value(communication?.papr_db), clipping_ratio_pct: value(communication?.clipping_ratio_pct), effective_rate_mbps: recordValue(communication?.rate_per_user_mbps, id), qos_status: value(adaptive?.qos_satisfied?.[id]) }));
  const localizationRows = localization ? [{ ...common, device_id: "D1", true_x_m: localization.true_position[0], true_y_m: localization.true_position[1], true_z_m: localization.true_position[2], estimated_x_m: localization.estimated_position[0], estimated_y_m: localization.estimated_position[1], estimated_z_m: localization.estimated_position[2], localization_error_m: localization.errors.instantaneous_m, localization_error_cm: localization.errors.instantaneous_m * 100, dpd_1: value(localization.measurements.unwrapped_phases[0]), dpd_2: value(localization.measurements.unwrapped_phases[1]), dpd_3: value(localization.measurements.unwrapped_phases[2]), i_1: value(localization.measurements.I[0]), q_1: value(localization.measurements.Q[0]), localization_power_w: value(localization.signals.tone_powers.reduce((sum, item) => sum + item, 0)), solver_iterations: localization.solver.iterations, solver_status: localization.quality.status, calibration_applied: localization.quality.calibration_applied }] : [];
  const powerRows = power ? state.leds.map((led) => ({ ...common, led_id: `L${led.id}`, device_id: "D1", total_power_budget_w: power.power_allocation.total_power_budget_w, localization_reserved_power_w: recordValue(power.power_allocation.localization_reserved_power_w, led.id), communication_available_power_w: recordValue(power.power_allocation.communication_available_power_w, led.id), allocated_power_w: recordValue(power.power_allocation.per_device_power_w, led.id), pre_eq_mode: power.pre_eq.mode, max_pre_eq_gain_db: power.pre_eq.max_gain_db, papr_db: recordValue(power.pre_eq.papr_after_db, led.id), clipping_ratio: recordValue(power.pre_eq.clipping_ratio, led.id), power_constraint_status: value(joint?.constraint_status.power_satisfied) })) : [];
  const optimizationRows = (joint?.history_summary ?? []).map((item) => ({ ...common, optimization_epoch: frameId, iteration: item.iteration, sum_rate_bps: item.sum_rate_bps, localization_error_m: item.localization_error_m, localization_requirement_m: value(joint.constraint_status.localization_target_m), localization_status: item.feasible, power_used_w: item.loc_power_w, feasible: item.feasible, converged: joint.converged, termination_reason: joint.convergence_reason }));
  return { telemetry_schema_version: "1.0.0", run_id: runId, frame_id: frameId, simulation_time_s: time, wall_clock_timestamp: new Date().toISOString(), sheets: { overview, environment, optical_channel: opticalChannel, communication: communicationRows, localization: localizationRows, power: powerRows, optimization: optimizationRows } };
}
