#!/usr/bin/env python
import sys
import os
import siteUtils
import metUtils
from flatnessTask import flatnessTask

raft_id = siteUtils.getUnitId()

# Find the TS5 metrology scan data by constructing the name of the data-taking step
acqjobname = siteUtils.getJobName().replace('_Analysis', '')
if ("Room_Temp_Measurement" in acqjobname and not "After" in acqjobname):
    acqjobname = "Pump_and_" + acqjobname

print('flatness_ts5:')
print(acqjobname)
print(siteUtils.getProcessName(acqjobname))
print('----')

# siteUtils returns a list with one member;
# here take the first (and only) member
infile = siteUtils.dependency_glob('*.csv',
                                   jobname=siteUtils.getProcessName(acqjobname),
                                   description='')[0]
print "infile = %s" % infile

flatnessTask(raft_id, infile, dtype='TS5', pickle_file='flatness_ts5.pickle')
