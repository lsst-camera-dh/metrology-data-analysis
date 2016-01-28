#!/usr/bin/env python
import siteUtils
import metUtils
from flatnessTask import flatnessTask

sensor_id = siteUtils.getUnitId()
ccd_vendor = siteUtils.getCcdVendor()

# Find the OGP metrology scan data
met_file = siteUtils.dependency_glob('*_Flatness*.DAT',jobname=siteUtils.getProcessName('OGP_Dimensional_Metrology_Upload'),description='OGP Flatness scan:')

met_file = met_file[0]  # siteUtils returns met_file as a list with one member;
                        # here take the first (and only) member

# The dtype below indicates the source of the data, which is always OGP
# for sensors measured at BNL
flatnessTask(sensor_id, met_file, dtype='OGP', pickle_file='flatness.pickle')
