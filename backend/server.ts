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

  // API Route: View 3D Simulation HTML
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
