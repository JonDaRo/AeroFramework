from os.path import isfile,isdir,join,basename,exists,dirname
from os import makedirs,remove,listdir
import xml.etree.ElementTree as ET
from copy import deepcopy
from shutil import copytree,rmtree,copy
from math import ceil
import numpy as np
import subprocess
import itertools
import re

_BASE_DIR=dirname(__file__)
_templates={
    "Case": join(_BASE_DIR,"templates/template_case.xml"),
    "Plane": join(_BASE_DIR,"templates/template_plane.xml"),
    "Analysis": join(_BASE_DIR,"templates/template_analysis.xml")
}
for name, path in _templates.items():
    if not exists(path):
        raise FileNotFoundError(f"Critical Error: The '{name}' template was not found at: {path}")


def _search_files(direc,exts=None):
    if not isinstance(direc,(str)):
        raise Exception("direc need to be a str variable")
    if not isdir(direc):
        raise Exception(direc+" is not a valid directory")
    if exts==None:
        files=[{"name":f,"path":direc+"/"+f} for f in listdir(direc) if isfile(direc+"/"+f)]
    elif isinstance(exts,(str,tuple)):
        files=[{"name":f,"path":direc+"/"+f} for f in listdir(direc) if f.lower().endswith(exts) and isfile(direc+"/"+f)]
    elif isinstance(exts,(list)):
        files=[{"name":f,"path":direc+"/"+f} for f in listdir(direc) for e in exts if f.lower().endswith(e) and isfile(direc+"/"+f)]
    else:
        raise Exception("exts need to be a str, list, tuple variable or None. If None take all files in the directory.")
    return files


def _get_files(direc,exts):
    files=[]
    if not isinstance(direc,(list)):
        direc=[direc]
    for d in direc:
        if isdir(d):
            files.extend(_search_files(d,exts))
        elif isfile(d) and d.lower().endswith(exts):
            files.append({"name":basename(d),"path":d})
    return files


def _XML_writer(data,file,xml_type=None):
    XML=file
    if xml_type !=None:
        if exists(file): 
            remove(file)
        XML=_templates[xml_type]

    tree=ET.parse(XML)
    root=tree.getroot()
    
    for key,value in data.items():
        parts=key.split('/')
        parent=root
        
        for part in parts:
            p=part.split('+')
            if len(p)==1:
                tag,n_part=part,1
            else:
                tag,n_part=p[0], int(p[1])+1
            
            elements=parent.findall(tag)
            
            while len(elements)<n_part:
                new_element=ET.SubElement(parent, tag)
                elements.append(new_element)
            
            parent=elements[n_part - 1]
            
        parent.text=str(value)
        
    ET.indent(root,'    ')
    tree.write(file, encoding='utf-8', xml_declaration=True)
    return 0


def flow5_case(Path:str, Threads:int, Fl5File:bool=False, StoreOP:bool=False, Gate:bool=True)->dict:
    '''Creates the folder structure and the case.xml file for Flow5.
    Args:
        Path (str): The path of the main folder.
        Threads (int): The number of threads to use for the analyses.
        Fl5File (bool): If True, creates a .fl5 file for each analysis. Default is False.
        StoreOP (bool): If True, stores the Operating Points for each analysis. Default is False. Flow5 7.55 is a bit bugged, for now is better to set it False.
        Gate (bool, optional): If False, no file/folder is modified or created. Default is True.
    Returns:
        CaseRes (dict): A dictionary with the paths of the folders and the case.xml file.
    '''

    if not isinstance(Path, str):
        raise TypeError("Path must be a string")
    if not isinstance(Threads, int):
        raise TypeError("Threads must be an integer")
    if not isinstance(Fl5File, bool):
        raise TypeError("Fl5File must be a boolean")
    if not isinstance(StoreOP, bool):
        raise TypeError("StoreOP must be a boolean")
    if not isinstance(Gate, bool):
        raise TypeError("Gate must be a boolean")

    multithreading="false"
    if Threads<1:
        Threads=1
    elif Threads>1:
        multithreading="true"
    Threads=str(Threads)
    Fl5File=str(Fl5File).lower()
    StoreOP=str(StoreOP).lower()

    case_path=join(Path,"flow5_case")
    AIRFOILS=join(case_path,"airfoils")
    ANALYSIS=join(case_path,"analysis")
    PLANES=join(case_path,"planes")
    RESULTS=join(case_path,"results")
    STORED=join(case_path,"stored")
    XFLR5_POLARS=join(case_path,"xflr5_polars")
    XFOIL_POLARS=join(case_path,"xfoil_polars")
    CASE_XML=join(case_path,"case.xml")

    CaseRes={"case_path":case_path,"airfoils_path":AIRFOILS,"xflr5_polars":XFLR5_POLARS,
    "xfoil_polars":XFOIL_POLARS,"analysis_path":ANALYSIS,"planes_path":PLANES,"results_path":RESULTS,
    "stored_path":STORED,"case_xml":CASE_XML}

    if not Gate:
        return CaseRes

    try:
        makedirs(AIRFOILS, exist_ok=True)
        makedirs(ANALYSIS, exist_ok=True)
        makedirs(PLANES, exist_ok=True)
        makedirs(RESULTS, exist_ok=True)
        makedirs(STORED, exist_ok=True)
        makedirs(XFLR5_POLARS, exist_ok=True)
        makedirs(XFOIL_POLARS, exist_ok=True)

        data={
            "Metadata/Make_project_file": Fl5File,
            "Metadata/Directories/output_dir": RESULTS,
            "Metadata/Directories/plane_definition_xml_dir": PLANES,
            "Metadata/Directories/plane_analysis_xml_dir": ANALYSIS,
            "Metadata/Directories/foil_files_dir": AIRFOILS,
            "Metadata/Directories/foil_polars_dir": XFLR5_POLARS,
            "Metadata/Directories/xfoil_polars_dir": XFOIL_POLARS,
            "Metadata/MultiThreading/Allow_Multithreading": multithreading,
            "Metadata/MultiThreading/Max_threads": Threads,
            "Plane_Analysis/Plane_Analysis_Output/make_oppoints": StoreOP,
            "Plane_Analysis/Plane_Analysis_Output/make_oppoints_text_file": StoreOP,
            "Plane_Analysis/Plane_Analysis_Output/export_oppoint_Cp": StoreOP
        }
        for key in data.keys():
            if not isinstance(data[key],str):
                data[key]=str(data[key])
        _XML_writer(data,CASE_XML,"Case")

    except Exception as err:
        raise RuntimeError(f"Flow5 case creation failed: {err}")

    return CaseRes


