#!/usr/bin/env python
import sys
import siteUtils
import metUtils
from absoluteHeightTask import absoluteHeightTask

sensor_id = siteUtils.getUnitId()
ccd_vendor = siteUtils.getCcdVendor()

if ccd_vendor == 'e2v':
    print "Absolute height analysis cannot not be performed with e2v vendor data.  Exiting producer script."
    sys.exit(0)

#patterns = dict(e2v='*CT100*.csv', ITL='*.txt')

#
# Find the vendor metrology scan data from the Data Catalog.  Sort the
# results in case of multiple vendor ingests so that we can use the
# most recent one based on SR-RCV-1 job id, assuming the filenames
# are the same for each delivery.
#
#met_file = metUtils.get_met_scan_data(sensor_id, patterns[ccd_vendor],
#                                      sort=True)[-1]
# Find the metrology scan data
met_file = siteUtils.dependency_glob('*_AbsZ_*.DAT',
		jobname=situUtils.getProcessName('OGP_Absolute_Height_Scan_Upload'),description='OGP files:')

absoluteHeightTask(sensor_id, met_file, dtype=ccd_vendor,
                   pickle_file='abs_height.pickle')
