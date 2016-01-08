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
    print fld.name
    if fld.name == "MinUplift" or fld.name == "MaxUplift":
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
msg("...adding uplift range field")          
rngFldName = "UpliftRange"
arcpy.AddField_management(upliftTable,rngFldName,"DOUBLE")

#Apply the calcStrings
msg("...calculating min likelihood")
arcpy.CalculateField_management(upliftTable,minFldName,minCalcStr,"PYTHON")
msg("...calculating max likelihood")
arcpy.CalculateField_management(upliftTable,maxFldName,maxCalcStr,"PYTHON")
msg("...calculating uplift range")
rangeCalcStr = "!{}! - !{}!".format(maxFldName,minFldName)
arcpy.CalculateField_management(upliftTable,rngFldName,rangeCalcStr,"PYTHON")

##Compute deciles on uplift values
#Get the field name of the average uplift values
avgFldName = "MeanUplift"

#Add the new field
msg("Computing uplift deciles on non zero scores")
msg("...adding uplift decile field")          
up2FldName = "UpRank2"
arcpy.AddField_management(upliftTable,up2FldName,"SHORT")

#Set the where clause
lowerBound = float("0") 
upperBound = float("0")
whereClause = "{0} < {1} OR {0} > {2}".format(avgFldName,lowerBound,upperBound)
selFC = arcpy.MakeFeatureLayer_management(upliftTable,"Lyr",whereClause)

#Get the number of records and determine the quantile size
numRecs = int(arcpy.GetCount_management(selFC).getOutput(0))
msg("...{} Records used".format(numRecs))
decileSize = numRecs / 10.0
#Set the counter variables
decile = 1              #Index of decile's upper limit
ceiling = decileSize    #Initial decile value
counter = 1             #Counter that increases with each record

#Create the update cursor, sorted on average uplift
records = arcpy.UpdateCursor(selFC,whereClause,"","{}; {}".format(avgFldName,up2FldName),"{} A".format(avgFldName))
rec = records.next()
while rec:
    #Check to see if we've entered a new decile, if so, increase the index
    if counter > ceiling:       #If the current rec passes the ceiling
        ceiling += decileSize   #...raise the ceiling
        decile += 1           #...up the decile value
    #Assign the quantile to the rank field
    rec.setValue(up2FldName,decile)
    records.updateRow(rec)
    #Move to the next record
    counter += 1
    rec = records.next()
#Finished
msg("Completed")
