#!/usr/bin/env python
import lcatr.schema
import siteUtils
import metUtils
from MetrologyData import md_factory

producer = 'SR-MET-07'
testtype = 'FLATNESS'

results = metUtils.aggregate_filerefs_ts5(producer, testtype)

raftData = md_factory.load('flatness_ts5.pickle')
peak_valley_95 = raftData.quantiles_filt['0.975'] - raftData.quantiles_filt['0.025']
peak_valley_100 = raftData.quantiles_filt['1.000'] - raftData.quantiles_filt['0.000']

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
results.append(lcatr.schema.valid(lcatr.schema.get('ts5_raft_flatness'),
                                  residual_025=raftData.quantiles['0.025'],
                                  residual_975=raftData.quantiles['0.975'],
                                  peak_valley_95=peak_valley_95,
                                  peak_valley_100=peak_valley_100,
                                  flatness_quantile=quantile_str,
                                  flatness_z=z_str))

# Parse the metadata from the scan file
temp_start = []
temp_end = []
for line in open(raftData.infile):
    if line.startswith('# start time ='):
        tokens = line.split()
        start_time = float(tokens[4])
        end_time = float(tokens[9])
    if line.startswith('# temperature'):
        tokens = line.split()
        temp_start.append(float(tokens[5]))
        temp_end.append(float(tokens[9]))

results.append(lcatr.schema.valid(lcatr.schema.get('ts5_raft_flatness2'),
                                  start_time=start_time,
                                  end_time=end_time,
                                  temp_A_start = temp_start[0],
                                  temp_B_start = temp_start[1],
                                  temp_C_start = temp_start[2],
                                  temp_D_start = temp_start[3],
                                  temp_A_end = temp_end[0],
                                  temp_B_end = temp_end[1],
                                  temp_C_end = temp_end[2],
                                  temp_D_end = temp_end[3]))

results.extend(siteUtils.packageVersions())

lcatr.schema.write_file(results)
lcatr.schema.validate_file()
