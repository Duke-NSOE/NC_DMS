# MISC_aggregate_to_HUC12.py
#
# Description:
#  Upscales catchment data to the HUC12 using area weighted means. The input feature
#  class must have a REACHCODE field and and shape_area field. 
#
# Fall 2015
# John.Fay@duke.edu

import sys, os, arcpy, csv, tempfile
arcpy.env.overwriteOutput = 1

# Input variables
inputFC = arcpy.GetParameterAsText(0)       #Feature class to upscale
upscaleFlds = arcpy.GetParameterAsText(1)   #Fields to upscale
outputFC = arcpy.GetParameterAsText(2)     #Output HUC12 feature class

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
#Copy the feature class to a temp copy
msg("Creating temp feature class")
tmpFC = arcpy.CopyFeatures_management(inputFC,"in_memory/tmpFC1")

#Add a HUC 12 field
msg("...adding HUC12 field")
arcpy.AddField_management(tmpFC,"HUC12","DOUBLE")

#Calculate HUC12 from ReachCode
msg("...calculating HUC12 from REACHCODE")
arcpy.CalculateField_management(tmpFC,"HUC12","!REACHCODE![:12]","PYTHON")

#Initilize the Dissolve field list
fldList = []

#Loop through fields

for fldName in upscaleFlds.split(";"):
    msg("...calculating wtd value for {}".format(fldName))

    #Create the wtd field
    fldName12 = "{}12".format(fldName)
    arcpy.AddField_management(tmpFC,fldName12,"DOUBLE")
    arcpy.CalculateField_management(tmpFC,fldName12,"!shape.area! * !{}!".format(fldName),"PYTHON")

    #Build the stats field list for the Dissolve commmand
    fldList.append((fldName12,"SUM"))

#Dissolve on HUC12
msg("Dissolving data on HUC12")
tmpFC2 = arcpy.Dissolve_management(tmpFC,"in_memory/tmpFC2","HUC12",fldList)

#Recalculate fields
for fldName in upscaleFlds.split(";"):
    #Rename the field
    arcpy.AlterField_management(tmpFC2,"SUM_{}12".format(fldName),fldName,fldName)
    #Revert area wtd values to just values
    arcpy.CalculateField_management(tmpFC2,fldName,"!{}! / !shape.area!".format(fldName),"PYTHON")

    #Save the output
    arcpy.CopyFeatures_management(tmpFC2,outputFC)
