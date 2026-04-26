# Flow5 Automation & Wing Geometry API

This repository provides a comprehensive suite of **Python tools** designed to automate geometry generation, analysis configuration, and result extraction for the **Flow5** aerodynamic analysis software.


### MATLAB API Wrapper
In addition to the native Python environment, this repository provides a **MATLAB API Wrapper**. This interface enables execution of the core automation functions directly from MATLAB by interfacing with the underlying Python engine.
The MATLAB functions are similar to the python ones, as you can see in the examples.

## Modules

### 1. `bridge_functions`
This module handles the interface between Python and Flow5, managing the creation of the folder structure and writing the configuration XML files.


#### `flow5_case`
Creates the folder structure and the `case.xml` file for Flow5.

* **Arguments:**
    * `Path` (str): The path of the main folder.
    * `Threads` (int): The number of threads to use for the analyses.
    * `Fl5File` (bool, optional): If True, creates a `.fl5` file for each analysis. Default is `False`.
    * `StoreOP` (bool, optional): If True, stores the Operating Points for each analysis. Default is `False`. (Note: Flow5 7.55 has known bugs with this feature; keeping it `False` is recommended).
    * `Gate` (bool, optional): If `False`, no file or folder is modified or created. Default is `True`.
* **Returns:**
    * `CaseRes` (dict): A dictionary containing the paths of the generated folders and the `case.xml` file.


#### `flow5_element`
Generates the data in list format for geometry visualization and in dictionary format for element generation in Flow5.

* **Arguments:**
    * `Name` (str): The name of the element.
    * `Type` (str): The type of element (`MAINWING`, `OTHERWING`, `ELEVATOR`, `FIN`).
    * `WingGeo` (dict): A dictionary containing the geometric data of the element. It must include:
        * `FullWing` (bool): If `True`, the element is symmetric with respect to the YZ plane.
        * `SecData` (list): A list of data for each section. Each section requires 5 values in order:
            * Position along the y-axis (m).
            * Chord length (m).
            * Offset (m).
            * Twist angle (deg).
            * Dihedral angle (deg).
    * `Airfoils` (list): A list of filenames for the airfoils corresponding to each section. Intermediate sections are represented by two profiles (one for the left side and one for the right).
    * `WingPos` (list): A list of three numbers representing the position (x, y, z) in meters of the element within the aircraft reference system.
    * `WingTilt` (list): A list of two numbers representing the rotation angles (Rx, Ry) in degrees.
    * `Panels` (int, optional): The number of panels to use along the x-direction (chord). Default is `25`.
* **Returns:**
    * `GeoElem` (list): A list containing the generic geometric data of the element for visualization purposes.
    * `Element` (dict): A dictionary containing the geometric data specifically formatted for generating the element in Flow5.


#### `flow5_plane`
Creates an XML file for the definition of an aircraft in Flow5.

* **Arguments:**
    * `CaseRes` (dict): The dictionary returned by `flow5_case`.
    * `Name` (str): The name of the aircraft.
    * `MassRes` (list): A list of dictionaries containing mass data for each element. Each dictionary must include:
        * The keys `coord` (a list of coordinates x, y, z in meters), `mass` (mass in kg), and `tag` (identifier for the mass point).
        * Alternatively, if `coord` is the name of a specific element, the `mass` is distributed automatically by Flow5 over that element (no `tag` key required).
    * `Elements` (list): A list of dictionaries containing geometric data for each aircraft element, obtained through `flow5_element`.
    * `Airfoils_dir` (str): The path to the directory containing the airfoil `.dat` files.
    * `Polars_dir` (str): The path to the directory containing the polar `.plr` or `.txt` files.
    * `BankAng` (float, optional): The bank angle in degrees to apply to the entire aircraft (clockwise rotation around the x-axis). Default is `0`.
    * `TotRefS` (bool, optional): If `True`, the total surface area of the aircraft is used as the reference for analyses (including `OTHERWING` elements). Default is `True`.
    * `Gate` (bool, optional): If `False`, no file or folder is modified or created. Default is `True`.
* **Returns:**
    * `PlaneRes` (dict): A dictionary containing metadata and data related to the defined aircraft.


#### `flow5_analysis`
Creates an XML file for a Flow5 analysis (T1, T2, T3, T5, or T8).

* **Arguments:**
    * `PlaneRes` (dict): The dictionary returned by `flow5_plane`.
    * `Name` (str): The name of the analysis.
    * `Type` (str): The type of analysis (`T1`, `T2`, `T3`, `T5`, `T8`).
    * `Method` (str): The analysis method (`LLT`, `VLM1`, `VLM2`, `QUADS`, `TRIUNIFORM`, `TRILINEAR`).
    * `ThinSurf` (bool, optional): If `True`, considers thin surfaces. Default is `True`.
    * `GrdEff` (bool, optional): If `True`, considers ground effect. Default is `False`.
    * `Height` (float, optional): The height above ground for ground effect. Default is `0.0`.
    * `Viscosity` (float, optional): The kinematic viscosity of the fluid. Default is `1.5e-05` $m^2/s$.
    * `Density` (float, optional): The density of the fluid. Default is `1.225` $kg/m^3$.
    * `Viscous` (bool, optional): If `True`, performs a viscous analysis. Default is `True`.
    * `Xflr5Visc` (bool, optional): If `True`, uses $C_L$ data for viscous analysis (XFLR5 method). Default is `True`.
    * `FixTAS` (float, optional): The fixed velocity for fixed speed analyses. Default is `0.0` $m/s$.
    * `FixAoA` (float, optional): The fixed angle of attack for fixed angle of attack analyses. Default is `0.0` deg.
    * `optional` (dict, optional): A dictionary containing any additional parameters to include in the XML file.
    * `Gate` (bool, optional): If `False`, no file or folder is modified or created. Default is `True`.