def flow5_analysis(PlaneRes:dict, Name:str, Type:str, Method:str, ThinSurf:bool=True, GrdEff:bool=False, Height:float=0.0, Viscosity:float=1.5e-05, Density:float=1.225, Viscous:bool=True, Xflr5Visc:bool=True, FixTAS:float=0.0, FixAoA:float=0.0, Optional:dict={}, Gate:bool=True)->dict:
    '''Creates an XML file for a Flow5 analysis.
    Args:
        PlaneRes (dict): The dictionary returned by flow5_plane.
        Name (str): The name of the analysis.
        Type (str): The type of analysis (T1, T2, T3, T5, T8).
        Method (str): The analysis method (LLT, VLM1, VLM2, QUADS, TRIUNIFORM, TRILINEAR).
        ThinSurf (bool, optional): If True, considers thin surfaces. Default is True.
        GrdEff (bool, optional): If True, considers ground effect. Default is False.
        Height (float, optional): The height above ground for ground effect. Default is 0.
        Viscosity (float, optional): The kinematic viscosity of the fluid. Default is 1.5e-05m^2/s.
        Density (float, optional): The density of the fluid. Default is 1.225kg/m^3.
        Viscous (bool, optional): If True, performs a viscous analysis. Default is True.
        Xflr5Visc (bool, optional): If True uses CL data for viscous analysis (XFLR5 method). Default is True.
        FixTAS (float, optional): The fixed velocity for fixed speed analyses. Default is 0m/s.
        FixAoA (float, optional): The fixed angle of attack for fixed angle of attack analyses. Default is 0deg.
        Optional (dict, optional): A dictionary with any additional parameters to include in the XML file. The key must be the XML parameter path like "Polar/Viscous_Analysis/TransAtHinge" associated to its value.
        Gate (bool, optional): If False no file/folder is modified or created. Default is True.
    Returns:
        AnalysisRes (dict): A dictionary with the data related to the analysis.
    '''

    if not isinstance(Gate, bool):
        raise TypeError("Gate must be a boolean")
    if not isinstance(PlaneRes, dict):
        raise TypeError("PlaneRes must be a dictionary")
    if not isinstance(Name, str):
        raise TypeError("Name must be a string")
    if not isinstance(Type, str):
        raise TypeError("Type must be a string")
    if not isinstance(Method, str):
        raise TypeError("Method must be a string")
    if not isinstance(ThinSurf, bool):
        raise TypeError("ThinSurf must be a boolean")
    if not isinstance(GrdEff, bool):
        raise TypeError("GrdEff must be a boolean")
    if not isinstance(Height, (int, float)):
        raise TypeError("Height must be a number")
    if not isinstance(Viscosity, (int, float)):
        raise TypeError("Viscosity must be a number")
    if not isinstance(Density, (int, float)):
        raise TypeError("Density must be a number")
    if not isinstance(Viscous, bool):
        raise TypeError("Viscous must be a boolean")
    if not isinstance(Xflr5Visc, bool):
        raise TypeError("Xflr5Visc must be a boolean")
    if not isinstance(FixTAS, (int, float)):
        raise TypeError("FixTAS must be a number")
    if not isinstance(FixAoA, (int, float)):
        raise TypeError("FixAoA must be a number")
    if not isinstance(Optional, dict):
        raise TypeError("Optional must be a dictionary")
    if not isinstance(Gate, bool):
        raise TypeError("Gate must be a boolean")
    
    for key in Optional.keys():
        if not isinstance(key,str):
            raise TypeError("All keys in optional must be strings")
    
    types={
        "T1": "FIXEDSPEEDPOLAR",
        "T2": "FIXEDLIFTPOLAR",
        "T3": "GLIDEPOLAR",
        #"T4": "FIXEDAOAPOLAR",
        "T5": "BETAPOLAR",
        #"T6": "CONTROLPOLAR",
        #"T7": "STABILITYPOLAR",
        "T8": "T8POLAR"
    }

    AnalysisRes=deepcopy(PlaneRes)
    AnalysisRes.update({"analysis":Name,"velocity":FixTAS,"type":types[Type]})
    if not Gate:
         return AnalysisRes

    ANALYSIS_XML=join(PlaneRes["analysis_path"],f"{Name}.xml")

    data={
        "Polar/Polar_Name": Name,
        "Polar/Plane_Name": PlaneRes["plane"],
        "Polar/Type": types[Type],
        "Polar/Method": Method,
        "Polar/Thin_Surfaces": ThinSurf,
        "Polar/Ground_Effect": GrdEff,
        "Polar/Ground_Height": Height,
        "Polar/Fluid/Viscosity": Viscosity,
        "Polar/Fluid/Density": Density,
        "Polar/Viscous_Analysis/Is_Viscous_Analysis": Viscous,
        "Polar/Viscous_Analysis/From_CL": Xflr5Visc,
        "Polar/Fixed_Velocity": FixTAS,
        "Polar/Fixed_AOA": FixAoA,
        "Polar/Reference_Dimensions/Reference_Area": PlaneRes["ref_data"][0],
        "Polar/Reference_Dimensions/Reference_Span_Length": PlaneRes["ref_data"][1],
        "Polar/Reference_Dimensions/Reference_Chord_Length": PlaneRes["ref_data"][2]
    }

    data.update(Optional)
    for key in data.keys():
        if not isinstance(data[key],str):
            data[key]=str(data[key])

    try:
        _XML_writer(data,ANALYSIS_XML,"Analysis")
    except Exception as err:
        raise RuntimeError(f"Flow5 analysis creation failed: {err}")
    return AnalysisRes


