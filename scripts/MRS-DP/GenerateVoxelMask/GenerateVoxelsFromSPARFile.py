import shutil, os
import re
import numpy
from fsl.wrappers import fslmaths
from GenerateVoxelMask.GenerateVoxelMaskInterface import GenerateVoxelMaskInterface


class GenerateVoxelFromSPARFile(GenerateVoxelMaskInterface):

    def __init__(self, structFile, datFile, outputPath):
        # Expected coordiante space is (X,Y,Z) == (LR,AP,CC)
        self.structfile = structFile
        self.datFile = datFile
        self.outputPath = outputPath
        self.POS = [0] * 3
        self.VOX = [0] * 3
        self.ZED = [0] * 3
        self.VST = [0] * 3
        self.ROT = 0
        self.ROW = [0] * 3
        self.COL = [0] * 3
        self.singleVoxel = 0;

        self.CSFValues = [0] * 3
        self.whiteMatter = [0] * 3
        self.greyMatter = [0] * 3

    def getPositionAndRotation(self, tempPath):
        angulationValues = [0] * 3
        xStepSize = 0.0
        yStepSize = 0.0
        xPoints = 0.0
        yPoints = 0.0
        with open(self.datFile, "rb") as file:
            for line in file:
                try:
                    decodedLine = line.decode("utf-8").strip()
                    # position
                    if re.findall("lr_off_center :", decodedLine):
                        self.POS[0] = float(decodedLine.split(':')[1])
                    elif re.findall("ap_off_center :", decodedLine):
                        self.POS[1] = float(decodedLine.split(':')[1])
                    elif re.findall("cc_off_center :", decodedLine):
                        self.POS[2] = float(decodedLine.split(':')[1])

                    # size
                    elif re.findall("lr_size :", decodedLine):
                        self.VOX[0] = float(decodedLine.split(':')[1])
                    elif re.findall("ap_size :", decodedLine):
                        self.VOX[1] = float(decodedLine.split(':')[1])
                    elif re.findall("cc_size :", decodedLine):
                        self.VOX[2] = float(decodedLine.split(':')[1])
                    elif re.findall("dim3_step :", decodedLine):
                        yStepSize = float(decodedLine.split(':')[1])
                    elif re.findall("dim2_step :", decodedLine):
                        xStepSize = float(decodedLine.split(':')[1])
                    elif re.findall("dim3_pnts :", decodedLine):
                        yPoints = float(decodedLine.split(':')[1])
                    elif re.findall("dim2_pnts :", decodedLine):
                        xPoints = float(decodedLine.split(':')[1])

                    # normal vector to thickness axis
                    # AP PLANE (Y,Z plane)
                    elif re.findall("lr_angulation :", decodedLine):
                        angulationValues[0] = float(decodedLine.split(':')[1])
                    # Coronal PLANE (X,Z plane)
                    elif re.findall("ap_angulation :", decodedLine):
                        angulationValues[1] = float(decodedLine.split(':')[1])
                    # Transverse PLANE (X,Y plane)
                    elif re.findall("cc_angulation :", decodedLine):
                        angulationValues[2] = float(decodedLine.split(':')[1])
                        # rotation about thickness
                        self.ROT = float(decodedLine.split(':')[1])

                    elif re.findall("rows :", decodedLine):
                        self.singleVoxel = True if float(decodedLine.split(':')[1]) == 1 else False

                except:
                    continue
        angulationValuesRadians = numpy.deg2rad(angulationValues)
        rotationValueRadians = numpy.deg2rad(self.ROT)
        # #Is the lareg FOV even or odd
        xEven = False
        yEven = False



        # # size of small voxels store in self.VOX
        originalVoxelSize = self.VOX[:]
        self.VOX[0] =  (xStepSize * 10)
        self.VOX[1] =  (yStepSize * 10)
        originalVoxelPosition = self.POS[:]
        originalOutputPath = self.outputPath

        self.ZED[0] = numpy.sin(angulationValuesRadians[1])
        self.ZED[1] = - (numpy.sin(angulationValuesRadians[0]) * numpy.cos(angulationValuesRadians[1]))
        self.ZED[2] = numpy.cos(angulationValuesRadians[0]) * numpy.cos(angulationValuesRadians[1])
        self.tempPath = tempPath

        numberOfVoxelsX = numpy.ceil(originalVoxelSize[0] / int(self.VOX[0]))
        numberOfVoxelsY = numpy.ceil(originalVoxelSize[1] / int(self.VOX[1]))
        tempPos0 = list()
        tempPos1 = list()

        if self.singleVoxel is True:
            self.VOX = originalVoxelSize[:]
            self.ROT = rotationValueRadians
            self.outputPath = originalOutputPath + "singleVoxel"
            self.convertXFM()
            self.getVoxeContents(True)
            return;

        rotationMatrixX = numpy.array([
            [1, 0, 0],
            [0, numpy.cos(angulationValuesRadians[0]), -numpy.sin(angulationValuesRadians[0])],
            [0, numpy.sin(angulationValuesRadians[0]), numpy.cos(angulationValuesRadians[0])]
        ])

        rotationMatrixY = numpy.array([
            [numpy.cos(angulationValuesRadians[1]), 0, numpy.sin(angulationValuesRadians[1])],
            [0, 1, 0],
            [-numpy.sin(angulationValuesRadians[1]), 0, numpy.cos(angulationValuesRadians[1])]
        ])

        rotationMatrixZ = numpy.array([
            [numpy.cos(-angulationValuesRadians[2]), -numpy.sin(-angulationValuesRadians[2]), 0],
            [numpy.sin(-angulationValuesRadians[2]), numpy.cos(-angulationValuesRadians[2]), 0],
            [0, 0, 1]
        ])

        voxGreyMatter = False
        voxWhiteMatter = False
        voxCSF = False
        tissueTypeFile = open("TissueTypesForEachVoxel.txt","w+");
        tissueTypeFile.write("\n (0,0) is at the corner of (L,P)"
                             "\n (0,n) is at the corner of (A,L) "
                             "\n (m,0) is at the corner of (R,P)"
                             "\n (m,n) is at the corner of (A,R)"
                             "\n---------------------\n\n")

        if numberOfVoxelsX % 2 == 0:
            xEven = True
        if numberOfVoxelsY % 2 == 0:
            yEven = True

        for i in range(0, int(numberOfVoxelsX)):
            for j in range(0, int(numberOfVoxelsY)):
                # if i == 0 or i == 7:
                #     if j== 0 or j ==7:
                xDisplacement = xStepSize * 10
                yDisplacement = yStepSize * 10

                # TODO: Find out why we need the -displacement/2 even for the odd number of voxels case
                if xEven:
                    self.POS[0] =  originalVoxelPosition[0] + ((numberOfVoxelsX * xDisplacement)/ 2 - xDisplacement/2) - i * xDisplacement
                elif not xEven:
                    self.POS[0] =  originalVoxelPosition[0] + ((numberOfVoxelsX * xDisplacement)/ 2 - xDisplacement/2) - i * xDisplacement
                self.POS[0] = self.POS[0] - originalVoxelPosition[0]

                if yEven:
                    self.POS[1] =  originalVoxelPosition[1] + ((numberOfVoxelsY * yDisplacement)/ 2 - yDisplacement/2) - j* yDisplacement
                elif not yEven:
                    self.POS[1] =  originalVoxelPosition[1] + ((numberOfVoxelsY * yDisplacement)/ 2 - yDisplacement/2) - j* yDisplacement
                self.POS[1] = self.POS[1] - originalVoxelPosition[1]

                self.POS[2] = originalVoxelPosition[2] - originalVoxelPosition[2]

                centreOfVoxelPosition = numpy.array(self.POS)
                self.POS = rotationMatrixZ.dot(centreOfVoxelPosition).tolist()
                centreOfVoxelPosition = numpy.array(self.POS)
                self.POS = rotationMatrixY.dot(centreOfVoxelPosition).tolist()
                centreOfVoxelPosition = numpy.array(self.POS)
                self.POS = rotationMatrixX.dot(centreOfVoxelPosition).tolist()

                self.POS[0] = self.POS[0] + originalVoxelPosition[0]
                self.POS[1] = self.POS[1] + originalVoxelPosition[1]
                self.POS[2] = self.POS[2] + originalVoxelPosition[2]

                tempPos1.append(self.POS[1])
                print("----------------\n\n _ "+ str(i) + "_" + str(j) + "\n\n")
                self.outputPath = originalOutputPath + "_" + str(i) + "_" + str(j)
                self.ROT = rotationValueRadians
                self.convertXFM()
                continue;
                values = self.getVoxeContents((i==0 and j==0))
                greyMatter = values[0]
                whiteMatter = values[1]
                CSF = values[2]
                totalVolume = values[3]


                tissueTypeFile.writelines(["\tVoxels at position (" + str(i) + "," + str(j) + ")",
                                           "\nGrey Matter Percentage: " + greyMatter,
                                           "\nWhite Matter Percentage: " + whiteMatter,
                                           "\nCSF Percentage: " + CSF,
                                           "\nTotal Volume: " + totalVolume,
                                           "\n\n"])

                if i == 0 and j == 0:
                    if os.path.exists(originalOutputPath + 'GreyMatterVoxel'):
                        shutil.rmtree(originalOutputPath + 'GreyMatterVoxel')

                    if os.path.exists(originalOutputPath + 'WhiteMatterVoxel'):
                        shutil.rmtree(originalOutputPath + 'WhiteMatterVoxel')

                    if os.path.exists(originalOutputPath + 'CSFVoxel'):
                        shutil.rmtree(originalOutputPath + 'CSFVoxel')

                    os.mkdir(originalOutputPath + 'GreyMatterVoxel')
                    os.mkdir(originalOutputPath + 'WhiteMatterVoxel')
                    os.mkdir(originalOutputPath + 'CSFVoxel')

                    shutil.copy2(self.outputPath + "_vox_final.nii.gz", self.outputPath + "copy_vox_final.nii.gz")
                    shutil.move(self.outputPath + "copy_vox_final.nii.gz", originalOutputPath + 'GreyMatterVoxel/constructedGreyMatterVoxel.nii.gz')

                    shutil.copy2(self.outputPath + "_vox_final.nii.gz", self.outputPath + "copy_vox_final.nii.gz")
                    shutil.move(self.outputPath + "copy_vox_final.nii.gz", originalOutputPath + 'WhiteMatterVoxel/constructedWhiteMatterVoxel.nii.gz')

                    shutil.copy2(self.outputPath + "_vox_final.nii.gz", self.outputPath + "copy_vox_final.nii.gz")
                    shutil.move(self.outputPath + "copy_vox_final.nii.gz", originalOutputPath + 'CSFVoxel/constructedCSFVoxel.nii.gz')

                    voxGreyMatter = fslmaths(originalOutputPath + 'GreyMatterVoxel/constructedGreyMatterVoxel.nii.gz')
                    voxWhiteMatter = fslmaths(originalOutputPath + 'WhiteMatterVoxel/constructedWhiteMatterVoxel.nii.gz')
                    voxCSF = fslmaths(originalOutputPath + 'CSFVoxel/constructedCSFVoxel.nii.gz')

                    voxGreyMatter.mul(greyMatter)
                    voxWhiteMatter.mul(whiteMatter)
                    voxCSF.mul(CSF)

                    voxGreyMatter.run(originalOutputPath + 'GreyMatterVoxel/constructedGreyMatterVoxel.nii.gz')
                    voxWhiteMatter.run(originalOutputPath + 'WhiteMatterVoxel/constructedWhiteMatterVoxel.nii.gz')
                    voxCSF.run(originalOutputPath + 'CSFVoxel/constructedCSFVoxel.nii.gz')
                    continue;

                shutil.copy2(self.outputPath + "_vox_final.nii.gz", originalOutputPath + 'GreyMatterVoxel')
                shutil.copy2(self.outputPath + "_vox_final.nii.gz", originalOutputPath + 'WhiteMatterVoxel')
                shutil.copy2(self.outputPath + "_vox_final.nii.gz", originalOutputPath + 'CSFVoxel')

                currentVoxGreyMatter = fslmaths(originalOutputPath + 'GreyMatterVoxel/' + "_" + str(i) + "_" + str(j) + "_vox_final.nii.gz")
                currentVoxWhiteMatter = fslmaths(originalOutputPath + 'WhiteMatterVoxel/' + "_" + str(i) + "_" + str(j) + "_vox_final.nii.gz")
                currentVoxCSF = fslmaths(originalOutputPath + 'CSFVoxel/' + "_" + str(i) + "_" + str(j) + "_vox_final.nii.gz")

                currentVoxGreyMatter.mul(greyMatter)
                currentVoxWhiteMatter.mul(whiteMatter)
                currentVoxCSF.mul(CSF)

                currentVoxGreyMatter.run(originalOutputPath + 'GreyMatterVoxel/' + "_" + str(i) + "_" + str(j) + "current_vox_final.nii.gz")
                currentVoxWhiteMatter.run(originalOutputPath + 'WhiteMatterVoxel/' + "_" + str(i) + "_" + str(j) + "current_vox_final.nii.gz")
                currentVoxCSF.run(originalOutputPath + 'CSFVoxel/' + "_" + str(i) + "_" + str(j) + "current_vox_final.nii.gz")

                voxGreyMatter = fslmaths(originalOutputPath + 'GreyMatterVoxel/constructedGreyMatterVoxel.nii.gz')
                voxWhiteMatter = fslmaths(originalOutputPath + 'WhiteMatterVoxel/constructedWhiteMatterVoxel.nii.gz')
                voxCSF = fslmaths(originalOutputPath + 'CSFVoxel/constructedCSFVoxel.nii.gz')

                voxGreyMatter.add(originalOutputPath + 'GreyMatterVoxel/' + "_" + str(i) + "_" + str(j) + "current_vox_final.nii.gz")
                voxWhiteMatter.add(originalOutputPath + 'WhiteMatterVoxel/' + "_" + str(i) + "_" + str(j) + "current_vox_final.nii.gz")
                voxCSF.add(originalOutputPath + 'CSFVoxel/' + "_" + str(i) + "_" + str(j) + "current_vox_final.nii.gz")

                voxGreyMatter.run(originalOutputPath + 'GreyMatterVoxel/constructedGreyMatterVoxel.nii.gz')
                voxWhiteMatter.run(originalOutputPath + 'WhiteMatterVoxel/constructedWhiteMatterVoxel.nii.gz')
                voxCSF.run(originalOutputPath + 'CSFVoxel/constructedCSFVoxel.nii.gz')


        tissueTypeFile.close();
        print(tempPos0)
        print(tempPos1)
        print(xEven)
        print(yEven)
