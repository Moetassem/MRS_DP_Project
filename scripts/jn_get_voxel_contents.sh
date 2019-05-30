#!/usr/bin/env
# script to calculate constituents in voxel
# derived from one received from Charlie Stagg
# mjt 2007-03-22
# changes to do all three components not just gm
# Matthew Taylor 2007-08-16
# some changes by Jamie Near as well 03/08/2010
#
# version 2 - works with siemens files now
# need to make work with mask image, not .voxel file
# 
# Matt 2008-04-08
# Jamie 2010-08-03

STRUCFILE=$1
VOXIMG=$2


DIR=./struc
#STRUCFILE=${HOME}/scratch/${STUDYID}/${INDIV}/images/${INDIV}/*anatomy*nii.gz
#VOXIMG=${DIR}/${INDIV}_${SUBDIR}_anat_mask.nii.gz
BRAINDIR=${DIR}/brains
BRAINIMG=${BRAINDIR}/brain
OUTFILE=${DIR}/voxel_contents.txt

# Do Brain Extraction
mkdir -p ${BRAINDIR}
echo Brain Extraction in progress, ${INDIV}
bet ${STRUCFILE} ${BRAINIMG}

# partial volume segmentation
echo partial volume segmentation in progress, ${INDIV}
fast  -t 1 -n 3 ${BRAINIMG}

grey_percent=`fslstats ${BRAINIMG}_pve_1 -k ${VOXIMG} -m -v | cut -d ' ' -f1`
total_volume=`fslstats ${BRAINIMG}_pve_1 -k ${VOXIMG} -m -v | cut -d ' ' -f3`
volume_of_grey=`echo ${grey_percent}*${total_volume} | bc` 
white_percent=`fslstats ${BRAINIMG}_pve_2 -k ${VOXIMG} -m `
csf_percent=`fslstats ${BRAINIMG}_pve_0 -k ${VOXIMG} -m`

echo grey_percent = ${grey_percent}
echo total_vol = ${total_volume}
echo volume of grey = ${volume_of_grey}
echo white_percent = ${white_percent}
echo csf_percent = ${csf_percent}
echo ${INDIV} ${3} ${grey_percent} ${white_percent} ${csf_percent} ${total_volume} >> ${OUTFILE}
play --no-show-progress --null --channels 1 synth 1 sine 440