#! python 
# -*- coding: utf-8 -*-

from voxelModeler import *
import waferQuery
import logging

_SEMulator3D_API_VERSION = "7.0"

_log = logging.getLogger("cov.extractProfile")

class ExtractProfile(CustomPythonFunction):

    def __init__(self, modeler, layerMap):
        CustomPythonFunction.__init__(self, modeler, layerMap)

    def Run(self, inVars, saveParams, isRestart):
        
        if isRestart:
            return
        
        doc = self.modeler.GetDocument()
        modeler     = self.modeler
        stepNum     = saveParams.stepNum
        stepName    = saveParams.stepName
        sequence    = saveParams.GetParentSequence()
        stepComments = saveParams.comments
    
        wafer       = inVars.GetVar("Wafer", type = VoxelWafer)
        p1          = inVars.GetVar("Start Point", type = float)
        p2          = inVars.GetVar("End Point", type = float)
        paramName   = inVars.GetVar("Parameter Name", type = str)

        extractOp = CModeler.CExtractProfileOp(modeler._GetCModeler())
        pointList = extractOp.extractProfile(wafer._GetCWafer(), p1, p2)
        
        profileNode = saveParams.AddProfileData(paramName)
        profileNode.SetProfileData(pointList)

        outputDir = self.doc.GetOutputDir(EAbsolutePath)
        fileName = profileNode.GetOutputFileRoot()
        outputFileFullPath = os.path.join(outputDir, fileName)

        f = open(outputFileFullPath, "w")

        _log.debug("Profile points: ")
        for p in pointList:
            lineStr = "%16.10f, %16.10f, %16.10f"%(p[0], p[1], p[2])
            _log.debug(lineStr)
            f.write(lineStr)
 
        _log.info("Profile data saved to %s."%(outputFileFullPath))
        f.close()
        