from aeroframework.flow5 import bridge_functions as bf
from aeroframework.flow5 import wing_params as wp
from plot import plot_wing_3d

# Setup paths
airfoils_dir = "dataset_airfoils"

# --- Wing Definition ---
# 'gov' (governor) vector: defines how geometric inputs are interpreted.
# Logic:
#   True  -> Value is a parameter (0 to 10), scaled between the limits defined below.
#   False -> Value is treated as a physical measure (m or deg).
#
# Index mapping: [span, taper, offset, twist, dihedral]
gov = [True, True, True, True, True, True, True]

# Multi-segment geometry definition
# For n segments, span/taper/offset/dihedral require n values. 
# Twist requires n+1 values (including root section).
span   = [7.0, 10.0]      # Segment span
taper  = [8.0, 1.0]       # Segment taper ratio
offset = [0.0, 0.0]       # Section offset (excluding root)
twist  = [5.0, 0.0, 0.0]  # Section twist [deg]
dih    = [0.0, 0.0]       # Segment dihedral [deg]

# Global Constraints & Targets
mirror           = True   # Generate full wing from semi-span
middle_gap       = 0.0    # Gap between semi-wings
S_target         = 0.7    # Target wing area [m^2]
max_wingspan     = 3.0    # Maximum allowable wingspan [m]
min_segment_span = 0.4    # Minimum allowable segment span [m]
chord_lim        = [0.15, 0.6] # Chord limits (min, max) [m]
twist_lim        = [-6.0, 6.0] # Twist limits [deg]
dih_lim          = [0.0, 10.0]  # Dihedral limits [deg]

# Element Attributes
nome_elemento = 'wing'
type_elem     = 'MAINWING' # Options: MAINWING, OTHERWING, ELEVATOR, FIN
airfoils      = ['opt6.0', 'opt6.0', 'opt6.0', 'opt6.0'] # Airfoil per section
position      = [0.0, 0.0, 0.0] # Root Leading Edge position (x, y, z)
tilt_angle    = [0.0, 0.0]      # Mounting angles (Rx, Ry)
x_panels      = 15              # Chordwise panel discretization

# Geometry Generation
winggeo = wp.trapez_wing(
    mirror, middle_gap, gov, span, taper, offset, twist, dih,
    S_target, max_wingspan, min_segment_span, chord_lim, twist_lim, dih_lim
)

# Flow5 Element Creation
# out1: Geometric data for visualization (GeoElem)
# elem1: Dictionary for XML generation
out1, elem1 = bf.flow5_element(
    nome_elemento, type_elem, winggeo, airfoils, position, tilt_angle, x_panels
)

# --- Tail Definition ---
gov_tail              = [True, True, True, True, True, True, True]
span_tail             = [10.0, 5.0]
taper_tail            = [10.0, 7.0]
offset_tail           = [10.0, 10.0]
twist_tail            = [5.0, 0.0, 0.0]
dih_tail              = [10.0, 10.0]
S_target_tail         = 0.1
max_wingspan_tail     = 0.8
min_segment_span_tail = 0.38
chord_lim_tail        = [0.1, 0.2]
dih_lim_tail          = [0.0, 45.0]

# Tail Geometry Generation
tailgeo = wp.trapez_wing(
    True, 0.0, gov_tail, span_tail, taper_tail, offset_tail, twist_tail, dih_tail,
    S_target_tail, max_wingspan_tail, min_segment_span_tail, chord_lim_tail, twist_lim, dih_lim_tail
)

# Tail Element Creation
out2, elem2 = bf.flow5_element(
    'tail', 'ELEVATOR', tailgeo, ['Joukovsky 0009']*4, [1, 0.0, 0.0], [0.0, 0.0], 10
)

# Lists for visualization and simulation
GeoElems_List = [out1, out2]
Elements_List = [elem1, elem2]

# --- Visualization ---
plot_wing_3d(GeoElems_List, airfoils_dir)