#!/usr/bin/env python
import lcatr.schema
import siteUtils
import metUtils
from MetrologyData import md_factory

producer = 'SR-MET-6'
testtype = 'FLATNESS'
results = metUtils.aggregate_filerefs(producer, testtype)

sensorData = md_factory.load('flatness.pickle')
peak_valley_95 = sensorData.quantiles['0.975'] - sensorData.quantiles['0.025']
results.append(lcatr.schema.valid(lcatr.schema.get('sensor_flatness'),
                                  peak_valley_95=peak_valley_95))

results.append(siteUtils.packageVersions())

lcatr.schema.write_file(results)
lcatr.schema.validate_file()
