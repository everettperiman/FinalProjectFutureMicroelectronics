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
from vdataOpHelper import *

# ==============================================================================================

# ==============================================================================================

class VDataOp():
    def __init__(self, inputVdataFile, outputVdataFile = "", enableOutputs = False):  
        if len(outputVdataFile) == 0:
            outputVdataFile = "test.vdata"      

        self._vdataOpHelper = VDataOpHelper(inputVdataFile, outputVdataFile, enableOutputs)           
        self._dopantData = {}     
            
    def __printPlaneEQs(self, wd, peqs, x, y, z):
        x = x - int(self._vdataOpHelper._modelOrigin[0])
        y = y - int(self._vdataOpHelper._modelOrigin[1])
        z = z - int(self._vdataOpHelper._modelOrigin[2])
        print('At (%d,%d,%d)\tvoxel: (%d,%d,%d)\tplane: (%f,%f,%f,%f)' % (x, y, z, wd[x][y][z][0], wd[x][y][z][1], wd[x][y][z][2], peqs[x][y][z][0], peqs[x][y][z][1], peqs[x][y][z][2], peqs[x][y][z][3]))

                    
    def workFunction(self):
        wd = None
        dd = None
        CaseReadDopant  = 0
        CaseWriteDopant = 1
        CaseDBGPlaneEQs = 2
        testCase = ""
        
        #testCase = CaseReadDopant
        testCase = CaseWriteDopant
        # For this option turn on export of plane equations in the VDATA expport step
        #testCase = CaseDBGPlaneEQs
                
        dopantToWrite = ""
        wd = self._vdataOpHelper.ReadWafer()        
        if testCase == CaseReadDopant:
            dd = self._vdataOpHelper.ReadDopant("/PType/B")                
            wd = self.replaceMaterial(wd, dd)
        elif testCase == CaseWriteDopant:
            dd = self._vdataOpHelper.ReadDopant("/PType/B")  
            wd = self.replaceMaterial(wd, dd)                          
            wd, dd = self.reducedDopant(wd, dd)   
            dopantToWrite = "/PType/B"                        
        elif testCase == CaseDBGPlaneEQs:
            peqs = self._vdataOpHelper.ReadPlaneEQs()

            print(peqs.shape)
            for i in range(10):
                self.__printPlaneEQs(wd, peqs, -112, 5, -19+i)
            print("\n")
            for i in range(10):
                self.__printPlaneEQs(wd, peqs, -112, 5, 10+i)
            print("\n")
            for i in range(10):
                self.__printPlaneEQs(wd, peqs, -112, 5, 40+i)
            print("\n")
            for i in range(10):
                self.__printPlaneEQs(wd, peqs, -112, 5, 71+i)
            print("\n")
            for i in range(10):
                self.__printPlaneEQs(wd, peqs, -112, 5, 101+i)
            print("\n")
            for i in range(10):
                self.__printPlaneEQs(wd, peqs, -112, 5, 131+i)
            print("\n")


            for i in range(10):
                self.__printPlaneEQs(wd, peqs, -62+i, 5, 61)
            print("\n")
            for i in range(10):
                self.__printPlaneEQs(wd, peqs, -74+i, 5, 94)
            print("\n")

        else:                      
            #wd = self.removeMaterial(wd, 2)
            #wd = self.createNewWafer(wd.shape, 2)
            wd = self.extendWafer(wd, 2)
        
        if wd is not None:
            self._vdataOpHelper.WriteWafer(wd)
            if 0 != len(dopantToWrite):
                self._vdataOpHelper.WriteDopant(dd, dopantToWrite)
            self._vdataOpHelper.InsertCDATA()
                             
    def reducedDopant(self, wd, dd):
        
        if dd is not None:
            boolIndex = dd[:,:,:] != 0
            dd[:,:,:][boolIndex] *= 0.01
                            
        return wd, dd     
        
    def replaceMaterial(self, wd, dd):
        
        if dd is not None:
            boolIndex = dd[:,:,:] > 1.0e16
            wd[:,:,:,1][boolIndex] = 1
            wd[:,:,:,2][boolIndex] = 1
        
        return wd                  
                                
    # Remove materials with integer id 'id' from the numpy wafer 'wd'
    def removeMaterial(self, wd, id):
        print('Removing material with id: %d' % id)

        # Change both materials with 'id' to air
        # Get boolean index where mat1 has id 'id'
        boolIndex = wd[:,:,:,1] == id

        # Set mat1 in those voxels to air
        wd[:,:,:,1][boolIndex] = 255

        # Do the same for mat2
        boolIndex = wd[:,:,:,2] == id
        wd[:,:,:,2][boolIndex] = 255   
        
        return wd             
        
    def createNewWafer(self, shape, id):
        # Initialize a wafer with X-Y extent specified with 'shape' 
        # (Has to be the shape of the original wafer!)
        height = 5    
        extW = np.zeros(shape[0] * shape[1] * height * shape[3], dtype=np.uint8)
        extW = extW.reshape(shape[0], shape[1], height, shape[3])
    
        # Fill with air
        extW[:,:,:,0] = 129
        extW[:,:,:,1] = 255
        extW[:,:,:,2] = 255
    
        # Add extrusion material
        xl = shape[0] / 2
        yl = shape[1] / 2
        xu = xl + 10
        yu = yl + 15
        extW[xl:xu, yl:yu, :, 0] = 129
        extW[xl:xu, yl:yu, :, 1] = id
        extW[xl:xu, yl:yu, :, 2] = id
        
        return extW

    def extendWafer(self, wd, id):
        extW = self.createNewWafer(wd.shape, id)
        extW = np.concatenate((wd, extW), axis = 2) # concatenate along z-di

        return extW        
                            
# ==============================================================================================

'''
Main program; read the voxel data from a .vdata file.
'''
# ==============================================================================================
def main():
    vdataOp = VDataOp(sys.argv[1], sys.argv[2])
    vdataOp.workFunction()


# ==============================================================================================
# ==============================================================================================
# ==============================================================================================
# End Main function

if __name__ == '__main__':
    status = main()
    sys.exit(status)
