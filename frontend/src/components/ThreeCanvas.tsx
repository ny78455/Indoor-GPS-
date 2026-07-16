import { useEffect, useRef } from "react";
import * as THREE from "three";
import { OrbitControls } from "three/examples/jsm/controls/OrbitControls.js";
import { SimulationState } from "../types";

interface ThreeCanvasProps {
  state: SimulationState;
}

export default function ThreeCanvas({ state }: ThreeCanvasProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const rendererRef = useRef<THREE.WebGLRenderer | null>(null);
  const sceneRef = useRef<THREE.Scene | null>(null);
  const cameraRef = useRef<THREE.PerspectiveCamera | null>(null);
  const controlsRef = useRef<OrbitControls | null>(null);

  // Group references to easily update positions
  const rxMeshRef = useRef<THREE.Group | null>(null);
  const rxFovConeRef = useRef<THREE.Mesh | null>(null);
  const ledsGroupRef = useRef<THREE.Group | null>(null);
  const obstaclesGroupRef = useRef<THREE.Group | null>(null);
  const raysGroupRef = useRef<THREE.Group | null>(null);
  const trajectoryLineRef = useRef<THREE.Line | null>(null);
  const roomGridRef = useRef<THREE.LineSegments | null>(null);

  // 1. Initial Scene Setup
  useEffect(() => {
    if (!containerRef.current) return;

    const width = containerRef.current.clientWidth;
    const height = containerRef.current.clientHeight;

    // Create scene with a dark tech theme background
    const scene = new THREE.Scene();
    scene.background = new THREE.Color(0x0a0f1d);
    sceneRef.current = scene;

    // Camera
    const camera = new THREE.PerspectiveCamera(50, width / height, 0.1, 50);
    // Position camera looking down into the room
    camera.position.set(state.room.width * 1.5, state.room.height * 1.8, state.room.length * 1.5);
    cameraRef.current = camera;

    // Renderer with antialiasing
    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    renderer.setSize(width, height);
    renderer.setPixelRatio(window.devicePixelRatio);
    containerRef.current.appendChild(renderer.domElement);
    rendererRef.current = renderer;

    // Controls
    const controls = new OrbitControls(camera, renderer.domElement);
    controls.enableDamping = true;
    controls.dampingFactor = 0.05;
    controls.maxPolarAngle = Math.PI / 2 - 0.01; // Don't go below floor
    controls.minDistance = 2;
    controls.maxDistance = 25;
    controls.target.set(state.room.width / 2, state.room.height / 3, state.room.length / 2);
    controls.update();
    controlsRef.current = controls;

    // Lighting
    const ambientLight = new THREE.AmbientLight(0xffffff, 0.25);
    scene.add(ambientLight);

    const dirLight1 = new THREE.DirectionalLight(0xffffff, 0.6);
    dirLight1.position.set(10, 15, 10);
    scene.add(dirLight1);

    const dirLight2 = new THREE.DirectionalLight(0x58a6ff, 0.2);
    dirLight2.position.set(-10, 5, -10);
    scene.add(dirLight2);

    // Helpers
    // 3D Grid floor
    const gridHelper = new THREE.GridHelper(20, 20, 0x30363d, 0x1f242c);
    gridHelper.position.set(5, 0, 5);
    scene.add(gridHelper);

    // 3D Coordinate Axes at origin (0, 0, 0)
    // Red: X, Green: Y, Blue: Z
    const axesHelper = new THREE.AxesHelper(1.5);
    axesHelper.position.set(0.01, 0.01, 0.01);
    // Make axes thicker
    (axesHelper.material as THREE.Material).depthWrite = true;
    scene.add(axesHelper);

    // Groups for active entities
    const ledsGroup = new THREE.Group();
    scene.add(ledsGroup);
    ledsGroupRef.current = ledsGroup;

    const obstaclesGroup = new THREE.Group();
    scene.add(obstaclesGroup);
    obstaclesGroupRef.current = obstaclesGroup;

    const raysGroup = new THREE.Group();
    scene.add(raysGroup);
    raysGroupRef.current = raysGroup;

    // Add Receiver model
    const rxGroup = new THREE.Group();
    
    // Photodiode base block
    const baseGeo = new THREE.CylinderGeometry(0.12, 0.15, 0.08, 16);
    const baseMat = new THREE.MeshStandardMaterial({ color: 0x388bfd, metalness: 0.8, roughness: 0.2 });
    const baseMesh = new THREE.Mesh(baseGeo, baseMat);
    baseMesh.position.y = 0.04;
    rxGroup.add(baseMesh);

    // Active APD circular sensor surface (glowing cyan)
    const pdGeo = new THREE.CylinderGeometry(0.07, 0.07, 0.01, 16);
    const pdMat = new THREE.MeshBasicMaterial({ color: 0x58a6ff });
    const pdMesh = new THREE.Mesh(pdGeo, pdMat);
    pdMesh.position.y = 0.085;
    rxGroup.add(pdMesh);

    // Dynamic orientation vector indicator (thick pin)
    const arrowGeo = new THREE.ConeGeometry(0.04, 0.15, 8);
    const arrowMat = new THREE.MeshBasicMaterial({ color: 0xffe27e });
    const arrowMesh = new THREE.Mesh(arrowGeo, arrowMat);
    arrowMesh.position.y = 0.2;
    arrowMesh.rotation.x = 0; // points up along local Y
    rxGroup.add(arrowMesh);

    scene.add(rxGroup);
    rxMeshRef.current = rxGroup;

    // Add Receiver FOV cone (translucent, pointer aligned)
    // Re-create dynamically with correct FOV size
    const fovRadius = 1.0 * Math.tan((state.receiver.fov * Math.PI) / 180);
    const fovConeGeo = new THREE.ConeGeometry(fovRadius, 1.0, 32, 1, true); // open ended
    // Rotate cone geometry so it points in the correct alignment direction
    fovConeGeo.translate(0, 0.5, 0); // shift origin to apex
    fovConeGeo.rotateX(Math.PI); // flip upside down so apex is at bottom
    const fovConeMat = new THREE.MeshBasicMaterial({
      color: 0x58a6ff,
      transparent: true,
      opacity: 0.12,
      side: THREE.DoubleSide,
      depthWrite: false
    });
    const fovCone = new THREE.Mesh(fovConeGeo, fovConeMat);
    rxGroup.add(fovCone);
    rxFovConeRef.current = fovCone;

    // Add Trajectory line
    const trajGeo = new THREE.BufferGeometry();
    const trajMat = new THREE.LineBasicMaterial({ color: 0x2ea44f, linewidth: 2 });
    const trajLine = new THREE.Line(trajGeo, trajMat);
    scene.add(trajLine);
    trajectoryLineRef.current = trajLine;

    // Handle container resize
    const handleResize = () => {
      if (!containerRef.current || !rendererRef.current || !cameraRef.current) return;
      const w = containerRef.current.clientWidth;
      const h = containerRef.current.clientHeight;
      cameraRef.current.aspect = w / h;
      cameraRef.current.updateProjectionMatrix();
      rendererRef.current.setSize(w, h);
    };
    window.addEventListener("resize", handleResize);

    // Animation Loop
    let animationFrameId: number;
    const animate = () => {
      animationFrameId = requestAnimationFrame(animate);
      if (controlsRef.current) controlsRef.current.update();
      if (rendererRef.current && sceneRef.current && cameraRef.current) {
        rendererRef.current.render(sceneRef.current, cameraRef.current);
      }
    };
    animate();

    return () => {
      window.removeEventListener("resize", handleResize);
      cancelAnimationFrame(animationFrameId);
      if (rendererRef.current && containerRef.current) {
        rendererRef.current.dispose();
        // eslint-disable-next-line react-hooks/exhaustive-deps
        containerRef.current.removeChild(renderer.domElement);
      }
    };
  }, []);

  // 2. Room boundaries update
  useEffect(() => {
    const scene = sceneRef.current;
    if (!scene) return;

    // Remove old room wireframe
    if (roomGridRef.current) {
      scene.remove(roomGridRef.current);
    }

    const { width, length, height } = state.room;

    // Room outer wireframe box
    const boxGeo = new THREE.BoxGeometry(width, height, length);
    const edges = new THREE.EdgesGeometry(boxGeo);
    const lineMat = new THREE.LineBasicMaterial({ color: 0x30363d, linewidth: 2 });
    const roomWireframe = new THREE.LineSegments(edges, lineMat);
    
    // Position wireframe center
    roomWireframe.position.set(width / 2, height / 2, length / 2);
    scene.add(roomWireframe);
    roomGridRef.current = roomWireframe;

    // Adjust camera look-at targets if room size changes drastically
    if (controlsRef.current) {
      controlsRef.current.target.set(width / 2, height / 3, length / 2);
    }
  }, [state.room]);

  // 3. Obstacles rebuild
  useEffect(() => {
    const group = obstaclesGroupRef.current;
    if (!group) return;

    // Clear old
    while (group.children.length > 0) {
      group.remove(group.children[0]);
    }

    state.obstacles.forEach((obs) => {
      let geo: THREE.BufferGeometry;
      const mat = new THREE.MeshStandardMaterial({
        color: 0xda3637, // crimson/red
        transparent: true,
        opacity: 0.6,
        roughness: 0.5,
        metalness: 0.2
      });

      if (obs.type === "sphere") {
        geo = new THREE.SphereGeometry(obs.scale[0], 24, 24);
      } else if (obs.type === "cylinder") {
        // scale: [radius, radius, height]
        geo = new THREE.CylinderGeometry(obs.scale[0], obs.scale[0], obs.scale[2], 24);
      } else {
        // box scale: [dx, dy, dz]
        geo = new THREE.BoxGeometry(obs.scale[0], obs.scale[2], obs.scale[1]); // height is z in python, y in three
      }

      const mesh = new THREE.Mesh(geo, mat);
      
      // Position
      // Note: In Python, Z is up. In Three.js, Y is up.
      // Python coordinates: [x, y, z] -> Three.js coordinates: [x, z, y]
      // Wait, let's map: Three.js [x, y, z] to Python [x, z, y] or keep it consistent:
      // Let's map Python Z to Three.js Y, and Python Y to Three.js Z.
      mesh.position.set(obs.position[0], obs.position[2], obs.position[1]);
      
      // Rotation
      mesh.rotation.set(
        THREE.MathUtils.degToRad(obs.rotation[0]),
        THREE.MathUtils.degToRad(obs.rotation[2]), // yaw around vertical
        THREE.MathUtils.degToRad(obs.rotation[1])
      );

      group.add(mesh);
    });
  }, [state.obstacles]);

  // 4. LEDs rebuild (and FOV Cones)
  useEffect(() => {
    const group = ledsGroupRef.current;
    if (!group) return;

    // Clear old
    while (group.children.length > 0) {
      group.remove(group.children[0]);
    }

    state.leds.forEach((led) => {
      const ledGroup = new THREE.Group();
      ledGroup.position.set(led.position[0], led.position[2], led.position[1]);

      // LED physical light fixture (gray disc)
      const fixtureGeo = new THREE.CylinderGeometry(0.12, 0.12, 0.04, 16);
      const fixtureMat = new THREE.MeshStandardMaterial({ color: 0x484f58, metalness: 0.8 });
      const fixture = new THREE.Mesh(fixtureGeo, fixtureMat);
      fixture.rotation.x = Math.PI / 2; // face down
      ledGroup.add(fixture);

      // LED active emitter (bright yellow glow sphere)
      const bulbGeo = new THREE.SphereGeometry(0.06, 12, 12);
      const bulbMat = new THREE.MeshBasicMaterial({ color: 0xffe27e });
      const bulb = new THREE.Mesh(bulbGeo, bulbMat);
      bulb.position.y = -0.02;
      ledGroup.add(bulb);

      // LED emission cone
      // Light cones spread downwards. Apex is at LED position (0, 0, 0 in group).
      // Height of room is 3m, let's draw cone to the floor (height of led is ledGroup.position.y)
      const coneHeight = led.position[2]; // down to Z=0
      const coneRadius = coneHeight * Math.tan((led.fov / 2 * Math.PI) / 180);
      const coneGeo = new THREE.ConeGeometry(coneRadius, coneHeight, 32, 1, true);
      coneGeo.translate(0, -coneHeight / 2, 0); // shift origin to apex
      coneGeo.rotateX(Math.PI); // point downwards

      // Light color: communication is yellow, localization is blue/cyan
      const color = led.id % 2 === 0 ? 0xffe27e : 0x58a6ff;
      const coneMat = new THREE.MeshBasicMaterial({
        color: color,
        transparent: true,
        opacity: 0.05,
        side: THREE.DoubleSide,
        depthWrite: false
      });
      const cone = new THREE.Mesh(coneGeo, coneMat);
      ledGroup.add(cone);

      group.add(ledGroup);
    });
  }, [state.leds]);

  // 5. Dynamic Frame updates (Receiver Position, Orientation, Trajectory, and Rays)
  useEffect(() => {
    // 5.1. Update Receiver position & orientation
    const rxGroup = rxMeshRef.current;
    if (rxGroup) {
      // Map Python [x, y, z] -> Three.js [x, z, y]
      // Wait, Z is height in python, so it goes to Three.js Y.
      // Y is length in python, so it goes to Three.js Z.
      const rxX = state.receiver.position[0];
      const rxY = state.receiver.position[2]; // height
      const rxZ = state.receiver.position[1]; // length
      rxGroup.position.set(rxX, rxY, rxZ);

      // Rotate receiver group according to roll, pitch, yaw
      rxGroup.rotation.set(
        THREE.MathUtils.degToRad(state.receiver.roll),
        THREE.MathUtils.degToRad(state.receiver.yaw),
        THREE.MathUtils.degToRad(state.receiver.pitch)
      );

      // Adjust Receiver FOV cone orientation (which is inside rxGroup, so it inherits rotation)
      // If we want to change FOV angle in real time:
      const fovCone = rxFovConeRef.current;
      if (fovCone) {
        const currentRadius = 1.2 * Math.tan(((state.receiver.fov / 2) * Math.PI) / 180);
        fovCone.scale.set(currentRadius, 1.2, currentRadius);
      }
    }

    // 5.2. Update Trajectory Line
    const trajLine = trajectoryLineRef.current;
    if (trajLine && state.trajectoryPoints.length > 1) {
      const points: THREE.Vector3[] = [];
      state.trajectoryPoints.forEach((pt) => {
        points.push(new THREE.Vector3(pt[0], pt[2], pt[1])); // mapping X, Z, Y
      });
      trajLine.geometry.setFromPoints(points);
      trajLine.geometry.computeBoundingSphere();
    }

    // 5.3. Update Optical Rays (LOS vs Blocked)
    const raysGroup = raysGroupRef.current;
    if (raysGroup) {
      // Clear old rays
      while (raysGroup.children.length > 0) {
        raysGroup.remove(raysGroup.children[0]);
      }

      state.leds.forEach((led) => {
        const isLos = state.losMatrix[led.id];
        const isFov = state.visibilityMatrix[led.id];
        const blockingObs = state.blockingObstacles[led.id];

        // Draw line from LED position to Receiver position
        const pLed = new THREE.Vector3(led.position[0], led.position[2], led.position[1]);
        const pRx = new THREE.Vector3(state.receiver.position[0], state.receiver.position[2], state.receiver.position[1]);

        let rayColor = 0xda3637; // Default blocked is red
        if (isLos) {
          rayColor = isFov ? 0x2ea44f : 0x8b949e; // Green if full LOS & active, grey if out of FOV
        }

        const points = [pLed, pRx];
        const rayGeo = new THREE.BufferGeometry().setFromPoints(points);
        
        let rayMat: THREE.Material;
        if (!isLos) {
          // Draw dashed line for blocked paths
          rayMat = new THREE.LineDashedMaterial({
            color: rayColor,
            dashSize: 0.1,
            gapSize: 0.08,
            linewidth: 1.5
          });
        } else {
          rayMat = new THREE.LineBasicMaterial({
            color: rayColor,
            linewidth: isFov ? 2.5 : 1
          });
        }

        const ray = new THREE.Line(rayGeo, rayMat);
        if (!isLos) ray.computeLineDistances(); // Required for dashed lines

        raysGroup.add(ray);

        // Optional: Draw a tiny visual marker on the blocking obstacle intersection
        if (!isLos && blockingObs) {
          const obs = state.obstacles.find(o => o.id === blockingObs);
          if (obs) {
            // Draw a tiny red intersection point near the obstacle
            const interGeo = new THREE.SphereGeometry(0.03, 8, 8);
            const interMat = new THREE.MeshBasicMaterial({ color: 0xff0000 });
            const interMesh = new THREE.Mesh(interGeo, interMat);
            // Midpoint approximation
            interMesh.position.copy(pLed).add(pRx).multiplyScalar(0.5);
            raysGroup.add(interMesh);
          }
        }
      });
    }
  }, [state.receiver, state.trajectoryPoints, state.leds, state.losMatrix, state.visibilityMatrix, state.blockingObstacles, state.obstacles]);

  return (
    <div id="three-canvas-container" className="relative w-full h-full rounded-xl overflow-hidden bg-slate-950 border border-slate-800">
      <div ref={containerRef} className="w-full h-full" />
      
      {/* Visual legends overlay */}
      <div className="absolute top-4 left-4 p-3 rounded-lg bg-slate-900/95 border border-slate-800/80 backdrop-blur-sm shadow-xl flex flex-col gap-2 text-xs text-slate-300 pointer-events-none select-none">
        <h4 className="font-semibold text-slate-200 border-b border-slate-800 pb-1 mb-1 flex items-center gap-1.5">
          <span className="w-2.5 h-2.5 rounded-full bg-blue-500 animate-pulse"></span>
          3D Visual Legend
        </h4>
        <div className="flex items-center gap-2">
          <span className="w-3 h-0.5 bg-green-500 rounded"></span>
          <span>Line-of-Sight (LOS) Ray</span>
        </div>
        <div className="flex items-center gap-2">
          <span className="w-3 h-0.5 border-t border-dashed border-red-500"></span>
          <span>Blocked Ray (NLOS)</span>
        </div>
        <div className="flex items-center gap-2">
          <span className="w-3 h-3 bg-yellow-400/20 rounded-full border border-yellow-400/40"></span>
          <span>Comm LED Cone</span>
        </div>
        <div className="flex items-center gap-2">
          <span className="w-3 h-3 bg-cyan-400/20 rounded-full border border-cyan-400/40"></span>
          <span>Loc LED Cone</span>
        </div>
        <div className="flex items-center gap-2">
          <span className="w-3 h-3 bg-blue-500/20 rounded-full border border-blue-500/50"></span>
          <span>Receiver FOV Cone</span>
        </div>
        <div className="flex items-center gap-2">
          <span className="w-3 h-3 bg-red-600/50 rounded border border-red-500"></span>
          <span>Obstacle Blockers</span>
        </div>
      </div>
    </div>
  );
}
