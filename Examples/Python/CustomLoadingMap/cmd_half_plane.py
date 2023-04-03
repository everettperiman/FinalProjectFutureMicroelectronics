#! python
# -*- coding: utf-8 -*-
# $Id: cmd_half_plane.py $
# Copyright (c) 2018, Coventor, Inc. All rights reserved.
#==============================================================================

# Change the loading map for half of the model by the multiplier inputted as a 'Parameter' in the UI.
import os
import sys
import numpy as np

#class where we will define our functions that modify the loading map (also an input in the UI)
class LoadingMapIO():
   
    #VoxelWafer and VoxelDocument can be accessed from within this class. (Optional)
    def __init__(self, wafer, doc):
        self._wafer = wafer
        self._doc = doc
        print("Hello from LoadingMapIO") # Print text to log (for demonstration)
        print("Document: %s" % self._doc.GetFileName()) # Print File Name (for demonstration)
        print("Wafer volume: %f" % self._wafer.FindVolume()) # Print Wafer Volume (for demonstration)
   
    #This function and all its input parameters are REQUIRED. 
    #lmap is a 2D numpy array that is PRE-INITIALIZED to the size of model bounds and is pre-populated with 1's (i.e. multiply etch rate by 1 everywhere).
    #numParams is a 1D array. Its elements correspond to 'Parameters' defined on the UI, under the class name. It's optional to use it in the function although it is required to have it as an input parameter.
    def load(self, lmap, numParams):
        
        print("lmap shape: %s" % str(lmap.shape))  # Print shape of lmap (for demonstration)
        print("numParams: %s" % str(numParams))    # Print the input parameters (for demonstration)
        # Set to 0.5 (defined on the UI as 'Parameter 1') on the left half 
        lmap[0:lmap.shape[0]//2,:] = numParams[0]
        
    

