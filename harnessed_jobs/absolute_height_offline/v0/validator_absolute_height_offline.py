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
    flatnesshalfband_95 = (z_quantile_0975 - z_quantile_0025)/2.

    zvalues, quantiles = [], []
    for key in sensorData.quantiles:
        quantiles.append(float(key))
        zvalues.append(sensorData.quantiles[key])

    zvalues.sort()
    quantiles.sort()

    znom = 12.992  # for ITL
    zbounds = (-0.009, 0.009)  # from CCD-030
    quant_low = np.interp(znom - zbounds[0], zvalues, quantiles)
    quant_high = np.interp(znom - zbounds[1], zvalues, quantiles)
    frac_outside = 1. - (quant_high - quant_low)

    results.append(lcatr.schema.valid(lcatr.schema.get('sensor_abs_height'),
                                      z_median_m_13=z_median_m_13,
                                      z_quantile_0025=z_quantile_0025,
                                      z_quantile_0975=z_quantile_0975,
                                      frac_outside=frac_outside,
                                      flatnesshalfband_95=flatnesshalfband_95))

results.extend(siteUtils.packageVersions())

lcatr.schema.write_file(results)
lcatr.schema.validate_file()
