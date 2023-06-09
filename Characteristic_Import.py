# -*- coding: utf-8 -*-
"""
Created on Sat May 28 08:49:17 2022

@author: SSIMON
"""

import pandas as pd
import datetime
import sys
#import numpy
import os
import time
from tkinter import Tk
from tkinter import filedialog
import powerfactory as pf    
import math
app = pf.GetApplication()
app.ClearOutputWindow()
ldf = app.GetFromStudyCase("ComLdf")

##########################################################################################################################################################################
#############################################################################   PARAMETRI   ##############################################################################
##########################################################################################################################################################################
# Parametri za izračun jalovih moči za gen, load, vac..... načeloma če delamo DC loadflow ni važno
# Za AC loadflow je treba porihtat oz najt neke boljše načine dodeljevanja jalovih.
# spreminjaj_jalovo = False  # Ali skripta sploh spreminja parametre proizvodnje/porabe jalove moči. False - jalova enaka, True - jalovo spreminja
# izhodiscni_cosfi = True     # Ce je true, bo cosfi enak kot v izhodiscnem modelu, sicer vzame vrednosti definirane spodaj (razmerje med Q in P)

#Namesto cosfi se vnese razmerje PQ_ratio = tan(acos(cosfi(0.xx)))
#Pri cosfi 0.98 ~ 0.2
#Pri cosfi 0.97 ~ 0.25
#Pri cosfi 0.96 ~ 0.3
# generator_PQ_ratio = 0.25 #Delez jalove
# load_PQ_ratio = 0.25
# voltagesource_PQ_ratio = 0

#Izkoristek omrezja (izgube)
# izkoristek_omrezja = 0.97 #(1-izgube)

#Imena uvoženih datotek, glej da se sklada z tistim kar nardi skripta za pretvorbo excel->csv. Ne rabis spreminjati
stringParameters = "Parametri.xlsx"
stringMarketDataFile = "Market Data.csv"
stringBorderFlowFile = "Robna vozlisca P.csv"
stringBorderInfoFile = "Robna vozlisca Info.csv"
stringIzbranaPFile = "Izbrana vozlisca P.csv"
stringIzbranaQFile = "Izbrana vozlisca Q.csv"
stringIzbranaInfoFile = "Izbrana vozlisca Info.csv"

#   ['UKNI','UK00','UA02','UA01','TR00','TN00','SK00','SI00','SE04','SE03','SE02','SE01','SA00','RU00',
#   'RS00','RO00','PT00','PS00','PL00','NSW0','NOS0','NON1','NOM1','NL00','MT00','MK00','ME00','MD00',
#   'MA00','LY00','LV00','LUV1','LUG1','LUF1','LUB1','LT00','ITSI','ITSA','ITS1','ITN1','ITCS','ITCN',
#   'ITCA','IS00','IL00','IE00','HU00','HR00','GR03','GR00','FR15','FR00','FI00','ES00','ELES Interconnectios',
#   'EG00','EE00','DZ00','DKW1','DKKF','DEKF','DE00','CZ00','CY00','CH00','BG00','BE00','BA00','AT00','AL00']

#Drzave/sistemi, ki jim spreminjamo parametre. Vnesi tako kot je v market datoteki ali v powerfactory modelu
# sistemi_spreminjanje_parametrov = ['SI00','ITN1','HU00','HR00','ELES Interconnectios']

##########################################################################################################################################################################
#############################################################################   PARAMETRI   ##############################################################################
##########################################################################################################################################################################


start_time = datetime.datetime.now().time().strftime('%H:%M:%S')
app.PrintPlain("Pričetek izvajanja programa ob " + str(start_time) + ".")
# else: print("Pričetek izvajanja programa ob " + str(start_time) + ".")

# IMPORT PODATKOV
app.PrintPlain("Izberi mapo z vhodnimi podatki (lahko je v ozadju)!")
Tk().withdraw() # we don't want a full GUI, so keep the root window from appearing
f_input_data_directory = filedialog.askdirectory()
app.PrintPlain("Mapa izbrana!")
#Beri datoteke
app.PrintPlain("Uvoz market datoteke")
dfMD = pd.read_csv(os.path.join(f_input_data_directory, stringMarketDataFile), index_col = [0])
app.PrintPlain("Uvoz podatkov čezmejnih pretokov")
dfCbFlow = pd.read_csv(os.path.join(f_input_data_directory, stringBorderFlowFile), index_col = [0])
dfCbInfo = pd.read_csv(os.path.join(f_input_data_directory, stringBorderInfoFile), index_col = [0])
app.PrintPlain("Uvoz izbranih vozlisc")
dfIzbP = pd.read_csv(os.path.join(f_input_data_directory, stringIzbranaPFile), header = [0], index_col = [0])
dfIzbQ = pd.read_csv(os.path.join(f_input_data_directory, stringIzbranaQFile), header = [0], index_col = [0])
dfIzbInfo = pd.read_csv(os.path.join(f_input_data_directory, stringIzbranaInfoFile), header = [0])
app.PrintPlain("Datoteke uvozene")
# df_select_nodes_info = pd.read_csv(input_path_select_nodes_info, index_col = [1], header = [0])
# return dfMD, dfCbFlow, dfCbInfo, dfIzbP, dfIzbQ, dfIzbInfo 

