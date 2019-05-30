from tkinter import filedialog
from tkinter import *
import time
import sys
import os
import shutil
from Exceptions.WrongNumberOfArguments import WrongNumberOfArguments
from GenerateVoxelMask.GenerateVoxelFromDATFile import GenerateVoxelFromDATFile
from GenerateVoxelMask.GenerateVoxelsFromSPARFile import GenerateVoxelFromSPARFile


def getUserData():
    if sys.argv.__len__() is 4:
        structurePath = sys.argv[1]
        datPath = sys.argv[2]
        outputPath = sys.argv[3]

    elif sys.argv.__len__() is 1:
        root = Tk()
        root.filename = filedialog.askopenfilename(initialdir="", title="Select the Structure file", filetypes=(("Struc files","*.nii.gz"),("all files","*.*")))
        structurePath = root.filename;
        structurePathParent = structurePath.split('/')[-2]
        root.filename = filedialog.askopenfilename(initialdir="", title="Select the MRS dat file", filetypes=(("dat files","*.dat"),("all files","*.*")))
        datPath = root.filename
        root.filename = filedialog.askdirectory(initialdir="", title="Select output directory")
        outputPath = str(time.time())+'-'+structurePathParent

    else:
        raise WrongNumberOfArguments("Wrong number of arguments!")

    # if Philips, pick one implementation, if siemens, pick another
    struct_temp = "struct/temp/"
    shutil.rmtree(struct_temp)
    if not os.path.exists(struct_temp):
        os.makedirs(struct_temp)
    if not os.path.exists(outputPath):
        os.makedirs(outputPath)
    if not os.path.exists(struct_temp+"mat/"):
        os.makedirs(struct_temp+"mat/")

    if re.findall(".dat",datPath):
        generateVoxelDAT = GenerateVoxelFromDATFile(structurePath, datPath, outputPath)
        generateVoxelDAT.getPositionAndRotation(struct_temp)
    elif re.findall(".SPAR", datPath):
        generateVoxelDAT = GenerateVoxelFromSPARFile(structurePath, datPath, outputPath)
        generateVoxelDAT.getPositionAndRotation(struct_temp)

getUserData()