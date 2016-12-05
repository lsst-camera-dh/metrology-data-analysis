#!/usr/bin/env python
import sys
import os
import siteUtils
import metUtils
from flatnessTask_delta import flatnessTask_delta
from qaPlot import qaPlot

raft_id = siteUtils.getUnitId()

# Find the TS5 metrology scan data for each of the measurement steps
acqjobnames = ['Pump_and_Room_Temp_Measurement', 'Cooling_Measurement-1',
               'Cooling_Measurement-2', 'Cold_Measurement',
               'Room_Temp_Measurement_After_Thermal_Cycle']

files = []
for acqjobname in acqjobnames: 
    files.append(siteUtils.dependency_glob('*.csv',
                                           jobname=siteUtils.getProcessName(acqjobname),
                                           description='')[0])

# The dtype below indicates the source of the data, which is always TS5
flatnessTask_delta(raft_id, files, dtype='TS5', pickle_file='flatness_ts5_delta.pickle')

# Make the QA plot
qaPlot(files, '%s_flatness_qa_plot.png' % raft_id, title='QA Plot: %s' % raft_id)
