#!/usr/bin/env python

import numpy as np
import MetrologyData as metData
from MetrologyData import md_factory

def flatness_task(sensor_id, infile, dtype='OGP'):
    sensorData = md_factory.create(infile, dtype=dtype)
    #
    # Fit and set the reference plane to the LSF to the sensor surface
    # points.
    #
    sensorData.set_ref_plane(sensorData.sensor.xyzPlane_fit(), zoffset=0)
    #
    # Write residual points relative to LSF surface.
    #
    outfile = '%s_flatness_residuals.txt' % sensor_id
    sensorData.write_residuals(outfile)
    #
    # Make a histogram of residual heights.
    #
    sensorData.plot_statistics(title='Sensor Flatness, %s' % infile)
    metData.plot.save('%s_flatness_residuals_hist.png' % sensor_id)
    #
    # Box and whisker plot of residual heights
    #
    sensorData.resids_boxplot()
    metData.plot.save('%s_flatness_residuals_boxplot.png' % sensor_id)
    #
    # Quantile table
    #
    sensorData.quantile_table(outfile='%s_flatness_quantile_table.txt' % sensor_id)
    #
    # Surface plots
    #
    azims = (10, 45)
    for azim in azims:
        sensorData.flatness_plot(azim=azim)
        metData.plot.save('%s_flatness_residuals_point_cloud_azim_%i.png' 
                          % (sensor_id, azim))

if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Sensor flatness analysis.')
    parser.add_argument('infile', help='Data file of xyz tuples containing sensor metrology points')
    parser.add_argument('sensor_id', help='LSST ID number of sensor')
    parser.add_argument('--datatype', type=str, default='OGP',
                        help='Formatting of input file: OGP, e2v, ITL')

    args = parser.parse_args()

    flatness_task(args.sensor_id, args.infile, dtype=args.datatype)