dfParams = pd.read_excel(os.path.join(f_input_data_directory, stringParameters), sheet_name = 'Parametri', index_col = 0, header = 0)
dfGrids = pd.read_excel(os.path.join(f_input_data_directory, stringParameters), sheet_name = 'Drzave', index_col = 0, header = 0)

if dfParams.at['KONSTANTNA JALOVA', 'VREDNOST'] == 'DA':
    spreminjaj_jalovo = False
elif dfParams.at['KONSTANTNA JALOVA', 'VREDNOST'] == 'NE':
    spreminjaj_jalovo = True
else:
    spreminjaj_jalovo = False
    
if dfParams.at['IZHODISCNI COSFI', 'VREDNOST'] == 'DA':
    izhodiscni_cosfi = True
elif dfParams.at['IZHODISCNI COSFI', 'VREDNOST'] == 'NE':
    izhodiscni_cosfi = False
else:
    izhodiscni_cosfi = True

try: generator_PQ_ratio = math.tan(math.acos(dfParams.at['COSFI GENERATORJI', 'VREDNOST']))
except: generator_PQ_ratio = 0.2

try: load_PQ_ratio = math.tan(math.acos(dfParams.at['COSFI BREMENA', 'VREDNOST']))
except: load_PQ_ratio = 0.2

try: robna_PQ_ratio = math.tan(math.acos(dfParams.at['COSFI ROBNA', 'VREDNOST']))
except: robna_PQ_ratio = 0.2

try: izkoristek_omrezja = 1 - dfParams.at['IZGUBE OMREZJA', 'VREDNOST']
except: izkoristek_omrezja = 1

sistemi_spreminjanje_parametrov = []

for country in dfGrids.index.to_list():
    if dfGrids.at[country, 'MODIFIKACIJA PARAMETROV'] == 'DA':
        sistemi_spreminjanje_parametrov.append(country)
        
app.PrintPlain("DRZAVE KATERE MODIFICIRAMO:")
app.PrintPlain(sistemi_spreminjanje_parametrov)

app.PrintPlain("Racunanje koeficientov generatorjev")
#NAJDI VSA IZBRANA IN VSE GEN
gen_izbrana = []
gen_other = []
market_grid_type_list = dfMD.columns.tolist()
app.PrintPlain(market_grid_type_list)
izbrana_list = dfIzbInfo.columns.tolist()
dgen_grid_type = {}
for generator in app.GetCalcRelevantObjects("*.ElmSym"):
    generator_name = generator.loc_name
    generator_grid = generator.cpGrid.loc_name
    if generator_name in dfIzbQ:
        gen_izbrana.append(generator)
    elif generator_grid in sistemi_spreminjanje_parametrov:
        try:generator_type = str(''.join(generator.pBMU.desc))
        except:generator_type = str(''.join(generator.desc))
        generator_grid_type = generator_grid + "_" + generator_type
        if generator_grid_type in market_grid_type_list:
            gen_other.append(generator)
            dgen_grid_type[generator] = generator_grid_type    
#Get ratios SUM and then calc ratio
grid_type_sum = {}
for generator in gen_other:
    try: grid_type_sum[dgen_grid_type[generator]] += generator.pgini
    except: grid_type_sum[dgen_grid_type[generator]] = generator.pgini
#Now calc ratio 
gen_ratio = {}
gen_PQratio = {}
for generator in gen_other:
    try: gen_ratio[generator] = generator.pgini/grid_type_sum[dgen_grid_type[generator]]
    #Če je error bo 0 in nastavimo 0
    except: gen_ratio[generator] = 0
app.PrintPlain("Izracunani koeficienti generatorjev")
app.PrintPlain(gen_ratio)

