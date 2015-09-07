# HABMODEL_CreateMaxentBatchFile.py
#
# Creates a batch file (.bat) used to run MaxEnt with the supplied files. The way
#  this script is configured, the workspace must contain a MaxEnt folder (containing
#  the MaxEnt.jar file) in the project's root folder. 
#
# Inputs include:
#  (1) the MaxEnt samples with data format (SWD) CSV file, 
#  (2) a list of field names to exclude by default in the analysis
#  (3) a list of fields that should be set to categorical
#  (4) a folder containing projection ASCII files
#
#  Model outputs will be sent to the Outputs folder in the MaxEnt directory.They include
#   the "runmaxent.bat" batch file and a final list of variables included in the analysis. 
#
# Spring 2015
# John.Fay@duke.edu

import sys, os, arcpy

# Input variables
swdFile = arcpy.GetParameterAsText(0)           # MaxEnt SWD formatted CSV file
excludeFlds = arcpy.GetParameterAsText(1)       # Fields to toggle off by default

# Derived variables
## Maxent batch file
maxentFile = os.path.join(os.path.dirname(swdFile),"RunMaxent.bat")
arcpy.SetParameterAsText(2,maxentFile)
## Variables file
variablesFile = os.path.join(os.path.dirname(swdFile),"VariablesUsed.txt")
arcpy.SetParameterAsText(3,variablesFile)

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
# Check that the maxent.jar file exists in the scripts folder
maxentJarFile = os.path.dirname(sys.argv[0])+"\\maxent.jar"
if not os.path.exists(maxentJarFile):
    msg("Maxent.jar file cannot be found in Scripts folder.\nExiting.","error")
    sys.exit(0)
else:
    msg("Maxent.jar found in Scripts folder".format(maxentJarFile))

# Check that the output folder exists; create it if not
outDir = os.path.abspath(os.path.dirname(swdFile)+"\\Output")
if not(os.path.exists(outDir)):
    msg("Creating output directory")
    os.mkdir(outDir)
else: msg("Setting output to {}".format(outDir))

# Begin creating the batch run string with boilerplate stuff
msg("Initializing the Maxent batch command")
runString = "java -mx2048m -jar {}".format(maxentJarFile)

# set samples file
msg("...Setting samples file to \n    {}".format(swdFile))
runString += " samplesfile={}".format(swdFile)

# set enviroment layers file
msg("...Setting enviroment layers file to \n    {}".format(swdFile))
runString += " environmentallayers={}".format(swdFile)
    
# set output directory
msg("...Setting output directory to {}\n    ".format(outDir))
runString += " outputdirectory={}".format(outDir)

# enable response curves
msg("...Enabling response curves")
runString += " responsecurves=false"

# enable jackknifing
msg("...Enabling jackknifing")
runString += " jackknife=false"

# disable pictures
msg("...Disabling drawing pictures")
runString += " pictures=false"

# Set nodata value 
msg("...Setting NoData value to -9999")
runString += " nodata=9999"

# enable 4 threads to speed processing
msg("...Running Maxent on 4 processors")
runString += " threads=8"

# setting to autorun
msg("...Disabling drawing pictures")
runString += " autorun=true"

# turn off background spp
msg('...Toggling "background" species')
runString += " togglespeciesselected=background"

# toggle off all species in excludeFields
## Create list from excludeFields input
excludeItems = excludeFlds.split(";")
## Remove species, X, and Y columns from list, if included
if ("Species") in excludeItems: excludeItems.remove("Species")
if ("X") in excludeItems: excludeItems.remove("X")
if ("Y") in excludeItems: excludeItems.remove("Y")

## Loop through list; if header item not in include list, toggle it off
for excludeItem in excludeItems: 
    msg("...disabling <{}>".format(excludeItem))
    runString += " togglelayerselected={}".format(excludeItem)
            
# Set stream order and FCODE to categorical fields (if not excluded)
for catItem in ("StreamOrde","FCODE"):
    if not (catItem in excludeItems):
        msg("...Setting <{}> to categorical".format(catItem))
        runString += " togglelayertype={}".format(catItem)

# Write commands to batch file
msg("Writing commands to batchfile {}".format(maxentFile))
outFile = open(maxentFile,'w')
outFile.write(runString)
outFile.close()

# Write variables to variables file
msg("Writing final variables list to {}".format(variablesFile))
outFile = open(variablesFile,'w')
for fld in arcpy.ListFields(swdFile):
    #if the field name is not in the exclude item, write it to the list
    if not (fld.name in (excludeItems) or fld.name in ("Species","X","Y")):
        msg("...adding <{}>".format(fld.name))
        outFile.write("{}\n".format(fld.name))
outFile.close()


    
