#!python
# -*- coding: utf-8 -*-
# -*- Mode: Python; tab-width: 4 -*-
# Copyright (c) 2017, Coventor, Inc. All rights reserved.
#
# Takes the cross-sectional area for a particular material along the X-Z or Y-Z plane.
# The measurement is taken using the following steps:
#   1. Copy the wafer, preserving the original model.
#   2. Crop the copied wafer to the provided metrology mask.
#   3. Rotate the copied wafer so that the area to be measured is now the top surface of the wafer.
#   4. Planarize the copied wafer so that the exposed surface is at the elevation defined by the center line of the
#      metrology mask.
#   5. Create a new metrology mask that is based on the bounds of the copied, rotated wafer. This new mask will
#      be used for the actual area measurement.
#   6. Deposit dummy material on the wafer surface to mark the area to be measured.
#   7. Apply a Virtual Metrology step to measure Interface Area between the specified material and the dummy
#      material. This step will write out the area to metrology.txt.

from voxelModeler import *
from voxelWafer import *
import logging
import coventor
import math

_SEMulator3D_API_VERSION = "6.0"

_log = logging.getLogger("cov.CrossSectionalArea")
#_log.setLevel(logging.DEBUG)                       # Uncomment for debug mode


def isNumber(x):
    return isinstance(x, (float, int))

'''
Some tests submit material names 
e.g.: testTransparent (Dev.RegularModeler.StraightEtch.StraightEtchTest.StraightEtchTest)
'''
def GetMaterialName(matStringOrCMaterial):
    if isinstance(matStringOrCMaterial, str):
        return matStringOrCMaterial
    else:
        return matStringOrCMaterial.GetName()

'''  
Return list of material and/or material group names
'''  
def GetMaterialsList(material):
    materials = ()        
    if material is None:
        return materials
    
    if isinstance(material, (tuple, list)):
        for mat in material:
            materials = materials + (GetMaterialName(mat),)
    else:
        materials = (GetMaterialName(material),)
                  
    _log.debug( "\tmaterials=%s", str(materials))  
    return materials

