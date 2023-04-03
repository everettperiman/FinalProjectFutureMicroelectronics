# ==============================================================================================
# ==============================================================================================
# ==============================================================================================
#
# Copyright (c) 2017, Coventor, Inc. All rights reserved.
#
# This file contains sample code which demonstrates how to read raw voxel data from a
# Coventor .vdata file.
# ==============================================================================================
# ==============================================================================================
# ==============================================================================================

import xml.etree.ElementTree
import os
import sys
import zlib
import base64
import struct
import socket

import numpy as np
from vdataOp import *
                        
from customPython import CustomPythonFunction

'''
A custom python step to export voxel data to a CSV file.
'''
class ProcessVDATA(CustomPythonFunction):

    def __init__(self, modeler, layerMap):
        CustomPythonFunction.__init__(self, modeler, layerMap)

    def Run(self, inVars, saveParams, isRestart):
        if isRestart:
            return

        # Default Parameters
        doc = self.modeler.GetDocument()
        modelerObj = self.modeler
        stepNum = saveParams.stepNum
        stepName = saveParams.stepName
        sequence = saveParams.GetParentSequence()
        stepComments = saveParams.comments

        # User-input parameters
        inputVdataFile = inVars.GetVar('Input VData')  # Input vdata
        matToReplace = inVars.GetVar('Replace Material')  
        replacementMaterial = inVars.GetVar('Replacement Material')          
        oputputVdataFile = inVars.GetVar('Output VData')  # Output vdata
        
        vdataOp = VDataOp(inputVdataFile, oputputVdataFile)
        vdataOp.workFunction()
        print("Done with running ProcessVDATA")            
        
    
