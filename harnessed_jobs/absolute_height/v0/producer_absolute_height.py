#!/usr/bin/env python
import sys
import siteUtils
import metUtils
from absoluteHeightTask import absoluteHeightTask

sensor_id = siteUtils.getUnitId()
ccd_vendor = siteUtils.getCcdVendor()

# Find the OGP metrology scan data
met_file = siteUtils.dependency_glob('*_AbsHeight*.DAT',
		jobname=siteUtils.getProcessName('OGP_Dimensional_Metrology_Upload'),description='OGP Absolute Height scan:')

met_file = met_file[0]  # siteUtils returns met_file as a list with one member;
			# here take the first (and only) member

# Below dtype is always 'OGP', i.e., for this task the source of the data
# is always the OGP scanner at BNL
absoluteHeightTask(sensor_id, met_file, dtype='OGP',
                   pickle_file='abs_height.pickle')
