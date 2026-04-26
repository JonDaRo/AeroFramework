clear; clc;

% Setup paths and import AeroFramework modules
root_dir = fileparts(fileparts(fileparts(pwd)));
lib_path = fullfile(root_dir, 'matlab');

% Units: SI (m, kg, s, °)
addpath(lib_path);
import flow5.bridge_functions.*
import flow5.wing_params.*

airfoils_dir = "dataset_airfoils";

%% Wing Definition
%% Wing Definition
% 'gov' (governor) vector: defines how geometric inputs are interpreted.
% Logic:
%   TRUE  -> Value is a parameter (0 to 10), scaled between the limits defined below.
%   FALSE -> Value is treated as a physical measure (m or deg).
%
% Index mapping: [span, taper, offset, twist, dihedral]
gov = [true, true, true, true, true, true, true];

% Multi-segment geometry definition
% For n segments, span/taper/offset/dihedral require n values. 
% Twist requires n+1 values (including root section).
span   = [7.0, 10.0];      % Segment span
taper  = [8.0, 1.0];       % Segment taper ratio
offset = [0.0, 0.0];       % Section offset (excluding root, defined below as the Root Leading Edge position)
twist  = [5.0, 0.0, 0.0];  % Section twist
dih    = [0.0, 0.0];       % Segment dihedral

% Global Constraints & Targets
mirror           = true;   % Generate full wing from semi-span
middle_gap       = 0.0;    % Gap between semi-wings
S_target         = 0.7;    % Target wing area [m^2]
max_wingspan     = 3.0;    % Maximum allowable wingspan [m]
min_segment_span = 0.4;    % Minimum allowable segment span [m]
chord_lim        = [0.15, 0.6]; % Chord limits (min, max) [m]
twist_lim        = [-6.0, 6.0]; % Twist limits [deg]
dih_lim          = [0.0, 10.0]; % Dihedral limits [deg]

% Element Attributes
nome_elemento = 'wing';
type          = 'MAINWING';  % Options: MAINWING, OTHERWING, ELEVATOR, FIN
airfoils      = {'opt6.0', 'opt6.0', 'opt6.0', 'opt6.0'}; % Airfoil per section
position      = [0, 0, 0];   % Root Leading Edge position (x, y, z)
tilt_angle    = [0, 0];      % Mounting angles (Rx, Ry)
x_panels      = 15;          % Chordwise panel discretization

% Geometry Generation
winggeo = trapez_wing(mirror, middle_gap, gov, span, taper, offset, twist, dih, ...
                      S_target, max_wingspan, min_segment_span, chord_lim, twist_lim, dih_lim);

[elem1, out1] = flow5_element(nome_elemento, type, winggeo, airfoils, position, tilt_angle, x_panels);

%% Tail Definition
gov              = [true, true, true, true, true, true, true];
span             = [10.0, 5.0];
taper            = [10.0, 7.0];
offset           = [10.0, 10.0];
twist            = [5.0, 0.0, 0.0];
dih              = [10.0, 10.0];
S_target         = 0.1;
max_wingspan     = 0.8;
min_segment_span = 0.38;
chord_lim        = [0.1, 0.2];
dih_lim          = [0, 40];

position   = [1, 0, 0];
tilt_angle = [0, 0];

tailgeo = trapez_wing(true, 0, gov, span, taper, offset, twist, dih, ...
                      S_target, max_wingspan, min_segment_span, chord_lim, twist_lim, dih_lim);

[elem2, out2] = flow5_element('tail', 'ELEVATOR', tailgeo, ...
                {'Joukovsky 0009', 'Joukovsky 0009', 'Joukovsky 0009', 'Joukovsky 0009'}, ...
                position, tilt_angle, x_panels);

%% Assembly and Visualization
GeoElems_List = {elem1, elem2};
plot_wing_3d(GeoElems_List, airfoils_dir);