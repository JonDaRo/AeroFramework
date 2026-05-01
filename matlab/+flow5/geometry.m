classdef geometry
    properties (Constant)
        py_wp=py.importlib.import_module('aeroframework.flow5.geometry');
    end
    methods (Access=public, Static)
        function WingData=trapez_wing(FullWing, MiddleGap, GorV, SpanG, TaperG, OffsetG, TwistG, DihedralG, TargetS, MaxSpan, MinSeg, ChordLim, TwistLim, DihedLim, Acc)
            %{
            Generates wing geometry parameters based on the input specifications. Units are in meters and degrees.
            Args:
                FullWing (logical): Indicates if the wing is full or half.
                MiddleGap (double): The gap between the two halves of the wing if FullWing is False.
                GorV (logical array): A logical array indicating which parameters are describe by a Gene value (from 0 to 10) or by its actual value.
                                      The order of the array corresponds to the parameters: [Span, Chord, Offset, Twist, Dihedral].
                SpanG (double array): An array of span values for each segment of the wing.
                TaperG (double array): An array of taper ratios for each segment of the wing.
                OffsetG (double array): An array of offset values for each segment of the wing.
                TwistG (double array): An array of twist values for each section (number of segment+1) of the wing.
                DihedralG (double array): An array of dihedral angles for each segment of the wing.
                TargetS (double): The target wing area for the optimization.
                MaxSpan (double): The maximum allowed wingspan for the optimization.
                MinSeg (double): The minimum allowed segment length for the optimization.
                ChordLim (double array): An array of limits for the chord length of the wing segments [min,max].
                TwistLim (double array): An array of limits for the twist angles of the wing segments [min,max].
                DihedLim (double array): An array of limits for the dihedral angles of the wing [min,max].
                Acc (double, opzionale): The acceptable accuracy for the optimization results. Default is 0.001.
            Returns:
                WingData (struct): A structure containing the generated wing geometry parameters, including:
                                  - "FullWing": The input FullWing value.
                                  - "SecData": A flattened array of section data for each segment of the wing, each section is described by [span posistion, chord, offset, twist, dihedral].
                                  - "S": The calculated wing area based on the generated geometry.
                                  - "WingSpan": The calculated wingspan based on the generated geometry.
                                  - "MAC": The calculated mean aerodynamic chord based on the generated geometry.
                                  - "AR": The calculated aspect ratio based on the generated geometry.
            %}

            if nargin < 15,Acc=0.001;end
            
            py_GorV     =py.list(num2cell(logical(GorV)));
            py_SpanG    =py.list(num2cell(double(SpanG)));
            py_TaperG   =py.list(num2cell(double(TaperG)));
            py_OffsetG  =py.list(num2cell(double(OffsetG)));
            py_TwistG   =py.list(num2cell(double(TwistG)));
            py_DihedralG=py.list(num2cell(double(DihedralG)));
            py_ChordLim =py.list(num2cell(double(ChordLim)));
            py_TwistLim =py.list(num2cell(double(TwistLim)));
            py_DihedLim =py.list(num2cell(double(DihedLim)));
            
            res_py=flow5.geometry.py_wp.trapez_wing(logical(FullWing),double(MiddleGap),py_GorV, py_SpanG, ...
                py_TaperG,py_OffsetG,py_TwistG,py_DihedralG,double(TargetS),double(MaxSpan), ...
                double(MinSeg),py_ChordLim,py_TwistLim,py_DihedLim,double(Acc));
            
            WingData = struct(res_py);
            if isfield(WingData, 'SecData') && ~isempty(WingData.SecData)
                WingData.SecData=cellfun(@double, cell(WingData.SecData));
            end
        end

        function plot_3d(GeoElem, Airfoils_Dir)
            %{
            Plots the 3D elements using PyVista.
            Args:
                GeoElem (structure array): An array of structures of geometric elements, each containing geometric data for the visualization.
                Airfoils_Dir (string): Directory path where airfoil coordinate files are stored.
            %}

            py_GeoElem = py.list();
            for i=1:length(GeoElem)
                py_GeoElem.append(GeoElem(i).raw);
            end

            flow5.geometry.py_wp.plot_3d(py_GeoElem, Airfoils_Dir);
        end

        function plot_3d_live(GeoElems, AirfoilsDir)
            %{
            Plots the 3D elements. The graph do not stop the progress of the script and can be updated during loops.
            Args:
                GeoElems (structure array): List of geometric elements, each containing geometric data for the visualization.
                AirfoilsDir (string): Directory path where airfoil coordinate files are stored.
            %}

            fig=figure('Name', 'AeroFramework Viewer', 'NumberTitle', 'off', 'Color', 'w');
            ax=axes(fig);
            hold(ax,'on');
            grid(ax,'on');
            axis(ax, 'equal');
            axis(ax, 'vis3d');
            set(ax,'Clipping', 'off');
            view(ax, 3);
            camlight(ax,'headlight');
            lighting(ax,'gouraud');
            
            for i = 1:length(GeoElems)
                flow5.geometry.add_element_matlab(ax, GeoElems(i), AirfoilsDir);
            end
            
            rotate3d(fig, 'on');
            zoom(fig, 'on');
            
            drawnow;
        end
    end
    methods (Access=private, Static)
        function add_element_matlab(ax, GeoElem, AirfoilsDir)
            name=char(GeoElem.name);
            type=char(GeoElem.type);
            full_wing=logical(GeoElem.full_wing);
            wing_pos=cellfun(@double,cell(GeoElem.wing_pos));
            wing_rot=cellfun(@double,cell(GeoElem.wing_tilt));
            airfoils=cell(1,length(GeoElem.airfoils));
            for j=1:length(GeoElem.airfoils)
                airfoils{j}=char(GeoElem.airfoils{j});
            end
            num_secs=length(GeoElem.geo_data);
            geo_data= zeros(num_secs,6);
            for j=1:num_secs
                geo_data(j, :) =double(GeoElem.geo_data{j});
            end

            sections=cell(1, length(airfoils)); 

            coord_2d_root =flow5.geometry.load_airfoil(airfoils{1},AirfoilsDir);
            sections{1} =flow5.geometry.modify_airfoil(coord_2d_root,geo_data(1,:));

            for j=2:length(airfoils)-1
                k=ceil(j/2);
                coord_2d= flow5.geometry.load_airfoil(airfoils{j},AirfoilsDir);
                sections{j}= flow5.geometry.modify_airfoil(coord_2d,geo_data(k,:));
            end

            coord_2d_tip =flow5.geometry.load_airfoil(airfoils{end}, AirfoilsDir);
            sections{end}=flow5.geometry.modify_airfoil(coord_2d_tip, geo_data(end,:));

            R=flow5.geometry.make_rot_matrix(wing_rot(1), wing_rot(2));

            color = flow5.geometry.get_element_color(type); 

            flow5.geometry.render_mesh(ax, sections, R, wing_pos, false, color);
            flow5.geometry.render_outlines(ax, sections, R, wing_pos, false);
            if full_wing
                flow5.geometry.render_mesh(ax, sections, R, wing_pos, true, color);
                flow5.geometry.render_outlines(ax, sections, R, wing_pos, true);
            end
            anchor_point=wing_pos+(R*sections{1}(1,:)')';
            text(ax, anchor_point(1), anchor_point(2),anchor_point(3),name, ...
                'FontSize',10,'FontWeight','bold','BackgroundColor','none');

        end

        
        function render_mesh(ax, sections, R, wing_pos, is_mirror, color)
            num_secs=length(sections);
            num_pts=size(sections{1}, 1);
            X=zeros(num_pts, num_secs);
            Y=zeros(num_pts, num_secs);
            Z=zeros(num_pts, num_secs);
            
            for i=1:num_secs
                s_mod = sections{i};
                if is_mirror
                    s_mod(:, 2)=-s_mod(:, 2);
                end
                transformed=(R*s_mod')'+wing_pos;
                
                X(:, i)=transformed(:, 1);
                Y(:, i)=transformed(:, 2);
                Z(:, i)=transformed(:, 3);
            end
            
            surf(ax, X, Y, Z, 'FaceColor', color, 'EdgeColor', 'none', ...
                'FaceLighting', 'gouraud', 'AmbientStrength', 0.5);
        end

        function render_outlines(ax, sections, R, wing_pos, is_mirror)
            for i=1:length(sections)
                s_mod = sections{i};
                if is_mirror
                    s_mod(:, 2) =-s_mod(:, 2);
                end
                transformed= (R*s_mod')'+wing_pos;
                
                plot3(ax,[transformed(:,1); transformed(1,1)], ...
                        [transformed(:,2); transformed(1,2)], ...
                        [transformed(:,3); transformed(1,3)], ...
                        'k-', 'LineWidth', 1.2);
            end
        end



        function coord_2d=load_airfoil(name, AirfoilsDir, num_pts)
            if nargin<3,num_pts=100;end
            path=fullfile(AirfoilsDir, sprintf('%s.dat',char(name)));
            
            try
                raw_data = readmatrix(path, 'FileType', 'text', 'NumHeaderLines', 1);
            catch E
                fprintf('Errore caricamento %s: %s\n', char(name), E.message);
                coord_2d = []; return;
            end
            dist = sqrt(diff(raw_data(:,1)).^2 + diff(raw_data(:,2)).^2);
            raw_data = raw_data([true; dist > 1e-16], :);

            dx=diff(raw_data(:,1));
            dz=diff(raw_data(:,2));
            ds=sqrt(dx.^2 + dz.^2);
            s=[0;cumsum(ds)];
            s_norm=s/s(end);

            t=linspace(0,1,num_pts)';
            s_new=t+0.15*sin(2*pi*t);
            
            new_x = interp1(s_norm, raw_data(:,1), s_new, 'linear');
            new_z = interp1(s_norm, raw_data(:,2), s_new, 'linear');
            coord_2d = [new_x, new_z];

            area = 0.5*sum(coord_2d(1:end-1, 1) .* coord_2d(2:end, 2) - ...
                            coord_2d(2:end, 1) .* coord_2d(1:end-1, 2));
            if area<0
                coord_2d=flipud(coord_2d);
            end
        end

        function coord_3d=modify_airfoil(coord_2d, mod)
            N=size(coord_2d, 1);
            x_raw=coord_2d(:,1);
            z_raw=coord_2d(:,2);
            y_raw=zeros(N,1);

            t1=deg2rad(mod(1));
            cos_t1=cos(t1); sin_t1=sin(t1);
            x_l=x_raw*cos_t1-z_raw*sin_t1;
            z_l=x_raw*sin_t1+z_raw*cos_t1;

            t2=deg2rad(mod(2));
            cos_t2=cos(t2); sin_t2 = sin(t2);
            y_l=y_raw*cos_t2-z_l*sin_t2;
            z_l=y_raw*sin_t2+z_l*cos_t2;

            chord=mod(3);
            x_l=x_l*chord;
            y_l=y_l*chord;
            z_l=z_l*chord;

            x_l=x_l+mod(4);
            y_l=y_l+mod(5);
            z_l=z_l+mod(6);

            coord_3d = [x_l,-y_l,z_l];
        end

        function R=make_rot_matrix(rx, ry)
            rx=deg2rad(rx); 
            ry=deg2rad(ry);
            
            Rx = [1, 0, 0; ...
                0, cos(rx), -sin(rx); ...
                0, sin(rx), cos(rx)];
            
            Ry = [cos(ry), 0, sin(ry); ...
                0, 1, 0; ...
                -sin(ry), 0, cos(ry)];
            
            R=Rx*Ry;
        end

        function color=get_element_color(type)
            switch char(type)
                case 'MAINWING'
                    color=[0.69, 0.77, 0.87];
                case 'OTHERWING'
                    color=[0.24, 0.70, 0.44];
                case 'ELEVATOR'
                    color=[0.80, 0.36, 0.36];
                case 'FIN'
                    color=[1.00, 0.55, 0.00];
                otherwise
                    color=[0.83, 0.83, 0.83];
            end
        end

    end
end