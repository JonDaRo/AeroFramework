function plot_wing_3d(GeoElems_list, airfoils_dir)
    %fatto da gemini in 3 secondi alle 3:15 di notte



    % GeoElems_list: Cell array contenente multipli output GeoElem

    figure('Name', 'Modello Aerodinamico Globale 3D', 'Color', 'w');
    hold on;
    grid on;
    axis equal;
    xlabel('X [m] - Asse Longitudinale');
    ylabel('Y [m] - Asse Trasversale');
    zlabel('Z [m] - Asse Verticale');
    view(3);
    
    % Generazione di una mappa di colori per distinguere gli elementi
    colors = lines(length(GeoElems_list));

    for e = 1:length(GeoElems_list)
        % Estrazione dei dati per l'elemento e-esimo
        GeoElem_cell = cell(GeoElems_list{e});
        
        SecData = double(GeoElem_cell{1}); 
        FullWing = logical(GeoElem_cell{2});
        WingPos = double(GeoElem_cell{3}); 
        WingTilt = double(GeoElem_cell{4}); 
        py_airfoils_list = cell(GeoElem_cell{5});
        Airfoils = cell(size(py_airfoils_list));
        for k = 1:length(py_airfoils_list)
            Airfoils{k} = char(py_airfoils_list{k});
        end

        num_sections = length(SecData) / 5;
        Sections_3D = cell(num_sections, 1);
        current_z = 0;
        
        % Matrici di Rotazione (Globali dell'elemento)
        Rx = WingTilt(1);
        Ry = WingTilt(2);
        RotX = [1, 0, 0; 0, cosd(Rx), -sind(Rx); 0, sind(Rx), cosd(Rx)];
        RotY = [cosd(Ry), 0, sind(Ry); 0, 1, 0; -sind(Ry), 0, cosd(Ry)];
        R_global = RotX * RotY; % Moltiplicazione matriciale Pitch -> Roll

        for i = 1:num_sections
            idx = (i-1)*5 + 1;
            y_sec = SecData(idx);
            chord = SecData(idx+1);
            offset = SecData(idx+2);
            twist = SecData(idx+3);
            dihedral = SecData(idx+4);
            
            airfoil_name = string(Airfoils{max(1, (i-1)*2)}); 
            file_path = fullfile(airfoils_dir, airfoil_name + ".dat");
            
            [X_prof, Z_prof] = read_airfoil_dat(file_path);
            
            % 1. Scalatura locale
            X_scaled = X_prof * chord;
            Z_scaled = Z_prof * chord;
            
            % 2. Twist locale
            X_rot = X_scaled * cosd(twist) - Z_scaled * sind(twist);
            Z_rot = X_scaled * sind(twist) + Z_scaled * cosd(twist);
            
            % 3. Diedro locale
            if i > 1
                dy = y_sec - SecData((i-2)*5 + 1);
                prev_dihedral = SecData((i-2)*5 + 5);
                current_z = current_z + dy * tand(prev_dihedral);
            end
            
            % Assemblaggio vettore coordinate locali
            X_local = X_rot + offset;
            Y_local = ones(size(X_local)) * y_sec;
            Z_local = Z_rot + current_z;
            
            Pts_local = [X_local, Y_local, Z_local]';
            
            % 4. Rototraslazione nel sistema globale
            Pts_global = R_global * Pts_local;
            
            X_final = Pts_global(1,:)' + WingPos(1);
            Y_final = Pts_global(2,:)' + WingPos(2);
            Z_final = Pts_global(3,:)' + WingPos(3);
            
            Sections_3D{i} = [X_final, Y_final, Z_final];
        end
        
        % Tracciamento superfici per l'elemento corrente
        for i = 1:(num_sections-1)
            plot_segment(Sections_3D{i}, Sections_3D{i+1}, colors(e,:));
            
            if FullWing
                % Specchiatura rispetto al piano XZ globale
                Sec_L_1 = Sections_3D{i};
                Sec_L_1(:, 2) = -Sec_L_1(:, 2); 
                
                Sec_L_2 = Sections_3D{i+1};
                Sec_L_2(:, 2) = -Sec_L_2(:, 2); 
                
                plot_segment(Sec_L_1, Sec_L_2, colors(e,:)); 
            end
        end
    end
    hold off;
end

function plot_segment(Sec1, Sec2, col)
    n_pts = min(size(Sec1, 1), size(Sec2, 1));
    X_surf = [Sec1(1:n_pts, 1), Sec2(1:n_pts, 1)];
    Y_surf = [Sec1(1:n_pts, 2), Sec2(1:n_pts, 2)];
    Z_surf = [Sec1(1:n_pts, 3), Sec2(1:n_pts, 3)];
    
    surf(X_surf, Y_surf, Z_surf, 'FaceColor', col, 'EdgeColor', 'none', 'FaceAlpha', 0.85);
    plot3(Sec1(:,1), Sec1(:,2), Sec1(:,3), 'k', 'LineWidth', 1);
    plot3(Sec2(:,1), Sec2(:,2), Sec2(:,3), 'k', 'LineWidth', 1);
end

function [X, Z] = read_airfoil_dat(filepath)
    if ~isfile(filepath)
        error('File del profilo non trovato: %s', filepath);
    end
    fid = fopen(filepath, 'r');
    data = textscan(fid, '%f %f', 'HeaderLines', 1, 'CollectOutput', true);
    fclose(fid);
    
    if isempty(data{1})
        error('Formato file DAT non riconosciuto in %s.', filepath);
    end
    X = data{1}(:, 1);
    Z = data{1}(:, 2);
end