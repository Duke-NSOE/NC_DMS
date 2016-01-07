# UPLIFT_CalcUpliftMinMax.py
#
# Description:
#  Appends columns to the merged uplift table that lists the most negative (min)
#  and most positive species uplift values.
#
#  The input tables must be in the format that the UPLIFT_MergeUpliftResults.py
#  generates, i.e., with all species uplift fields ending with "_up"
#
# Jan 2016
# John.Fay@duke.edu

import sys, os, arcpy, csv, tempfile
arcpy.env.overwriteOutput = 1

# Input variables
upliftTable = arcpy.GetParameterAsText(0)

## ---Functions---
def msg(txt,type="message"):
    print txt
    if type == "message":
        arcpy.AddMessage(txt)
    elif type == "warning":
        arcpy.AddWarning(txt)
    elif type == "error":
        arcpy.AddError(txt)
        
def checkFile(fileName):
    if not os.path.exists(fileName):
        msg("{} not found.\nExiting.".format(fileName),"error")
        sys.exit(1)
    else: return
    
#Create list of spp uplift fields. Also, check whether the fields already exist; exit if so
upliftFlds = []
for fld in arcpy.ListFields(upliftTable):
    if fld.name == "minUplift" or fld.name == "maxUplift":
        msg("{} already exists for this table. Exiting".format(fld.name),"error")
        sys.exit(0)
    elif fld.name[-3:] == "_up":
        upliftFlds.append(fld.name)

#Create calc strings
minCalcStr = "min("
maxCalcStr = "max("
for fld in upliftFlds:
    minCalcStr += "!{}!,".format(fld)
    maxCalcStr += "!{}!,".format(fld)
minCalcStr = minCalcStr[:-1] + ")"
maxCalcStr = maxCalcStr[:-1] + ")"

#Add min & max uplift fields
msg("...adding min uplift field")          
minFldName = "MinUplift"
arcpy.AddField_management(upliftTable,minFldName,"DOUBLE")
msg("...adding max uplift field")          
maxFldName = "MaxUplift"
arcpy.AddField_management(upliftTable,maxFldName,"DOUBLE")

#Apply the calcStrings
msg("...calculating min likelihood")
arcpy.CalculateField_management(upliftTable,minFldName,minCalcStr,"PYTHON")
msg("...calculating max likelihood")
arcpy.CalculateField_management(upliftTable,maxFldName,maxCalcStr,"PYTHON")

#Finished
msg("Completed")
