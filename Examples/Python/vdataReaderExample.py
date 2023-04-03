# ==============================================================================================
# ==============================================================================================
# ==============================================================================================
#
# Copyright (c) 2017-2018, Coventor, Inc. All rights reserved.
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

# ==============================================================================================

# ==============================================================================================

'''
Convert model coordinates mc (x,y,z) to voxel coordinates

'''
def Model2Voxel(mc, modelResolution, modelOrigin):
    return (int((mc[0] - modelOrigin[0]) / modelResolution),
            int((mc[1] - modelOrigin[1]) / modelResolution),
            int((mc[2] - modelOrigin[2]) / modelResolution))

# ==============================================================================================    
'''
Convert voxel coordinates vc (i,j,k) into model coordinates
'''
def Voxel2Model(vc, modelResolution, modelOrigin):
    return (vc[0] * modelResolution + modelOrigin[0],
            vc[1] * modelResolution + modelOrigin[1],
            vc[2] * modelResolution + modelOrigin[2])

class VDataReader():
    def __init__(self, vdataFile):
        print("Reading voxel data file '%s'."%(vdataFile))

        xmlTree = xml.etree.ElementTree.parse(sys.argv[1])
        self._root = xmlTree.getroot()

    def PrintHeader(self):
        # Read model information
        modelProperties, materialProperties, dopantProperties = self.ReadProperties(self._root)
        print("\n ## Model properties: ## ")
        for key in modelProperties:
            print(key + " = " +  str(modelProperties[key]))
        print("\n ## Materials properties: ## ")
        for key in materialProperties:
            print(key + " = " +  str(materialProperties[key]))
        print("\n ## Dopant properties: ## ")
        for key in dopantProperties:
            print(key + " = " +  str(dopantProperties[key]))
        print("\n")

        # Get model information from the properties dictionary read previously
        self._modelResolution = float(modelProperties['VoxelSize']['Value'])
        self._modelOrigin = (float(modelProperties['ModelOrigin']['X']), 
                             float(modelProperties['ModelOrigin']['Y']), 
                             float(modelProperties['ModelOrigin']['Z']))
        self._modelSize = (float(modelProperties['NumVoxels']['NX']), 
                           float(modelProperties['NumVoxels']['NY']), 
                           float(modelProperties['NumVoxels']['NZ']))

    def PrintVoxelFillFractions(self):
        for child in self._root.iter('VoxelData'):
            asciiData = child.text
            binaryData = base64.b64decode(asciiData)
            #print(binaryData.type)

            voxelData = self._unpackZlibBuffer(binaryData)

            # We expect three bytes per voxel.
            if len(voxelData)%3 != 0:
                raise ValueError("Voxel data is invalid or truncated; size is not a multiple of 3 bytes.")


            numVoxels = len(voxelData)//3
            print("Read %d voxels:"%(numVoxels))

            print("(x,y,z): fraction, materialID1 materialID2")
            m1m2 = self._modelSize[1] * self._modelSize[2]
            for vi in range(0,numVoxels):
                # This is the new one simply replace NX NY by NY NZ
                ii = int(vi / m1m2)
                jj = int((vi - ii * m1m2) / self._modelSize[2])
                kk = int(vi -  ii * m1m2 - jj * self._modelSize[2])
                vCoord = Voxel2Model((ii,jj,kk), self._modelResolution, self._modelOrigin)
                print("(%f %f %f): %d %d %d" % (vCoord[0], vCoord[1], vCoord[2], voxelData[vi*3], voxelData[vi*3+1], voxelData[vi*3+2]))

    def PrintDopantConcentrations(self):
        # Read out dopant concentrations for each voxel --- dopant data export is optional in SEMulator3D
        for dopants in self._root.iter('DopantData'):
            for dopant in dopants:
                asciiData = dopant.text
                binaryData = base64.b64decode(asciiData)
                dopantData = self._unpackZlibBuffer(binaryData)

                # Dopant data is stored as floats, so we expect four bytes per voxel.
                if len(dopantData)%4 != 0:
                    raise ValueError("Dopant data is invalid or truncated; size is not a multiple of 4 bytes.")
            
                numVoxels = len(dopantData) // 4        # floats
                print("\n\nRead %d voxels:"%(numVoxels))

                print("(x,y,z): " + dopant.attrib['DopantName'])
                m1m2 = self._modelSize[1] * self._modelSize[2]
                for vi in range(0,numVoxels):
                    # This is the new one simply replace NX NY by NY NZ
                    ii = int(vi / m1m2)
                    jj = int((vi - ii * m1m2) / self._modelSize[2])
                    kk = int(vi -  ii * m1m2 - jj * self._modelSize[2])
                    vCoord = Voxel2Model((ii,jj,kk), self._modelResolution, self._modelOrigin)
                    print("(%f %f %f): %g" % (vCoord[0], vCoord[1], vCoord[2], struct.unpack("f", dopantData[vi*4:(vi+1)*4])[0]))  

    # ==============================================================================================

    '''
    Read header information from a .vdata file
    '''
    def ReadProperties(self, root):
        modelProperties = {}
        for prop in root.find('Properties'):
            modelProperties[prop.tag] = prop.attrib

        materialProperties = {}
        matIndex = 0
        for prop in root.find('Materials'):
            materialProperties[prop.tag + "_" + str(matIndex)] = prop.attrib
            matIndex = matIndex + 1

        dopantIndex = 0
        dopantProperties = {}
        for prop in root.find('Dopants'):
            dopantProperties[prop.tag + "_" + str(dopantIndex)] = prop.attrib
            dopantIndex = dopantIndex + 1

        return modelProperties, materialProperties, dopantProperties

        return modelProperties, materialProperties, dopantProperties

    # ==============================================================================================

    '''
    Utility function to read a single zlib-compressed block from a buffer.
    Each zlib block has a 14-byte header containing:
        - !zlib!, in 6 bytes of raw ascii text
        - the unpacked data size in bytes, stored as a 4-byte unsigned int in network byte order
        - the packed data size in bytes, stored as a 4-byte unsigned int in network byte order

    Returns a tuple containing the unpacked data and any remaining buffer data.
    '''
    def _readZlibBlock(self, buffer):
        
        
        # Check for the expected header.
        if len(buffer) < 15 or not buffer[0:6] == b'!zlib!':
            print("Buffer is not a zlib compressed block.")
            
            
            return None

        # Read the unpacked and packed sizes.  Remember to use ntohl to get the correct byte order!
        originalSize = socket.ntohl(struct.unpack("I", buffer[6:10])[0])
        packedSize = socket.ntohl(struct.unpack("I", buffer[10:14])[0])
    
        print("Unpacking zlib block with packed size %d and unpacked size %d."%(packedSize, originalSize))
    
        # Consistency check.
        if len(buffer) < packedSize + 14:
            print("Buffer is truncated or invalid.")
            return None
    
        # Uncompress the data.
        data = zlib.decompress(buffer[14:])
        
        # Make sure we got what we expected.
        if not len(data) == originalSize:
            raise ValueError("Unpacked data has the wrong size.  Expected %d bytes, but found %d."%(originalSize, len(data)))
        
        # Return the uncompressed data, and any unconsumed data from the original buffer.
        return data, buffer[packedSize+14:]

    # ==============================================================================================

    '''
    Utility function to unpack a buffer consisting of one or more compressed zlib blocks.
    Returns the raw binary unpacked buffer.
    '''
    def _unpackZlibBuffer(self, buffer):
        unpackedData = ""
    
        # Unpack data block by block, appending as we go.
        while len(buffer) > 0:
            bufferTuple = self._readZlibBlock(buffer)
            
            if not bufferTuple:
                break
            
            #unpackedData = unpackedData + 
            buffer = bufferTuple[1]
        
        return bufferTuple[0]
    
# ==============================================================================================

'''
Main program; read the voxel data from a .vdata file.
'''
# ==============================================================================================
def main():
    vdataReader = VDataReader(sys.argv[1])
    vdataReader.PrintHeader()
    vdataReader.PrintVoxelFillFractions()
    vdataReader.PrintDopantConcentrations()

# ==============================================================================================
# ==============================================================================================
# ==============================================================================================
# End Main function

if __name__ == '__main__':
    status = main()
    sys.exit(status)
