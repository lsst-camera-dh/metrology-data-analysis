#!/usr/bin/env python
import lcatr.schema
import siteUtils
import metUtils
from MetrologyData import md_factory

producer = 'SR-MET-05'
testtype = 'FLATNESS'
results = metUtils.aggregate_filerefs(producer, testtype)

sensorData = md_factory.load('flatness.pickle')
peak_valley_95 = sensorData.quantiles['0.975'] - sensorData.quantiles['0.025']
flatnesshalfband_95 = peak_valley_95/2.

results.append(lcatr.schema.valid(lcatr.schema.get('flatness_sensor'),
                                  peak_valley_95=peak_valley_95))
                                  flatnesshalfband_95=flatnesshalfband_95))

results.extend(siteUtils.packageVersions())

lcatr.schema.write_file(results)
lcatr.schema.validate_file()