def _wingparams(SecData):
    S=0
    l=int(len(SecData)/5)-1
    for i in range(l):
        k=i+1
        S+=(SecData[k*5]-SecData[i*5])*(SecData[1+k*5]+SecData[1+i*5])
    wingspan=2*SecData[-5]

    media=0
    for i in range(l):
        k=i+1
        taper=SecData[1+k*5]/SecData[1+i*5]
        MAC_seg=SecData[1+i*5]*2/3*(1+taper+taper*taper)/(1+taper)
        S_seg=(SecData[1+k*5]+SecData[1+i*5])*(SecData[k*5]-SecData[i*5])
        media+=S_seg*MAC_seg
    MAC=media/S
    return S,wingspan,MAC


def _geo_element(SecData):
    
    n_sec=len(SecData)//5
    geo_data=[]
    prev_data=[SecData[4],0,0,0]
    
    for i in range(n_sec):
        sec_data=[-SecData[i*5+3], (prev_data[0]+SecData[i*5+4])/2, SecData[i*5+1]]
        x=SecData[i*5+2]
        y=prev_data[2]+(SecData[i*5]-prev_data[1])*np.cos(np.radians(prev_data[0]))
        z=prev_data[3]+(SecData[i*5]-prev_data[1])*np.sin(np.radians(prev_data[0]))
        prev_data=[SecData[i*5+4],SecData[i*5],y,z]
        sec_data.extend([x,y,z])
        geo_data.append(sec_data)

    return geo_data