app.PrintPlain("Racunanje koeficientov bremen")
#NAJDI VSA IZBRANA IN VSE LOAD
load_izbrana = []
load_other = []
# market_grid_type_list = dfMD.columns.tolist() # ZE MAMO
# izbrana_list = dfIzbInfo.columns.tolist() # ZE MAMO
dload_grid_type = {}
for load in app.GetCalcRelevantObjects("*.ElmLod"):
    load_name = load.loc_name
    load_grid = load.cpGrid.loc_name
    if load_name in izbrana_list:
        load_izbrana.append(load)
    elif load_grid in sistemi_spreminjanje_parametrov:
        load_grid_type = load_grid + "_LOAD"
        if load_grid_type in market_grid_type_list:
            load_other.append(load)
            dload_grid_type[load] = load_grid_type
#Get ratios SUM and then calc ratio
# grid_type_sum = {} ze mamo od generatorjev, load je kot type grid_LOAD
for load in load_other:
    try: grid_type_sum[dload_grid_type[load]] += load.plini
    except: grid_type_sum[dload_grid_type[load]] = load.plini
#Now calc ratio 
load_ratio = {}
load_PQratio = {}
for load in load_other:
    try: load_ratio[load] = load.plini/grid_type_sum[dload_grid_type[load]]
    #Če je error bo 0 in nastavimo 0
    except: load_ratio[load] = 0
    try: load_PQratio[load] = load.qlini/load.plini
    except: load_PQratio[load] = 0
app.PrintPlain("Izracunani koeficientov bremen")
app.PrintPlain(load_ratio)

voltagesource_list = dfCbInfo.index.to_list()
robna_list = []
robna_PQratio = {}
for voltagesource in app.GetCalcRelevantObjects("*.ElmVac"):
    voltagesource_name = voltagesource.loc_name
    voltagesource_grid = voltagesource.cpGrid.loc_name
    if voltagesource_name in voltagesource_list and voltagesource_grid in sistemi_spreminjanje_parametrov:
        robna_list.append(voltagesource)
        robna_PQratio[voltagesource] = voltagesource.Qgen/voltagesource.Pgen
app.PrintPlain("Robna vozlisca:")
app.PrintPlain(voltagesource_list)
app.PrintPlain(robna_list)
        
#Uredi podatke, odstej izbrana od market
global df_checking
df_checking = pd.DataFrame()
global df_izbrana_grid_type_sum
global dfMarketSlo
dfMarketSlo = dfMD.filter(regex='SI00')
df_izbrana_grid_type_sum = pd.DataFrame()
df_checking["Market SUM"] = dfMarketSlo["SI00_sum"]

#suma izbranih voslisc po tipu energenta
for izb_voz in dfIzbP.columns:
    # dfIzbInfo.drop(labels = 'Unnamed: 0', axis = 1, inplace = True)
    izb_grid_type = dfIzbInfo.at[0,izb_voz]
    try:
        df_izbrana_grid_type_sum[izb_grid_type] = df_izbrana_grid_type_sum[izb_grid_type] + dfIzbP[izb_voz]
    except:
        df_izbrana_grid_type_sum[izb_grid_type] = dfIzbP[izb_voz]
        
#Mam df sume izbranih vozlisc
#Se kompletno
app.PrintPlain("obdelava podatkov")
cols_to_sum = [col for col in df_izbrana_grid_type_sum.columns if "LOAD" not in col]
df_izbrana_grid_type_sum["SI00_sum"] = df_izbrana_grid_type_sum.apply(lambda row: row[cols_to_sum].sum(), axis=1)
df_checking["Izbrana SUM"] = df_izbrana_grid_type_sum["SI00_sum"]

delta = dfMarketSlo.sub(df_izbrana_grid_type_sum, fill_value = 0)
list_type_ignore = ["28","29","44","45"]
for column in delta.columns.to_list():
    if not any(type_ignore in column for type_ignore in list_type_ignore):
        delta[column] = delta[column].clip(lower = 0)
        
prefixes = {col[:4] for col in delta.columns}
for prefix in prefixes:
    cols_to_sum = [col for col in delta.columns if col.startswith(prefix) and "sum" not in col and "LOAD" not in col and "Balance" not in col and "Dump" not in col and "DSR" not in col]
    delta["SI00_NEWmarketsum"] = delta.apply(lambda row: row[cols_to_sum].sum(), axis=1)

df_checking["Market-IzbranaSUM"] = delta["SI00_NEWmarketsum"]
df_checking["New Mark+Izb SUM"] = df_checking["Market-IzbranaSUM"] + df_checking["Izbrana SUM"]
df_checking["New DELTA"] = df_checking["New Mark+Izb SUM"] - df_checking["Market SUM"]

