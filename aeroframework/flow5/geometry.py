import pyvista as pv
import numpy as np
from os.path import join
from scipy.interpolate import interp1d
from math import ceil
import threading
import time
import vtk

vtk.vtkObject.GlobalWarningDisplayOff()

def trapez_wing(FullWing:bool, MiddleGap:float, GorV:list, SpanG:list, TaperG:list, OffsetG:list, TwistG:list, DihedralG:list, TargetS:float, MaxSpan: float, MinSeg:float, ChordLim:list, TwistLim:list, DihedLim:list, Accuracy:float=0.001)->dict:
    """Generates wing geometry parameters based on the input specifications. Units are in meters and degrees.
    Args:
        FullWing (bool): Indicates if the wing is full or half.
        MiddleGap (float): The gap between the two halves of the wing if FullWing is False.
        GorV (bool list): A list of booleans indicating which parameters are describe by a Gene value (from 0 to 10) or by its actual value.
                     The order of the list corresponds to the parameters: [Span, Chord, Offset, Twist, Dihedral].
        SpanG (float list): A list of span values for each segment of the wing.
        TaperG (float list): A list of taper ratios for each segment of the wing.
        OffsetG (float list): A list of offset values for each segment of the wing.
        TwistG (float list): A list of twist values for each section (number of segment+1) of the wing.
        DihedralG (float list): A list of dihedral angles for each segment of the wing.
        TargetS (float): The target wing area for the optimization.
        MaxSpan (float): The maximum allowed wingspan for the optimization.
        MinSeg (float): The minimum allowed segment length for the optimization.
        ChordLim (float list): A list of limits for the chord length of the wing segments [min,max].
        TwistLim (float list): A list of limits for the twist angles of the wing segments [min,max].
        DihedLim (float list): A list of limits for the dihedral angles of the wing [min,max].
        Accuracy (float, opzionale): The acceptable accuracy for an iterative loop (if used). Default is 0.001.
    Returns:
        WingData (dict): A dictionary containing the generated wing geometry parameters, including:
            - "FullWing": The input FullWing value.
            - "SecData": A flattened list of section data for each segment of the wing, each section is described by [span posistion, chord, offset, twist, dihedral].
            - "S": The calculated wing area based on the generated geometry.
            - "WingSpan": The calculated wingspan based on the generated geometry.
            - "MAC": The calculated mean aerodynamic chord based on the generated geometry.
            - "AR": The calculated aspect ratio based on the generated geometry.
    """

    if not isinstance(FullWing,bool):
        raise TypeError("FullWing must be a boolean")
    if not isinstance(MiddleGap,(int,float)):
        raise TypeError("MiddleGap must be an integer or a float")
    if not isinstance(GorV,list):
        raise TypeError("GorV must be a list")
    if not isinstance(TwistG,list):
        raise TypeError("TwistG must be a list")
    if not isinstance(DihedralG,list):
        raise TypeError("DihedralG must be a list")
    if not isinstance(OffsetG,list):
        raise TypeError("OffsetG must be a list")
    if not isinstance(TaperG,list):
        raise TypeError("TaperG must be a list")
    if not isinstance(SpanG,list):
        raise TypeError("SpanG must be a list")
    if not isinstance(MaxSpan,(int,float)):
        raise TypeError("MaxSpan must be an integer or a float")
    if not isinstance(MinSeg,(int,float)):
        raise TypeError("MinSeg must be an integer or a float")
    if not isinstance(ChordLim,list):
        raise TypeError("ChordLim must be a list")
    if not isinstance(TwistLim,list):
        raise TypeError("TwistLim must be a list")
    if not isinstance(DihedLim,list):
        raise TypeError("DihedLim must be a list")
    if not isinstance(TargetS,(int,float)):
        raise TypeError("TargetS must be an integer or a float")
    if not isinstance(Accuracy,(int,float)):
        raise TypeError("Accuracy must be an integer or a float")
    
    WingData={"FullWing":FullWing,"SecData":[],"S":0,"WingSpan":0,"MAC":0,"AR":0}
    
    ts=1
    if FullWing:
        ts=2

    n_seg=len(SpanG)
    if GorV[0]:
        max_span=MaxSpan/ts
        min_span=MinSeg

        if max_span<min_span*n_seg:
            min_span=max_span/n_seg

    else:
        max_span=sum(SpanG)
        min_span=sum(SpanG)

        S_max=100000
        S_min=-100000

    if GorV[1]:
        min_c=min(ChordLim)
        max_c=max(ChordLim)

        if max_c<min_c:
            min_c=max_c

        if min_c<0.001:
            min_c=0.001

    if GorV[0] or GorV[1]:
        if GorV[0] and not GorV[1]:
            S_max=0
            S_min=1
        else:
            S_max=max_span*max_c*ts
            S_min=min_span*min_c*ts

            max_span_n=TargetS/min_c/ts
            if max_span_n<max_span:
                max_span=max_span_n

    if (S_max<TargetS or S_min>TargetS or max_span<min_span):
        return WingData

    if GorV[0]:
        span=[0]*(n_seg+1)
        r_span=max_span
        for i in range(n_seg):
            a=r_span-min_span*(n_seg-i)
            b=min_span
            span[i+1]=SpanG[i]*a/10+b
            WingData["WingSpan"]+=span[i+1]*ts
            r_span-=span[i+1]
    else:
        span=[0]+SpanG
        WingData["WingSpan"]=SpanG[-1]*ts

    if GorV[1]:
        chord=[0]*(n_seg+1)
        chord[0]=max_c

        for i in range(n_seg):
            chord[i+1]=TaperG[i]*(chord[i]-min_c)/10+min_c
            WingData["S"]+=(chord[i+1]+chord[i])*span[i+1]/(3-ts)

        it=0
        err=abs(WingData["S"]-TargetS)
        while err>Accuracy and it<1000:
            it+=1
            x=abs(TargetS/WingData["S"])
            chord[0]=chord[0]*x
            if chord[0]>max_c:
                chord[0]=max_c
            elif chord[0]<min_c:
                chord[0]=min_c
    
            WingData["S"]=0
            for k in range(n_seg):
                chord[k+1]=chord[k+1]*x
                if chord[k+1]>chord[k]:
                    chord[k+1]=chord[k]
                elif chord[k+1]<min_c:
                    chord[k+1]=min_c
                WingData["S"]+=(chord[k+1]+chord[k])*span[k+1]/(3-ts)
            err=abs(WingData["S"]-TargetS)
    else:
        chord=TaperG
        for i in range(n_seg):
            WingData["S"]+=(chord[i+1]+chord[i])*span[i+1]/(3-ts)

    WingData["AR"]=WingData["WingSpan"]*WingData["WingSpan"]/WingData["S"]
    media=0
    for i in range(n_seg):
        taper=chord[i+1]/chord[i]
        MAC_seg=chord[i]*2/3*(1+taper+taper*taper)/(1+taper)
        S_seg=(chord[i]+chord[i+1])*span[i+1]/(3-ts)
        media+=S_seg*MAC_seg
    WingData["MAC"]=media/WingData["S"]

    twist=TwistG
    dihedral=DihedralG+[0]
    offset=[0]+OffsetG

    if GorV[3]:
        twist=[0]*(n_seg+1)
        min_twist=min(TwistLim)
        max_twist=max(TwistLim)
        twist[0]=TwistG[0]/10*(max_twist-min_twist)+min_twist
        for i in range(n_seg):
            twist[i+1]=-TwistG[i+1]/10*(twist[i]-min_twist)+twist[i]

    if GorV[4]:
        dihedral=[0]*(n_seg+1)
        min_dihedral=min(DihedLim)
        max_dihedral=max(DihedLim)
        dihedral[0]=DihedralG[0]/10*(max_dihedral-min_dihedral)+min_dihedral
        for i in range(1,n_seg):
            dihedral[i]=DihedralG[i]/10*(max_dihedral-min_dihedral)+min_dihedral
            
    if GorV[2]:
        offset=[0]*(n_seg+1)
        for i in range(n_seg):
            offset[i+1]=OffsetG[i]/10*(chord[i]-chord[i+1])+offset[i]

    y=[MiddleGap]*(n_seg+1)
    for i in range(n_seg):
        y[i+1]=span[i+1]+y[i]

    for i in range(n_seg+1):
        WingData["SecData"].extend([y[i],chord[i],offset[i],twist[i],dihedral[i]])

    if S_max<TargetS or S_min>TargetS:
        WingData={"FullWing":FullWing,"SecData":[],"S":0,"WingSpan":0,"MAC":0,"AR":0}
    
    return WingData


