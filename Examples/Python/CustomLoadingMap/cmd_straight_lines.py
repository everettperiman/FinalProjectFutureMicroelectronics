#! python
# -*- coding: utf-8 -*-
# $Id: cmd_straight_lines.py $
# Copyright (c) 2018, Coventor, Inc. All rights reserved.
#==============================================================================

# Change the loading map for a straight line 5 voxels inside the modeling domain based on the multiplier inputted as a 'Parameter' in the UI.
import os
import sys
import numpy as np

#class where we will define our functions that modify the loading map (also an input in the UI)
class LoadingMapIO():
    def __init__(self, wafer, doc):
        self._wafer = wafer
        self._doc = doc

	#This function and all its input parameters are REQUIRED. 
    #lmap is a 2D numpy array that is PRE-INITIALIZED to the size of model bounds and is pre-populated with 1's (i.e. multiply etch rate by 1 everywhere).
    #numParams is a 1D array. Its elements correspond to 'Parameters' defined on the UI, under the class name. It's optional to use it in the function although it is required to have it as an input parameter.
    def load(self, lmap, numParams):
        # Set to 0.5 (set by 'Parameters' on the UI) on lines dist from the boundaries
        shape = lmap.shape
        dist = 5
        lmap[dist            ,:              ] = numParams[0] 
        lmap[:               ,dist           ] = numParams[0] 
        lmap[shape[0]-1-dist ,:              ] = numParams[0] 
        lmap[:               ,shape[1]-1-dist] = numParams[0] 
    
