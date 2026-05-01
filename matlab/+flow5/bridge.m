classdef bridge
    properties (Constant)
        py_bf=py.importlib.import_module('aeroframework.flow5.bridge');
    end
    methods (Static)
        
        function CaseRes=flow5_case(Path, Threads, Fl5File, StoreOP, Gate)
            %{
            Creates the folder structure and the case.xml file for Flow5.
            Args:
                Path (string): The path of the main folder.
                Threads (integer): The number of threads to use for the analyses.
                Fl5File (logical, optional): If True, creates a .fl5 file for each analysis. Default is False.
                StoreOP (logical, optional): If True, stores the Operating Points for each analysis. Default is False. Flow5 7.55 is a bit bugged, for now is better to set it False.
                Gate (logical, optional): If False, no file/folder is modified or created. Default is True.
            Returns:
                CaseRes (struct): A structure with the paths of the folders and the case.xml file.   
            %}
            
            if nargin < 3,Fl5File = false;end
            if nargin < 4,StoreOP = false;end
            if nargin < 5,Gate = true;end
            
            res_py=flow5.bridge.py_bf.flow5_case(Path, int32(Threads), pyargs('Fl5File', logical(Fl5File), 'StoreOP', logical(StoreOP), 'Gate', logical(Gate)));
            
            CaseRes=struct(res_py);
            CaseRes.raw=res_py;
        end
    
        function [GeoElem,Element]=flow5_element(Name, Type, WingGeo, Airfoils, WingPos, WingTilt, Panels)
            %{
            Generates a structure for geometry generation and a structure for element generation in Flow5.
            Args:
                Name (string): The name of the element.
                Type (string): The type of element (MAINWING, OTHERWING, ELEVATOR, FIN).
                WingGeo (struct): A structure with the geometric data of the element, with the following fields:
                                -FullWing (logical): If True, the element is symmetric with respect to the central plane (wing or half-wing). Default is False.
                                -SecData (double array): An array of data for each section of the element. Each section must be represented by 5 values in this order:
                                            -the position along the y axis in m;
                                            -the chord in m;
                                            -the offset in m;
                                            -the twist angle in degrees;
                                            -the dihedral angle in degrees.
                Airfoils (string array): An array of file names for the airfoils corresponding to each section.
                                Intermediate sections are represented by two profiles: one for the left side and one for the right side.
                WingPos (double array): An array of three numbers representing the position in m of the element in the aircraft reference system (x, y, z).
                WingTilt (double array): An array of two numbers representing the rotation angle in deg of the element around the x, y axes (Rx, Ry).
                Panels (integer, optional): The number of panels along the x direction (chord) to use. Default is 25.
            Returns:
                GeoElem (struct): A structure containing the geometric data of the element for the visualization.
                Element (struct): A structure containing the geometric data for the generation of the element in Flow5.
            %}

            if nargin < 7,Panels = 25;end
            
            py_WingGeo=py.dict(pyargs('FullWing', logical(WingGeo.FullWing), 'SecData', py.list(num2cell(double(WingGeo.SecData)))));
            py_Airfoils=py.list(cellstr(Airfoils));
            py_WingPos=py.list(num2cell(double(WingPos)));
            py_WingTilt=py.list(num2cell(double(WingTilt)));
            
            out_tuple=flow5.bridge.py_bf.flow5_element(Name, Type, py_WingGeo, ...
                py_Airfoils, py_WingPos, py_WingTilt, pyargs('Panels', int32(Panels)));
            
            GeoElem=struct(out_tuple{1});
            GeoElem.raw=out_tuple{1};
            Element=struct(out_tuple{2});
            Element.raw=out_tuple{2};
        end
        
        function PlaneRes=flow5_plane(CaseRes, Name, MassRes, Elements, AirfoilsDir, PolarsDir, BankAng, TotRefS, Gate)
            %{
            Creates an XML file for the definition of an aircraft in Flow5.
            Args:
                CaseRes (struct): The structure returned by flow5_case.
                Name (string): The name of the aircraft.
                MassRes (struct array): An array of structures with the mass data for each element of the aircraft. Each structure must contain: 
                                -the keys "coord" (an array of three numbers for the coordinates x, y, z in m), "mass" (the mass in Kg)
                                    and "tag" (a name to identify the mass point);
                                -if the key "coord" is the name of the element, the key "mass" is its mass in kg (automatically distributed over the entire element by flow5) and there is no key "tag".
                Elements (struct array): An array of structures with the geometric data for each element of the aircraft obtained through flow5_element.
                AirfoilsDir (string): The path of the folder containing the airfoils .dat files.
                PolarsDir (string): The path of the folder containing the polars .plr or .txt files.
                BankAng (double, optional): The bank angle in deg to apply to the entire aircraft (positive is clockwise rotation around the x-axis). Default is 0.
                TotRefS (logical, optional): If True, considers the total surface area of the aircraft as reference for the analyses (include OTHERWING elements). Default is False.
                Gate (logical, optional): If False no file/folder is modified or created. Default is True.
            Returns:
                PlaneRes (struct): A structure with the data related to the aircraft.
            %}

            if nargin < 7,BankAng = 0;end
            if nargin < 8,TotRefS = false;end
            if nargin < 9,Gate = true;end
            
            py_MassRes=py.list();
            for i=1:length(MassRes)
                m=MassRes(i);
                coord_py=py.list(num2cell(double(m.coord)));
                dict_py=py.dict(pyargs('coord', coord_py, 'mass', double(m.mass), 'tag', m.tag));
                py_MassRes.append(dict_py);
            end
            
            py_Elements=py.list();
            for i=1:length(Elements)
                py_Elements.append(Elements(i).raw);
            end
            
            res_py=flow5.bridge.py_bf.flow5_plane(CaseRes.raw, Name, py_MassRes, py_Elements, AirfoilsDir, PolarsDir, pyargs('BankAng', double(BankAng),'TotRefS', logical(TotRefS), 'Gate', logical(Gate)));
            
            PlaneRes=struct(res_py);
            PlaneRes.raw=res_py;
        end
        
        function AnalysisRes=flow5_analysis(PlaneRes, Name, Type, Method, FixTAS, FixAoA, ThinSurf, GrdEff, Height, Viscosity, Density, Viscous, Xflr5Visc, Optional)
            %{
            Creates an XML file for a Flow5 analysis.
            Args:
                PlaneRes (struct): The structure returned by flow5_plane.
                Name (string): The name of the analysis.
                Type (string): The type of analysis (T1, T2, T3, T5, T8).
                Method (string): The analysis method (LLT, VLM1, VLM2, QUADS, TRIUNIFORM, TRILINEAR).
                ThinSurf (logical, optional): If True, considers thin surfaces. Default is True.
                GrdEff (logical, optional): If True, considers ground effect. Default is False.
                Height (double, optional): The height above ground for ground effect. Default is 0.
                Viscosity (double, optional): The kinematic viscosity of the fluid. Default is 1.5e-05m^2/s.
                Density (double, optional): The density of the fluid. Default is 1.225kg/m^3.
                Viscous (logical, optional): If True, performs a viscous analysis. Default is True.
                Xflr5Visc (logical, optional): If True uses CL data for viscous analysis (XFLR5 method). Default is True.
                FixTAS (double, optional): The fixed velocity for fixed speed analyses. Default is 0m/s.
                FixAoA (double, optional): The fixed angle of attack for fixed angle of attack analyses. Default is 0deg.
                Optional (struct, optional): A structure with any additional parameters to include in the XML file. The key must be the XML parameter path like "Polar/Viscous_Analysis/TransAtHinge" associated to its value.
                Gate (logical, optional): If False no file/folder is modified or created. Default is True.
            Returns:
                AnalysisRes (struct): A structure with the data related to the analysis.
            %}

            if nargin < 5,FixTAS = 0;end
            if nargin < 6,FixAoA = 0;end
            if nargin < 7,ThinSurf = true;end
            if nargin < 8,GrdEff = false;end
            if nargin < 9,Height = 0;end
            if nargin < 10,Viscosity = 1.5e-05;end
            if nargin < 11,Density = 1.225;end
            if nargin < 12,Viscous = true;end
            if nargin < 13,Xflr5Visc = true;end
            if nargin < 14,Optional = struct();end
            
            res_py=flow5.bridge.py_bf.flow5_analysis(PlaneRes.raw, Name, Type, Method, logical(ThinSurf),...
            logical(GrdEff), double(Height), double(Viscosity), double(Density), logical(Viscous),...
            logical(Xflr5Visc), double(FixTAS), double(FixAoA), pyargs('optional', py.dict(Optional)));
            
            AnalysisRes=struct(res_py);
            AnalysisRes.raw=res_py; 
        end
        
        function RunRes=flow5_run(ExePath, AnalysisRes, T12Range, T3Range, T5Range, T8Range, Run, Store, Gate)
            %{
            Executes the analyses in Flow5.
            Args:
                ExePath (string): The path of the Flow5 executable.
                AnalysisRes (struct array): An array of structures with the data for each analysis obtained through flow5_analysis.
                T12Range (double array, optional): An array of three numbers representing the range and step of the angle of attack in deg [min, max, step] for T1 and T2 analyses. Default is [0, 0, 0].
                T3Range (double array, optional): An array of three numbers representing the range and step of the angle of attack in deg [min, max, step] for T3 analyses. Default is [0, 0, 0].
                T5Range (double array, optional): An array of three numbers representing the range and step of the sideslip angle in deg [min, max, step] for T5 analyses. Default is [0, 0, 0].
                T8Range (double array, optional): An array of three numbers representing the angle of attack (deg), sideslip angle (deg) and speed (m/s) of the drone [AoA, Beta, Speed] for T8 analyses. Default is [0, 0, 0].
                Run (logical, optional): If True, executes the analyses. Default is True.
                Store (logical, optional): If True, stores the results in the "stored" folder. Default is False.
                Gate (logical, optional): If False no file/folder is modified or created and no analyses are executed. Default is True.
            Returns:
                RunRes (struct array): An array of structures with the data related to the results of each analysis.
            %}

            if nargin<3,T12Range=[0,0,0];end
            if nargin<4,T3Range=[0,0,0];end
            if nargin<5,T5Range=[0,0,0];end
            if nargin<6,T8Range=[0,0,0];end
            if nargin<7,Run=true;end
            if nargin<8,Store=false;end
            if nargin<9,Gate=true;end
            
            py_AnalList = py.list();
            for i=1:length(AnalysisRes)
                py_AnalList.append(AnalysisRes(i).raw);
            end
            
            py_T12Range=py.list(num2cell(double(T12Range)));
            py_T3Range=py.list(num2cell(double(T3Range)));
            py_T5Range=py.list(num2cell(double(T5Range)));
            py_T8Range=py.list(num2cell(double(T8Range)));
            
            res_py_list=flow5.bridge.py_bf.flow5_run(ExePath, py_AnalList, ...
                pyargs('T12Range', py_T12Range, 'T3Range', py_T3Range, ...
                       'T5Range', py_T5Range, 'T8Range', py_T8Range, ...
                       'Run', logical(Run), 'Store', logical(Store), 'Gate', logical(Gate)));
            
            num_analyses=length(res_py_list);
            RunRes=struct('raw',cell(1, num_analyses));
            
            for i=1:num_analyses
                RunRes(i).raw=res_py_list{i};
            end
        end



        function [ResMatrix, Headers, AnalysisName]=flow5_results(RunRes, Data, OpPoints)
            %{
            Collects the results of the analyses in Flow5.
            Args:
                RunRes (struct): A structure with the data related to the results of an analysis executed by flow5_run.
                Data (string array): An array of names of data to collect. They must be present in the files containing the results obtained
                                    from Flow5 (without any parentheses that may contain the units).
                OpPoints (logical, optional): If True, also reads the results from the individual Operating Points files. Default is False. Flow5 7.55 is a bit bugged, for now is better to set it False.
            Returns:
                ResMatrix (double array): A matrix containing the numerical results of the analysis.
                Headers (string array): An array of strings containing the names of the variables in each column of ResMatrix.
                AnalysisName (string): The name of the analysis extracted from Flow5.
            %}

            if nargin < 3,OpPoints = false;end

            py_Data=py.list(cellstr(Data));
            res_tuple=flow5.bridge.py_bf.flow5_results(RunRes.raw, py_Data, pyargs('OpPoints', logical(OpPoints)));
            
            AnalysisName=string(res_tuple{2}); 

            Results_py=res_tuple{1};
            Results_cell=cell(Results_py);

            Headers_cell=cell(Results_cell{1});
            num_cols=length(Headers_cell);
            Headers=strings(1, num_cols);
            for c=1:num_cols
                Headers(c)=string(Headers_cell{c});
            end
            
            num_rows=length(Results_cell)-1;
            ResMatrix=zeros(num_rows,num_cols);
            for r=1:num_rows
                riga=cell(Results_cell{r+1});
                for c=1:num_cols
                    ResMatrix(r, c)=double(riga{c});
                end
            end
        end
    end
end