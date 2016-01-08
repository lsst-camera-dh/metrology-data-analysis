#!/usr/bin/env python
import glob
import lcatr.schema
import siteUtils
from MetrologyData import md_factory

sensor_id = siteUtils.getUnitId()

png_files = glob.glob('%(sensor_id)s_flatness*.png'% locals())
results = [lcatr.schema.fileref.make(x) for x in png_files]

txt_files = glob.glob('%(sensor_id)s_flatness*.txt'% locals())
results.extend([lcatr.schema.fileref.make(x) for x in txt_files])

sensorData = md_factory.load('flatness.pickle')
results.append(lcatr.schema.valid(lcatr.schema.get('flatness'),
                                  residual_025=sensorData.quantiles['0.025'],
                                  residual_975=sensorData.quantiles['0.975']))

results.append(siteUtils.packageVersions())

lcatr.schema.write_file(results)
lcatr.schema.validate_file()
