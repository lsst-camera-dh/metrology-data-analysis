#!/usr/bin/env python
import sys
import os
import siteUtils
#import metUtils
from absoluteHeightTask import absoluteHeightTask

#os.system("rsync -r LSSTuser@172.17.100.2:jobHarness/jh_stage/e2v-CCD/An-e2v-CCD/\* /home/LSSTuser/jobHarness/jh_stage/e2v-CCD/")

sensor_id = siteUtils.getUnitId()
ccd_vendor = siteUtils.getCcdVendor()

# Find the OGP metrology scan data
#met_file = siteUtils.dependency_glob('*/*/*_AbsHeight*.DAT',
direcs = siteUtils.dependency_glob('*',
		jobname=siteUtils.getProcessName('OGP_Dimensional_Metrology_Upload'),description='OGP Absolute Height scan:')
print "direcs:"
print direcs
print "------------------------------"

dimdir = ""
for line in direcs :
    if "DimensionalMetrology" in line :
        dimdir = line

print "dimensional metrology directory = %s" % dimdir


met_file = ""

for root, dirs, met_files in os.walk(dimdir):
    for file in met_files:
        if file.endswith(".DAT"):
             met_file=os.path.join(root, file)

#met_file = met_file[0]  # siteUtils returns met_file as a list with one member;
			# here take the first (and only) member

print "met_file = %s" % met_file

# Below dtype is always 'OGP', i.e., for this task the source of the data
# is always the OGP scanner at BNL
absoluteHeightTask(sensor_id, met_file, dtype='OGP',
                   pickle_file='abs_height.pickle')