* **Returns:**
    * `AnalysisRes` (dict): A dictionary with the data related to the defined analysis.


#### `flow5_run`
Executes the analyses in Flow5 by calling the executable through subprocesses.

* **Arguments:**
    * `ExePath` (str): The path to the Flow5 executable file.
    * `AnalysisRes` (list): A list of dictionaries containing analysis data, obtained through `flow5_analysis`.
    * `T12Range` (list, optional): A list of three numbers representing the range and step of the angle of attack (AoA) in degrees `[min, max, step]` for T1 and T2 analyses. Default is `[0, 0, 0]`.
    * `T3Range` (list, optional): A list of three numbers representing the range and step of the angle of attack in degrees `[min, max, step]` for T3 analyses. Default is `[0, 0, 0]`.
    * `T5Range` (list, optional): A list of three numbers representing the range and step of the sideslip angle ($\beta$) in degrees `[min, max, step]` for T5 analyses. Default is `[0, 0, 0]`.
    * `T8Range` (list, optional): A list of three numbers representing the angle of attack (deg), sideslip angle (deg), and speed (m/s) for T8 analyses formatted as `[AoA, Beta, Speed]`. Default is `[0, 0, 0]`.
    * `Run` (bool, optional): If `True`, the analyses are physically executed. Default is `True`.
    * `Store` (bool, optional): If `True`, the results are moved to and stored in the "stored" folder. Default is `False`.
    * `Gate` (bool, optional): If `False`, no files/folders are modified and no analyses are executed. Default is `True`.
* **Returns:**
    * `RunRes` (list): A list of dictionaries containing metadata and paths related to the results of each executed analysis.


#### `flow5_results`
Collects the results of the analyses performed in Flow5.

* **Arguments:**
    * `RunRes` (dict): A dictionary containing data related to the results of an analysis executed by `flow5_run`.
    * `Data` (list): A list of names of the specific data to collect. These names must correspond to the headers in the Flow5 result files (excluding any parentheses containing units).
    * `OpPoints` (bool, optional): If `True`, the function also reads results from the individual Operating Points files. Default is `False`. (Note: Flow5 7.55 has known bugs with this feature; it is recommended to keep it `False` for now).
* **Returns:**
    * `Results` (tuple): The data extracted from the analysis files.
    * `Analysis` (str): The name of the analysis associated with the results.

---
### 2. `wing_params.py`
This repository contains a set of Python tools designed to automate geometry generation for the **Flow5** aerodynamic analysis software.

#### `trapez_wing`
Generates a trapezoidal wing geometry, the parameters are based on the input specifications, including automated scaling to reach a target surface area. Units are in meters and degrees.

* **Arguments:**
    * `FullWing` (bool): Indicates if the wing is a full wing or a half-wing.
    * `MiddleGap` (float): The gap between the two halves of the wing (applicable if `FullWing` is `False`).
    * `GorV` (list): A list of booleans indicating which parameters are described by a "Gene" value (range -10 to 10 for optimization) or by their actual physical value. The order is: `[Span, Chord, Offset, Twist, Dihedral]`.
    * `SpanG` (list): A list of span values for each segment of the wing.
    * `TaperG` (list): A list of taper ratios for each segment of the wing.
    * `OffsetG` (list): A list of offset values for each segment of the wing.
    * `TwistG` (list): A list of twist values for each section (number of segments + 1).
    * `DihedralG` (list): A list of dihedral angles for each segment of the wing.
    * `TargetS` (float): The target wing area for the optimization/scaling process.
    * `MaxSpan` (float): The maximum allowed wingspan.
    * `MinSeg` (float): The minimum allowed length for an individual segment.
    * `ChordLim` (list): A list defining the constraints for the chord length `[min, max]`.
    * `TwistLim` (list): A list defining the constraints for the twist angles `[min, max]`.
    * `DihedLim` (list): A list defining the constraints for the dihedral angles `[min, max]`.
    * `Acc` (float, optional): The acceptable accuracy for the optimization results. Default is `0.001`.
* **Returns:**
    * `dict`: A dictionary containing the generated wing geometry parameters:
        * `"FullWing"`: The input symmetry configuration.
        * `"SecData"`: A flattened list of section data `[y-position, chord, offset, twist, dihedral]` for each section.
        * `"S"`: The calculated wing area.
        * `"WingSpan"`: The total calculated wingspan.
        * `"MAC"`: The calculated Mean Aerodynamic Chord.
        * `"AR"`: The calculated Aspect Ratio.