from aeroframework.flow5 import bridge as br
from aeroframework.flow5 import geometry as gm
import os

## Initialization
flow5_dir    = os.getcwd()           # Directory where flow5 case folder will be created
airfoils_dir = 'dataset_airfoils'    # Directory for .dat airfoil files
polars_dir   = 'dataset_polars'      # Directory for .plr and .txt polar files
n_threads    = 14                    # CPU threads for parallel execution

# Initialize Flow5 Case
case_res = br.flow5_case(flow5_dir, n_threads, True)

## Geometry Definition (Refer to main_geometry.py for detailed parameters)
# Wing
gov    = [True]*5
span   = [7.0, 10.0] 
taper  = [8.0, 1.0]
offset = [0.0, 0.0]
twist  = [5.0, 0.0, 0.0]
dih  = [0.0, 0.0]

winggeo = gm.trapez_wing(True, 0, gov, span, taper, offset, twist, dih, 
                            0.55, 3, 0.4, [0.15, 0.6], [-6, 6], [0, 10])

geo1, elem1 = br.flow5_element('wing', 'MAINWING', winggeo, ['opt6.0']*4, [0, 0, 0], [0, 0], 15)

# Tail
tailgeo = gm.trapez_wing(True, 0, gov, [10.0, 5.0], [10.0, 7.0], [10.0, 10.0], 
                            [5.0, 0.0, 0.0], [10.0, 10.0], 0.1, 0.8, 0.38, 
                            [0.1, 0.2], [-6, 6], [0, 40])

geo2, elem2 = br.flow5_element('tail', 'ELEVATOR', tailgeo, ['Joukovsky 0009']*4, [1, 0, 0], [0, 0], 15)

elements = [elem1, elem2]

## Plane Definition
# Mass distribution: define coordinates [x, y, z], mass [kg], and optional tags.
mass_res = [{'coord': [0.11, 0, 0], 'mass': 6.0, 'tag': 'CG'}]

plane_name = 'plane1'
plane_res  = br.flow5_plane(case_res, plane_name, mass_res, elements, airfoils_dir, polars_dir, 5)

# 3D live plot
gm.plot_3d_live([geo1, geo2], airfoils_dir)

## Analysis Setup (Analysis 1)
speed_1 = 30      # Cruise speed [m/s]
an_name_1 = 'Analysis 1' # Analysis identifier
type_1 = 'T1'     # Analysis type
method = 'VLM2'   # Numerical method (e.g., Vortex Lattice Method 2)

anal_res_1 = br.flow5_analysis(plane_res, an_name_1, type_1, method, FixTAS=speed_1)

## Analysis Setup (Analysis 2)
speed_2 = 25      # Cruise speed [m/s]
an_name_2 = 'Analysis 2' # Analysis identifier
type_2 = 'T5'     # Analysis type

anal_res_2 = br.flow5_analysis(plane_res, an_name_2, type_2, method, FixTAS=speed_2)

## Execution
flow5_exe_path = 'flow5'          # Executable path
alpha_range    = [0.0, 2.0, 1.0]  # Angles of Attack [start, stop, step]
beta_range     = [0.0, 1.0, 1.0]  # Sideslip Angles [start, stop, step]

run_res = br.flow5_run(flow5_exe_path, [anal_res_1, anal_res_2], 
                        alpha_range, [0, 0, 0], beta_range, [0, 0, 0])

## Results Extraction
# Specify coefficients to extract from flow5 output
keys = ['α', 'β', 'φ', 'CL', 'CD', 'Cm', 'CY', 'Cl', 'Cn']

data_matrix1, name1 = br.flow5_results(run_res[0], keys)
data_matrix2, name2 = br.flow5_results(run_res[1], keys)

def print_table(headers, rows):
    col_widths=[max(len(str(item)) for item in [header] + [row[i] for row in rows]) for i, header in enumerate(headers)]
    header_row=" | ".join(f"{header:<{col_widths[i]}}" for i, header in enumerate(headers))
    print(header_row)
    print("-" * len(header_row))
    for row in rows:
        print(" | ".join(f"{str(item):<{col_widths[i]}}" for i, item in enumerate(row)))

print(f"\nResults for {name1}:\n")
print_table(data_matrix1[0], data_matrix1[1:])
print(f"\nResults for {name2}:\n")
print_table(data_matrix2[0], data_matrix2[1:])

#Stop the live viewer and close the plot when done.
gm.finalize_plot_3d_live()