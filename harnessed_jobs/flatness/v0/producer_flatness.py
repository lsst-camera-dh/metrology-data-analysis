#!/usr/bin/env python
import siteUtils
import metUtils
from flatnessTask import flatnessTask

sensor_id = siteUtils.getUnitId()
ccd_vendor = siteUtils.getCcdVendor()

#patterns = dict(e2v='*CT100*.csv', ITL='*.txt')

#
# Find the vendor metrology scan data from the Data Catalog.  Sort the
# results in case of multiple vendor ingests so that we can use the
# most recent one based on SR-RCV-1 job id, assuming the filenames
# are the same for each delivery.
#
#met_file = metUtils.get_met_scan_data(sensor_id, patterns[ccd_vendor],
#                                      sort=True)[-1]
# Find the vendor metrology scan data
met_file = siteUtils.dependency_glob('*_Flat_*.DAT',jobname=siteUtils.getProcessName('OGP_Edge_Flatness_Scan_Upload'),description='OGP Flatnes scan:')

flatnessTask(sensor_id, met_file, dtype=ccd_vendor,
             pickle_file='flatness.pickle')
