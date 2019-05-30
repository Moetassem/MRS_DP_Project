import numpy

import re
import os
import numpy
from shutil import copy2
from fsl.wrappers.flirt import concatxfm, invxfm
from fsl.data.image import Image
from fsl.wrappers.bet import bet
from fsl.wrappers.fast import fast
from Utils.FSLWrappers import *
from nipype.interfaces.c3 import C3dAffineTool
from ants.registration import apply_transforms
from ants import image_read, image_write


class GenerateVoxelMaskInterface:

    def getPositionAndRotation(self):
        raise NotImplementedError("Implement Me!")

    def convertXFM(self):
        print("Starting covert_xfm from fslpy")
        print("-------------------")

        self.negativeZED = [x * (-1) for x in self.ZED]

        matrixSize = 4

        rotationMatrix = numpy.zeros((matrixSize, matrixSize))
        columnStart = numpy.zeros((matrixSize, matrixSize))

        rotationMatrix[0][0] = (numpy.cos(self.ROT)) + numpy.square(self.negativeZED[0]) * (1 - numpy.cos(self.ROT))
        rotationMatrix[0][1] = (self.negativeZED[0] * self.negativeZED[1] * (1 - numpy.cos(self.ROT))) - (
                self.negativeZED[2] * numpy.sin(self.ROT))
        rotationMatrix[0][2] = (self.negativeZED[0] * self.negativeZED[2] * (1 - numpy.cos(self.ROT))) + (
                self.negativeZED[1] * numpy.sin(self.ROT))
        rotationMatrix[0][3] = 0

        rotationMatrix[1][0] = (self.negativeZED[1] * self.negativeZED[0] * (1 - numpy.cos(self.ROT))) + (
                self.negativeZED[2] * numpy.sin(self.ROT))
        rotationMatrix[1][1] = (numpy.cos(self.ROT)) + numpy.square(self.negativeZED[1]) * (1 - numpy.cos(self.ROT))
        rotationMatrix[1][2] = (self.negativeZED[1] * self.negativeZED[2] * (1 - numpy.cos(self.ROT))) - (
                self.negativeZED[0] * numpy.sin(self.ROT))
        rotationMatrix[1][3] = 0

        rotationMatrix[2][0] = (self.negativeZED[2] * self.negativeZED[0] * (1 - numpy.cos(self.ROT))) - (
                self.negativeZED[1] * numpy.sin(self.ROT))
        rotationMatrix[2][1] = (self.negativeZED[2] * self.negativeZED[1] * (1 - numpy.cos(self.ROT))) + (
                self.negativeZED[0] * numpy.sin(self.ROT))
        rotationMatrix[2][2] = (numpy.cos(self.ROT)) + numpy.square(self.negativeZED[0]) * (1 - numpy.cos(self.ROT))
        rotationMatrix[2][3] = 0

        rotationMatrix[3][0] = 0
        rotationMatrix[3][1] = 0
        rotationMatrix[3][2] = 0
        rotationMatrix[3][3] = 1


        columnStart[2][0] = 1 / (numpy.sqrt(numpy.square(-1 * self.negativeZED[2] / self.negativeZED[1]) + 1))
        columnStart[1][0] = -1.0 * columnStart[2][0] * self.negativeZED[2] / self.negativeZED[1]

        columnStart[3][0] = 0
        columnStart[3][1] = 0
        columnStart[3][2] = 0
        columnStart[3][3] = 1

        numpy.savetxt(self.tempPath + "mat/mat_Raxisangle", rotationMatrix, delimiter=" ", fmt='%f')
        numpy.savetxt(self.tempPath + "mat/mat_colStart", columnStart, delimiter=" ", fmt='%f')
        concatxfm(self.tempPath + "mat/mat_colStart", self.tempPath + "mat/mat_Raxisangle",
                  self.tempPath + "mat/mat_colVector")

        print("got the mat_colVector.txt")
        print("-------------------")

        columnValues = [0] * 3
        with open(self.tempPath + "mat/mat_colVector", "r") as columnVectorFile:
            for i in range(3):
                columnValues[i] = float(columnVectorFile.readline().split(" ")[0])

        rowVector = [0] * 3
        rowVector[0] = columnValues[1] * self.negativeZED[2] - columnValues[2] * self.negativeZED[1]
        rowVector[1] = columnValues[2] * self.negativeZED[0] - columnValues[0] * self.negativeZED[2]
        rowVector[2] = columnValues[0] * self.negativeZED[1] - columnValues[1] * self.negativeZED[0]

        self.negativeZED[2] = self.negativeZED[2] * -1

        print("POS:" + str(self.POS) + '\n' +
              "VOX:" + str(self.VOX) + '\n' +
              "ROW:" + str(rowVector) + '\n' +
              "COL:" + str(columnValues) + '\n' +
              "ZED:" + str(self.negativeZED))

        self.ROW = rowVector
        self.COL = columnValues

        print("-------------------")
        print("-------------------")
        self.getVoxelInformation()

    def getVoxelInformation(self):
        print("Getting voxel dimension from the structural image")

        self.VST = [0] * 3

        FSLInfoOutput = fslInfo(self.structfile)
        FSLInfoOutputLines = FSLInfoOutput[0].split("\n")
        for line in FSLInfoOutputLines:
            if re.findall("pixdim1", line):
                self.VST[0] = float(line.replace(" ", "").split("pixdim1")[1])
            if re.findall("pixdim2", line):
                self.VST[1] = float(line.replace(" ", "").split("pixdim2")[1])
            if re.findall("pixdim3", line):
                self.VST[2] = float(line.replace(" ", "").split("pixdim3")[1])

        self.POS[0] = self.POS[0] * -1
        self.POS[1] = self.POS[1] * -1
        self.ROW[0] = self.ROW[0] * -1
        self.ROW[1] = self.ROW[1] * -1
        self.COL[0] = self.COL[0] * -1
        self.COL[1] = self.COL[1] * -1

        fslValueOutput = []
        for i in range(4):
            temp = list(fslValue(self.structfile, str(i + 1)))[0]
            temp = temp.replace("\n", "").strip().split(" ")
            fslValueOutput.append(list(map(float, temp)))
        numpy.savetxt(self.tempPath + "mat/mat_st2sc", numpy.array(fslValueOutput), fmt="%f")

        self.line265()

    def line265(self):
        structuralFSLImage = Image(self.structfile)
        isNeurologicalCoordinates = structuralFSLImage.isNeurological()
        if isNeurologicalCoordinates:
            print("Is neurological coordinates")
            # TODO: Ticket #25
        else:
            print("Is not neurological coordiantes")
            with open(self.tempPath + "mat/mat_nvox2fmm", "w+") as file:
                file.writelines(str(self.VST[0]) + " 0 0 0\n")
        with open(self.tempPath + "mat/mat_nvox2fmm", "a") as file:
            file.writelines("0 " + str(self.VST[1]) + " 0 0\n"
                            + "0 0 " + str(self.VST[2]) + " 0\n"
                            + "0 0 0 1")

        invxfm(self.tempPath + "mat/mat_nvox2fmm", self.tempPath + "mat/mat_fmm2nvox")

        concatxfm(self.tempPath + "mat/mat_fmm2nvox", self.tempPath + "mat/mat_st2sc", self.tempPath + "mat/mat_st2sc")
        invxfm(self.tempPath + "mat/mat_st2sc", self.tempPath + "mat/mat_sc2st")

        self.VOXStructuralUnits = [0] * 3
        self.VOXStructuralUnits[0] = self.VOX[0] / self.VST[0]
        self.VOXStructuralUnits[1] = self.VOX[1] / self.VST[1]
        self.VOXStructuralUnits[2] = self.VOX[2] / self.VST[2]

        fslMathsWithROI(self.structfile, self.VOXStructuralUnits, self.tempPath)

        with open(self.tempPath + "mat/mat_sp2sc_R", "w") as file:
            file.writelines(str(self.ROW[0]) + " " + str(self.COL[0]) + " " + str(self.negativeZED[0]) + " 0\n" +
                            str(self.ROW[1]) + " " + str(self.COL[1]) + " " + str(self.negativeZED[1]) + " 0\n" +
                            str(self.ROW[2]) + " " + str(self.COL[2]) + " " + str(self.negativeZED[2]) + " 0\n" +
                            "0 0 0 1")

        with open(self.tempPath + "mat/mat_sc_Tc", "w") as file:
            file.writelines("0 0 0 " + str(self.POS[0]) + "\n" +
                            "0 0 0 " + str(self.POS[1]) + "\n" +
                            "0 0 0 " + str(self.POS[2]) + "\n" +
                            "0 0 0 0")

        with open(self.tempPath + "mat/mat_sc_Tv", "w") as file:
            file.writelines("1 0 0 " + str(-0.5 * self.VOX[0]) + "\n" +
                            "0 1 0 " + str(-0.5 * self.VOX[1]) + "\n" +
                            "0 0 1 " + str(-0.5 * self.VOX[2]) + "\n" +
                            "0 0 0 1")

        concatxfm(self.tempPath + "mat/mat_sc_Tc", self.tempPath + "mat/mat_sc2st", self.tempPath + "mat/mat_st_Tc")

        self.TVariable = [0] * 3
        i = 0
        with open(self.tempPath + "mat/mat_st_Tc", "r") as file:
            for i in range(3):
                line = file.readline()
                self.TVariable[i] = float(line.split(" ")[6])

        with open(self.tempPath + "mat/mat_Id_st_Tc", "w") as file:
            file.writelines("1 0 0 " + str(self.TVariable[0]) + "\n" +
                            "0 1 0 " + str(self.TVariable[1]) + "\n" +
                            "0 0 1 " + str(self.TVariable[2]) + "\n" +
                            "0 0 0 1")

        concatxfm(self.tempPath + "mat/mat_sp2sc_R", self.tempPath + "mat/mat_sc2st", self.tempPath + "mat/mat_sp2st_R")
        concatxfm(self.tempPath + "mat/mat_sc_Tv", self.tempPath + "mat/mat_sp2st_R",
                  self.tempPath + "mat/mat_sp2st_Tv_R")
        concatxfm(self.tempPath + "mat/mat_sp2st_Tv_R", self.tempPath + "mat/mat_Id_st_Tc",
                  self.tempPath + "mat/mat_final")

        copy2(self.tempPath + "mat/mat_final", self.tempPath + "mat/mat_final.txt")

        affineTransformFile = open(self.tempPath + "_vox_start2final.txt", "w")
        affineTransformFile.close()
        c3 = C3dAffineTool()
        c3.inputs.source_file = self.tempPath + '_vox_start.nii.gz'
        c3.inputs.itk_transform = affineTransformFile.name
        c3.inputs.fsl2ras = True
        c3.inputs.reference_file = self.structfile
        c3.inputs.transform_file = self.tempPath + "mat/mat_final.txt"
        c3.run()

        structFileAsANTsImage = image_read(self.structfile, 3)
        voxFileAsANTsImage = image_read(self.tempPath + "_vox_start.nii.gz")
        outputFinal = apply_transforms(structFileAsANTsImage, voxFileAsANTsImage, [affineTransformFile.name])
        image_write(outputFinal, self.outputPath + "_vox_final.nii.gz")

        # fslEyes(self.structfile, self.outputPath + "_vox_final.nii.gz")
        # self.getVoxeContents()

    """
    Function that returns an array with [greyMatter, whiteMatter, CSF, Total Volume]
    """
    def getVoxeContents(self, firstRun = False):
        print("-------------")
        print("Brain extraction in progress for voxel contents")
        print("-------------")
        bet(self.structfile, self.outputPath[:-4] + "brains")
        # TODO: Fix the whole naming issue where SPAR has many voxels, but DAT only makes 1
        if firstRun is True:
            fast(self.outputPath[:-4] + "brains.nii.gz", self.outputPath[:-4] + "brains" )
        temp = fslStats(self.outputPath[:-4] + "brains_pve_1", self.outputPath + "_vox_final.nii.gz", v=True)
        greyMatterPercentage = list(temp)[0].split(" ")[0]
        whiteMatterPercentage = fslStats(self.outputPath[:-4] + "brains_pve_2", self.outputPath + "_vox_final.nii.gz")
        CSFPercentage = fslStats(self.outputPath[:-4] + "brains_pve_0", self.outputPath + "_vox_final.nii.gz")
        totalVolume = list(temp)[0].split(" ")[2]

        print("\n\n")
        print("Grey Percentage: " + greyMatterPercentage)
        print("Total Volume: " + totalVolume)
        print("White Matter Percentage: " + list(whiteMatterPercentage)[0].strip())
        print("CSF Percentage: " + list(CSFPercentage)[0].strip())
        print("Volume of Grey matter: " + str(float(greyMatterPercentage) * float(totalVolume)))
        os.system("play --no-show-progress --null --channels 1 synth 1 sine 440")
        return ([greyMatterPercentage, list(whiteMatterPercentage)[0].strip(), list(CSFPercentage)[0].strip(), totalVolume])

