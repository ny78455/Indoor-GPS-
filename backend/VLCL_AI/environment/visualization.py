import os
import json
from typing import Dict, Any, List
from loguru import logger

class Offline3DVisualizer:
    """
    Renders the VLCL 3D environment scene.
    Since execution often occurs in headless containers (such as AI Studio or Cloud servers)
    where OpenGL/PyVista canvas windows are unavailable, this engine generates a fully-featured, 
    interactive, zoomable, and rotatable 3D Plotly scene exported directly to an HTML file.
    This offers an interactive web visualizer without graphics card requirements!
    """
    def __init__(self, room_dims: List[float]):
        self.room_dims = room_dims
        self.points_trajectory = []

    def add_trajectory_point(self, pos: List[float]):
        self.points_trajectory.append(pos)

    def generate_interactive_html(self, scene_spec: Dict[str, Any], state: Any, 
                                  filename: str = "VLCL_AI/logs/simulation_3d.html") -> str:
        """
        Creates a high-fidelity Plotly 3D scatter/mesh representation of the laboratory room,
        LED array cones, receiver orientation, obstacle meshes, and direct/blocked optical rays.
        """
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        
        # Build JSON telemetry data for offline loading
        telemetry_data = {
            "scene": scene_spec,
            "state": state.to_dict() if hasattr(state, "to_dict") else state,
            "trajectory": self.points_trajectory
        }
        
        # We can construct a highly styled standalone HTML file that uses Plotly.js (loaded via CDN)
        # to render a full-screen, gorgeous, dark/light themed 3D Digital Twin!
        # This makes it completely responsive, interactive, and beautifully visualizable.
        
        html_template = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>VLCL Digital Twin 3D Environment</title>
    <script src="https://cdn.plot.ly/plotly-2.24.1.min.js"></script>
    <style>
        body {{
            margin: 0;
            padding: 0;
            background-color: #0d1117;
            color: #c9d1d9;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif;
            overflow: hidden;
        }}
        #header {{
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            background: rgba(22, 27, 34, 0.9);
            border-bottom: 1px solid #30363d;
            padding: 10px 20px;
            box-sizing: border-box;
            z-index: 10;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        #header h1 {{
            margin: 0;
            font-size: 18px;
            color: #58a6ff;
            font-weight: 600;
        }}
        #header .meta {{
            font-size: 12px;
            color: #8b949e;
        }}
        #plot {{
            width: 100vw;
            height: 100vh;
        }}
        #overlay {{
            position: absolute;
            bottom: 20px;
            left: 20px;
            background: rgba(22, 27, 34, 0.95);
            border: 1px solid #30363d;
            border-radius: 6px;
            padding: 15px;
            width: 320px;
            z-index: 10;
            box-shadow: 0 4px 12px rgba(0,0,0,0.5);
            font-size: 13px;
        }}
        .metric-row {{
            display: flex;
            justify-content: space-between;
            margin-bottom: 6px;
            border-bottom: 1px solid rgba(48, 54, 61, 0.5);
            padding-bottom: 4px;
        }}
        .metric-row:last-child {{
            border-bottom: none;
        }}
        .label {{
            color: #8b949e;
            font-weight: 500;
        }}
        .val {{
            font-family: monospace;
            color: #58a6ff;
            font-weight: 600;
        }}
        .badge-los {{
            background-color: #2ea44f;
            color: white;
            padding: 1px 5px;
            border-radius: 3px;
            font-size: 10px;
        }}
        .badge-blocked {{
            background-color: #da3637;
            color: white;
            padding: 1px 5px;
            border-radius: 3px;
            font-size: 10px;
        }}
    </style>
