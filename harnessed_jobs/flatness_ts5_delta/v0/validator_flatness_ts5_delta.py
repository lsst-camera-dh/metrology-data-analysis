#!/usr/bin/env python
import lcatr.schema
import siteUtils
import metUtils
from MetrologyData import md_factory

producer = 'SR-MET-07'
testtype = 'FLATNESS'

global raftname
raftname = siteUtils.getUnitId()

results = metUtils.aggregate_filerefs_ts5(producer, testtype)

raftData = md_factory.load('flatness_ts5_delta.pickle')
peak_valley_95 = raftData.quantiles['0.975'] - raftData.quantiles['0.025']
results.append(lcatr.schema.valid(lcatr.schema.get('raft_flatness'),
                                  residual_025=raftData.quantiles['0.025'],
                                  residual_975=raftData.quantiles['0.975'],
                                  peak_valley_95=peak_valley_95))

results.append(siteUtils.packageVersions())

lcatr.schema.write_file(results)
lcatr.schema.validate_file()