def flow5_element(Name:str, Type:str, WingGeo:dict, Airfoils:list, WingPos:list, WingTilt:list, Panels:int=25)->tuple:
    '''Generates a dictionary for the geometry visualization and another dictionary for element generation in Flow5.
    Args:
        Name (str): The name of the element.
        Type (str): The type of element (MAINWING, OTHERWING, ELEVATOR, FIN).
        WingGeo (dict): A dictionary containing the geometric data of the element. It must contain the following keys:
                        -FullWing (bool): If True, the element is symmetric with respect to the YZ plane (wing or half-wing). Default is False.
                        -SecData (float list): A list of data for each section of the element. Each section must be represented by 5 values in that order:
                                         -Position along the y-axis (m).;
                                         -Chord length (m).
                                         -Offset (m).
                                         -Twist angle (deg).
                                         -Dihedral angle (deg).
        Airfoils (str list): A list of file names for the airfoils corresponding to each section.
                         Intermediate sections are represented by two profiles: one for the left side and one for the right side.
        WingPos (float list): A list of three numbers representing the position in m of the element in the aircraft reference system (x, y, z).
        WingTilt (float list): A list of two numbers representing the rotation angle in deg of the element around the x, y axes (Rx, Ry).
        Panels (int, optional): TThe number of panels to use along the x-direction (chord). Default is 25.
    Returns:
        GeoElem (dict): A dictionary containing the geometric data of the element for the visualization.
        Element (dict): A dictionary containing the geometric data for the generation of the element in Flow5.
    '''

    if not isinstance(Name, str):
        raise TypeError("Name must be a string")
    if not isinstance(Type, str):
        raise TypeError("Type must be a string")
    if not isinstance(WingGeo, dict):
        raise TypeError("WingGeo must be a dictionary")
    if not isinstance(Airfoils, list):
        raise TypeError("Airfoils must be a list")
    if not isinstance(WingPos, list):
        raise TypeError("WingPos must be a list")
    if not isinstance(WingTilt, list):
        raise TypeError("WingTilt must be a list")
    if not isinstance(Panels, int):
        raise TypeError("Panels must be an integer")

    FullWing=WingGeo["FullWing"]
    SecData=WingGeo["SecData"]

    if not isinstance(FullWing, bool):
        raise TypeError("FullWing must be a boolean")
    if not isinstance(SecData, list):
        raise TypeError("SecData must be a list")

    Element={}

    if len(SecData)/5!=int(len(Airfoils)/2+1):
        raise ValueError("len(SecData) must be same of len(Airfoils)/2+1")
    
    sections=[]
    xn_p=Panels
    a=Airfoils[0]
    y=SecData[0]
    ny=SecData[5]
    c=SecData[1]
    nc=SecData[6]
    o=SecData[2]
    t=SecData[3]
    d=SecData[4]
    y_dist="TANH"
    yn_p=ceil((ny-y)/(c+nc)*xn_p)+3
    if yn_p>150:
        yn_p=150
    sections.append({"y":round(y,3),"c":round(c,3),"o":round(o,3),"d":round(d,3),"t":round(t,3),"xp_num":xn_p,
        "yp_num":yn_p,"yp_dis":y_dist,"left_s":a,"right_s":a})

    for i in range(1,int(len(Airfoils)/2)):
        a1=Airfoils[i*2-1]
        a2=Airfoils[i*2]
        y=SecData[i*5]
        ny=SecData[(i+1)*5]
        c=SecData[1+i*5]
        nc=SecData[1+(i+1)*5]
        o=SecData[2+i*5]
        t=SecData[3+i*5]
        d=SecData[4+i*5]
        y_dist="TANH"
        yn_p=ceil((ny-y)/(c+nc)*xn_p+3)
        if yn_p>150:
            yn_p=150
        sections.append({"y":round(y,3),"c":round(c,3),"o":round(o,3),"d":round(d,3),"t":round(t,3),"xp_num":xn_p,
        "yp_num":1,"yp_dis":"UNIFORM","left_s":a1,"right_s":a1})
        sections.append({"y":round(y,3),"c":round(c,3),"o":round(o,3),"d":round(d,3),"t":round(t,3),"xp_num":xn_p,
        "yp_num":yn_p,"yp_dis":y_dist,"left_s":a2,"right_s":a2})

    a=Airfoils[-1]
    y=SecData[-5]
    c=SecData[-4]
    o=SecData[-3]
    t=SecData[-2]
    d=SecData[-1]
    sections.append({"y":round(y,3),"c":round(c,3),"o":round(o,3),"d":round(d,3),"t":round(t,3),"xp_num":xn_p,
        "yp_num":1,"yp_dis":"UNIFORM","left_s":a,"right_s":a})
    
    S,wingspan,MAC=_wingparams(SecData)

    Element={"name":Name,"type":Type,"full_wing":FullWing,"wing_pos":WingPos,"wing_tilt":WingTilt,"sections":sections,"ref_data":[S,wingspan,MAC]}

    GeoElem=deepcopy(Element)
    GeoElem.pop("ref_data")
    GeoElem.pop("sections")
    GeoElem["airfoils"]=Airfoils
    GeoElem["geo_data"]=_geo_element(SecData)

    return GeoElem, Element


def _update1_plane_xml(data,el,n_el,mass,BankAng):

    x=el['wing_pos'][0]
    y=el['wing_pos'][1]*np.cos(np.radians(BankAng))-el['wing_pos'][2]*np.sin(np.radians(BankAng))
    z=el['wing_pos'][1]*np.sin(np.radians(BankAng))+el['wing_pos'][2]*np.cos(np.radians(BankAng))
    rx=el['wing_tilt'][0]+BankAng
    ry=el['wing_tilt'][1]

    data.update({
        f"Plane/wing+{n_el}/Name":el["name"],
        f"Plane/wing+{n_el}/Type":el["type"],
        f"Plane/wing+{n_el}/Position":f"{x},{y},{z}",
        f"Plane/wing+{n_el}/Tip_Strips":"1",
        f"Plane/wing+{n_el}/Rx_angle":str(rx),
        f"Plane/wing+{n_el}/Ry_angle":str(ry),
        f"Plane/wing+{n_el}/symmetric":"true",
        f"Plane/wing+{n_el}/Two_Sided":str(el['full_wing']),
        f"Plane/wing+{n_el}/Closed_Inner_Side":"false",
        f"Plane/wing+{n_el}/AutoInertia":"true",
        f"Plane/wing+{n_el}/Inertia/Mass":mass
    })

    airfoils=[]
    for i,s in enumerate(el['sections']):
        data.update({
            f"Plane/wing+{n_el}/Sections/Section+{i}/y_position":str(round(s['y'],3)),
            f"Plane/wing+{n_el}/Sections/Section+{i}/Chord":str(round(s['c'],3)),
            f"Plane/wing+{n_el}/Sections/Section+{i}/xOffset":str(round(s['o'],3)),
            f"Plane/wing+{n_el}/Sections/Section+{i}/Dihedral":str(round(s['d'],3)),
            f"Plane/wing+{n_el}/Sections/Section+{i}/Twist":str(round(s['t'],3)),
            f"Plane/wing+{n_el}/Sections/Section+{i}/x_number_of_panels":str(s['xp_num']),
            f"Plane/wing+{n_el}/Sections/Section+{i}/x_panel_distribution":"TANH",
            f"Plane/wing+{n_el}/Sections/Section+{i}/y_number_of_panels":str(s['yp_num']),
            f"Plane/wing+{n_el}/Sections/Section+{i}/y_panel_distribution":s['yp_dis'],
            f"Plane/wing+{n_el}/Sections/Section+{i}/Left_Side_FoilName":f"{s['left_s']}",
            f"Plane/wing+{n_el}/Sections/Section+{i}/Right_Side_FoilName":f"{s['right_s']}"
        })
        airfoils.extend([s['left_s'],s['right_s']])
    return data,airfoils


