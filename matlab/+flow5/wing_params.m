classdef wing_params
    properties (Constant)
        py_wp=py.importlib.import_module('aeroframework.flow5.wing_params');
    end
    methods (Static)
        function out=trapez_wing(FullWing, MiddleGap, GorV, SpanG, TaperG, OffsetG, TwistG, DihedralG, TargetS, MaxSpan, MinSeg, ChordLim, TwistLim, DihedLim, Acc)
            %{
            Generates wing geometry parameters based on the input specifications. Units are in meters and degrees.
            Args:
                FullWing (logical): Indicates if the wing is full or half.
                MiddleGap (double): The gap between the two halves of the wing if FullWing is False.
                GorV (logical array): A logical array indicating which parameters are describe by a Gene value (from -10 to 10) or by its actual value.
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
                struct: A structure containing the generated wing geometry parameters, including:
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
            
            res_py=flow5.wing_params.py_wp.trapez_wing(logical(FullWing),double(MiddleGap),py_GorV, py_SpanG, ...
                py_TaperG,py_OffsetG,py_TwistG,py_DihedralG,double(TargetS),double(MaxSpan), ...
                double(MinSeg),py_ChordLim,py_TwistLim,py_DihedLim,double(Acc));
            
            out = struct(res_py);
            if isfield(out, 'SecData') && ~isempty(out.SecData)
                out.SecData=cellfun(@double, cell(out.SecData));
            end
        end
    end
end