# Measure the cross-sectional at a location specified by a mask
class CrossSectionalArea(CustomPythonFunction):
    def __init__(self, modeler, layerMap):
        CustomPythonFunction.__init__(self, modeler, layerMap)

    # entry point
    def Run(self, inVars, saveParams, isRestart):

        # isRestart is true if the function is being call before the restart point in an incremental rebuild, otherwise it's false.
        if isRestart:
            return;

        # default inputs
        doc = self.modeler.GetDocument()
        modelerObj = self.modeler
        stepNum = saveParams.stepNum
        stepName = saveParams.stepName
        sequence = saveParams.GetParentSequence()
        stepComments = saveParams.comments

        # user-defined inputs
        wafer = inVars.GetVar("Wafer", type=VoxelWafer)
        metrologyMask = inVars.GetVar("Mask Name", type=Mask)
        paramName = inVars.GetVar("Parameter Name", type=str)  # Metrology param name
        targetMaterials = inVars.GetVar("Target Materials", type=Material)  # metal
        
        targetMaterialsNameList = GetMaterialsList(targetMaterials)

        # Error check input parameters
        if not paramName:  # empty parameter name
            raise ValueError("Parameter Name cannot be empty.")

        if metrologyMask.GetNumFaces() > 1:
            raise RuntimeError("Too many faces in the metrology mask.")
        elif metrologyMask.GetNumFaces() == 0:
            raise RuntimeError("Metrology mask is empty.")

        debugSeq = sequence.AddSequence(stepName,stepNum)  # Used to save wafer output in debug mode

        # Copy the wafer. Since taking the cross-sectional area requires slicing the wafer and is "destructive",
        # the original wafer is retained by making a copy for use with metrology.
        xSectionWafer = VoxelWafer(modelerObj)
        xSectionWafer.Copy(wafer)
        if _log.isEnabledFor(logging.DEBUG):
            outParams = OutputParams(debugSeq, "Copy Wafer", -1)
            xSectionWafer.Save(outParams)

        # Crop the copied wafer to the bounds specified by the metrology mask to restrict the measured region.
        cropWaferProps = StepProperties("WaferOperations")
        cropWaferProps.operation = 'crop'
        cropWaferProps.crop.type = 'mask'
        cropWaferProps.crop.type.mask.name = metrologyMask.GetName()
        xSectionWafer.WaferOperations(cropWaferProps)
        outParams = OutputParams(debugSeq, "Crop Copied Wafer", -1)
        if _log.isEnabledFor(logging.DEBUG):
            xSectionWafer.Save(outParams)

        # Determine the bounds of the metrology mask. Uses the bounds to determine:
        #     1. Direction (in X or Y) to "slice" the model for area measurement
        #     2. Polish amount, to expose the area that corresponds to the mask centerline
        modelUnits = doc.GetModelUnits()
        metMaskBounds = metrologyMask.GetBounds(modelUnits)
        _log.debug("CrossSectionalArea: Bounds Mask is %f, %f, %f, %f", metMaskBounds[0], metMaskBounds[1], metMaskBounds[2], metMaskBounds[3])
        # Calculate polish distance needed to expose rotated wafer to center line
        deltaX = metMaskBounds[2] - metMaskBounds[0]
        deltaY = metMaskBounds[3] - metMaskBounds[1]
        planarizeDistance = 0
        wfrRotateProps = StepProperties("WaferOperations")
        wfrRotateProps.operation = 'rotate'
        wfrRotateProps.operation.rotate.angle = 90
        if deltaY > deltaX:          # mask is longer in Y than X
            planarizeDistance = deltaX/2
            wfrRotateProps.operation.rotate.axis = 'y'      # rotate around y-axis
        else:                                               # mask is longer in X than Y
            planarizeDistance = deltaY/2
            wfrRotateProps.operation.rotate.axis = 'x'      # rotate around x-axis

        # Rotate wafer in the required direction, so that the area to be measured is now parallel to the
        # X-Y plane i.e. it will become the model's top surface.
        xSectionWafer.WaferOperations(wfrRotateProps)
        if _log.isEnabledFor(logging.DEBUG):
            outParams = OutputParams(debugSeq, "Rotate Copied Wafer", -1)
            xSectionWafer.Save(outParams)

        # Slice (planarize) model copy to center line of the original metrology mask.
        planarizeProps = StepProperties("Polish")
        planarizeProps.waferSide = 'top'
        planarizeProps.type = 'stopOnReferencePlane'
        planarizeProps.stopOnReferencePlane.referencePlane = 'highest'
        planarizeProps.stopOnReferencePlane.distance = planarizeDistance
        xSectionWafer.Polish(planarizeProps)
        if _log.isEnabledFor(logging.DEBUG):
            outParams = OutputParams(debugSeq, "Polish to Expose Area", -1)
            xSectionWafer.Save(outParams)

        # Add a temporary dummy material to the materials database
        dummyMat = doc.AddMaterial("semu_dummy",(190,0,0),CONDUCTOR,-1,DUP_ADD_ALLOW)
    
        # To mark the area for measurement, deposit a dummy material on the surface.
        modelResolution = doc.GetModelResolution()
        planarDepProps = StepProperties("Deposit")
        planarDepProps.material = dummyMat.GetName()
        planarDepProps.thickness = 4.0 * modelResolution          # deposit 4 voxels
        planarDepProps.type = 'straight'
        planarDepProps.waferSide = 'top'
        xSectionWafer.Deposit(planarDepProps)
        if _log.isEnabledFor(logging.DEBUG):
            outParams = OutputParams(debugSeq, "Straight Deposit Dummy Material", -1)
            xSectionWafer.Save(outParams)

        # Construct a new metrology mask that includes the area to be measured.
        xSectionWaferBounds = xSectionWafer.GetOctreeBounds()
        _log.debug("CrossSectionalArea: Wafer Bounds(XY) is %f, %f, %f, %f", xSectionWaferBounds[0],xSectionWaferBounds[1], xSectionWaferBounds[3], xSectionWaferBounds[4])

        # Create a metrology mask box based on Bounds Mask edge
        maskUnits = modelerObj.GetDefaultMaskUnitsPerMicron()
        xSectionAreaMask = Mask("__XsectionAreaMask", maskUnits)
        
        xSectionAreaMask.AddRectangle(xSectionWaferBounds[0], xSectionWaferBounds[1], xSectionWaferBounds[3],xSectionWaferBounds[4], modelUnits)

        numMetFaces = xSectionAreaMask.GetNumFaces()
        _log.debug("CrossSectionalArea: metrology mask contains %d faces.", numMetFaces)

        # add mask to active mask list
        modelerObj.AddActiveMask(xSectionAreaMask)

        # take Area measurement -- use interface area between material of interest and the dummy material
        metrologyProps = StepProperties("Metrology")
        metrologyProps.mask = '__XsectionAreaMask'
        metrologyProps.parameterName = paramName
        metrologyProps.type = 'interfaceArea'
        for mat in targetMaterialsNameList:
            metrologyProps.type.interfaceArea.materials.add(mat)
            metrologyProps.type.interfaceArea.materials[mat].materialSet = 'set1'
        metrologyProps.type.interfaceArea.materials.add(dummyMat.GetName())
        metrologyProps.type.interfaceArea.materials[dummyMat.GetName()].materialSet = 'set2'
        outParams = OutputParams(debugSeq, paramName, -1)
        xSectionWafer.Metrology(metrologyProps, outParams)
        if _log.isEnabledFor(logging.DEBUG):
            outParams = OutputParams(debugSeq, paramName, -1)
            xSectionWafer.Save(outParams)

        # remove temporary CD Mask
        modelerObj.RemoveActiveMask('__XsectionAreaMask')

        return VarList()