def _update2_plane_xml(data,pl_inertia):
    for i,pl in enumerate(pl_inertia):
        data.update({
            f"Plane/Inertia/Point_Mass+{i}/Tag":pl["tag"],
            f"Plane/Inertia/Point_Mass+{i}/Mass":str(pl["mass"]),
            f"Plane/Inertia/Point_Mass+{i}/coordinates":f"{pl['coord'][0]},{pl['coord'][1]},{pl['coord'][2]}"
        })
    return data


def _update_case_xml(CASE_XML,airfoils_dict):
    data={}
    for i,af in enumerate(airfoils_dict):
        airfoil_path=af["dat"]
        xflr5_polar_path=af["plr"]

        data.update({
            f"Plane_Analysis/Foil_Dat_Files/Foil_File_Name+{i}":airfoil_path
        })
        if xflr5_polar_path!=None:
            data.update({
                f"Plane_Analysis/Foil_Polar_Files/Polar_File_Name+{i}":xflr5_polar_path
            })
    _XML_writer(data,CASE_XML)
    return


def _add_airfoils_files(airfoils,AirfoilsDir,PolarsDir,AIRFOILS_PATH,XFLR5_POLARS_PATH,XFOIL_POLARS_PATH):
    airfoils_dict=[]
    unique_airfoils=set(airfoils)

    raw_txt_list=_get_files(PolarsDir,"txt")
    txt_data={af:[] for af in unique_airfoils}
    for txt in raw_txt_list:
        name=txt["name"].split(".")[0].split("_")[0]
        if name in unique_airfoils:
            txt_data[name].append(txt["path"])

    for af in unique_airfoils:
        in_dat=join(AirfoilsDir,f"{af}.dat")
        in_plr=join(PolarsDir,f"{af}.plr")

        out_dat=None
        out_plr=None
        
        if not isfile(in_dat):
            raise FileNotFoundError(f"Airfoil .dat file not found: {in_dat}")
        else:
            out_dat=join(AIRFOILS_PATH,f"{af}.dat")
            copy(in_dat,out_dat)

        if not isfile(in_plr) and len(txt_data[af])==0:
            raise FileNotFoundError(f"Polar file not found for airfoil {af}: expected {in_plr} or .txt files with name starting with '{af}_' in {PolarsDir}. Airfoil names must not contain underscores.")
        elif isfile(in_plr):
            out_plr=join(XFLR5_POLARS_PATH,f"{af}.plr")
            copy(in_plr,out_plr)
        
        if len(txt_data[af])>0:
            for in_txt in txt_data[af]:
                out_txt=join(XFOIL_POLARS_PATH,basename(in_txt))
                copy(in_txt,out_txt)
        
        airfoils_dict.append({"dat":out_dat,"plr":out_plr})

    return airfoils_dict


def _planeparams(Element,TotRefS):
    S=0
    wingspan=0
    MAC=0
    for el in Element:
        if el["type"]=="MAINWING":
            S+=el["ref_data"][0]
            wingspan=el["ref_data"][1]
            MAC=el["ref_data"][2]
        elif el["type"]=="OTHERWING" and TotRefS:
            S+=el["ref_data"][0]
    return S,wingspan,MAC