_element_color=lambda t: {
    "MAINWING": "lightsteelblue",
    "OTHERWING": "mediumseagreen",
    "ELEVATOR": "indianred",
    "FIN": "darkorange"
}.get(t, "lightgray")


def _add_element(plotter, GeoElem, AirfoilsDir):
    elem_name=GeoElem["name"]
    elem_type=GeoElem["type"]
    geo_data=GeoElem["geo_data"]
    mirror=GeoElem["full_wing"]
    wing_pos=GeoElem["wing_pos"]
    wing_rot=GeoElem["wing_tilt"]
    airfoil_names=GeoElem["airfoils"]

    coord_2d_root=_load_airfoil(airfoil_names[0], AirfoilsDir)
    sections=[_modify_airfoil(coord_2d_root, geo_data[0])]
    
    for i in range(1, len(airfoil_names)-1):
        k=ceil(i/2)
        coord_2d=_load_airfoil(airfoil_names[i], AirfoilsDir)
        sections.append(_modify_airfoil(coord_2d, geo_data[k]))
        
    coord_2d_tip=_load_airfoil(airfoil_names[-1], AirfoilsDir)
    sections.append(_modify_airfoil(coord_2d_tip, geo_data[-1]))

    R=_make_rot_matrix(wing_rot[0], wing_rot[1])

    def create_mesh(secs, is_mirror=False):
        n_points =len(secs[0])
        n_sections=len(secs)
        
        all_coords=[]
        for s in secs:
            s_mod=s.copy()
            if is_mirror:
                s_mod[:, 1]= -s_mod[:, 1]
            
            rotated=(R @ s_mod.T).T+wing_pos
            all_coords.append(rotated)
            
        grid_coords=np.vstack(all_coords)
        
        grid=pv.StructuredGrid()
        grid.points=grid_coords
        grid.dimensions=[n_points, n_sections, 1]
        return grid

    mesh_args = dict(
        color=_element_color(elem_type),
        smooth_shading=True,
        split_sharp_edges=True
    )
    plotter.add_mesh(create_mesh(sections, False), **mesh_args)
    if mirror:
        plotter.add_mesh(create_mesh(sections, True), **mesh_args)

    def add_section_outlines(secs, is_mirror):
        for s in secs:
            s_mod = s.copy()
            if is_mirror:
                s_mod[:, 1] = -s_mod[:, 1]
            transformed_coords = (R @ s_mod.T).T + wing_pos
            polyline = pv.PolyData(transformed_coords)
            n_points = len(transformed_coords)
            cells = np.array([n_points + 1] + list(range(n_points)) + [0])
            polyline.lines = cells
            polyline.verts = np.array([], dtype=np.int_)
            plotter.add_mesh(
                polyline, 
                color="black", 
                line_width=2, 
                style='wireframe',
                render_lines_as_tubes=False,
                label=None
            )
    add_section_outlines(sections, False)
    if mirror:
        add_section_outlines(sections, True)

    anchor_point=wing_pos+(R @ sections[0][0])
    plotter.add_point_labels(
        [anchor_point], 
        [elem_name], 
        font_size=14, 
        text_color='black',
        shadow=True,
        show_points=False,
        always_visible=True,
        shape_opacity=0 
    )