for column in dfMD.columns.to_list():
    if column in delta:
        dfMD[column] = delta[column]
        # app.PrintPlain(f"Subtracted {column} in delta from market")
    
    # replace_negatives = lambda x: 0 if x < 0 and x.name != 'SI00_29' else x
    # delta = delta.apply(replace_negatives)
    # delta = delta.applymap(lambda x: 0 if x < 0 and "28" not in x.name and "29" not in x.name and "44" not in x.name and "45" not in x.name else x)
    # dfMarketData = dfMarketData - df_izbrana_grid_type_sum
    
    # dfMarketData[] = df.apply(lambda row: row[[col for col in df.columns if col.startswith('C')]].sum(),

####################################################  UVOZ V POWERFACTORY  ##############################################################################
    
app.PrintPlain("Izdelava karakteristik in uvoz podatkov v powerfactory")
#Make time scale for a year in libry folder
fLibrary = app.GetProjectFolder("lib") #Get library folder
timescale_name = "Time Scale"
timescale = fLibrary.SearchObject(timescale_name)
if not timescale:
    try:
        app.PrintPlain("No timescale named " + timescale_name + " exists, creating")
        fLibrary.CreateObject("TriTime", timescale_name)
        timescale = fLibrary.GetContents(timescale_name + ".TriTime")[0]
        app.PrintPlain("Made " + timescale_name + " vector!")
    except:
        app.PrintWarn("Problem creating timescale")
if timescale:
    app.PrintPlain("Timescale vector " + timescale_name + " exists!")
    timescale.SetAttribute("unit", 3)
    timescale_vector = list(range(1,8761))
    timescale.SetAttribute("scale", timescale_vector)
    app.PrintPlain("Edited " + timescale_name + " vector!")
      
#Se za gen
for generator in gen_izbrana:
    generator_name = generator.GetAttribute("loc_name")
    try:
        #Assign P vector
        for chaOld in generator.GetContents("pgini*.ChaVec"): chaOld.Delete() 
        chaPgini = generator.CreateObject("ChaVec", "pgini")
        chaPgini.SetAttribute("scale", timescale)
        chaPgini.SetAttribute("vector", dfIzbP[generator_name].to_list())
        chaPgini.SetAttribute("usage", 2)
        app.PrintPlain(f"Created and assigned {chaPgini} for {generator}")
    except: app.PrintPlain(f"Error creating char P for {generator}")
    try:
        #Assign Q vector
        for chaOld in generator.GetContents("qgini*.ChaVec"): chaOld.Delete() 
        chaQgini = generator.CreateObject("ChaVec", "qgini")
        chaQgini.SetAttribute("scale", timescale)
        chaQgini.SetAttribute("vector", dfIzbQ[generator_name].to_list())
        chaQgini.SetAttribute("usage", 2)
        app.PrintPlain(f"Created and assigned {chaQgini} for {generator}")
    except: app.PrintPlain(f"Error creating char Q for {generator}")
    
for generator in gen_other:
    try:
        #Assign P vector
        for chaOld in generator.GetContents("pgini*.ChaVec"): chaOld.Delete() 
        chaPgini = generator.CreateObject("ChaVec", "pgini")
        chaPgini.SetAttribute("scale", timescale)
        p_vector = [val * gen_ratio[generator] for val in dfMD[dgen_grid_type[generator]].to_list()]
        chaPgini.SetAttribute("vector", p_vector)
        chaPgini.SetAttribute("usage", 2)
        app.PrintPlain(f"Created and assigned {chaPgini} for {generator}")
    except: app.PrintPlain(f"Error creating char P for {generator}")
    if spreminjaj_jalovo:
        try:
            #Assign Q vector
            for chaOld in generator.GetContents("qgini*.ChaVec"): chaOld.Delete() 
            if izhodiscni_cosfi: 
                q_vector = [val * gen_PQratio[generator] for val in p_vector]
            else: #Cosfi iz parametrov
                q_vector = [val * generator_PQ_ratio for val in p_vector]
            chaQgini = generator.CreateObject("ChaVec", "qgini")
            chaQgini.SetAttribute("scale", timescale)
            chaQgini.SetAttribute("vector", q_vector)
            chaQgini.SetAttribute("usage", 2)
            app.PrintPlain(f"Created and assigned {chaQgini} for {generator}")
        except: app.PrintPlain(f"Error creating char Q for {generator}")
    
