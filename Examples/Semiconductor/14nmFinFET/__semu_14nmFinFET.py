#! python 
# -*- coding: utf-8 -*-
# 

# Autogenerated by Coventor SEMulator3D on 4/2/2023, 20:23:37
# SEMulator3D 

# Using model file:        C:\FinalProjectFutureMicroelectronics\Examples\Semiconductor\14nmFinFET\14nmFinFET.zam
# Using process file:      C:/FinalProjectFutureMicroelectronics/Examples/Semiconductor/14nmFinFET/14nmFinFET-Input/14nmFinFET.vproc
# Using analysis file:     C:/FinalProjectFutureMicroelectronics/Examples/Semiconductor/14nmFinFET/14nmFinFET-Input/14nmFinFET.vanalysis
# Using material file:     C:/FinalProjectFutureMicroelectronics/Examples/Semiconductor/14nmFinFET/14nmFinFET-Input/14nmFinFET.vmpd
# Using layout file:       C:/FinalProjectFutureMicroelectronics/Examples/Semiconductor/14nmFinFET/14nmFinFET-Input/14nmFinFET.gds

# ============================================================== 
# Command line arguments
import sys
import getopt
from voxelDocument import MonitorKillFile

opts, args = getopt.getopt(sys.argv[1:], '', ["fpw=","mpw=","spw=","encrypted","killFile="])

fpw, mpw, spw = '', '', ''
encrypted = False
for opt, arg in opts:
   if opt == "--fpw":
      fpw = arg
   elif opt == "--mpw":
      mpw = arg
   elif opt == "--spw":
      spw = arg
   elif opt == "--encrypted":
      encrypted = True
   elif opt == "--killFile":
      MonitorKillFile(arg)
# ============================================================== 
# Choose our python API version
_SEMulator3D_API_VERSION = '10.3'

# ============================================================== 
# Import Python built-in modules
import math
import time
import traceback
import logging

# Import SEMulator3D modules
from voxelModeler import *

# Logging
_log = logging.getLogger("cov.modelBuilding")
startTime = time.time()

#============================================================== 
# Setup Masks 
layoutFile = 'C:/FinalProjectFutureMicroelectronics/Examples/Semiconductor/14nmFinFET/14nmFinFET-Input/14nmFinFET.gds'
layoutTopCell = 'ARRAY3X3_LIBSRAM_CELL_172_432'

# GDS layer map info
layerMap = {}
layerMap['Active'] = (5, 0)
layerMap['ActiveBasic'] = (19, 0)
layerMap['BB1'] = (6, 0)
layerMap['BB2'] = (33, 0)
layerMap['BB3'] = (34, 0)
layerMap['BB4'] = (130, 0)
layerMap['CD_FIN'] = (24, 0)
layerMap['CD_MAND'] = (23, 0)
layerMap['Fin'] = (0, 0)
layerMap['Gate'] = (4, 0)
layerMap['GateCut'] = (9, 0)
layerMap['GateUncut'] = (8, 0)
layerMap['LI'] = (17, 0)
layerMap['NWell'] = (2, 0)
layerMap['Outline'] = (43, 0)
layerMap['SP_FINNN'] = (25, 0)
layerMap['SP_FINNP'] = (26, 0)
layerMap['SP_FINPP'] = (27, 0)
layerMap['THK_STI'] = (28, 0)


#============================================================== 
# Setup Modeler and Documents
modelResolution = 1
modelUnits = 'nm'

voxDoc = VoxelDocument('C:/FinalProjectFutureMicroelectronics/Examples/Semiconductor/14nmFinFET/14nmFinFET.zam', modelResolution, modelUnits, LOAD)

modeler = VoxelModeler(voxDoc)

# Active masks in the process
activeLayoutMaskNames = ('Active', 'BB1', 'BB2', 'CD_MAND', 'Fin', 'GateCut', 'GateUncut', 'LI', 'NWell', 'SP_FINNP', )
maskFile = MaskFile(layoutFile, layoutTopCell)

modeler.SetDefaultMaskUnitsPerMicron(maskFile.GetUnitsPerMicron())

for maskName in activeLayoutMaskNames:
    if maskName in layerMap.keys():
        mask = maskFile.GetLayerWithDataType(layerMap[maskName][0], layerMap[maskName][1])
        mask.SetName(maskName)
        modeler.AddActiveMask(mask)

# Fix build boundary based on current masks.
modeler.CacheBuildBoundary()


#============================================================== 
# Load Process 
procDoc = CProcessData.ProcessDocument()
procDoc.openWithPasswords('C:/FinalProjectFutureMicroelectronics/Examples/Semiconductor/14nmFinFET/14nmFinFET-Input/14nmFinFET.vproc', fpw, mpw, encrypted)

#============================================================== 
# Load Analysis 
analysisDoc = CProcessData.AnalysisDocument()
analysisDoc.openWithPasswords('C:/FinalProjectFutureMicroelectronics/Examples/Semiconductor/14nmFinFET/14nmFinFET-Input/14nmFinFET.vanalysis', fpw, mpw, encrypted)

#============================================================== 
# Setup Materials and Dopants
matDoc = CMaterialData.MaterialDocument()
matDoc.openWithPasswords('C:/FinalProjectFutureMicroelectronics/Examples/Semiconductor/14nmFinFET/14nmFinFET-Input/14nmFinFET.vmpd', fpw, mpw, encrypted)
for mat in matDoc.getActiveMaterialsInProcess(procDoc):
    voxDoc.GetMaterials().Add(mat, DUP_ADD_ALLOW)

for dopant in matDoc.getActiveDopantsInProcess(procDoc):
    voxDoc.GetDopants().Add(dopant, DUP_ADD_ALLOW)

if analysisDoc:
    for mat in matDoc.getActiveMaterialsInProcess(analysisDoc):
        voxDoc.GetMaterials().Add(mat, DUP_ADD_ALLOW)
    
    for dopant in matDoc.getActiveDopantsInProcess(analysisDoc):
        voxDoc.GetDopants().Add(dopant, DUP_ADD_ALLOW)

success = voxDoc.GetProperties().IsModelBuildComplete() #True

#============================================================== 
# Build Model
success = modeler.BuildModel(procDoc, analysisDoc, spw)

#============================================================== 
# Save Model Build
if not voxDoc.IsOutputEnabled():
    modeler.SaveFinalStep()

voxDoc.GetProperties().SetModelBuildComplete(success)
voxDoc.Save()

endTime = time.time()
_log.info('Build process completed.')
_log.info('Elapsed Time %d seconds.', (endTime-startTime))

if voxDoc.GetProperties().GetStartViewer():
    voxDoc.StartViewer(False)

if not success:
    # Though the build terminated cleanly, it was not considered successful.
    sys.exit(1)

