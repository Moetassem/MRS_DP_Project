import re
from fsl.wrappers.misc import fslreorient2std
from GenerateVoxelMask.GenerateVoxelMaskInterface import GenerateVoxelMaskInterface


class GenerateVoxelFromDATFile(GenerateVoxelMaskInterface):

    def __init__(self, structFile, datFile, outputPath):
        # Expected coordiante space is (X,Y,Z) == (LR,AP,CC)
        fslreorient2std(structFile, outputPath + "structural_image_in_std.nii.gz")
        self.structfile = outputPath + "structural_image_in_std.nii.gz"
        self.datFile = datFile
        self.outputPath = outputPath
        self.POS = [0] * 3
        self.VOX = [0] * 3
        self.ZED = [0] * 3
        self.VST = [0] *3
        self.ROT = 0
        self.ROW = [0] *3
        self.COL = [0] *3


    def getPositionAndRotation(self, tempPath):
        with open(self.datFile, "rb") as file:
            for line in file:
                try:
                    decodedLine = line.decode("utf-8").strip()
                    # position
                    if re.findall("sSpecPara.sVoI.sPosition.dSag.*=", decodedLine):
                        self.POS[0] = float(decodedLine.split('=')[1])
                    elif re.findall("sSpecPara.sVoI.sPosition.dCor.*=", decodedLine):
                        self.POS[1] = float(decodedLine.split('=')[1])
                    elif re.findall("sSpecPara.sVoI.sPosition.dTra.*=", decodedLine):
                        self.POS[2] = float(decodedLine.split('=')[1])

                    #size
                    elif re.findall("sSpecPara.sVoI.dReadoutFOV.*=", decodedLine):
                        self.VOX[0] = float(decodedLine.split('=')[1])
                    elif re.findall("sSpecPara.sVoI.dPhaseFOV.*=", decodedLine):
                        self.VOX[1] = float(decodedLine.split('=')[1])
                    elif re.findall("sSpecPara.sVoI.dThickness.*=", decodedLine):
                        self.VOX[2] = float(decodedLine.split('=')[1])

                    #normal vector to thickness axis
                    elif re.findall("sSpecPara.sVoI.sNormal.dSag.*=", decodedLine):
                        self.ZED[0] = float(decodedLine.split('=')[1])
                    elif re.findall("sSpecPara.sVoI.sNormal.dCor.*=", decodedLine):
                        self.ZED[1] = float(decodedLine.split('=')[1])
                    elif re.findall("sSpecPara.sVoI.sNormal.dTra.*=", decodedLine):
                        self.ZED[2] = float(decodedLine.split('=')[1])

                    #rotation about thickness
                    elif re.findall("sSpecPara.sVoI.dInPlaneRot.*=", decodedLine):
                        self.ROT = float(decodedLine.split('=')[1])
                except:
                    continue
        self.tempPath = tempPath
        self.outputPath = self.outputPath + "_0_0"
        self.convertXFM()
        self.getVoxeContents(False)