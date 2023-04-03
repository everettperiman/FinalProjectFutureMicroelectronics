#! python 
# -*- coding: utf-8 -*-
# Copyright (c) 2007-2018, Coventor, Inc. All rights reserved. 

from voxelModeler import *

_SEMulator3D_API_VERSION = "6.0"

# This example demonstrates how to write a new modeling operation in a custom python step.
# New modeling operations can be created from a sequence of fundamental modeling operations.
class modelingOperationExample(CustomPythonFunction):

    def __init__(self, modeler, layerMap):
        CustomPythonFunction.__init__(self, modeler, layerMap)

    def Run(self, inVars, saveParams, isRestart):
        
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
    
        # These are the user-defined parameters.
        inWafer     = inVars.GetVar("InputWafer", type = VoxelWafer)
        inMask      = inVars.GetVar("InputMask", type = Mask)
        inMaterial  = inVars.GetVar("InputMat", type = Material)
        inDepth     = inVars.GetVar("Depth", type = float)

        # If a custom python step performs several modeling operations, it may be useful to Save()
        # the modified wafer several times.
        # In order to save the wafer more than once, you must create a new sequence.
        newSequence = sequence.AddSequence(stepName,stepNum)
        
        # We have the 'saveParams' variable which is of the type OutputParams(seqName, stepName, stepNumber)
		# To save the wafer in the newSequence, create a new OutputParams(seqName, stepName, stepNumber) object.
		# Pass -1 as the stepNumber to append the wafer to the "newSequence" sequence.  		
        outParams = OutputParams(newSequence,"Initial wafer", -1)
		
        inWafer.Save(outParams)

        # Straight Etch
        # Create the property element for Etch operation
        etchprops = StepProperties("Etch")
        etchprops.type="straight"
        etchprops.depth =inDepth
        etchprops.waferSide="top"
        etchprops.materials = GetMaterialsList(inMaterial)
        if hasattr(etchprops, "selectivity"):    
            etchprops.selectivity=False
        etchprops.advanced.setEnabled(True)
        etchprops.mask.name=inMask.GetName()
        etchprops.mask.polarity = 1

        #Create the OutputParams object
        outParams = OutputParams(newSequence,"Straight Etch Using Mask", -1)		

        # call the "Etch" function. Pass the property element and the OutputParams to it.
        inWafer.Etch(etchprops, outParams)        

        # Get the model units
        modelUnits  = doc.GetModelUnits()

        # create a square mask
        maskUnits = modeler.GetDefaultMaskUnitsPerMicron()
        newMask = Mask("newMask2", maskUnits)
        vertices = ((0,0),(15,0),(15,15),(0,15),)
        newMask.AddPolygon(vertices, modelUnits)

        # add the newly created mask to the active masks list before it can be used in a modelling operation( like in Straight below)
        modeler.AddActiveMask(newMask)

        # Straight Etch with the newly created mask
        # Create the property element for Etch operation
        etchprops = StepProperties("Etch")
        etchprops.type="straight"
        etchprops.depth =inDepth
        etchprops.waferSide="top"
        etchprops.materials = GetMaterialsList(inMaterial)
        if hasattr(etchprops, "selectivity"):    
            etchprops.selectivity=False
        etchprops.advanced.setEnabled(True)
        etchprops.mask.name=newMask.GetName()
        etchprops.mask.polarity = 1
         
        outParams = OutputParams(newSequence,"Etch With New Mask", -1)

        # Perform etch operation on the newWafer
        inWafer.Etch(etchprops, outParams) 

        #Conformal Deposit
        #Create the property element for the deposit operation
        depProps = StepProperties("Deposit")
        depProps.type ="conformal"
        depProps.material = inMaterial.GetMaterialName()
        depProps.thickness=inDepth
        depProps.waferSide="top"
        depProps.lateralRatio=1.0
        depProps.advanced.cornerType="rounded"
		
		#Create the OutputParams object
        outParams = OutputParams(newSequence,"Conformal Deposit", -1)
		
        # call the "Deposit" function. Pass the property element and the OutputParams to it.
        inWafer.Deposit(depProps, outParams)
		
  
#Return list of material and/or material group names
def GetMaterialsList(material):
    materials = ()
        
    if material is None:
        return materials
    
    if isinstance(material, (tuple, list)):
        for mat in material:
            materials = materials + (GetMaterialName(mat),)
    else:
        materials = (GetMaterialName(material),)
 
    return materials
        
	
# Returns the material name (string)		
def GetMaterialName(matStringOrCMaterial):
    if isinstance(matStringOrCMaterial, str):
        return matStringOrCMaterial
    else:
        return matStringOrCMaterial.GetName()

		
				
    
   