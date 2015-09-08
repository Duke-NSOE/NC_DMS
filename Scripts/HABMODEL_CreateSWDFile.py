# HABMODEL_CreateSWDFile.py
#
# Description: Creates a MaxEnt input CSV file in SWD (species with data) format. Includes a
#  column listing the species/background along with columns for all the env vars. Records produced
#  are limited to only catchments with recorded presences from any species in Endries' data.
#
# Spring 2015
# John.Fay@duke.edu

import sys, os, arcpy, csv
arcpy.env.overwriteOutput = True

# Input variables
speciesTbl = arcpy.GetParameterAsText(0)   # SH_Correlations.csv file
speciesName = arcpy.GetParameterAsText(1) # SpeciesOccurrences table
resultsTbl = arcpy.GetParameterAsText(2)   # <species_name>_RedundantVars.html file
stats_folder = arcpy.GetParameterAsText(3) # ResponseVars table

## ---Functions---
def msg(txt,type="message"):
    print txt
    if type == "message":
        arcpy.AddMessage(txt)
    elif type == "warning":
        arcpy.AddWarning(txt)
    elif type == "error":
        arcpy.AddError(txt)

## ---SET SCRIPT VARIABLES---
# Set the species folder 
msg("Locating species stats folder in root folder")
sppFolder = os.path.join(stats_folder,speciesName)
if not os.path.exists(sppFolder):
    msg("Species folder not found at {}".format(sppFolder),"error")
    sys.exit(1)
# Set the SHCorrelations.csv file
msg("Locating species-habitat correlations file in species folder")
varFilterCSV = os.path.join(sppFolder,"SH_Correlations.csv")
if not os.path.exists(varFilterCSV):
    msg("SHCorrelations.csv file not found","error")
    sys.exit(1)
# Set the RedundantVariables html file
msg("Locating redundant variables file in species folder")
varFilterHTML = os.path.join(sppFolder,"{}_RedundantVars.html".format(speciesName))
if not os.path.exists(varFilterHTML):
    msg("{}_RedundantVars.html file not found".format(speciesName),"error")
    sys.exit(1)

# Output variable (derived)
swdCSV = os.path.join(sppFolder,"{}_SWD.csv".format(speciesName))
arcpy.SetParameterAsText(4,swdCSV) #Output SWD format CSV file to create

# temp varables
sppOnlyTbl = "in_memory/SppTble"
resultsCopyTbl = "in_memory/Results2"
counter = 0

## ---Processes---
# Extract Catchments with species
msg("Pulling catchment records for {}".format(speciesName))
arcpy.TableSelect_analysis(speciesTbl, sppOnlyTbl,'"{}" = 1'.format(speciesName))

# Make a copy of the environment variable table and join the species table to it
msg("...Creating temporary table of the environment variables")
#arcpy.CopyRows_management(resultsTbl,resultsCopyTbl)
arcpy.TableSelect_analysis(resultsTbl,resultsCopyTbl,"LENGTHKM > 0")

# Remove uncorrelated fields
f = open(varFilterCSV,'rt')
keepList = ["OBJECTID","GRIDCODE","FEATUREID"]
for row in csv.reader(f):
    keepList.append(row[0])
f.close()
fldList = arcpy.ListFields(resultsCopyTbl)
for fld in fldList:
    if not fld.name in keepList:
        msg("   Removing <{}> (not correlated with presence)".format(fld.name))
        arcpy.DeleteField_management(resultsCopyTbl,fld.name)

# Remove redundant fields
f = open(varFilterHTML, 'rt')       #open the file
lineString = f.readline()           #get the info
f.close()                           #close the file
lineItems = lineString.split("<br>")[1:-1]
fldList = arcpy.ListFields(resultsCopyTbl)
for fld in fldList:
    if fld.name in lineItems:
        msg("   Removing <{}> (redundant)".format(fld.name))
        arcpy.DeleteField_management(resultsCopyTbl,fld.name)
        

# Join the species data to the results table so that the records where the species
# is present can be isolated. 
msg("...Joining species presence values to environment variables")
arcpy.JoinField_management(resultsCopyTbl,"GRIDCODE",sppOnlyTbl,"GRIDCODE","{}".format(speciesName))

# Create a list of field names
msg("Generating a list of environment variables for processing") 
fldList = [] #[speciesName] #start the list with the MaxEnt format: {species name, x, y}
for fld in arcpy.ListFields(resultsCopyTbl):
    fldList.append(str(fld.name))

## WRITE THE SPECIES RECORDS TO THE FILE ##
msg("Initializing the output species file...")
# Initialize the species output csv file & create the writer object
msg("...Initializing the output CSV files")
csvFile = open(swdCSV,'wb')
writer = csv.writer(csvFile)

# Write header row to CSV file
msg("...Writing headers to CSV file")
writer.writerow(["Species","X","Y"] + fldList[3:-1]) #<- the 3: is to skip the first three columns in the fldList

# Create a search cursor for the resultsTbl
msg("...Writing presence values to CSV file")
whereClause = '"{}" = 1'.format(speciesName)
# Create a cursor including all but the first and last fields (species names)
cursor = arcpy.da.SearchCursor(resultsCopyTbl,fldList[1:-1],whereClause) #<- the 1: skips the first & last field
for row in cursor:
    #write the species name + all the row data
    writer.writerow([speciesName] + list(row))
    counter += 1
msg("{} presence records writted to file".format(counter))
counter = 0

# Create a search cursor for the resultsTbl
msg("...Writing background values to CSV file")
whereClause = '"{}" IS Null'.format(speciesName)
cursor = arcpy.da.SearchCursor(resultsCopyTbl,fldList[1:-1],whereClause)
for row in cursor:
    #write the species name + all the row data
    writer.writerow(['background'] + list(row))
    counter +=1
msg("{} absence records writted to file".format(counter))

# Close file and clean up
csvFile.close()

msg("Finished")