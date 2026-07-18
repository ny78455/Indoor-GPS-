# visualization.py
import numpy as np
import plotly.graph_objects as go
from typing import List, Dict, Any

def generate_physics_heatmap(
    room_dims: List[float],
    led_positions: List[List[float]],
    grid_res: int = 25
) -> go.Figure:
    """
    Generates a 3D Plotly surface representing optical coverage or intensity on the floor plane.
    """
    W, L, H = room_dims
    xs = np.linspace(0, W, grid_res)
    ys = np.linspace(0, L, grid_res)
    x_grid, y_grid = np.meshgrid(xs, ys)
    
    # Calculate simple power sum received at each grid point
    z_floor = 0.85
    power_grid = np.zeros_like(x_grid)
    
    for led_pos in led_positions:
        dx = x_grid - led_pos[0]
        dy = y_grid - led_pos[1]
        dz = z_floor - led_pos[2]
        dist_sq = dx**2 + dy**2 + dz**2
        dist = np.sqrt(dist_sq)
        
        # Lambertian emission order m=1 nominal
        cos_phi = np.abs(dz) / dist
        gain = (2 * 1e-4 / (2 * np.pi * dist_sq)) * cos_phi
        power_grid += 20.0 * gain
        
    fig = go.Figure(data=[go.Surface(
        z=power_grid,
        x=x_grid,
        y=y_grid,
        colorscale='Viridis',
        colorbar_title='Optical Power (W)'
    )])
    
    fig.update_layout(
        title='Visible Light Communication: Power Heatmap on Receiver Plane',
        scene=dict(
            xaxis_title='X (m)',
            yaxis_title='Y (m)',
            zaxis_title='Received Power (W)'
        ),
        margin=dict(l=0, r=0, b=0, t=50)
    )
    return fig
