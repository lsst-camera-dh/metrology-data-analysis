#!/usr/bin/env python
import sys
import os
import siteUtils
import metUtils
from flatnessTask import flatnessTask

os.system("rsync -r LSSTuser@172.17.100.2:jobHarness/jh_stage/e2v-CCD/An-e2v-CCD/\* /home/LSSTuser/jobHarness/jh_stage/e2v-CCD/")

sensor_id = siteUtils.getUnitId()
ccd_vendor = siteUtils.getCcdVendor()

# Find the OGP metrology scan data
#flat_file = siteUtils.dependency_glob('*/*/*_AbsHeight*.DAT',
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


flat_file = ""

for root, dirs, flat_files in os.walk(dimdir):
    for file in flat_files:
        if file.endswith(".DAT"):
             flat_file=os.path.join(root, file)

#flat_file = flat_file[0]  # siteUtils returns flat_file as a list with one member;
    # here take the first (and only) member

print "flat_file = %s" % flat_file

# The dtype below indicates the source of the data, which is always OGP
# for sensors measured at BNL
flatnessTask(sensor_id, flat_file, dtype='OGP', pickle_file='flatness.pickle')
