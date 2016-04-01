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
    ZNOM = dict(ITL=12998., e2v=13000.)
    sensorData = md_factory.load(pickle_file)
    dzdx, dzdy, z0 = sensorData.plane_functor.pars
    zmean = np.mean(sensorData.sensor.z)
    znom = ZNOM[ccd_vendor]
    znom_residual_025 = sensorData.quantiles['0.025']
    znom_residual_975 = sensorData.quantiles['0.975']
    results.append(lcatr.schema.valid(lcatr.schema.get('absolute_height'),
                                      dzdx=dzdx, dzdy=dzdy, z0=z0,
                                      zmean=zmean, znom=znom,
                                      znom_residual_025=znom_residual_025,
                                      znom_residual_975=znom_residual_975))

results.append(siteUtils.packageVersions())

lcatr.schema.write_file(results)
lcatr.schema.validate_file()
