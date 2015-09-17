# UPLIFT_CalculateUplift.py
#
# Description: Computes the difference between habitat likelihood under current and uplift
#  scenarios. Identifies the catchments in the top 10%.
#
#  Prior to running this script,
#
# Pseudo-code:
#  - Locates Maxent output files
#  - 
#
# Sept 2015, John.Fay@duke.edu

# Import arcpy module
import sys, os, arcpy

# Check out any necessary licenses
arcpy.CheckOutExtension("spatial")

#User variables
speciesName = arcpy.GetParameterAsText(0)
scenarioName = arcpy.GetParameterAsText(1)   # Prefix used to identify outputs
statsFolder = arcpy.GetParameterAsText(2)    # Stats root folder containing all species models
speciesFC = arcpy.GetParameterAsText(3)      # Input catchment feature class; used to display output values 
HUCFilter = arcpy.GetParameterAsText(4)      # HUC filter

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
        msg("{} not found.\nExiting.".format(fileName),"error")
        sys.exit(1)
    else: return
    
##---DERIVED INPUTS---
#Get the species stats folder in the stats root folder
msg("...Locating the species folder")
sppFolder = os.path.join(statsFolder,speciesName)
checkFile(sppFolder)

#Get the scenario folder holding all the Maxent run results
msg("...Locating the scenario folder")
scenarioFolder = os.path.join(sppFolder,"{}_Output".format(scenarioName))
checkFile(scenarioFolder)

#Get the GRIDCODE.asc file (scenario folder); this is an ordered listing of gridcodes use to match output to catchments
msg("...Locating GRIDCODE.asc file")
gridcodeASC = os.path.join(scenarioFolder,"GRIDCODE.asc")
checkFile(gridcodeASC)

#Get the current conditions (scenario folder); this is the baseline from which uplift is calculated
msg("...Locating the current conditions output for HUC {}".format(HUCFilter))
currentASC = os.path.join(sppFolder,"XX_Output","{}_XX_Output.asc".format(speciesName))
checkFile(currentASC)

#Get the ASCII file containing the projected likelihood
msg("...Locating the projected conditions output for HUC {}".format(HUCFilter))
projectedASC = os.path.join(scenarioFolder,"{}_{}_Output.asc".format(speciesName,scenarioName))
checkFile(projectedASC)

#Set output parameters
outCSV = os.path.join(scenarioFolder,"{}_Uplift.csv".format(scenarioName))
outFC = os.path.join(scenarioFolder,"{}_Uplift.shp".format(scenarioName))
arcpy.SetParameterAsText(5,outFC)

##---PROCESSES----
# Read in GRIDCODE values from the gridcode ASCII file
file = open(gridcodeASC,'r')
gridcodes = file.readlines()[6:] #skip the first 6 lines (header info)
file.close()

# Read in the current condition projections
file = open(currentASC,'r')
currentPredictions = file.readlines()[6:] #skip the first 6 lines (header info)
file.close()

# Read in the modified condition projections
file = open(projectedASC,'r')
upliftPredictions = file.readlines()[6:] #skip the first 6 lines (header info)
file.close()

# Set the projected likelihood field name
prjFldName = "Proj_{}".format(scenarioName)

# Write the files to an output csv file
outFile = open(outCSV,'w')
outFile.write("GRIDCODE,Current,{}\n".format(prjFldName))
for i in range(len(gridcodes)):
    gridcode = int(gridcodes[i])
    currentLikelihood = float(currentPredictions[i])
    upliftLikelihood = float(upliftPredictions[i])
    outFile.write("{},{},{}\n".format(gridcode,currentLikelihood,upliftLikelihood))

# Make a table from the CSV to enable joining
tmpTbl = arcpy.CopyRows_management(outCSV,"in_memory/tmpTbl")

#Make a feature layer of the catchment features (to trim fields)
msg("Initializing the output catchment feature class")
msg("...Selecting columns")
fldInfo = arcpy.FieldInfo()
for f in arcpy.ListFields(speciesFC):
    fName = f.name
    if fName in ("OBJECTID","Shape","GRIDCODE","REACHCODE",speciesName):
        fldInfo.addField(fName,fName,"VISIBLE","")
    else:
        fldInfo.addField(fName,fName,"HIDDEN","")
catchLyr = arcpy.MakeFeatureLayer_management(speciesFC,"catchLyr","","",fldInfo)

# Select records from the Species Occurrence feature class
msg("...Writing to temp feature class")
whereClause = "REACHCODE LIKE '{}%'".format(HUCFilter)
tmpFC = arcpy.Select_analysis(catchLyr,outFC,whereClause)

# Join the CSV to the catchment FC
msg("Joining uplift data to catchment FC")
fldNames = ["Current",prjFldName]
arcpy.JoinField_management(tmpFC,"GRIDCODE",tmpTbl,"GRIDCODE","Current;{}".format(prjFldName))

# Add the uplift field
upliftFldName= "Uplift_{}".format(scenarioName)
msg("Adding the uplift field")
arcpy.AddField_management(tmpFC,upliftFldName,"DOUBLE")

# Calculate uplift
msg("Calculating uplift")
arcpy.CalculateField_management(tmpFC,upliftFldName,"[{}] - [Current]".format(prjFldName))

# Save the file
msg("Saving the output")
#arcpy.CopyFeatures_management(tmpFC,outFC)
