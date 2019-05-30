from fsl.wrappers.wrapperutils import fslwrapper, applyArgStyle, SHOW_IF_TRUE

@fslwrapper
def fslInfo(input):
    return ['fslinfo', input]


@fslwrapper
def fslValue(structureFile, index):
    return ['fslval', structureFile, " sto_xyz:" + str(index)]


@fslwrapper
def fslMathsWithROI(structfile, VOXStandardUnit, tempDirectory):
    return ['fslmaths', structfile, '-mul', '0', '-add', '1', '-roi', '0', str(VOXStandardUnit[0]), '0',
            str(VOXStandardUnit[1]), '0', str(VOXStandardUnit[2]), '0', '1', tempDirectory + "_vox_start"]

@fslwrapper
def fslEyes(structfile, voxel):
    return ['fsleyes', structfile, voxel]

@fslwrapper
def fslStats(inputFile, voxel, **kwargs):
    cmd  = ['fslstats', inputFile, "-k", voxel, "-m"]
    return cmd + applyArgStyle('-',valmap={"v" : SHOW_IF_TRUE}, **kwargs)