</head>
<body>
    <div id="header">
        <div>
            <h1>VLCL Research Lab 3D Digital Twin</h1>
            <div class="meta">Integrated Visible Light Communication and Localization Simulation Engine</div>
        </div>
        <div class="meta">Simulation Time: <span style="color:#58a6ff; font-weight:bold;">{state.current_time:.2f}s</span> | FPS: <span style="color:#2ea44f;">{state.fps:.1f}</span></div>
    </div>

    <div id="plot"></div>

    <div id="overlay">
        <h3 style="margin-top:0; color:#58a6ff; border-bottom: 1px solid #30363d; padding-bottom:6px;">Terminal Metrics</h3>
        <div class="metric-row">
            <span class="label">Receiver position:</span>
            <span class="val">[{state.receiver_position[0]:.2f}, {state.receiver_position[1]:.2f}, {state.receiver_position[2]:.2f}] m</span>
        </div>
        <div class="metric-row">
            <span class="label">Orientation (R/P/Y):</span>
            <span class="val">{state.receiver_angles['roll']:.1f}&deg;, {state.receiver_angles['pitch']:.1f}&deg;, {state.receiver_angles['yaw']:.1f}&deg;</span>
        </div>
        <div class="metric-row">
            <span class="label">Velocity:</span>
            <span class="val">[{state.receiver_velocity[0]:.2f}, {state.receiver_velocity[1]:.2f}, {state.receiver_velocity[2]:.2f}] m/s</span>
        </div>
        
        <h4 style="margin-bottom:6px; color:#58a6ff;">LED Channel Status</h4>
        <div id="led-list"></div>
    </div>

    <script>
        const telemetry = {json.dumps(telemetry_data)};
        const scene = telemetry.scene;
        const state = telemetry.state;
        const traj = telemetry.trajectory;
        
        // Populate HTML UI
        const ledListDiv = document.getElementById("led-list");
        Object.keys(state.led_positions).forEach(id => {{
            const dist = state.metrics.distances[id];
            const isLos = state.visibility.los_matrix[id];
            const inFov = state.visibility.visibility_matrix[id];
            const gain = state.metrics.dc_gains[id];
            const statusBadge = isLos ? '<span class="badge-los">LOS</span>' : '<span class="badge-blocked">BLOCKED</span>';
            
            const row = document.createElement("div");
            row.className = "metric-row";
            row.innerHTML = `
                <span class="label">LED ${{id}} (D: ${{dist.toFixed(2)}}m):</span>
                <span>${{statusBadge}} <span class="val" style="color: ${{inFov ? '#58a6ff' : '#8b949e'}}">${{gain > 0 ? gain.toExponential(2) : "0.00"}}</span></span>
            `;
            ledListDiv.appendChild(row);
        }});

        // Generate Plotly 3D traces
        const data = [];
        
        // 1. Room box outline
        const rx = scene.room.width;
        const ry = scene.room.length;
        const rz = scene.room.height;
        
        const roomOutline = {{
            type: 'scatter3d',
            mode: 'lines',
            name: 'Room Boundaries',
            x: [0, rx, rx, 0, 0, 0, rx, rx, 0, 0, 0, 0, rx, rx, rx, rx],
            y: [0, 0, ry, ry, 0, 0, 0, ry, ry, 0, ry, ry, ry, 0, 0, ry],
            z: [0, 0, 0, 0, 0, rz, rz, rz, rz, rz, rz, 0, 0, 0, rz, rz],
            line: {{ color: '#8b949e', width: 3 }},
            showlegend: true
        }};
        data.push(roomOutline);
        
        // 2. Trajectory trace
        if (traj.length > 0) {{
            data.push({{
                type: 'scatter3d',
                mode: 'lines',
                name: 'Receiver Trajectory',
                x: traj.map(p => p[0]),
                y: traj.map(p => p[1]),
                z: traj.map(p => p[2]),
                line: {{ color: '#2188ff', width: 4, dash: 'dash' }}
            }});
        }}
        
        // 3. LED nodes
        scene.leds.forEach(led => {{
            // LED position dot
            data.push({{
                type: 'scatter3d',
                mode: 'markers+text',
                name: `LED ${{led.id}}`,
                x: [led.position[0]],
                y: [led.position[1]],
                z: [led.position[2]],
                text: [`LED ${{led.id}}`],
                textposition: 'top center',
                marker: {{
                    size: 8,
                    color: '#f9e2af',
                    symbol: 'circle'
                }}
            }});
            
            // Light Cones
            // Approximate cone by drawing multiple lines from LED to circular footprint
            const coneAngle = led.fov / 2;
            const h = led.position[2];
            const r = h * Math.tan(coneAngle * Math.PI / 180);
            
            const cx = [];
            const cy = [];
            const cz = [];
            for (let i = 0; i <= 16; i++) {{
                const theta = (i * 2 * Math.PI) / 16;
                cx.push(led.position[0] + r * Math.cos(theta));
                cy.push(led.position[1] + r * Math.sin(theta));
                cz.push(0); // Floor plane
            }}
            
            data.push({{
                type: 'scatter3d',
                mode: 'lines',
                name: `LED ${{led.id}} Field of View`,
                x: cx, y: cy, z: cz,
                line: {{ color: 'rgba(249, 226, 175, 0.15)', width: 2 }},
                showlegend: false
            }});
            
            // Draw lines down the cone
            for (let i = 0; i < 4; i++) {{
                const idx = i * 4;
                data.push({{
                    type: 'scatter3d',
                    mode: 'lines',
                    x: [led.position[0], cx[idx]],
                    y: [led.position[1], cy[idx]],
                    z: [led.position[2], cz[idx]],
                    line: {{ color: 'rgba(249, 226, 175, 0.12)', width: 2 }},
                    showlegend: false
                }});
            }}
        }});
        
        // 4. Receiver node
        data.push({{
            type: 'scatter3d',
            mode: 'markers',
            name: 'APD Receiver',
            x: [state.receiver_position[0]],
            y: [state.receiver_position[1]],
            z: [state.receiver_position[2]],
            marker: {{
                size: 10,
                color: '#58a6ff',
                symbol: 'diamond'
            }}
        }});
        
        // Receiver orientation arrow vector
        const orientationLength = 0.5;
        const rxDir = state.receiver_orientation;
        data.push({{
            type: 'scatter3d',
            mode: 'lines',
            name: 'Rx Normal Vector',
            x: [state.receiver_position[0], state.receiver_position[0] + rxDir[0]*orientationLength],
            y: [state.receiver_position[1], state.receiver_position[1] + rxDir[1]*orientationLength],
            z: [state.receiver_position[2], state.receiver_position[2] + rxDir[2]*orientationLength],
            line: {{ color: '#58a6ff', width: 6 }}
        }});
        
        // 5. Obstacles
        scene.obstacles.forEach(obs => {{
            if (obs.type === 'box') {{
                const dx = obs.scale[0]/2;
                const dy = obs.scale[1]/2;
                const dz = obs.scale[2]/2;
                const cx = obs.position[0];
                const cy = obs.position[1];
                const cz = obs.position[2];
                
                // Outer corners of the box
                data.push({{
                    type: 'scatter3d',
                    mode: 'lines',
                    name: `Obstacle: ${{obs.id}}`,
                    x: [cx-dx, cx+dx, cx+dx, cx-dx, cx-dx, cx-dx, cx+dx, cx+dx, cx-dx, cx-dx, cx-dx, cx-dx, cx+dx, cx+dx, cx+dx, cx+dx],
                    y: [cy-dy, cy-dy, cy+dy, cy+dy, cy-dy, cy-dy, cy-dy, cy+dy, cy+dy, cy-dy, cy+dy, cy+dy, cy+dy, cy-dy, cy-dy, cy+dy],
                    z: [cz-dz, cz-dz, cz-dz, cz-dz, cz-dz, cz+dz, cz+dz, cz+dz, cz+dz, cz+dz, cz+dz, cz-dz, cz-dz, cz-dz, cz+dz, cz+dz],
                    line: {{ color: '#da3637', width: 4 }}
                }});
            }} else if (obs.type === 'cylinder') {{
                // cylinder approximation
                const r = obs.scale[0];
                const h = obs.scale[2];
                const cx = obs.position[0];
                const cy = obs.position[1];
                const cz = obs.position[2];
                
                const thetaArr = [];
                const xTop = [], yTop = [], zTop = [];
                const xBot = [], yBot = [], zBot = [];
                for (let i = 0; i <= 16; i++) {{
                    const t = (i * 2 * Math.PI) / 16;
                    xTop.push(cx + r * Math.cos(t));
                    yTop.push(cy + r * Math.sin(t));
                    zTop.push(cz + h/2);
                    
                    xBot.push(cx + r * Math.cos(t));
                    yBot.push(cy + r * Math.sin(t));
                    zBot.push(cz - h/2);
                }}
                
                data.push({{
                    type: 'scatter3d',
                    mode: 'lines',
                    name: `Obstacle: ${{obs.id}} (Top)`,
                    x: xTop, y: yTop, z: zTop,
                    line: {{ color: '#da3637', width: 3 }},
                    showlegend: false
                }});
                data.push({{
                    type: 'scatter3d',
                    mode: 'lines',
                    name: `Obstacle: ${{obs.id}} (Bottom)`,
                    x: xBot, y: yBot, z: zBot,
                    line: {{ color: '#da3637', width: 3 }},
                    showlegend: false
                }});
                
                // vertical ribs
                for (let i = 0; i < 4; i++) {{
                    const idx = i * 4;
                    data.push({{
                        type: 'scatter3d',
                        mode: 'lines',
                        x: [xBot[idx], xTop[idx]],
                        y: [yBot[idx], yTop[idx]],
                        z: [zBot[idx], zTop[idx]],
                        line: {{ color: '#da3637', width: 3 }},
                        showlegend: false
                    }});
                }}
            }}
        }});
        
        // 6. Direct line rays (LOS vs Blocked)
        scene.leds.forEach(led => {{
            const isLos = state.visibility.los_matrix[led.id];
            const inFov = state.visibility.visibility_matrix[led.id];
            const rayColor = isLos ? '#2ea44f' : '#da3637'; // Green for LOS, Red for blocked
            const rayDash = isLos ? 'solid' : 'dot';
            const rayName = isLos ? `Ray LED ${{led.id}} (LOS)` : `Ray LED ${{led.id}} (Blocked)`;
            
            data.push({{
                type: 'scatter3d',
                mode: 'lines',
                name: rayName,
                x: [led.position[0], state.receiver_position[0]],
                y: [led.position[1], state.receiver_position[1]],
                z: [led.position[2], state.receiver_position[2]],
                line: {{
                    color: rayColor,
                    width: inFov ? 4 : 1.5,
                    dash: rayDash
                }}
            }});
        }});

        // Plotly layout configurations
        const layout = {{
            paper_bgcolor: '#0d1117',
            plot_bgcolor: '#0d1117',
            margin: {{ l: 0, r: 0, b: 0, t: 0 }},
            scene: {{
                xaxis: {{
                    title: 'X (Width - m)',
                    backgroundcolor: '#161b22',
                    gridcolor: '#30363d',
                    showbackground: true,
                    zerolinecolor: '#30363d',
                    range: [0, rx]
                }},
                yaxis: {{
                    title: 'Y (Length - m)',
                    backgroundcolor: '#161b22',
                    gridcolor: '#30363d',
                    showbackground: true,
                    zerolinecolor: '#30363d',
                    range: [0, ry]
                }},
                zaxis: {{
                    title: 'Z (Height - m)',
                    backgroundcolor: '#161b22',
                    gridcolor: '#30363d',
                    showbackground: true,
                    zerolinecolor: '#30363d',
                    range: [0, rz]
                }},
                camera: {{
                    eye: {{ x: 1.5, y: 1.5, z: 1.2 }}
                }},
                aspectratio: {{ x: 1, y: 1, z: 0.6 }}
            }},
            legend: {{
                font: {{ color: '#c9d1d9' }},
                x: 0.85,
                y: 0.95
            }}
        }};

        Plotly.newPlot('plot', data, layout);
    </script>
</body>
</html>
"""
        with open(filename, 'w') as f:
            f.write(html_template)
            
        logger.info(f"Saved highly-interactive offline 3D visualization HTML to {filename}")
        return filename
