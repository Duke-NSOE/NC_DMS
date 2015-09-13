# UPLIFT_MergeUpliftResults.py
#
# Description:
#  Merges uplift FCs for multiple species into a single FC with average values
#
# Fall 2015
# John.Fay@duke.edu

import sys, os, arcpy, csv, tempfile
arcpy.env.overwriteOutput = 1

# Input variables
scenarioPrefix = arcpy.GetParameterAsText(0)  #Prefix used to represent scenarion (e.g. BU for buffer)
statsRootFldr = arcpy.GetParameterAsText(1)   #Folder containing all species stats results

# Script variables
resultsFC = "ME_output.shp"        # The name of the feature class contianing maxent results"
tmpOutput = "in_memory/tmpOutFC"    # FC name to hold temp output; this format allows alter field command

# Output variables
outFC = os.path.join(statsRootFldr,"{}_UpliftResults.shp".format(scenarioPrefix))
arcpy.SetParameterAsText(2,outFC)         #Output feature class for the species

## ---Functions---
def msg(txt,type="message"):
    print txt
    if type == "message":
        arcpy.AddMessage(txt)
    elif type == "warning":
        arcpy.AddWarning(txt)
    elif type == "error":
        arcpy.AddError(txt)

## ---Processes---
#Get a list of species output folders
msg("Getting list of species folders")
sppDirs = os.listdir(statsRootFldr)

#Initialize a list of uplift fields
upliftFlds = []

#Loop through the species folders and append the uplift columns to a master FC
for sppDir in sppDirs:
    #Truncate the species name to first letter of genus and 1st five letters of species
    genus,species = sppDir.split("_")
    sppName = genus[0].upper()+"_"+species[:7]

    msg("Processing {} as {}".format(sppDir,sppName))
    
    #Fields to modify
    fromFlds = ("PRED__{}".format(scenarioPrefix),"Uplift_{}".format(scenarioPrefix))
    toFlds = ("{}_{}_pred".format(scenarioPrefix,sppName),"{}_{}_up".format(scenarioPrefix,sppName))

    #Add the new uplift field to the list
    upliftFlds.append(toFlds[1])
    
    #Get the results fc
    sppFC = os.path.join(statsRootFldr,sppDir,resultsFC)

    if sppDir == sppDirs[0]:
        #If its the first folder, copy the  ME_output file to the temp outputFC
        msg("Initializing temporary output feature class")
        firstFC = os.path.join(sppDirs[0],sppFC)
        arcpy.CopyFeatures_management(firstFC,tmpOutput)

    else:
        #Otherwise, join the prediction and uplift fields of the ME_output file to the outputFC
        msg("...appending fields")
        arcpy.JoinField_management(tmpOutput,"GRIDCODE",sppFC,"GRIDCODE",fromFlds)

    #Rename last two fields to hold the species name
    for i in (0,1):
        fromFld = fromFlds[i]
        toFld = toFlds[i]
        arcpy.AlterField_management(tmpOutput,fromFld,toFld,toFld)

##Compute averge uplift across species
#Make a calculate string from the upliftFlds
msg("Calculating average uplift")
msg("...constructing the equation")
calcString = "("
for upliftFld in upliftFlds:
    calcString += "[{}] + ".format(upliftFld)

#Modify the string to calculate averages
calcString = calcString[:-3] + ") / {}".format(len(upliftFlds))

#Add a field to the output FC for average uplift
msg("...adding the average field")
avgFld = "{}_avgUplift".format(scenarioPrefix)
arcpy.AddField_management(tmpOutput,avgFld,"DOUBLE")

#Apply the calcString
msg("...calculating average uplift")
arcpy.CalculateField_management(tmpOutput,avgFld,calcString)

##Compute deciles
#Add decile field
msg("...adding the decile field")
decileFld = "{}_decile".format(scenarioPrefix)
arcpy.AddField_management(tmpOutput,decileFld,"LONG")

#Get the number of records and determine the quantile size
numRecs = int(arcpy.GetCount_management(tmpOutput).getOutput(0))
decileSize = numRecs / 10.0
#deciles = range(decileSize,numRecs+1,decileSize) #list of decile upper limits
decile = 1   #Index of decile's upper limit
ceiling = decileSize  #Initial decile value
counter = 1 #Counter that increases with each record

#Create the update cursor, sorted on average uplift
records = arcpy.UpdateCursor(tmpOutput,"","","{}; {}".format(avgFld,decileFld),"{} A".format(avgFld))
rec = records.next()
while rec:
    #Check to see if we've entered a new decile, if so, increase the index
    if counter > ceiling:       #If the current rec passes the ceiling
        ceiling += decileSize   #...raise the ceiling
        decile += 1           #...up the decile value
    #Assign the quantile to the decileFld
    rec.setValue(decileFld,decile)
    records.updateRow(rec)
    #Move to the next record
    counter += 1
    rec = records.next()
        

#Save results
arcpy.CopyFeatures_management(tmpOutput,outFC)