def plot_3d(GeoElems, AirfoilsDir):
    """Plots the 3D elements using PyVista.
    Args:
        GeoElems (dict list): List of geometric elements, each containing geometric data for the visualization.
        AirfoilsDir (str): Directory path where airfoil coordinate files are stored.
    """
    Plotter=pv.Plotter(title="AeroFramework Viewer")
    Plotter.enable_terrain_style()
    Plotter.add_axes()
    for GeoElem in GeoElems:
        _add_element(Plotter, GeoElem, AirfoilsDir)

    Plotter.show_grid(
        xtitle='X [m]', 
        ytitle='Y [m]', 
        ztitle='Z [m]',
        color='black',
        font_size=10,
        location='outer',
        all_edges=False,
        fmt="%.2f"
    )
    Plotter.view_isometric()
    Plotter.show()


class AutonomousViewer:
    def __init__(self):
        self.plotter = None
        self.thread = None
        self.render_lock = threading.Lock()
        self.current_elements = []
        self.airfoils_dir = ""
        self.needs_update = False

    def _render_loop(self):
        self.plotter = pv.Plotter(title="AeroFramework Live Viewer")
        self.plotter.enable_terrain_style()
        self.plotter.show(interactive_update=True)

        while self.plotter.render_window is not None:
            with self.render_lock:
                if self.needs_update:
                    self.plotter.clear()
                    for GeoElem in self.current_elements:
                        self.plotter.enable_lightkit()
                        _add_element(self.plotter, GeoElem, self.airfoils_dir)
                        self.plotter.add_axes()
                    self.plotter.show_grid(
                        xtitle='X [m]', 
                        ytitle='Y [m]', 
                        ztitle='Z [m]',
                        color='black',
                        font_size=10,
                        location='outer',
                        all_edges=False,
                        fmt="%.2f"
                    )
                    self.plotter.view_isometric()
                    self.needs_update = False
            
            self.plotter.update()
            time.sleep(0.016)

    def update_live(self, GeoElems, AirfoilsDir):
        with self.render_lock:
            self.current_elements = GeoElems
            self.airfoils_dir = AirfoilsDir
            self.needs_update = True
        
        if self.thread is None or not self.thread.is_alive():
            self.thread = threading.Thread(target=self._render_loop, daemon=True)
            self.thread.start()
            time.sleep(0.5)

