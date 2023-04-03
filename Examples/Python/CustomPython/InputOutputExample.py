#! python 
# -*- coding: utf-8 -*-
# Copyright (c) 2007-2018, Coventor, Inc. All rights reserved. 

from voxelModeler      import *

_SEMulator3D_API_VERSION = "6.0"

# This example script demonstrates how input parameters are passed 
# to a Python script that implements a Custom Python Step,
# and how output parameters are returned from the Custom Python script 
# to the main script and used in a subsequent Custom Python step.

# This step shows how to pass all possible variable types to 
# a custom Python script, and how to return all possible variable types
#
# 'isRestart' is a special parameter used only by 'restart' version - see ExampleStep1_restart(), below.
#

class ExampleStep1(CustomPythonFunction):

    def __init__(self, modeler, layerMap):
        CustomPythonFunction.__init__(self, modeler, layerMap)

    def Run(self, inVars, saveParams, isRestart):

        # isRestart is true if the function is being call before the restart point in an incremental rebuild, otherwise it's false.
        if isRestart:
            return;
			
        # This is the Voxel Document object for the process.
        doc = self.modeler.GetDocument()
	
        # This is the voxel modeling kernel object.
        modeler     = self.modeler
	
        # The step number for this step in the process.  This is a string, and may contain several 
        # nested sequence  numbers (ie, "3.27.9")
        stepNum     = saveParams.stepNum
	
        # The name of the step, assigned by the user in the process editor.
        stepName    = saveParams.stepName
	
        # The output sequence into which we should save.
        # This is often (but not always!) equal to doc.GetModel().
        # It may also be a child sequence if this step sits inside a sequence in the process editor.
        sequence    = saveParams.GetParentSequence()

        # The comments entered by the user in the "Comments" section of the Process-Editor custom-python interface.
        stepComments = saveParams.comments
		
        inWafer     = inVars.GetVar('InWafer', type = VoxelWafer)
        inMask      = inVars.GetVar('InMask', type = Mask)
        inMaterial  = inVars.GetVar('InMat', type = Material)
        maskName    = inVars.GetVar('MaskName', defaultValue="defaultMask", type=str)
        thickness   = inVars.GetVar('Thickness', defaultValue=10, type=float)
    
   
        # Print the input parameters for the benefit of this example
        print("\n  ---- Step %s Input Parameters ----" % (stepNum))  
        print("  InWafer:    ",inWafer)
        print("  InMask:     ",inMask.GetName())
        print("  InMaterial: ",inMaterial.GetName())
        print("  MaskName:   ",maskName)
        print("  Thickness:  ",thickness)
        print()
    
        # additional operations on any of the input parameters can be added here
        modelUnits  = doc.GetModelUnits()

        # create a square mask
        maskUnits = modeler.GetDefaultMaskUnitsPerMicron()
        newMask = Mask("maskName", maskUnits)
        vertices = ((0,0),(10,0),(10,10),(0,10),)
        newMask.AddPolygon(vertices, modelUnits)

        # add a new material to document.  We use AddOrUpdateMaterial() so that we are compatible with auto rebuild.
        newMat = doc.AddOrUpdateMaterial("Unobtainium", (255, 2, 200), CONDUCTOR)
 
        # create a rectangular wafer
        newWafer = VoxelWafer(modeler)
        props = CProcessData.ProcessProperties("WaferSetup")
        props.material=inMaterial.GetName()
        props.thickness=thickness
        newWafer.Initialize(props)
    
        # Print the output parameters for the benefit of this example    
        print("\n  ---- Step %s Output Parameters ----" % (stepNum))
        print("  OutputWafer:    ",newWafer)
        print("  OutputMask:     ",newMask.GetName())
        print("  OutputMaterial: ",newMat.GetName())
        print()

        # Any wafers that are modified or created in a Custom Python step should be saved.
        # In this case, a new wafer has been created and must be saved.
        if doc.IsOutputEnabled():
            newWafer.Save(saveParams)
        
        # Marshall the local variables that are to be returned to the calling script 
        # into the outVars object
        outVars = VarList()
        outVars.SetVar("OutputMask", newMask, type = Mask )
        outVars.SetVar("OutputWafer", newWafer, type = VoxelWafer)
        return outVars


# This step shows how variables that were returned from a preceding Custom Python step, 
# ExampleStep1, can be used in a subsequent Custom Python step.
class ExampleStep2(CustomPythonFunction):

    def __init__(self, modeler, layerMap):
        CustomPythonFunction.__init__(self, modeler, layerMap)

    def Run(self, inVars, saveParams, isRestart):

        if isRestart:
            return;

        inWafer     = inVars.GetVar("InputWafer", type = VoxelWafer)
        inMask      = inVars.GetVar("InputMask", type = Mask)
       
        
        stepNum     = saveParams.stepNum
		
        # Print the input parameters for the benefit of this example
        print("\n  ---- Step %s Input Parameters ----" % (stepNum))  
        print("  InputWafer:    ",inWafer)
        print("  InputMask:     ",inMask.GetName())
        print()