def flow5_plane(CaseRes:dict, Name:str, MassRes:list, Elements:list, AirfoilsDir:str, PolarsDir:str, BankAng:float=0, TotRefS:bool=True, Gate:bool=True)->dict:
    '''Creates an XML file for the definition of an aircraft in Flow5.
    Args:
        CaseRes (dict): The dictionary returned by flow5_case.
        Name (str): The name of the aircraft.
        MassRes (dict list): A list of dictionaries with the mass data for each element of the aircraft. Each dictionary must contain: 
                        -the keys "coord" (a list of three numbers for the coordinates x, y, z in m), "mass" (the mass in kg)
                            and "tag" (a name to identify the mass point);
                        -if the key "coord" is the name of the element, the key "mass" is its mass in kg (automatically distributed over the entire element by flow5) and there is no key "tag".
        Elements (dict list): A list of dictionaries with the geometric data for each element of the aircraft obtained through flow5_element.
        AirfoilsDir (string): The path of the folder containing the airfoils .dat files.
        PolarsDir (string): The path of the folder containing the polars .plr or .txt files.
        BankAng (float, optional): The bank angle in deg to apply to the entire aircraft (positive is clockwise rotation around the x-axis). Default is 0 deg.
        TotRefS (bool, optional): If True, considers the total surface area of the aircraft as reference for the analyses (include OTHERWING elements). Default is False.
        Gate (bool, optional): If False no file/folder is modified or created. Default is True.
    Returns:
        PlaneRes (dict): A dictionary with the data related to the aircraft.
    '''

    if not isinstance(CaseRes, dict):
        raise TypeError("CaseRes must be a dictionary")
    if not isinstance(Name, str):
        raise TypeError("Name must be a string")
    if not isinstance(MassRes, list):
        raise TypeError("MassRes must be a list")
    if not isinstance(Elements, list):
        raise TypeError("Element must be a list")
    if not isinstance(AirfoilsDir, str):
        raise TypeError("AirfoilsDir must be a string")
    if not isinstance(PolarsDir, str):
        raise TypeError("PolarsDir must be a string")
    if not isinstance(BankAng, (int, float)):
        raise TypeError("BankAng must be a number")
    if not isinstance(TotRefS, bool):
        raise TypeError("TotRefS must be a boolean")
    if not isinstance(Gate, bool):
        raise TypeError("Gate must be a boolean")
    
    for mr in MassRes:
        if not isinstance(mr, dict):
            raise TypeError("All items in MassRes must be dictionaries")

    PLANE_XML=join(CaseRes["planes_path"],f"{Name}.xml")
    CASE_XML=join(CaseRes["case_path"],"case.xml")
    AIRFOILS_PATH=CaseRes["airfoils_path"]
    XFLR5_POLARS_PATH=CaseRes["xflr5_polars"]
    XFOIL_POLARS_PATH=CaseRes["xfoil_polars"]

    airfoils=[]
    el_inertia=[]
    pl_inertia=[]

    for i in MassRes:
        if isinstance(i["coord"], list):
            pl_inertia.append(i)
        else:
            el_inertia.append(i)

    data={"Plane/Name": Name}
    for k,el in enumerate(Elements):
        mass="0"
        for i in el_inertia:
            if i["coord"]==el["name"]:
                mass=i["mass"]
        data,a=_update1_plane_xml(data,el,k,mass,BankAng)
        airfoils.extend(a)

    airfoils_dict=_add_airfoils_files(airfoils,AirfoilsDir,PolarsDir,AIRFOILS_PATH,XFLR5_POLARS_PATH,XFOIL_POLARS_PATH)
    S,wingspan,MAC=_planeparams(Elements,TotRefS)

    PlaneRes=deepcopy(CaseRes)
    PlaneRes.update({"plane":Name,"ref_data":[round(S,3),round(wingspan,3),round(MAC,3)],"bank_angle":BankAng})

    _update_case_xml(CASE_XML,airfoils_dict)

    if Gate:
        if len(pl_inertia)!=0:
            data=_update2_plane_xml(data,pl_inertia)
        _XML_writer(data,PLANE_XML,"Plane")
    return PlaneRes


def _update_case(g,CASE_XML,T12Range,T3Range,T5Range,T8Range):
    plane=join(g[0]["planes_path"],g[0]["plane"])
    data={
        "Plane_Analysis/Plane_Definition_Files/Process_All_Files":"false",
        "Plane_Analysis/Plane_Definition_Files/Plane_File_Name":f"{plane}.xml",
        "Plane_Analysis/Plane_Analysis_Files/Process_All_Files":"false",
        "Plane_Analysis/Plane_Analysis_Data/T12_Range":','.join(f'{n:.2f}' for n in T12Range),
        "Plane_Analysis/Plane_Analysis_Data/T3_Range":','.join(f'{n:.2f}' for n in T3Range),
        "Plane_Analysis/Plane_Analysis_Data/T5_Range":','.join(f'{n:.2f}' for n in T5Range),
        "Plane_Analysis/Plane_Analysis_Data/T8_Range":','.join(f'{n:.2f}' for n in T8Range)
    }

    for i,a in enumerate(g):
        anal=join(g[0]["analysis_path"],a["analysis"])
        data.update({f"Plane_Analysis/Plane_Analysis_Files/Analysis_File_Name+{i}":f"{anal}.xml"})

    _XML_writer(data,CASE_XML)
    return


def _store(folder,source,STORED):
    makedirs(STORED, exist_ok=True)
    destination = join(STORED, folder)
    if isdir(source):
        copytree(source, destination)
    return 0


def _delete(RESULTS):
    for folder in listdir(RESULTS):
        folder_path = join(RESULTS, folder)
        if isdir(folder_path):
            rmtree(folder_path)
    return 0


