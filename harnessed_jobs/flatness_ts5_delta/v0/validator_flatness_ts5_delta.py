#!/usr/bin/env python
import glob
import lcatr.schema
import siteUtils
import metUtils
from MetrologyData import md_factory

producer = 'SR-MET-07'
testtype = 'FLATNESS'

results = metUtils.aggregate_filerefs_ts5(producer, testtype)

# Add the QA plot to the results
raft_id = siteUtils.getUnitId()
qafile = glob.glob('*_qa_plot.png')[0]
#print('qafile:  %s' % qafile)
#print('raft_id:  %s' % raft_id)

md = siteUtils.DataCatalogMetadata(CCD_MANU=siteUtils.getCcdVendor(),
                                   LSST_NUM=siteUtils.getUnitId(),
                                   PRODUCER=producer,
                                   ORIGIN=siteUtils.getSiteName(),
                                   TESTTYPE=testtype,
                                   TEST_CATEGORY='MET')

results.extend([lcatr.schema.fileref.make(qafile,metadata=md(DATA_PRODUCT='QA_PLOT'))])

raftData = md_factory.load('flatness_ts5_delta.pickle')
peak_valley_95 = raftData.quantiles['0.975'] - raftData.quantiles['0.025']
peak_valley_100 = raftData.quantiles['1.000'] - raftData.quantiles['0.000']

# Make strings out of the quantile information
quantiles = raftData.quantiles
quantile_levels = quantiles.keys()
quantile_str = '' 
z_str = ''
for key in sorted(quantile_levels):
    quantile_str += key + ', '
    z_str += "%.2f" % quantiles[key] + ', '
quantile_str = quantile_str[0:len(quantile_str)-2]
z_str = z_str[0:len(z_str)-2]

results.append(lcatr.schema.valid(lcatr.schema.get('ts5_flatness_delta'),
                                  residual_025=raftData.quantiles['0.025'],
                                  residual_975=raftData.quantiles['0.975'],
                                  peak_valley_95=peak_valley_95,
                                  peak_valley_100=peak_valley_100,
                                  flatness_quantile=quantile_str,
                                  flatness_z=z_str))

results.append(siteUtils.packageVersions())

lcatr.schema.write_file(results)
lcatr.schema.validate_file()
