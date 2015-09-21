# UPLIFT_AlterResponseVariableFld.py
#
# Description: Copies and modfies the response variables to represent a scenario of where
#  the selected field is changed by the provided change factor. For example, to increase
#  stream velocity to 90% of its current value, the user would input "V0001E" as the change
#  field and "0.90" as the factor. The output is then a new table with the modified value# 
#
# The revised table is then used as an input to the ModelUplift scripts.
#
# Sept 2015, John.Fay@duke.edu

# Import arcpy module
import sys, os, arcpy

#User variables
origRVTbl = arcpy.GetParameterAsText(0)     # Catchment variables under current conditions
changeFld = arcpy.GetParameterAsText(1)     # Field to change
changeFactor = arcpy.GetParameterAsText(2)  # Factor by which to change the field
upliftTbl = arcpy.GetParameterAsText(3)     # Revised catchment attribute table

#Set environments
arcpy.env.overwriteOutput = True

## FUNCTIONS
def msg(txt,type="message"):
    print txt
    if type == "message":
        arcpy.AddMessage(txt)
    elif type == "warning":
        arcpy.AddWarning(txt)
    elif type == "error":
        arcpy.AddError(txt)

## PROCESSES 
#Make a copy of the responseVariableTable
msg("Copying catchment current conditions table")
upliftTbl = arcpy.CopyRows_management(origRVTbl,upliftTbl)

#Alter the field by the factor
msg("Changing {} by a factor of {}".format(changeFld,changeFactor))
arcpy.CalculateField_management(upliftTbl,changeFld,"[{}] * {}".format(changeFld,changeFactor))