def _criteria(data):
    groups=[]
    index=[]
    for i in range(len(data)):
        d=data[i]
        if type(d)!=dict:
            continue
        else:
            b1=True
            for g,idx in zip(groups,index):
                b2=True
                for a in g:
                    if a["plane"]!=d["plane"]:
                        b2=False
                    else:
                        continue
                if b2:
                    g.append(d)
                    idx.append(i)
                    b1=False
                    break
            if b1==True:
                groups.append([d])
                index.append([i])
    return groups,index


def _angles_num(a):
    try:
        n=int(1+(a[1]-a[0])/a[2])
    except:
        n=0
    return n


def flow5_run(ExePath: str, AnalysisRes:list, T12Range:list=[0,0,0], T3Range:list=[0,0,0], T5Range:list=[0,0,0], T8Range:list=[0,0,0], Run:bool=True, Store:bool=False, Gate:bool=True)->list:
    '''Executes the analyses in Flow5.
    Args:
        ExePath (str): The path of the Flow5 executable.
        AnalysisRes (dict list): A list of dictionaries with the data for each analysis obtained through flow5_analysis.
        T12Range (float list, optional): A list of three numbers representing the range and step of the angle of attack in deg [min, max, step] for T1 and T2 analyses. Default is [0, 0, 0].
        T3Range (float list, optional): A list of three numbers representing the range and step of the angle of attack in deg [min, max, step] for T3 analyses. Default is [0, 0, 0].
        T5Range (float list, optional): A list of three numbers representing the range and step of the sideslip angle in deg [min, max, step] for T5 analyses. Default is [0, 0, 0].
        T8Range (float list, optional): A list of three numbers representing the angle of attack (deg), sideslip angle (deg) and speed (m/s) of the drone [AoA, Beta, Speed] for T8 analyses. Default is [0, 0, 0].
        Run (bool, optional): If True, executes the analyses. Default is True.
        Store (bool, optional): If True, stores the results in the "stored" folder. Default is False.
        Gate (bool, optional): If False no file/folder is modified or created and no analyses are executed. Default is True.
    Returns:
        RunRes (dict list): A list of dictionaries with the data related to the results of each analysis.
    '''

    if not isinstance(ExePath, str):
        raise TypeError("ExePath must be a string")
    if not isinstance(AnalysisRes, list):
        raise TypeError("AnalysisRes must be a list")
    if not isinstance(T12Range, list):
        raise TypeError("T12Range must be a list")
    if not isinstance(T3Range, list):
        raise TypeError("T3Range must be a list")
    if not isinstance(T5Range, list):
        raise TypeError("T5Range must be a list")
    if not isinstance(T8Range, list):
        raise TypeError("T8Range must be a list")
    if not isinstance(Run, bool):
        raise TypeError("Run must be a boolean")
    if not isinstance(Store, bool):
        raise TypeError("Store must be a boolean")
    if not isinstance(Gate, bool):
        raise TypeError("Gate must be a boolean")

    if not Gate:
        return print("Gate=False")
    CASE_XML=None
    STORED=None
    RESULTS=None
    for a in AnalysisRes:
        if type(a)==dict:
            STORED=a["stored_path"]
            RESULTS=a["results_path"]
            CASE_XML=a["case_xml"]
            break

    if CASE_XML is None or STORED is None or RESULTS is None:
        raise ValueError("CASE_XML, STORED and RESULTS must be defined in AnalysisRes")
    
    cmd=f'{ExePath} -p -s "{CASE_XML}"'
    
    groups,index=_criteria(AnalysisRes)
    if Run:
        _delete(RESULTS)
        for g in groups:
            _update_case(g,CASE_XML,T12Range,T3Range,T5Range,T8Range)
            si=subprocess.STARTUPINFO()
            si.dwFlags=subprocess.STARTF_USESHOWWINDOW
            si.wShowWindow=0#SW_HIDE
            CREATE_NO_WINDOW=0x08000000
            subprocess.run(cmd,creationflags=CREATE_NO_WINDOW,startupinfo=si)
    else:
        print("Run=False")
    try:
        folders=listdir(RESULTS)
        results_folder=[]
        for f in folders:
            results_folder.append(join(RESULTS, f))
        if Store:
            for f,p in zip(folders,results_folder):
                _store(f,p,STORED)

        RunRes = [None] * len(AnalysisRes)
        angles=[_angles_num(T12Range),_angles_num(T3Range),_angles_num(T5Range),1]
        
        for k,g in enumerate(groups):
            for g,i in zip(groups[k],index[k]):
                if AnalysisRes[i]["type"] in ["FIXEDSPEEDPOLAR","FIXEDLIFTPOLAR"]:
                    n=angles[0]
                elif AnalysisRes[i]["type"]=="GLIDEPOLAR":
                    n=angles[1]
                elif AnalysisRes[i]["type"]=="BETAPOLAR":
                    n=angles[2]
                elif AnalysisRes[i]["type"]=="T8POLAR":
                    n=angles[3]
                else:
                    n=0

                raw_results=deepcopy(AnalysisRes[i])
                raw_results.update({"results_folder":results_folder[k],"angles":n})
                RunRes[i]=raw_results
    except Exception as e:
        print(f"Error collecting results: {e}")
        RunRes=None

    return RunRes


