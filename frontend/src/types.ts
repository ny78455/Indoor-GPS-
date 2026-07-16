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
  
  // Real-time calculated telemetry
  distances: Record<number, number>;
  incidentAngles: Record<number, number>;
  irradianceAngles: Record<number, number>;
  dcGains: Record<number, number>;
  losMatrix: Record<number, boolean>;
  visibilityMatrix: Record<number, boolean>;
  blockingObstacles: Record<number, string>;
  trajectoryPoints: [number, number, number][];
}
