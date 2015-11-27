#!/usr/bin/env python

import numpy as np
import MetrologyData as metData
from MetrologyData import md_factory, XyzPlane

def absolute_height_task(sensor_id, infile, dtype='OGP', zoffset=0):
    sensorData = md_factory.create(infile, dtype=dtype)
    if dtype == 'OGP':
        #
        # Fit and set the reference plane to the gauge blocks.
        #
        sensorData.set_ref_plane(sensorData.refPlane_fit(), zoffset=zoffset)
    elif dtype == 'ITL':
        #
        # Set reference plane at znom=12.998 mm
        #
        sensorData.set_ref_plane(XyzPlane(0, 0, 12998.))
    else:
        raise RuntimeError("%s not supported for absolute height analysis" 
                           % dtype)
    #
    # Write surface height data points.
    #
    outfile = '%s_abs_height_residuals.txt' % sensor_id
    sensorData.write_residuals(outfile)
    #
    # Make a histogram of residual heights.
    #
    sensorData.plot_statistics(title='Sensor Absolute Height, %s' % infile)
    metData.plot.save('%s_abs_height_hist.png' % sensor_id)
    #
    # Box and whisker plot of residual heights
    #
    sensorData.resids_boxplot()
    metData.plot.save('%s_abs_height_boxplot.png' % sensor_id)
    #
    # Quantile table
    #
    sensorData.quantile_table(outfile='%s_abs_height_quantile_table.txt'
                           % sensor_id)
    #
    # Surface plots
    #
    azims = (10, 45)
    for azim in azims:
        sensorData.absolute_height_plot(azim=azim)
        metData.plot.save('%s_abs_height_point_cloud_azim_%i.png' 
                          % (sensor_id, azim))

if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Perform absolute height analysis on OGP data.')
    parser.add_argument('ogp_file', help='OGP data file of xyz tuples containing gauge block and sensor metrology points')
    parser.add_argument('sensor_id', help='LSST ID number of sensor')
    parser.add_argument('--zoffset', type=float, default=-1.2,
                        help='z-offset')

    args = parser.parse_args()

    absolute_height_task(args.sensor_id, args.ogp_file, zoffset=args.zoffset)