def _get_data1(CSV_PATH,Data,angles):
    Results=[]
    Ident=[]
    Data1=[]
    Data2=[]
    if not exists(CSV_PATH):
        return Results,Ident,Data2
    
    file_data=[]
    with open(CSV_PATH,mode='r',encoding="utf8") as file:
        file_data=file.readlines()

    ns=np.inf
    for n,row in enumerate(file_data):
        r=row.split()
        if len(r)==0:
            continue
        elif r[0]=="Ctrl":
            ns=n
            break
    
    data_file=[row[:-1] for row in file_data[ns:] if len(row.split())>0]
    matrix=[row.split() for row in data_file]
    def clean_name(name):
        return re.sub(r'_\([^)]*\)$','',name)
    matrix[0]=[clean_name(x) for x in matrix[0]]
    matrix[0] = [item for item in matrix[0] if not (item.startswith('(') and item.endswith(')'))]
    matrix=list(map(list, zip(*matrix)))

    Ident=matrix[0:4]
    Ident=list(map(list, zip(*Ident)))
    Ident[0]=[i.lower() for i in Ident[0]]

    if angles>len(Ident)-1:
        print("Some results may be missing")

    for col in matrix:
        if col[0] in Data:
            Results.append(col)
            Data1.append(col[0])
    Data2=[d for d in Data if d not in Data1]
    Results=list(map(list, zip(*Results)))
    
    return Results,Ident,Data2


def _get_data2(Results,CSV_PATH,Data,Ident,Analysis):
    file_data=[]
    with open(CSV_PATH,mode='r',encoding="utf8") as file:
        file_data=file.readlines()

    ns=0
    ne=0
    for n,row in enumerate(file_data):
        r=row.split()
        if len(r)==0:
            continue
        elif r[0]==Analysis:
            ns=n+1
        elif r[0]=="Main" and n>ns:
            ne=n
            break
    
    data_file2=[row[:-1] for row in file_data[ns:ne] if len(row.split())>0]

    row2=[r.split() for r in data_file2]
    titles=[row2[i] for i in range(0,len(row2),2)]
    titles=list(itertools.chain.from_iterable(titles))
    def clean_name(name):
        return re.sub(r'\([^)]*\)$','',name)
    titles=[clean_name(x) for x in titles]
    titles=[item for item in titles if not (item.startswith('(') and item.endswith(')'))]
    titles[0:4]=[t.lower() for t in titles[0:4]]
    values=[row2[i] for i in range(1,len(row2),2)]
    values=list(itertools.chain.from_iterable(values))
    titles_ident=Ident[0]
    idx_ident=[titles_ident.index(t) for t in titles if t in titles_ident]

    Ident_temp=list(map(list, zip(*Ident)))
    Ident=[]
    for i in idx_ident:
        Ident.append(Ident_temp[i])
    Ident=list(map(list, zip(*Ident)))

    res_idx=np.nan
    for n,val in enumerate(Ident[1:]):
        if values[0:4]==val:
            res_idx=n+1
            break

    if np.isnan(res_idx):
        return Results
    
    for d in Data:
        if d in titles:
            title_idx=titles.index(d)
            Results[res_idx].append(values[title_idx])
            if d not in Results[0]:
                Results[0].append(d)

    return Results


def flow5_results(RunRes:dict, Data:list, OpPoints:bool=False)->tuple:
    '''Collects the results of the analyses in Flow5.
    Args:
        RunRes (dict): A dictionary with the data related to the results of an analysis executed by flow5_run.
        Data (str list): A list of names of data to collect. They must be present in the files containing the results obtained from Flow5 (without any parentheses that may contain the units).
        OpPoints (bool, optional): If True, also reads the results from the individual Operating Points files. Default is False. Flow5 7.55 is a bit bugged, for now is better to set it False.
    Returns:
        Results (str/float tuple): The results obtained from reading the analysis files (headers and values).
        Analysis (str): The name of the analysis.
    '''

    if not isinstance(RunRes, dict):
        raise TypeError("RunRes must be a dictionary")
    if not isinstance(Data, list):
        raise TypeError("Data must be a list")
    if not isinstance(OpPoints, bool):
        raise TypeError("OpPoints must be a boolean")
    

    angles=RunRes["angles"]
    Analysis=RunRes["analysis"]
    base_path=join(RunRes["results_folder"],RunRes["plane"],RunRes["analysis"])
    
    CSV1_PATH=join(base_path+".csv")
    Results,Ident,Data2=_get_data1(CSV1_PATH,Data,angles)

    if OpPoints:
        files=_get_files(base_path,("csv","txt"))
        for f in files:
            Results=_get_data2(Results,f["path"],Data2,Ident,RunRes["analysis"])
        
    for n,res in enumerate(Results[1:]):
        Results[n+1] = [float(x) for x in res]

    #Until Flow5 bank angle is not implemented in xml files
    if 'φ' in Results[0]:
        idx=Results[0].index('φ')
        for n,res in enumerate(Results[1:]):
            Results[n+1][idx]=RunRes["bank_angle"]
    
    return Results,Analysis
