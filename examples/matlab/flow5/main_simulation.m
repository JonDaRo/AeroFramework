clear; clc;

% Setup paths and import AeroFramework modules
root_dir = fileparts(fileparts(fileparts(pwd)));
lib_path = fullfile(root_dir, 'matlab');

% Units: SI (m, kg, s, °)
addpath(lib_path);
import flow5.bridge_functions.*
import flow5.wing_params.*

%% Initialization
flow5_dir    = pwd;                % Directory where flow5 case folder will be created
airfoils_dir = 'dataset_airfoils'; % Directory for .dat airfoil files
polars_dir   = 'dataset_polars';   % Directory for .plr and .txt polar files
n_threads    = 14;                 % CPU threads for parallel execution

% Initialize Flow5 Case
CaseRes = flow5_case(flow5_dir, n_threads);

%% Geometry Definition (Refer to main_geometry.m for detailed parameters)
% Wing
gov    = [true, true, true, true, true, true, true];
span   = [7, 10.0]; 
taper  = [8, 1];
twist  = [5.0, 0.0, 0.0];
winggeo = trapez_wing(true, 0, gov, span, taper, [0,0], twist, [0,0], 0.55, 3, 0.4, [0.15, 0.6], [-6, 6], [0, 10]);
[elem1, out1] = flow5_element('wing', 'MAINWING', winggeo, {'opt6.0','opt6.0','opt6.0','opt6.0'}, [0,0,0], [0,0], 15);

% Tail
tailgeo = trapez_wing(true, 0, gov, [10, 5], [10, 7], [10, 10], [5, 0, 0], [10, 10], 0.1, 0.8, 0.38, [0.1, 0.2], [-6, 6], [0, 40]);
[elem2, out2] = flow5_element('tail', 'ELEVATOR', tailgeo, {'Joukovsky 0009','Joukovsky 0009','Joukovsky 0009','Joukovsky 0009'}, [1, 0, 0], [0, 0], 15);

elements = [out1, out2];

%% Plane Definition
% Mass distribution: define coordinates [x, y, z], mass [kg], and optional tags.
MassRes = [struct('coord', [0.11, 0, 0], 'mass', 6.0, 'tag', 'CG')];

plane_name = 'plane1';
PlaneRes   = flow5_plane(CaseRes, plane_name, MassRes, elements, airfoils_dir, polars_dir, 5);

plot_wing_3d({elem1, elem2}, airfoils_dir);

%% Analysis Setup
speed   = 30;     % Cruise speed [m/s]
an_name = 'an1';  % Analysis identifier
type    = 'T1';   % Analysis type
method  = 'VLM2'; % Numerical method (e.g., Vortex Lattice Method 2)

AnalRes1 = flow5_analysis(PlaneRes, an_name, type, method, speed);

%% Analysis Setup
speed   = 25;     % Cruise speed [m/s]
an_name = 'an2';  % Analysis identifier
type    = 'T5';   % Analysis type
method  = 'VLM2'; % Numerical method (e.g., Vortex Lattice Method 2)

AnalRes2 = flow5_analysis(PlaneRes, an_name, type, method, speed);

%% Execution
flow5_exe_path = 'flow5';         % Executable path (ensure 'flow5' is in system PATH or use the full path to the executable)
alpha_range    = [0.0, 2.0, 1.0]; % Angles of Attack [start, stop, step]
beta_range     = [0.0, 1.0, 1.0]; % Sideslip Angles [start, stop, step]

RunRes = flow5_run(flow5_exe_path, [AnalRes1, AnalRes2], alpha_range, [0,0,0], beta_range, [0,0,0]);

%% Results Extraction
% Specify coefficients to extract from flow5 output
keys = {'α', 'β', 'φ', 'CL', 'CD', 'Cm', 'CY', 'Cl', 'Cn'};
[Data_Matrix1, Headers1, Name1] = flow5_results(RunRes(1), keys);
[Data_Matrix2, Headers2, Name2] = flow5_results(RunRes(2), keys);

% Display results first analysis
ResultsTable = array2table(Data_Matrix1, 'VariableNames', Headers1);
fprintf('\nSimulation Results of %s:\n',Name1);
disp(ResultsTable);

% Display results second analysis
ResultsTable2 = array2table(Data_Matrix2, 'VariableNames', Headers2);
fprintf('\nSimulation Results of %s:\n',Name2);
disp(ResultsTable2);