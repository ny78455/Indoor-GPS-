import express from "express";
import path from "path";
import fs from "fs";
import { exec } from "child_process";
import { createServer as createViteServer } from "vite";

async function startServer() {
  const app = express();
  const PORT = process.env.PORT ? parseInt(process.env.PORT, 10) : 3000;

  const BASE_DIR = fs.existsSync(path.join(__dirname, "package.json"))
    ? __dirname
    : path.join(__dirname, "..");

  app.use(express.json());

  // API Route: Get configuration
  app.get("/api/config", (req, res) => {
    const configPath = path.join(BASE_DIR, "VLCL_AI", "configs", "default.yaml");
    if (fs.existsSync(configPath)) {
      res.send(fs.readFileSync(configPath, "utf-8"));
    } else {
      // Fallback with default content if it doesn't exist yet
      const defaultConfig = `room:
  width: 5.0
  length: 5.0
  height: 3.0
  wall_reflectivity: 0.8
  floor_reflectivity: 0.2
  ceiling_reflectivity: 0.5

leds:
  - id: 1
    position: [1.25, 1.25, 3.0]
    orientation: [0, 0, -1]
    power: 20.0
    bias_current: 0.5
    frequency: 100000.0
    lambertian_order: 1.0
    beam_angle: 60.0
    fov: 60.0
  - id: 2
    position: [3.75, 1.25, 3.0]
    orientation: [0, 0, -1]
    power: 20.0
    bias_current: 0.5
    frequency: 150000.0
    lambertian_order: 1.0
    beam_angle: 60.0
    fov: 60.0
  - id: 3
    position: [1.25, 3.75, 3.0]
    orientation: [0, 0, -1]
    power: 20.0
    bias_current: 0.5
    frequency: 200000.0
    lambertian_order: 1.0
    beam_angle: 60.0
    fov: 60.0
  - id: 4
    position: [3.75, 3.75, 3.0]
    orientation: [0, 0, -1]
    power: 20.0
    bias_current: 0.5
    frequency: 250000.0
    lambertian_order: 1.0
    beam_angle: 60.0
    fov: 60.0

receiver:
  position: [2.5, 2.5, 0.85]
  orientation: [0, 0, 1]
  velocity: [0.2, 0.1, 0.0]
  acceleration: [0.0, 0.0, 0.0]
  fov: 70.0
  apd_size: 1e-4
  noise: 1e-14
  gain: 1.0

mobility:
  type: "circular" # static, linear, circular, random_walk, waypoint, spline
  speed: 0.5
  radius: 1.5
  center: [2.5, 2.5, 0.85]

obstacles:
  - id: "obs_human"
    type: "cylinder" # box, cylinder, sphere
    position: [2.0, 3.0, 0.9]
    rotation: [0, 0, 0]
    scale: [0.3, 0.3, 1.8] # x_radius, y_radius, height
    reflectivity: 0.3
    material: "skin_fabric"
`;
      res.send(defaultConfig);
    }
  });

  // API Route: Save configuration
  app.post("/api/config", (req, res) => {
    const { content } = req.body;
    const configPath = path.join(BASE_DIR, "VLCL_AI", "configs", "default.yaml");
    try {
      fs.mkdirSync(path.dirname(configPath), { recursive: true });
      fs.writeFileSync(configPath, content, "utf-8");
      res.json({ success: true });
    } catch (err: any) {
      res.status(500).json({ error: err.message });
    }
  });

  // API Route: Run python simulation
  app.post("/api/run", (req, res) => {
    const scriptPath = path.join(BASE_DIR, "VLCL_AI", "examples", "demo_environment.py");
    
    // Ensure directories exist
    fs.mkdirSync(path.join(BASE_DIR, "VLCL_AI", "logs"), { recursive: true });
    
    // Execute python script
    const isWin = process.platform === "win32";
    const venvPythonPath = isWin
      ? path.join(BASE_DIR, "VLCL_AI", ".venv", "Scripts", "python.exe")
      : path.join(BASE_DIR, "VLCL_AI", ".venv", "bin", "python3");
    const pythonCmd = fs.existsSync(venvPythonPath) ? venvPythonPath : (isWin ? "python" : "python3");

    exec(`${pythonCmd} "${scriptPath}"`, { cwd: BASE_DIR, env: { ...process.env, PYTHONIOENCODING: "utf-8" } }, (error, stdout, stderr) => {
      res.json({
        success: !error,
        stdout,
        stderr,
        error: error ? error.message : null
      });
    });
  });

  // API Route: Real-time Physics Engine computation
  app.post("/api/physics", (req, res) => {
    const envState = req.body;

    const isWin = process.platform === "win32";
    const venvPythonPath = isWin
      ? path.join(BASE_DIR, "VLCL_AI", ".venv", "Scripts", "python.exe")
      : path.join(BASE_DIR, "VLCL_AI", ".venv", "bin", "python3");
    const pythonCmd = fs.existsSync(venvPythonPath) ? venvPythonPath : (isWin ? "python" : "python3");

    // Inline Python script that instantiates PhysicsEngine and computes metrics
    const inlineScript = `
import sys, os, json
sys.path.insert(0, r"${BASE_DIR.replace(/\\/g, "\\\\")}")
from VLCL_AI.environment.state import EnvironmentState
from VLCL_AI.physics.physics_engine import PhysicsEngine

with open(sys.argv[1], "r", encoding="utf-8") as f:
    data = json.load(f)

state = EnvironmentState(
    current_time=data.get("current_time", 0.0),
    frame_index=data.get("frame_index", 0),
    fps=data.get("fps", 60.0),
    receiver_position=data["receiver_position"],
    receiver_orientation=data["receiver_orientation"],
    receiver_velocity=data.get("receiver_velocity", [0,0,0]),
    receiver_acceleration=data.get("receiver_acceleration", [0,0,0]),
    receiver_angles=data.get("receiver_angles", {"roll":0,"pitch":0,"yaw":0}),
    room_dims=data.get("room_dims", [5.0, 5.0, 3.0]),
    led_positions={int(k): v for k,v in data["led_positions"].items()},
    led_powers={int(k): v for k,v in data["led_powers"].items()},
    led_active={int(k): v for k,v in data["led_active"].items()},
    led_orientations={int(k): v for k,v in data["led_orientations"].items()},
    led_beam_angles={int(k): v for k,v in data["led_beam_angles"].items()},
    distances={int(k): v for k,v in data["distances"].items()},
    incident_angles_rad={int(k): v for k,v in data["incident_angles"].items()},
    irradiance_angles_rad={int(k): v for k,v in data["irradiance_angles"].items()},
    visibility_matrix={int(k): v for k,v in data["visibility_matrix"].items()},
    los_matrix={int(k): v for k,v in data["los_matrix"].items()},
    blocking_obstacles={int(k): v for k,v in data["blocking_obstacles"].items()},
    obstacles=data.get("obstacles", [])
)

engine = PhysicsEngine()
engine.compute(state)
result = engine.export()

def str_keys(d):
    return {str(k): v for k,v in d.items()} if isinstance(d, dict) else d

output = {
    "snrs": str_keys(result.get("snrs", {})),
    "received_powers": str_keys(result.get("received_powers", {})),
    "los_gains": str_keys(result.get("los_gains", {})),
    "nlos_gains": str_keys(result.get("nlos_gains", {})),
    "electrical_currents": str_keys(result.get("electrical_currents", {})),
    "voltages": str_keys(result.get("voltages", {})),
    "metrics": result.get("metrics", {})
}
print(json.dumps(output))
`;

    // Use a temp file approach for reliability (avoids shell escaping issues)

    const tmpScript = path.join(BASE_DIR, "VLCL_AI", "logs", "_physics_tmp.py");
    const tmpInput = path.join(BASE_DIR, "VLCL_AI", "logs", "_physics_input.json");

    try {
      fs.mkdirSync(path.join(BASE_DIR, "VLCL_AI", "logs"), { recursive: true });
      fs.writeFileSync(tmpScript, inlineScript, "utf-8");
      fs.writeFileSync(tmpInput, JSON.stringify(envState), "utf-8");
    } catch (e: any) {
      return res.status(500).json({ error: "Failed to write temp files: " + e.message });
    }

    exec(
      `${pythonCmd} "${tmpScript}" "${tmpInput}"`,
      { cwd: BASE_DIR, env: { ...process.env, PYTHONIOENCODING: "utf-8", LOGURU_LEVEL: "WARNING" }, timeout: 8000 },
      (error, stdout, stderr) => {
        if (error) {
          return res.status(500).json({ error: stderr || error.message });
        }
        try {
          const result = JSON.parse(stdout.trim());
          res.json({ success: true, physics: result });
        } catch {
          res.status(500).json({ error: "Failed to parse physics output", raw: stdout });
        }
      }
    );
  });

  // API Route: Real-time Communication Engine computation (Module 3)
  // Chains Physics → Communication Engine and returns OFDM/VLC KPIs
  app.post("/api/communication", (req, res) => {
    const envState = req.body;

    const isWin = process.platform === "win32";
    const venvPythonPath = isWin
      ? path.join(BASE_DIR, "VLCL_AI", ".venv", "Scripts", "python.exe")
      : path.join(BASE_DIR, "VLCL_AI", ".venv", "bin", "python3");
    const pythonCmd = fs.existsSync(venvPythonPath) ? venvPythonPath : (isWin ? "python" : "python3");

    const inlineScript = `
import sys, os, json
sys.path.insert(0, r"${BASE_DIR.replace(/\\/g, "\\\\")}")
from VLCL_AI.environment.state import EnvironmentState
from VLCL_AI.physics.physics_engine import PhysicsEngine
from VLCL_AI.communication.engine import CommunicationEngine

with open(sys.argv[1], "r", encoding="utf-8") as f:
    data = json.load(f)

env_state = EnvironmentState(
    current_time=data.get("current_time", 0.0),
    frame_index=data.get("frame_index", 0),
    fps=data.get("fps", 60.0),
    receiver_position=data["receiver_position"],
    receiver_orientation=data["receiver_orientation"],
    receiver_velocity=data.get("receiver_velocity", [0,0,0]),
    receiver_acceleration=data.get("receiver_acceleration", [0,0,0]),
    receiver_angles=data.get("receiver_angles", {"roll":0,"pitch":0,"yaw":0}),
    room_dims=data.get("room_dims", [5.0, 5.0, 3.0]),
    led_positions={int(k): v for k,v in data["led_positions"].items()},
    led_powers={int(k): v for k,v in data["led_powers"].items()},
    led_active={int(k): v for k,v in data["led_active"].items()},
    led_orientations={int(k): v for k,v in data["led_orientations"].items()},
    led_beam_angles={int(k): v for k,v in data["led_beam_angles"].items()},
    distances={int(k): v for k,v in data["distances"].items()},
    incident_angles_rad={int(k): v for k,v in data["incident_angles"].items()},
    irradiance_angles_rad={int(k): v for k,v in data["irradiance_angles"].items()},
    visibility_matrix={int(k): v for k,v in data["visibility_matrix"].items()},
    los_matrix={int(k): v for k,v in data["los_matrix"].items()},
    blocking_obstacles={int(k): v for k,v in data["blocking_obstacles"].items()},
    obstacles=data.get("obstacles", [])
)

# Step 1: Run Physics Engine to get PhysicsState
physics_engine = PhysicsEngine()
physics_state = physics_engine.compute(env_state)

# Step 2: Run Communication Engine using Physics results
comm_engine = CommunicationEngine()
comm_state = comm_engine.step(env_state, physics_state)

# Return lightweight summary dict safe for JSON
print(json.dumps(comm_state.to_summary_dict()))
`;

    const tmpScript = path.join(BASE_DIR, "VLCL_AI", "logs", "_comm_tmp.py");
    const tmpInput  = path.join(BASE_DIR, "VLCL_AI", "logs", "_comm_input.json");

    try {
      fs.mkdirSync(path.join(BASE_DIR, "VLCL_AI", "logs"), { recursive: true });
      fs.writeFileSync(tmpScript, inlineScript, "utf-8");
      fs.writeFileSync(tmpInput,  JSON.stringify(envState), "utf-8");
    } catch (e: any) {
      return res.status(500).json({ error: "Failed to write temp files: " + e.message });
    }

    exec(
      `${pythonCmd} "${tmpScript}" "${tmpInput}"`,
      { cwd: BASE_DIR, env: { ...process.env, PYTHONIOENCODING: "utf-8", LOGURU_LEVEL: "WARNING" }, timeout: 15000 },
      (error, stdout, stderr) => {
        if (error) {
          return res.status(500).json({ error: stderr || error.message });
        }
        try {
          const result = JSON.parse(stdout.trim());
          res.json({ success: true, communication: result });
        } catch {
          res.status(500).json({ error: "Failed to parse communication output", raw: stdout });
        }
      }
    );
  });


  // API Route: Real-time Localization Engine computation (Module 4 — A-DPDOA)
  // Chains Physics → LocalizationEngine and returns A-DPDOA position estimate + metrics
  app.post("/api/localization", (req, res) => {
    const envState = req.body;

    const isWin = process.platform === "win32";
    const venvPythonPath = isWin
      ? path.join(BASE_DIR, "VLCL_AI", ".venv", "Scripts", "python.exe")
      : path.join(BASE_DIR, "VLCL_AI", ".venv", "bin", "python3");
    const pythonCmd = fs.existsSync(venvPythonPath) ? venvPythonPath : (isWin ? "python" : "python3");

    const inlineScript = `
import sys, os, json
try:
    sys.path.insert(0, r"${BASE_DIR.replace(/\\/g, "\\\\")}")
    from VLCL_AI.environment.state import EnvironmentState
    from VLCL_AI.physics.physics_engine import PhysicsEngine
    from VLCL_AI.localization.engine import LocalizationEngine

    with open(sys.argv[1], "r", encoding="utf-8") as f:
        data = json.load(f)

    env_state = EnvironmentState(
        current_time=data.get("current_time", 0.0),
        frame_index=data.get("frame_index", 0),
        fps=data.get("fps", 60.0),
        receiver_position=data["receiver_position"],
        receiver_orientation=data["receiver_orientation"],
        receiver_velocity=data.get("receiver_velocity", [0,0,0]),
        receiver_acceleration=data.get("receiver_acceleration", [0,0,0]),
        receiver_angles=data.get("receiver_angles", {"roll":0,"pitch":0,"yaw":0}),
        room_dims=data.get("room_dims", [5.0, 5.0, 3.0]),
        led_positions={int(k): v for k,v in data["led_positions"].items()},
        led_powers={int(k): v for k,v in data["led_powers"].items()},
        led_active={int(k): v for k,v in data["led_active"].items()},
        led_orientations={int(k): v for k,v in data["led_orientations"].items()},
        led_beam_angles={int(k): v for k,v in data["led_beam_angles"].items()},
        distances={int(k): v for k,v in data["distances"].items()},
        incident_angles_rad={int(k): v for k,v in data["incident_angles"].items()},
        irradiance_angles_rad={int(k): v for k,v in data["irradiance_angles"].items()},
        visibility_matrix={int(k): v for k,v in data["visibility_matrix"].items()},
        los_matrix={int(k): v for k,v in data["los_matrix"].items()},
        blocking_obstacles={int(k): v for k,v in data["blocking_obstacles"].items()},
        obstacles=data.get("obstacles", [])
    )

    # Step 1: Run Physics Engine to get PhysicsState
    physics_engine = PhysicsEngine()
    physics_state = physics_engine.compute(env_state)

    # Step 2: Run Localization Engine
    loc_engine = LocalizationEngine()
    loc_state = loc_engine.step(env_state, physics_state)

    # Convert dict keys to str for JSON serialisation
    result = loc_state.to_dict()
    def str_keys(d):
        return {str(k): v for k, v in d.items()} if isinstance(d, dict) else d

    result["signals"]["received_powers"] = str_keys(result["signals"]["received_powers"])
    result["signals"]["localization_snr"] = str_keys(result["signals"]["localization_snr"])

    print(json.dumps(result))
except Exception as e:
    import traceback
    print(json.dumps({"__error__": str(e), "__traceback__": traceback.format_exc()}))
    sys.exit(1)
`;

    const tmpScript = path.join(BASE_DIR, "VLCL_AI", "logs", "_loc_tmp.py");
    const tmpInput  = path.join(BASE_DIR, "VLCL_AI", "logs", "_loc_input.json");

    try {
      fs.mkdirSync(path.join(BASE_DIR, "VLCL_AI", "logs"), { recursive: true });
      fs.writeFileSync(tmpScript, inlineScript, "utf-8");
      fs.writeFileSync(tmpInput,  JSON.stringify(envState), "utf-8");
    } catch (e: any) {
      return res.status(500).json({ error: "Failed to write temp files: " + e.message });
    }

    exec(
      `${pythonCmd} "${tmpScript}" "${tmpInput}"`,
      { cwd: BASE_DIR, env: { ...process.env, PYTHONIOENCODING: "utf-8", LOGURU_LEVEL: "WARNING" }, timeout: 30000 },
      (error, stdout, stderr) => {
        if (error && !stdout.trim()) {
          return res.status(500).json({ error: stderr || error.message });
        }
        try {
          const result = JSON.parse(stdout.trim());
          // Python emitted a caught exception — treat as error
          if (result.__error__) {
            return res.status(500).json({ error: result.__error__, traceback: result.__traceback__ });
          }
          res.json({ success: true, localization: result });
        } catch {
          res.status(500).json({ error: "Failed to parse localization output", raw: stdout.slice(0, 500) });
        }
      }
    );
  });


  // API Route: Real-time Integrated VLCL Engine computation (Module 5)
  // Chains Physics -> IntegratedVLCLEngine and returns composite communication + localization metrics
  app.post("/api/integrated", (req, res) => {
    const envState = req.body;

    const isWin = process.platform === "win32";
    const venvPythonPath = isWin
      ? path.join(BASE_DIR, "VLCL_AI", ".venv", "Scripts", "python.exe")
      : path.join(BASE_DIR, "VLCL_AI", ".venv", "bin", "python3");
    const pythonCmd = fs.existsSync(venvPythonPath) ? venvPythonPath : (isWin ? "python" : "python3");

    const inlineScript = `
import sys, os, json
try:
    sys.path.insert(0, r"${BASE_DIR.replace(/\\/g, "\\\\")}")
    from VLCL_AI.environment.state import EnvironmentState
    from VLCL_AI.physics.physics_engine import PhysicsEngine
    from VLCL_AI.integrated_vlcl.engine import IntegratedVLCLEngine

    with open(sys.argv[1], "r", encoding="utf-8") as f:
        data = json.load(f)

    env_state = EnvironmentState(
        current_time=data.get("current_time", 0.0),
        frame_index=data.get("frame_index", 0),
        fps=data.get("fps", 60.0),
        receiver_position=data["receiver_position"],
        receiver_orientation=data["receiver_orientation"],
        receiver_velocity=data.get("receiver_velocity", [0,0,0]),
        receiver_acceleration=data.get("receiver_acceleration", [0,0,0]),
        receiver_angles=data.get("receiver_angles", {"roll":0,"pitch":0,"yaw":0}),
        room_dims=data.get("room_dims", [5.0, 5.0, 3.0]),
        led_positions={int(k): v for k,v in data["led_positions"].items()},
        led_powers={int(k): v for k,v in data["led_powers"].items()},
        led_active={int(k): v for k,v in data["led_active"].items()},
        led_orientations={int(k): v for k,v in data["led_orientations"].items()},
        led_beam_angles={int(k): v for k,v in data["led_beam_angles"].items()},
        distances={int(k): v for k,v in data["distances"].items()},
        incident_angles_rad={int(k): v for k,v in data["incident_angles"].items()},
        irradiance_angles_rad={int(k): v for k,v in data["irradiance_angles"].items()},
        visibility_matrix={int(k): v for k,v in data["visibility_matrix"].items()},
        los_matrix={int(k): v for k,v in data["los_matrix"].items()},
        blocking_obstacles={int(k): v for k,v in data["blocking_obstacles"].items()},
        obstacles=data.get("obstacles", [])
    )

    # Step 1: Run Physics Engine
    physics_engine = PhysicsEngine()
    physics_state = physics_engine.compute(env_state)

    # Step 2: Run Integrated Engine
    integrated_engine = IntegratedVLCLEngine()
    integrated_state = integrated_engine.step(env_state, physics_state)

    # Convert dict keys to str for JSON serialization
    result = integrated_state.to_dict()
    
    print(json.dumps(result))
except Exception as e:
    import traceback
    print(json.dumps({"__error__": str(e), "__traceback__": traceback.format_exc()}))
    sys.exit(1)
`;

    const tmpScript = path.join(BASE_DIR, "VLCL_AI", "logs", "_integrated_tmp.py");
    const tmpInput  = path.join(BASE_DIR, "VLCL_AI", "logs", "_integrated_input.json");

    try {
      fs.mkdirSync(path.join(BASE_DIR, "VLCL_AI", "logs"), { recursive: true });
      fs.writeFileSync(tmpScript, inlineScript, "utf-8");
      fs.writeFileSync(tmpInput,  JSON.stringify(envState), "utf-8");
    } catch (e: any) {
      return res.status(500).json({ error: "Failed to write temp files: " + e.message });
    }

    exec(
      `${pythonCmd} "${tmpScript}" "${tmpInput}"`,
      { cwd: BASE_DIR, env: { ...process.env, PYTHONIOENCODING: "utf-8", LOGURU_LEVEL: "WARNING" }, timeout: 35000 },
      (error, stdout, stderr) => {
        if (error && !stdout.trim()) {
          return res.status(500).json({ error: stderr || error.message });
        }
        try {
          const result = JSON.parse(stdout.trim());
          if (result.__error__) {
            return res.status(500).json({ error: result.__error__, traceback: result.__traceback__ });
          }
          res.json({ success: true, integrated: result });
        } catch {
          res.status(500).json({ error: "Failed to parse integrated output", raw: stdout.slice(0, 500) });
        }
      }
    );
  });

  app.get("/api/visualization", (req, res) => {
    const htmlPath = path.join(BASE_DIR, "VLCL_AI", "logs", "simulation_3d.html");
    if (fs.existsSync(htmlPath)) {
      res.sendFile(htmlPath);
    } else {
      res.status(404).send("Visualization not found. Run the simulation first.");
    }
  });

  app.get("/api/export-zip", (req, res) => {
    const zipPath = path.join(BASE_DIR, "dist", "VLCL_AI_Module1.zip");
    fs.mkdirSync(path.dirname(zipPath), { recursive: true });
    
    // Use the system zip command
    exec(`zip -r "${zipPath}" VLCL_AI`, { cwd: BASE_DIR }, (error, stdout, stderr) => {
      if (error) {
        return res.status(500).json({ error: "Failed to zip package: " + error.message });
      }
      res.download(zipPath, "VLCL_AI_Module1.zip");
    });
  });

  app.get("/api/files", (req, res) => {
    const basePath = path.join(BASE_DIR, "VLCL_AI");
    const filesList: any[] = [];
    
    function scanDir(dir: string) {
      if (!fs.existsSync(dir)) return;
      const items = fs.readdirSync(dir);
      for (const item of items) {
        const fullPath = path.join(dir, item);
        const stat = fs.statSync(fullPath);
        const relPath = path.relative(basePath, fullPath);
        if (stat.isDirectory()) {
          if (item !== "__pycache__" && item !== "logs" && item !== "assets") {
            scanDir(fullPath);
          }
        } else {
          // Read up to 2MB text
          filesList.push({
            path: relPath,
            name: item,
            content: fs.readFileSync(fullPath, "utf-8")
          });
        }
      }
    }
    
    try {
      scanDir(basePath);
      res.json(filesList);
    } catch (err: any) {
      res.status(500).json({ error: err.message });
    }
  });

  // Vite middleware for development
  if (process.env.NODE_ENV !== "production") {
    const vite = await createViteServer({
      server: { middlewareMode: true },
      appType: "spa",
      root: path.join(BASE_DIR, "../frontend"),
    });
    app.use(vite.middlewares);
  } else {
    const distPath = path.join(BASE_DIR, "../frontend/dist");
    app.use(express.static(distPath));
    app.get('*', (req, res) => {
      res.sendFile(path.join(distPath, 'index.html'));
    });
  }

  app.listen(PORT, "0.0.0.0", () => {
    console.log(`Server running on port ${PORT}`);
  });
}

startServer();
