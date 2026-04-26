import os
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

def plot_wing_3d(geo_elems_list, airfoils_dir):
    """
    3D visualization with strictly equal axis scaling (1:1:1).
    """
    fig = plt.figure(figsize=(12, 10))
    ax = fig.add_subplot(111, projection='3d')
    
    ax.set_xlabel('X [m]')
    ax.set_ylabel('Y [m]')
    ax.set_zlabel('Z [m]')

    # Inizializziamo i limiti per il calcolo del bounding box
    min_xyz = np.array([np.inf, np.inf, np.inf])
    max_xyz = np.array([-np.inf, -np.inf, -np.inf])

    for e_idx, geo_elem in enumerate(geo_elems_list):
        # --- Estrazione Dati ---
        sec_data     = np.array(geo_elem[0])
        is_mirrored  = bool(geo_elem[1])
        wing_pos     = np.array(geo_elem[2]).reshape(3, 1)
        wing_tilt    = geo_elem[3]
        airfoil_list = geo_elem[4]

        num_sections = len(sec_data) // 5
        sections_xyz = []
        r_global = make_rot_matrix(wing_tilt[0], wing_tilt[1])
        current_pos_local = np.zeros((3, 1))

        for i in range(num_sections):
            idx = i * 5
            y_coord = sec_data[idx]
            chord = sec_data[idx+1]
            offset = sec_data[idx+2]
            twist = sec_data[idx+3]
            dihedral = sec_data[idx+4]

            if i > 0:
                dy = y_coord - sec_data[idx-5]
                prev_dih = sec_data[idx-1]
                current_pos_local[2, 0] += dy * np.tan(np.radians(prev_dih))
            
            current_pos_local[1, 0] = y_coord
            
            x_p, z_p = read_airfoil_dat(os.path.join(airfoils_dir, f"{airfoil_list[min(i, len(airfoil_list)-1)]}.dat"))
            
            cos_t, sin_t = np.cos(np.radians(twist)), np.sin(np.radians(twist))
            x_l = (x_p * cos_t - z_p * sin_t) * chord + offset
            z_l = (x_p * sin_t + z_p * cos_t) * chord
            
            pts_l = np.vstack([x_l, np.zeros_like(x_l), z_l]) + current_pos_local
            pts_g = (r_global @ pts_l) + wing_pos
            
            final_coords = pts_g.T
            sections_xyz.append(final_coords)

            # Aggiornamento limiti per Bounding Box (inclusa eventuale specchiatura)
            all_pts = final_coords.copy()
            if is_mirrored:
                mirrored_pts = final_coords.copy()
                mirrored_pts[:, 1] *= -1
                all_pts = np.vstack([all_pts, mirrored_pts])
            
            min_xyz = np.minimum(min_xyz, all_pts.min(axis=0))
            max_xyz = np.maximum(max_xyz, all_pts.max(axis=0))

        # --- Rendering ---
        color = plt.cm.tab10(e_idx % 10)
        for i in range(num_sections - 1):
            render_segment(ax, sections_xyz[i], sections_xyz[i+1], color)
            if is_mirrored:
                s1m, s2m = sections_xyz[i].copy(), sections_xyz[i+1].copy()
                s1m[:, 1] *= -1; s2m[:, 1] *= -1
                render_segment(ax, s1m, s2m, color)

    # --- FORZATURA SCALA 1:1 (EQUIVALENTE A 'AXIS EQUAL') ---
    mid_xyz = (max_xyz + min_xyz) / 2
    max_range = np.max(max_xyz - min_xyz) / 2
    
    ax.set_xlim(mid_xyz[0] - max_range, mid_xyz[0] + max_range)
    ax.set_ylim(mid_xyz[1] - max_range, mid_xyz[1] + max_range)
    ax.set_zlim(mid_xyz[2] - max_range, mid_xyz[2] + max_range)

    plt.show()


def make_rot_matrix(rx, ry):
    """Aeronautical rotation matrix: Rx (Roll) then Ry (Pitch)."""
    rx, ry = np.radians(rx), np.radians(ry)
    
    # Rotation around X (Roll)
    Rx = np.array([[1, 0, 0],
                   [0, np.cos(rx), -np.sin(rx)],
                   [0, np.sin(rx), np.cos(rx)]])
    
    # Rotation around Y (Pitch)
    Ry = np.array([[np.cos(ry), 0, np.sin(ry)],
                   [0, 1, 0],
                   [-np.sin(ry), 0, np.cos(ry)]])
    
    return Rx @ Ry

def render_segment(ax, s1, s2, color):
    """Draws the surface between two sections using a surface plot."""
    # Reshape for surface plot: [N_points x 2]
    x = np.column_stack([s1[:, 0], s2[:, 0]])
    y = np.column_stack([s1[:, 1], s2[:, 1]])
    z = np.column_stack([s1[:, 2], s2[:, 2]])
    
    ax.plot_surface(x, y, z, color=color, alpha=0.6, edgecolors='k', lw=0.1)
    # Highlight section profiles
    ax.plot(s1[:, 0], s1[:, 1], s1[:, 2], color='black', lw=0.5)

def read_airfoil_dat(filepath):
    """Robust parser for .dat airfoil files (Selig format)."""
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Airfoil file not found: {filepath}")
    
    with open(filepath, 'r') as f:
        lines = f.readlines()[1:] # Skip header
    
    coords = []
    for line in lines:
        parts = line.split()
        if len(parts) == 2:
            coords.append([float(parts[0]), float(parts[1])])
            
    coords = np.array(coords)
    return coords[:, 0], coords[:, 1]