# UPLIFT_CalculateUplift.py
#
# Description: Computes the difference between habitat likelihood under current and uplift
#  scenarios. Identifies the catchments in the top 10%. 

# Import arcpy module
import sys, os, arcpy

# Check out any necessary licenses
arcpy.CheckOutExtension("spatial")

#User variables
speciesName = arcpy.GetParameterAsText(0)
scenarioName = arcpy.GetParameterAsText(1)   # Prefix used to identify outputs
statsFolder = arcpy.GetParameterAsText(2)    # Stats root folder containing all species models

#Set environments
arcpy.env.overwriteOutput = True

# Local variables:
rvLyr = "RespVarsLyr"

##---Functions---
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
        msg("{} not found.\Exiting.".format(fileName),"error")
        sys.exit(1)
    else: return
    
##---DERIVED INPUTS---
msg("...Locating the species folder")
sppFolder = os.path.join(statsFolder,speciesName)
checkFile(sppFolder)

msg("...Locating the scenario folder")
scenarioFolder = os.path.join(sppFolder,"{}_Output".format(scenarioName))
checkFile(scenarioFolder)

msg("...Locating the current conditions output")
currentCSV = os.path.join(scenarioFolder,"{}.csv".format(speciesName))
checkFile(currentCSV)

msg("...Locating GRIDCODE.asc file")
gridcodeASCII = os.path.join(scenarioFolder,"GRIDCODE.asc")
checkFile(gridcodeASCII)

msg("...Locating the projected conditions output")
projectedCSV = os.path.join(scenarioFolder,"{}_{}_Output.asc".format(speciesName,scenarioName))
checkFile(projectedCSV)

msg("...Locating results feature class")
catchmentFC = os.path.join(sppFolder,"ME_output.shp")
checkFile(catchmentFC)
arcpy.SetParameterAsText(3,catchmentFC)

#Set output parameters
outCSV = os.path.join(scenarioFolder,"{}_Uplift.csv".format(scenarioName))


##---PROCESSES----
# Read in GRIDCODE values from the gridcode ASCII file
file = open(gridcodeASCII,'r')
gridcodes = file.readlines()[6:] #skip the first 6 lines (header info)
file.close()

# Read in prediction values from the prediction ASCII file
file = open(projectedCSV,'r')
predictions = file.readlines()[6:] #skip the first 6 lines (header info)
file.close()

# Set the name of the field holding the projected habitat likelihood
fldName = "Pred__{}".format(scenarioName)

# Write the two to an output csv file
outFile = open(outCSV,'w')
outFile.write("GRIDCODE,{}\n".format(fldName))
for i in range(len(gridcodes)):
    gridcode = int(gridcodes[i])
    prediction = float(predictions[i])
    outFile.write("{},{}\n".format(gridcode,prediction))

# Make a table from the CSV to enable joining
tmpTbl = arcpy.CopyRows_management(outCSV,"in_memory/tmpTbl")

# Add a new field to the catchment FC, if not there already
if len(arcpy.ListFields(catchmentFC,fldName)) > 0:
    msg("Removing existing {} field in catchment feature class".format(fldName))
    #arcpy.AddField_management(catchmentFC,fldName,"DOUBLE")
    arcpy.DeleteField_management(catchmentFC,fldName)

# Join the CSV to the catchment FC
msg("Joining uplift data to catchment FC")
arcpy.JoinField_management(catchmentFC,"GRIDCODE",tmpTbl,"GRIDCODE",[fldName])

# Add the uplift field
upliftFldName= "Uplift_{}".format(scenarioName)
if len(arcpy.ListFields(catchmentFC,upliftFldName)) > 0:
    msg("Removing existing {} field in catchment feature class".format(fldName))
    arcpy.DeleteField_management(catchmentFC,upliftFldName)
msg("Adding the uplift field name")
arcpy.AddField_management(catchmentFC,upliftFldName,"DOUBLE")

# Calculate uplift
msg("Calculating uplift")
arcpy.CalculateField_management(catchmentFC,upliftFldName,"[{}] - [Likelihood]".format(fldName))