for load in load_izbrana:
    load_name = load.GetAttribute("loc_name")
    try:
        #Assign P vector
        for chaOld in load.GetContents("plini*.ChaVec"): chaOld.Delete() 
        chaPlini = load.CreateObject("ChaVec", "plini")
        chaPlini.SetAttribute("scale", timescale)
        chaPlini.SetAttribute("vector", dfIzbP[load_name].to_list())
        chaPlini.SetAttribute("usage", 2)
        app.PrintPlain(f"Created and assigned {chaPlini} for {load}")
    except: app.PrintPlain(f"Error creating char P for {load}")
    try:
        #Assign Q vector
        for chaOld in load.GetContents("qlini*.ChaVec"): chaOld.Delete() 
        chaQlini = load.CreateObject("ChaVec", "qlini")
        chaQlini.SetAttribute("scale", timescale)
        chaQlini.SetAttribute("vector", dfIzbQ[load_name].to_list())
        chaQlini.SetAttribute("usage", 2)
        app.PrintPlain(f"Created and assigned {chaQlini} for {load}")
    except: app.PrintPlain(f"Error creating char Q for {load}")
    
for load in load_other:
    load_name = load.GetAttribute("loc_name")
    try:
        #Assign P vector
        for chaOld in load.GetContents("plini*.ChaVec"): chaOld.Delete() 
        chaPlini = load.CreateObject("ChaVec", "plini")
        chaPlini.SetAttribute("scale", timescale)
        p_vector = [val * load_ratio[load] * izkoristek_omrezja for val in dfMD[dload_grid_type[load]].to_list()]
        chaPlini.SetAttribute("vector", p_vector)
        chaPlini.SetAttribute("usage", 2)
        app.PrintPlain(f"Created and assigned {chaPlini} for {load}")
    except: app.PrintPlain(f"Error creating char P for {load}")
    if spreminjaj_jalovo:
        try:
            # Assign Q vector
            # Remove old data
            for chaOld in load.GetContents("qlini*.ChaVec"): chaOld.Delete() 
            # Assign controller to load
            if izhodiscni_cosfi: 
                q_vector = [val * load_PQratio[load] for val in p_vector]
            else: #Cosfi iz parametrov
                q_vector = [val * load_PQ_ratio for val in p_vector]
            chaQlini = load.CreateObject("ChaVec", "qlini")
            chaQlini.SetAttribute("scale", timescale)
            chaQlini.SetAttribute("vector", q_vector)
            chaQlini.SetAttribute("usage", 2)
            app.PrintPlain(f"Created and assigned {chaQlini} for {load}")
        except: app.PrintPlain(f"Error creating char Q for {load}")
        
for voltagesource in robna_list:
    voltagesource_name = voltagesource.GetAttribute("loc_name")
    try:
        #Assign P vector
        for chaOld in voltagesource.GetContents("Pgen*.ChaVec"): chaOld.Delete() 
        chaPgen = voltagesource.CreateObject("ChaVec", "Pgen")
        chaPgen.SetAttribute("scale", timescale)
        p_vector = [val * dfCbInfo.at[voltagesource_name,'DELEZ'] * dfCbInfo.at[voltagesource_name,'POMNOZITI'] for  val in dfCbFlow[dfCbInfo.at[voltagesource_name,'MEJA']].to_list()]
        chaPgen.SetAttribute("vector", p_vector)
        chaPgen.SetAttribute("usage", 2)
        app.PrintPlain(f"Created and assigned {chaPgen} for {voltagesource}")
    except: app.PrintPlain(f"Error creating char P for {voltagesource}")
    if spreminjaj_jalovo:
        try:
            # Assign Q vector
            # Remove old data
            for chaOld in voltagesource.GetContents("Qgen*.ChaVec"): chaOld.Delete() 
            # Assign controller to load
            if izhodiscni_cosfi: 
                q_vector = [val * robna_PQratio[voltagesource] for val in p_vector]
            else: #Cosfi iz parametrov
                q_vector = [val * robna_PQ_ratio for val in p_vector]
            chaQlini = load.CreateObject("ChaVec", "qlini")
            chaQlini.SetAttribute("scale", timescale)
            chaQlini.SetAttribute("vector", q_vector)
            chaQlini.SetAttribute("usage", 2)
            app.PrintPlain(f"Created and assigned {chaQlini} for {load}")
        except: app.PrintPlain(f"Error creating char Q for {load}")

#################################################################################### MAIN #######################################################

#################### IZPIS URE #################

end_time = datetime.datetime.now().time().strftime('%H:%M:%S')
total_time=(datetime.datetime.strptime(end_time,'%H:%M:%S') - datetime.datetime.strptime(start_time,'%H:%M:%S'))
now = datetime.datetime.now()
current_time = now.strftime("%H:%M:%S")
app.PrintPlain("Konec izvajanja programa ob " + str(current_time) + ". Potreben čas: " + str(total_time) + '.')
