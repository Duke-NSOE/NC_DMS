# HABSTATS_EditResponseVariableList.py
#
# Description: A check box interface to allow users to remove variables from analysis
#
# John Fay
# Fall 2015

# Import modules
import sys, os, arcpy

# Set path variables
scriptsDir = os.path.dirname(sys.argv[0])
rootDir = os.path.dirname(scriptsDir)
dataDir = os.path.join(rootDir,"Data")

# Script Inputs
shCorFile = arcpy.GetParameterAsText(0) #SH Correlation csv file
varList = arcpy.GetParameterAsText(1)   #List of variables 
outCSV = os.path.join(os.path.dirname(shCorFile),"IncludedVariables.csv")
arcpy.SetParameterAsText(2,outCSV) 

##---FUNCTIONS-----
# Messaging function
def msg(txt,type="message"):
    print txt
    if type == "message":
        arcpy.AddMessage(txt)
    elif type == "warning":
        arcpy.AddWarning(txt)
    elif type == "error":
        arcpy.AddError(txt)

       
##---PROCESSES----
#open the CSV
f = open(outCSV,'w')

vars = varList.split(";")
for var in vars:
    f.write("{}\n".format(var))
    msg("{}".format(var))

msg("Values saved to {}".format(outCSV))

f.close()