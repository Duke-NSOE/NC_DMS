# HABMODEL_CreateDataFile.py
#
# Description: Creates a CSV format table listing all the catchments in each HUC8 in which a
#   selected species is found. The table includes a column indicating whether the species was
#   observed in the catchment and all environment environment data. Any environment layer with
#   missing data is omitted completely. 
#
# The procedure first finds all the HUC8s in which the species occurs, then
#   extracts all the catchments within these HUC8s. Those catchments where the
#   species was observed (via Endries' data) are tagged with 1, others with 0.bit_length
#   Environment variables with missing data are eliminated. 
#
# Spring 2015
# John.Fay@duke.edu

import sys, os, csv, arcpy, datetime
arcpy.env.overwriteOutput = 1

# Input variables
speciesTbl = arcpy.GetParameterAsText(0)    # Table of all ENDRIES surveyed catchments with a binary column for each species presence...
speciesName = arcpy.GetParameterAsText(1)   # Species to model; this should be a field in the above table
envVarsTbl = arcpy.GetParameterAsText(2)    # Table listing all the catchment attributes to be used as environment layer values
statsFolder = arcpy.GetParameterAsText(3) #Root folder to hold all species model stuff and into which a species subfolder will be created

# Script variables
sppOnlyTbl = "in_memory/sppOnlyTbl"
freqTbl = "in_memory/FreqTbl"
resultsCopyTbl = "in_memory/Results2"
counter = 0
##
## ---Functions---
def msg(txt,type="message"):
    print txt
    if type == "message":
        arcpy.AddMessage(txt)
    elif type == "warning":
        arcpy.AddWarning(txt)
    elif type == "error":
        arcpy.AddError(txt)
##
## ---Processes---
# Create the species data folder, 
outFolder = os.path.join(statsFolder,speciesName)
                         
# Create the output folder, if not present
if os.path.exists(outFolder):
    if arcpy.env.overwriteOutput == True:
        msg("...Using existing output folder.")
    else:
        msg("Output exists and overwrite disabled.\nExiting","error")
        sys.exit(1)
else:
    msg("...{} does not exist, creating it".format(outFolder))
    os.mkdir(outFolder)
    
# Set the output folder as a model output parameter    
arcpy.SetParameterAsText(5,outFolder) #Output Folder

# Set the output species and log filenames
speciesCSV = os.path.join(outFolder,"AllHUC8Records.csv")
logFilename = speciesCSV[:-4]+"_metadata.txt"

# Get the current time and initialize the log file
now = datetime.datetime.now()
logFile = open(logFilename,'w')
logFile.write("File created at {}:{} on {}/{}/{}\n".format(now.hour,now.minute,now.month,now.day,now.year))

# Extract Catchments with species
msg("...Pulling catchment records for {}".format(speciesName))
arcpy.TableSelect_analysis(speciesTbl, sppOnlyTbl,'"{}" = 1'.format(speciesName))
msg("{} records extracted".format(arcpy.GetCount_management(sppOnlyTbl)))

# Make a list of HUC8s
msg("...Making a list of HUCs in which {} was observed".format(speciesName))
HUC6s = []
HUC8s = []
for rec in arcpy.da.SearchCursor(sppOnlyTbl,("REACHCODE")):
    HUC8 = str(rec[0][:8])
    if not HUC8 in HUC8s:
        HUC8s.append(HUC8)
    HUC6 = str(rec[0][:6])
    if not HUC6 in HUC6s:
        HUC6s.append(HUC6)
msg("{} was found in {} HUC6s and {} HUC8s".format(speciesName,len(HUC6s),len(HUC8s)),"warning")

# Set a filename to save info on the species (list of HUC8s and HUC6s)
logFile.write("{} was found in {} HUC6s and {} HUC8s\n".format(speciesName,len(HUC6s),len(HUC8s)))
logFile.write("HUC8s:\n")
for HUC8 in HUC8s:
    logFile.write("\t{}\n".format(HUC8))


#Select data rows in the response variables that are within the specified HUC8s
# Create a where clause from the HUC8s
msg("...Creating the query string to extract records")
whereClause = ""
for HUC8 in HUC8s:
    whereClause += "REACHCODE LIKE '{}%' OR ".format(HUC8)
# Trim of the last "OR "
whereClause = whereClause[:-3]

# Select the records...
# Make a copy of the environment variable table and join the species table to it
msg("...Creating temporary table of the response variables")
arcpy.TableSelect_analysis(envVarsTbl,resultsCopyTbl,whereClause)

# Join the species data to the results table so that the records where the species
# is present can be isolated. 
msg("...Joining species presence values to environment variables")
arcpy.JoinField_management(resultsCopyTbl,"GRIDCODE",sppOnlyTbl,"GRIDCODE",["{}".format(speciesName)])

# Create a list of field names: remove non-numeric fields and extranneous fields
outFldList = []
for fld in arcpy.ListFields(resultsCopyTbl):
    if fld.type not in ("OID","String") and not fld.name in (speciesName):
        outFldList.append(fld.name)

# Filter the field list: remove fields with null values
fldList = []
for fld in outFldList[2:]: #Skip the first two fields (GRIDCODE and REACHCODE)
    #Create the SQL filter
    sql = "{} IN (-9998.0,-9999)".format(fld)
    #Select records
    tmpTbl = arcpy.TableSelect_analysis(resultsCopyTbl,"in_memory/tmpSelect",sql)
    #See if any records are selected
    if int(arcpy.GetCount_management(tmpTbl).getOutput(0)) == 0:
        fldList.append(fld)
    else:
        msg("   Field <<{}>> has null values and will be removed".format(fld),"warning")
        logFile.write("Field <<{}>> has null values and will be removed\n".format(fld))

# Insert GRIDCODE and REACHCODE
fldList.insert(0,"REACHCODE")
fldList.insert(0,"GRIDCODE")
if "Shape_Length" in fldList: fldList.remove("Shape_Length")
if "Shape_Area" in fldList: fldList.remove("Shape_Area")

## WRITE THE SPECIES RECORDS TO THE FILE ##
msg("...Creating the output species file")
# Initialize the species output csv file & create the writer object
msg("...Initializing the output CSV files")
csvFile = open(speciesCSV,'wb')
writer = csv.writer(csvFile)

# Write header row to CSV file
msg("...Writing headers to CSV file")
writer.writerow(["Species"] + fldList)

# Create a search cursor for the resultsTbl
msg("...Writing presence values to CSV file")
whereClause = '"{}" = 1'.format(speciesName)
# Create a cursor including all but the first and last fields (species names)
cursor = arcpy.da.SearchCursor(resultsCopyTbl,fldList,whereClause) #<- the 1: skips the first & last field
for row in cursor:
    #write the species name + all the row data
    writer.writerow([1] + list(row))
    counter += 1
msg("{} presence records written to file".format(counter))
logFile.write("{} presence records written to file\n".format(counter))
counter = 0

# Create a search cursor for the resultsTbl
msg("...Writing background values to CSV file")
whereClause = '"{}" IS Null'.format(speciesName)
cursor = arcpy.da.SearchCursor(resultsCopyTbl,fldList,whereClause)
for row in cursor:
    #write the species name + all the row data
    writer.writerow([0] + list(row))
    counter +=1
msg("{} absence records writted to file".format(counter))
logFile.write("{} absence records writted to file\n".format(counter))

# Close file and clean up
logFile.close()
csvFile.close()

# Set the output parameters
arcpy.SetParameterAsText(4,speciesCSV)                 #Output CSV 