_viewer = AutonomousViewer()

def plot_3d_live(GeoElems, AirfoilsDir):
    """Plots the 3D elements using PyVista. The graph do not stop the progress of the script and can be updated during loops.
    Args:
        GeoElems (dict list): List of geometric elements, each containing geometric data for the visualization.
        AirfoilsDir (str): Directory path where airfoil coordinate files are stored.
    """
    _viewer.update_live(GeoElems, AirfoilsDir)

def finalize_plot_3d_live():
    '''Finalizes the PyVista plot_3d_live and waits for the window to be closed by the user.'''
    if _viewer.plotter is not None:
        try:
            while _viewer.plotter.render_window is not None:
                time.sleep(0.1)
        except Exception:
            pass
    if _viewer.thread:
        _viewer.thread.join(timeout=1.0)


def _load_airfoil(name, AirfoilsDir, num_pts=100):
    path=join(AirfoilsDir, f"{name}.dat")
    
    try:
        raw_data=np.loadtxt(path, skiprows=1)
    except Exception as e:
        print(f"Errore caricamento {name}: {e}")
        return None

    dist=np.sqrt(np.diff(raw_data[:,0])**2+np.diff(raw_data[:,1])**2)
    raw_data=raw_data[np.insert(dist>1e-12,0,True)]

    dx=np.diff(raw_data[:, 0])
    dz=np.diff(raw_data[:, 1])
    ds=np.sqrt(dx**2+dz**2)
    s=np.insert(np.cumsum(ds),0,0)
    s_norm=s/s[-1]

    t=np.linspace(0,1,num_pts)
    s_new=t+0.15*np.sin(2*np.pi*t)
    
    f_x=interp1d(s_norm, raw_data[:, 0], kind='linear')
    f_z=interp1d(s_norm, raw_data[:, 1], kind='linear')
    
    coord_2d=np.vstack([f_x(s_new),f_z(s_new)]).T

    area=0.5*np.sum(coord_2d[:-1, 0]*coord_2d[1:, 1] - coord_2d[1:, 0]*coord_2d[:-1, 1])
    if area<0:
        coord_2d=coord_2d[::-1]

    return coord_2d


def _modify_airfoil(coord_2d_root,mod):
    coord_3d_root=np.insert(coord_2d_root, 1, 0, axis=1)
    
    cos_t,sin_t=np.cos(np.radians(mod[0])), np.sin(np.radians(mod[0]))
    x_l=coord_3d_root[:, 0]*cos_t - coord_3d_root[:, 2]*sin_t
    z_l=coord_3d_root[:, 0]*sin_t + coord_3d_root[:, 2]*cos_t
    
    cos_t, sin_t = np.cos(np.radians(mod[1])), np.sin(np.radians(mod[1]))
    y_l = coord_3d_root[:, 1]*cos_t - z_l*sin_t
    z_l = coord_3d_root[:, 1]*sin_t + z_l*cos_t
    
    x_l*=mod[2]
    y_l*=mod[2]
    z_l*=mod[2]
    
    x_l+=mod[3]
    y_l+=mod[4]
    z_l+=mod[5]

    coord_3d_root[:, 0]=x_l
    coord_3d_root[:, 1]=-y_l
    coord_3d_root[:, 2]=z_l

    return coord_3d_root


def _make_rot_matrix(rx,ry):
    rx,ry=np.radians(rx),np.radians(ry)
    Rx=np.array([[1,0,0],
                   [0,np.cos(rx),-np.sin(rx)],
                   [0,np.sin(rx),np.cos(rx)]])
    Ry=np.array([[np.cos(ry),0,np.sin(ry)],
                   [0,1,0],
                   [-np.sin(ry),0,np.cos(ry)]])
    return Rx @ Ry