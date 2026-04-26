
def trapez_wing(FullWing:bool, MiddleGap:float, GorV:list, SpanG:list, TaperG:list, OffsetG:list, TwistG:list, DihedralG:list, TargetS:float, MaxSpan: float, MinSeg:float, ChordLim:list, TwistLim:list, DihedLim:list, Acc:float=0.001)->dict:
    """Generates wing geometry parameters based on the input specifications. Units are in meters and degrees.
    Args:
        FullWing (bool): Indicates if the wing is full or half.
        MiddleGap (float): The gap between the two halves of the wing if FullWing is False.
        GorV (list): A list of booleans indicating which parameters are describe by a Gene value (from -10 to 10) or by its actual value.
                     The order of the list corresponds to the parameters: [Span, Chord, Offset, Twist, Dihedral].
        SpanG (list): A list of span values for each segment of the wing.
        TaperG (list): A list of taper ratios for each segment of the wing.
        OffsetG (list): A list of offset values for each segment of the wing.
        TwistG (list): A list of twist values for each section (number of segment+1) of the wing.
        DihedralG (list): A list of dihedral angles for each segment of the wing.
        TargetS (float): The target wing area for the optimization.
        MaxSpan (float): The maximum allowed wingspan for the optimization.
        MinSeg (float): The minimum allowed segment length for the optimization.
        ChordLim (list): A list of limits for the chord length of the wing segments [min,max].
        TwistLim (list): A list of limits for the twist angles of the wing segments [min,max].
        DihedLim (list): A list of limits for the dihedral angles of the wing [min,max].
        Acc (float, opzionale): The acceptable accuracy for the optimization results. Default is 0.001.
    Returns:
        dict: A dictionary containing the generated wing geometry parameters, including:
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
    if not isinstance(Acc,(int,float)):
        raise TypeError("Acc must be an integer or a float")
    
    results={"FullWing":FullWing,"SecData":[],"S":0,"WingSpan":0,"MAC":0,"AR":0}
    
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
        return results

    if GorV[0]:
        span=[0]*(n_seg+1)
        r_span=max_span
        for i in range(n_seg):
            a=r_span-min_span*(n_seg-i)
            b=min_span
            span[i+1]=SpanG[i]*a/10+b
            results["WingSpan"]+=span[i+1]*ts
            r_span-=span[i+1]
    else:
        span=[0]+SpanG
        results["WingSpan"]=SpanG[-1]*ts

    if GorV[1]:
        chord=[0]*(n_seg+1)
        chord[0]=max_c

        for i in range(n_seg):
            chord[i+1]=TaperG[i]*(chord[i]-min_c)/10+min_c
            results["S"]+=(chord[i+1]+chord[i])*span[i+1]/(3-ts)

        it=0
        err=abs(results["S"]-TargetS)
        while err>Acc and it<1000:
            it+=1
            x=abs(TargetS/results["S"])
            chord[0]=chord[0]*x
            if chord[0]>max_c:
                chord[0]=max_c
            elif chord[0]<min_c:
                chord[0]=min_c
    
            results["S"]=0
            for k in range(n_seg):
                chord[k+1]=chord[k+1]*x
                if chord[k+1]>chord[k]:
                    chord[k+1]=chord[k]
                elif chord[k+1]<min_c:
                    chord[k+1]=min_c
                results["S"]+=(chord[k+1]+chord[k])*span[k+1]/(3-ts)
            err=abs(results["S"]-TargetS)
    else:
        chord=TaperG
        for i in range(n_seg):
            results["S"]+=(chord[i+1]+chord[i])*span[i+1]/(3-ts)

    results["AR"]=results["WingSpan"]*results["WingSpan"]/results["S"]
    media=0
    for i in range(n_seg):
        taper=chord[i+1]/chord[i]
        MAC_seg=chord[i]*2/3*(1+taper+taper*taper)/(1+taper)
        S_seg=(chord[i]+chord[i+1])*span[i+1]/(3-ts)
        media+=S_seg*MAC_seg
    results["MAC"]=media/results["S"]

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
        results["SecData"].extend([y[i],chord[i],offset[i],twist[i],dihedral[i]])

    if S_max<TargetS or S_min>TargetS:
        results={"FullWing":FullWing,"SecData":[],"S":0,"WingSpan":0,"MAC":0,"AR":0}
    
    return results

def geo_element(Name:str, Type:str, FullWing:bool, SecData:list, Airfoils:list, WingPos:list, WingTilt:list, Panels:int=25)->tuple:
    '''Generates the data in list format for geometry generation.
    Args:
        Name (str): The name of the element.
        Type (str): The type of element (MAINWING, OTHERWING, ELEVATOR, FIN).
        FullWing (bool): If True, the element is symmetric with respect to the plane YZ (wing or half-wing). Default is False.
        SecData (list): A list of data for each section of the element. Each section must be represented by 5 values in this order:
                        -the position along the y-axis in m;
                        -the chord in m;
                        -the offset in m;
                        -the twist angle in deg;
                        -the dihedral angle in deg.
        Airfoils (list): A list of file names for the airfoils corresponding to each section.
                         Intermediate sections are represented by two profiles: one for the left side and one for the right side.
        WingPos (list): A list of three numbers representing the position in m of the element in the aircraft reference system (x, y, z).
        WingTilt (list): A list of two numbers representing the rotation angle in deg of the element around the x, y axes (Rx, Ry).
        Panels (int, optional): The number of panels along the x direction (chord) to use. Default is 25.
    Returns:
        GeoElem (list): A list containing the generic geometric data of the element, for the visualization.
        Element (dict): A dictionary containing the geometric data for the generation of the element in Flow5.
    '''

    if not isinstance(Name, str):
        raise TypeError("Name must be a string")
    if not isinstance(Type, str):
        raise TypeError("Type must be a string")
    if not isinstance(SecData, list):
        raise TypeError("SecData must be a list")
    if not isinstance(Airfoils, list):
        raise TypeError("Airfoils must be a list")
    if not isinstance(WingPos, list):
        raise TypeError("WingPos must be a list")
    if not isinstance(WingTilt, list):
        raise TypeError("WingTilt must be a list")
    if not isinstance(Panels, int):
        raise TypeError("Panels must be an integer")

    if len(SecData)/5!=int(len(Airfoils)/2+1):
        raise ValueError("len(SecData) must be same of len(Airfoils)/2+1")

    GeoElem=[SecData,FullWing,WingPos,WingTilt,Airfoils]

    return GeoElem