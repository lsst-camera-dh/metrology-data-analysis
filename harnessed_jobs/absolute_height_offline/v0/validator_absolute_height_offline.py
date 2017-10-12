#!/usr/bin/env python
import os
import numpy as np
import lcatr.schema
import siteUtils
import metUtils
from MetrologyData import md_factory

ccd_vendor = siteUtils.getCcdVendor()

producer = 'SR-MET-05'
testtype = 'ABS_HEIGHT'
results = metUtils.aggregate_filerefs(producer, testtype)

#
# Extract numerical results from pickled MetrologyData object, if it exists.
#
pickle_file = 'abs_height.pickle'
if os.path.isfile(pickle_file):
    sensorData = md_factory.load(pickle_file)
    z_median_m_13 = np.median(sensorData.sensor.z) - 13000.
    z_quantile_0025 = sensorData.quantiles['0.025']
    z_quantile_0975 = sensorData.quantiles['0.975']

    results.append(lcatr.schema.valid(lcatr.schema.get('abs_height_sensor'),
                                      z_median_m_13=z_median_m_13,
                                      z_quantile_0025=z_quantile_0025,
                                      z_quantile_0975=z_quantile_0975,
                                      frac_outside=metUtils.frac_outside(sensorData.quantiles)))

results.extend(siteUtils.packageVersions())

lcatr.schema.write_file(results)
lcatr.schema.validate_file()
