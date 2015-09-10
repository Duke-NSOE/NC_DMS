# UPLIFT_UpdateNLCD.py
#
# Description: Updates the NLCD Columns in ResponseVars table

# Import arcpy module
import sys, os, arcpy

# Check out any necessary licenses
arcpy.CheckOutExtension("spatial")

#User variables
respvarsFC = arcpy.GetParameterAsText(0)     # Copy of the response vars table *THIS WILL BE MODIFIED*
nlcdRaster = arcpy.GetParameterAsText(1)     # NLCD raster datasets (original or modified)
catchmentRaster = arcpy.GetParameterAsText(2)# Catchment raster, used to compute catchment stats

#Set environments
arcpy.env.overwriteOutput = True

# Get paths
rootWS = os.path.dirname(sys.path[0])
dataWS = os.path.join(rootWS,"Data")

# Local variables:
rvLyr = "RespVarsLyr"

# ---Functions---
def msg(txt,type="message"):
    print txt
    if type == "message":
        arcpy.AddMessage(txt)
    elif type == "warning":
        arcpy.AddWarning(txt)
    elif type == "error":
        arcpy.AddError(txt)

## PROCESSES
# Make NLCD level 1 dataset (e.g. classes 21, 22, 23, 24 become class "2")
msg("...Making level 1 NLCD raster dataset")
NLCD1_raster = arcpy.sa.Int(arcpy.Raster(nlcdRaster) / 10)

# Tabulate areas of each class within the catchments
msg("...Tabulating NLCD areas in each catchment")
nlcdStats = arcpy.sa.TabulateArea(catchmentRaster,"VALUE",NLCD1_raster,"VALUE","in_memory/statsTbl")

# Make a table view of the respVarsFC to enable joins
msg("...creating table view of response variables")
rvLyr = arcpy.MakeTableView_management(respvarsFC,rvLyr)

# Join updateTbl to layer
msg("...joining tables")
rvJoin = arcpy.AddJoin_management(rvLyr,"GRIDCODE",nlcdStats,"VALUE")

# Loop through the update fields
for fld in arcpy.ListFields(nlcdStats)[2:]:
    toFld = fld.name
    fromFld = toFld.replace("VALUE_","NLCD")
    msg("...updating {}".format(fromFld))
    
    # Get the update and calc field names
    updateFld = os.path.basename(respvarsFC) + "." + fromFld
    valueFld = "statsTbl." + toFld

    # Check that the update field actually exists
    if arcpy.ListFields(rvLyr,updateFld) == []:
        msg("{} field does not exist; skipping","warning")
        continue

    # Update the values
    arcpy.CalculateField_management(rvLyr,updateFld,"[{}] / 1000".format(valueFld))

#Return the merged table
arcpy.SetParameterAsText(3,respvarsFC)
