#!/usr/bin/env python
import sys
import os
import siteUtils
import metUtils
from flatnessTask import flatnessTask

#os.system("rsync -r LSSTuser@172.17.100.2:jobHarness/jh_stage/e2v-CCD/An-e2v-CCD/\* /home/LSSTuser/jobHarness/jh_stage/e2v-CCD/")

raft_id = siteUtils.getUnitId()
ccd_vendor = siteUtils.getCcdVendor()

# Find the TS5 metrology scan data
direcs = siteUtils.dependency_glob('*',
                                   jobname=siteUtils.getProcessName('TS5_Metrology_Upload'),description='TS5 metrology scan:')
Look up the files that are relevant for this run
print "direcs:"
print direcs
print "------------------------------"

dimdir = ""
for line in direcs :
    if "Metrology_Upload" in line :
        dimdir = line

print 'TS5 metrology directory = %s' % dimdir


flat_file = ""

for root, dirs, flat_files in os.walk(dimdir):
    for file in flat_files:
        if file.endswith(".csv"):
             flat_file=os.path.join(root, file)

#flat_file = flat_file[0]  # siteUtils returns flat_file as a list with one member;
    # here take the first (and only) member

print "flat_file = %s" % flat_file

# The dtype below indicates the source of the data, which is always TS5
flatnessTask_delta(raft_id, flat_file, dtype='TS5', pickle_file='flatness_ts5_delta.pickle')
