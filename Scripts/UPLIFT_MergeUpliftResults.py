# UPLIFT_MergeUpliftResults.py
#
# Description:
#  Merges uplift tables for multiple species into a single table
#
# Summer 2015
# John.Fay@duke.edu

import sys, os, arcpy, csv, tempfile
arcpy.env.overwriteOutput = 1

# Input variables
scenarioPrefix = arcpy.GetParameterAsText(0) #Prefix used to represent scenarion (e.g. BU for buffer)
scenarioFldr = arcpy.GetParameterAsText(1)   #Folder containing Maxent outputs
catchmentsFC = arcpy.GetParameterAsText(2)   #Catchments feature class to which results are joined

# Output variables
outCSV = arcpy.GetParameterAsText(3)         #Output feature class for the species

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
#Get a list of scenario uplift files
arcpy.env.workspace = scenarioFldr
meFiles = arcpy.ListFiles("*{}_maxent.csv".format(scenarioPrefix)) #Maxent results

# Make a copy of the master variables table
msg("...internalizing variables")
varTbl = arcpy.CopyRows_management(catchmentsFC,"in_memory/vars")

# Initialize outFields list - list of fields to write out; start with GRIDCODE
outFields = ["GRIDCODE"]

# Loop through each CSV and join it to the copy
msg("...looping through uplift files")
for meFile in meFiles:

    #Extract the species name
    sppName = meFile[7:-14]
    #Split the name into genus and species, then shorten it to 1st letter of genus and 1st 5 of spp
    genus, species = sppName.split("_")
    sppName = genus[0]+"_"+species[:5]

    #--MAXENT--
    msg("      processing {} (Maxent)".format(sppName))
    #Make a local copy (for joining)
    sppTbl = arcpy.CopyRows_management(meFile, "in_memory/spp")
    #Join the maxent fields
    arcpy.JoinField_management(varTbl,"GRIDCODE",sppTbl,"GRIDCODE","{0};{0}_uplift".format(scenarioPrefix))
    #Rename the joined fields
    arcpy.AlterField_management(varTbl,"{0}".format(scenarioPrefix),"{0}_LogProb".format(sppName))
    arcpy.AlterField_management(varTbl,"{0}_uplift".format(scenarioPrefix),"{0}_Uplift".format(sppName))
    #Add fields to output field list
    outFields.append("{0}_LogProb".format(sppName))
    outFields.append("{0}_Uplift".format(sppName))

# Initialize the output CSV file
msg("...initializing output CSV")
f = open(outCSV,'wb')
writer = csv.writer(f)

# Write the header items
writer.writerow(["GRIDCODE","mean_Uplift"]+outFields[1:])

# Loop thru records and write the data to the CSV file
msg("...writing data to CSV")
cur = arcpy.da.SearchCursor(varTbl,outFields)
for row in cur:
    #Get the gridcode
    gridcode = row[0]
    
    #Replace null values with zeros
    outValues = []
    for val in row:
        if not val: outValues.append(0)
        else: outValues.append(val)
        
    #Initialize running sum variables
    LogProbSum = 0
    UpliftSum = 0
    counter = 0

    #Calculate running sums by looping through columns, set step to 2 as two columns are written
    for ColIdx in range(1,len(outValues),2):
        #Running sums of LogProb values, Uplift values, and a counter to calc averages
        LogProbSum += float(outValues[ColIdx])
        UpliftSum += float(outValues[ColIdx + 1]) #index offest = 1  
        counter += 1
                              
    #Calculate averages from the sums
    LogProbAvg = ME_LogProbSum / counter
    UpliftAvg = ME_UpliftSum / counter

    #Write values to CSV
    writer.writerow([gridcode,UpliftAvg]+outValues[1:])
    
f.close()
