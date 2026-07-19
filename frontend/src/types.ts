export interface RoomParams {
  width: number;
  length: number;
  height: number;
  wallReflectivity: number;
  floorReflectivity: number;
  ceilingReflectivity: number;
}

export interface LEDParams {
  id: number;
  position: [number, number, number];
  orientation: [number, number, number];
  power: number;
  biasCurrent: number;
  frequency: number;
  lambertianOrder: number;
  beamAngle: number;
  fov: number;
  communicationEnabled: boolean;
  localizationEnabled: boolean;
}

export interface ReceiverParams {
  position: [number, number, number];
  orientation: [number, number, number];
  velocity: [number, number, number];
  acceleration: [number, number, number];
  fov: number;
  apdSize: number;
  noise: number;
  gain: number;
  roll: number;
  pitch: number;
  yaw: number;
}

export interface ObstacleParams {
  id: string;
  type: "box" | "cylinder" | "sphere";
  position: [number, number, number];
  rotation: [number, number, number]; // roll, pitch, yaw
  scale: [number, number, number]; // box: [dx,dy,dz], cylinder: [r,r,h], sphere: [r,r,r]
  reflectivity: number;
  material: string;
}

export interface MobilityParams {
  type: "static" | "linear" | "circular" | "random_walk" | "waypoint";
  speed: number;
  radius: number;
  center: [number, number, number];
  waypoints: [number, number, number][];
}

// Full physics metrics returned by the PhysicsEngine
export interface PhysicsMetrics {
  snrs: Record<string, number>;               // dB per LED
  received_powers: Record<string, number>;    // Watts per LED
  los_gains: Record<string, number>;          // LOS channel gain per LED
  nlos_gains: Record<string, number>;         // NLOS channel gain per LED
  electrical_currents: Record<string, number>; // Amps per LED
  voltages: Record<string, number>;           // Volts per LED
  metrics: {
    average_channel_gain: number;
    average_snr: number;                      // dB
    visible_leds: number;
    blocked_leds: number;
    propagation_delay: number;                // seconds
    total_optical_power: number;              // Watts
  };
}

export interface SimulationState {
  currentTime: number;
  frameIndex: number;
  fps: number;
  isPlaying: boolean;
  speedFactor: number;
  room: RoomParams;
  leds: LEDParams[];
  receiver: ReceiverParams;
  obstacles: ObstacleParams[];
  mobility: MobilityParams;
  
  // Real-time calculated telemetry (JS)
  distances: Record<number, number>;
  incidentAngles: Record<number, number>;
  irradianceAngles: Record<number, number>;
  dcGains: Record<number, number>;
  losMatrix: Record<number, boolean>;
  visibilityMatrix: Record<number, boolean>;
  blockingObstacles: Record<number, string>;
  trajectoryPoints: [number, number, number][];

  // Full physics engine metrics (Python backend)
  physicsMetrics: PhysicsMetrics | null;
  physicsLoading: boolean;
}
