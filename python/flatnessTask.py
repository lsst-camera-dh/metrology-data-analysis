import numpy as np
import MetrologyData as metData
from MetrologyData import md_factory

#def flatnessTask(sensor_id, infile, dtype='OGP', pickle_file=None):
def flatnessTask(sensor_id, infile, dtype, pickle_file):
    print "In flatnessTask"
    print "dtype:  %s" % dtype
    print sensor_id
    print infile
    print pickle_file
    sensorData = md_factory.create(infile, dtype=dtype)
    #
    # Fit and set the reference plane to the LSF to the sensor surface
    # points.
    #
    print "sensorData:"
    print sensorData
    sensorData.set_ref_plane(sensorData.sensor.xyzPlane_fit(), zoffset=0)
    #
    # Write residual points relative to LSF surface.
    #
    outfile = '%s_flatness_residuals.txt' % sensor_id
    sensorData.write_residuals(outfile)
    #
    # Make a histogram of residual heights.
    #
    print "Histogram"
    sensorData.plot_statistics(title='Sensor Flatness, %s' % infile)
    metData.plot.save('%s_flatness_residuals_hist.png' % sensor_id)
    #
    # Box and whisker plot of residual heights
    #
    print "Box and whisker"
    sensorData.resids_boxplot()
    metData.plot.save('%s_flatness_residuals_boxplot.png' % sensor_id)
    #
    # Quantile table
    #
    print "Quantile table"
    sensorData.quantile_table(outfile='%s_flatness_quantile_table.txt' % sensor_id)
    #
    # Surface plots
    #
    azims = (10, 45)
    for azim in azims:
        sensorData.flatness_plot(azim=azim)
        metData.plot.save('%s_flatness_residuals_point_cloud_azim_%i.png' 
                          % (sensor_id, azim))

    if pickle_file is not None:
	print "Saving pickle file"
        sensorData.persist(pickle_file)
