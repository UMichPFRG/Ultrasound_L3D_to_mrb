"""
Created on Mon Nov  2 17:09:06 2020

@author:    Mariana Masteling
            mastelin@umich.edu
            University of Michigan, USA

# This scrip is based on the work of Dr. Ahmet Kemal:https://github.com/mdAhmetKemal/L3dfiletoMhd
# It translated a .l3d file output by the BK ultrasound machine and exports it 
# in .mhd file.
# .raw is a small and easialy readable file by 3D Slicer.

# ************* It uses Python 2.7 *********************

# It was adapted from the original GitHub repository to only output the raw 
# files and use a batch approach to loop through all .l3d files in a folder.


# Other required files:
# fileSpesification_DataFinder -> function fileSpesification_DataFinder(L3DfileName)
# rawDatato3dVolume -> function volumeFinder -> defines raw volume
#                    -> function mhd_HeaderFileWriter -> writes mhd file 

#                   -> Both functions are needed. While we don't need the raw 
#                       volume, if we don't create it, the mhd file does not open
#                       in slicer. 

"""

#%% Imports 
import glob
import os
import numpy as np
import struct
import binascii
import zlib,sys, struct
from math import atan2, pi, hypot,floor,ceil
#%% Functions

def fileSpesification_DataFinder(L3DfileName):
    with open(L3DfileName, 'rb') as file:
        file.seek(79)
        temp_Loadedfile = file.read()
        file.close()
        
    L3DfileName = L3DfileName[:-4]
    
    templeTuple = struct.unpack("<bb", str(temp_Loadedfile[0:2]))

    if "(40, 0)" == str(templeTuple):
        ##this find 3d volume data size from file
        binarySizeXYZ = str(temp_Loadedfile[6:10])+\
        str(temp_Loadedfile[18:22])+\
        str(temp_Loadedfile[30:34])
        all_integerSizeX_Y_Z = struct.unpack("<iii ", binarySizeXYZ)
        Slice2dImagesizeX =all_integerSizeX_Y_Z[0]
        Slice2dImagesizeY =all_integerSizeX_Y_Z[1]
        SliceNumberZ =all_integerSizeX_Y_Z[2]
        

    ##--Find file matematical Specification from file
    count =0
    triple_xFF =0
    SpecificationArray =np.zeros(200,dtype=np.int)
    while "(0,)" != str(templeTuple)  :
        triple_xFF = int(temp_Loadedfile.find("03ff".decode("hex"),triple_xFF+2))
        templeTuple = struct.unpack("<b", str(temp_Loadedfile[triple_xFF+2:triple_xFF+3]))
        templeTuple2 = struct.unpack("<h", str(temp_Loadedfile[triple_xFF+6:triple_xFF+8]))
        SpecificationArray[count] = templeTuple2[0]
        count = count + 1
        
        templeTuple2 = struct.unpack("<h", str(temp_Loadedfile[triple_xFF+8:triple_xFF+10]))
        SpecificationArray[count] = templeTuple2[0]
        count = count + 1
    triple_xFF=int(temp_Loadedfile.find("03ff".decode("hex"),triple_xFF+3))
    templeTuple2 = struct.unpack("<III", str(temp_Loadedfile[triple_xFF+2:triple_xFF+14]))
    usgAngle =  SpecificationArray[17]
    
    #zlib decompressed image file 
    decompresObject= zlib.decompressobj(zlib.MAX_WBITS|32)
    zippedFilePart = str(temp_Loadedfile[triple_xFF+18:len(temp_Loadedfile)])
    decompanseFile=  decompresObject.decompress(zippedFilePart)
 
    #Control between file length
    if len(decompanseFile)== templeTuple2[2]:
        print  ( "zlib successful")
    else :
        print ( "zlib unsuccessful!!")
        
  
    rawArrayUint8=np.fromstring(decompanseFile,dtype=np.uint8)

    angle= 360
   
    ## --volume Function write same folder  mhd file
    volumeFinder(rawArrayUint8,Slice2dImagesizeX,Slice2dImagesizeY,\
                 SliceNumberZ,angle,L3DfileName,probDiameterSize=43)
 


def volumeFinder(raw,probAxissizeX,sizeY,sliceZ,angle,fileName,probDiameterSize=55):
    rawDataSize=len(raw)
    volumeSizeZ=(sizeY+probDiameterSize)*2+1
    if angle ==360:
        volumeSizeY= (sizeY+probDiameterSize)*2+1
    elif angle == 180:
        volumeSizeY= (sizeY+probDiameterSize)+1
    
    mhd_HeaderFileWriter(probAxissizeX,volumeSizeY,volumeSizeZ,fileName)
    volume3d=np.zeros((volumeSizeZ,volumeSizeY,probAxissizeX),dtype=np.uint8)
    stepAngle=(angle/float(sliceZ))
    for indxZ in range(0,volumeSizeZ-1):
        for indxY in range(0,volumeSizeY-1):
            if angle==360:
                cartesianY = indxY-(sizeY+probDiameterSize+1)
            elif angle==180:
                cartesianY = indxY 
            cartesianZ = indxZ -(sizeY+probDiameterSize)
            ## find angle of image on between image slice
            anglePoint = (((atan2(cartesianY,cartesianZ))*180.0/pi)-0.0001+360)%angle
            image1numberZ = int(ceil(anglePoint/ stepAngle))
            image2numberZ = int(floor(anglePoint/ stepAngle))
            image2powerZ =  (stepAngle -(anglePoint % stepAngle+0.001))/stepAngle
            image1powerZ =  1-image2powerZ 
            
            ## find bilateral filter of  piksel  on between two piksel
            pikselDiameterValueOnVolume = hypot(cartesianY,cartesianZ)
            pikselDiameterValueOnImageSlice = sizeY-(pikselDiameterValueOnVolume - probDiameterSize-1)
            upperindexNumberY=int(floor(pikselDiameterValueOnImageSlice))
            downerindexNumberY=int(ceil(pikselDiameterValueOnImageSlice))
            upperindexPowerY= downerindexNumberY-pikselDiameterValueOnImageSlice
            downerindexPowerY = 1-upperindexPowerY
            if image1numberZ == 600:
                image1numberZ =0
                image2numberZ = 599
            if image1numberZ == 0:
                image1numberZ =0
                image2numberZ = 599
            if image1numberZ == image2numberZ:
                image2numberZ=0
            # Added the last if to not go out of bounds
            if upperindexNumberY>0 and downerindexNumberY<sizeY and image1numberZ*probAxissizeX*(sizeY) != rawDataSize:
              
                N1p1=raw[image1numberZ*probAxissizeX*(sizeY)+upperindexNumberY*probAxissizeX:image1numberZ*probAxissizeX*(sizeY)+upperindexNumberY*probAxissizeX+probAxissizeX]
                N1p2=raw[image1numberZ*probAxissizeX*(sizeY)+downerindexNumberY*probAxissizeX:image1numberZ*probAxissizeX*(sizeY)+downerindexNumberY*probAxissizeX+probAxissizeX]
                N2p1=raw[image2numberZ*probAxissizeX*(sizeY)+upperindexNumberY*probAxissizeX:image2numberZ*probAxissizeX*(sizeY)+upperindexNumberY*probAxissizeX+probAxissizeX]
                N2p2=raw[image2numberZ*probAxissizeX*(sizeY)+downerindexNumberY*probAxissizeX:image2numberZ*probAxissizeX*(sizeY)+downerindexNumberY*probAxissizeX+probAxissizeX]
            
                total=image1powerZ*(N1p1*upperindexPowerY+N1p2*downerindexPowerY) + image2powerZ*(N2p1*upperindexPowerY+N2p2*downerindexPowerY)
              
                volume3d[indxZ][indxY][:]=total
            else:
                volume3d[indxZ][indxY][:] =  0
    fileData =open(fileName+".raw",'wb')
    fileData.write(volume3d.tostring())
    fileData.close()
    
def mhd_HeaderFileWriter(sizeX,volumeSizeY,volumeSizeZ,nameFile):

    mhdHeadStr ="ObjectType = Image\nNDims = 3\nBinaryData = True\nBinaryDataByteOrderMSB = False\nCompressedData = False\n"
    mhdHeadStr =mhdHeadStr + "ElementType = MET_UCHAR\nAnatomicalOrientation = LPI\nTransformMatrix = -1 0 0 0 -1 0 0 0 1\n"
    mhdHeadStr =mhdHeadStr +"CenterOfRotation = 0 0 0\nElementSpacing = 0.134 0.132 0.132\nDimSize = "
    t = open(str(nameFile)+".mhd", 'wb')
    t.write(mhdHeadStr)
    t.write(str(sizeX)+" "+str(volumeSizeY)+" "+str(volumeSizeZ))
    t.write("\nElementDataFile = ")
    t.write(nameFile+".raw")
    t.close()
#%%

files_to_convert = []

ultrasound_folder = r'C:\Users\mastelin\Downloads\20230209_ Test\20230209_ Test\test_new'
extension = '.l3d'

# Get all of the files from the folder that are the correct type
for file in glob.glob(ultrasound_folder + '\*' + extension):
    files_to_convert.append(os.path.split(file)[1])
#
#
subject_number = 1
n_subjects_in_folder = len(files_to_convert)
for ultrasound_file in files_to_convert:
    print("Processing ", ultrasound_file)
    print(subject_number, " of ", n_subjects_in_folder)
    subject_number = subject_number +1
    file_with_extension = ultrasound_folder + '\\' + ultrasound_file
    
    ##  write this a file name on l3d folder
    fileSpesification_DataFinder(file_with_extension)

    

print('**********Finished***************')
