import numpy as np
import MetrologyData as metData
from MetrologyData import md_factory

def flatnessTask_delta(raft_id, infiles, dtype='OGP', pickle_file=None):
    # This is modified from flatnessTask to accept a list of two data files as
    # input, the two room-temperature scans for a TS5 run, and evaluate the
    # change in flatness between the two scans.
    
    # This routine implicitly assumes that the scan grids are exactly
    # the same for the different data sets.  It does keep track of
    # which scan points are missing in the various data sets.

    # From Peter:  "This step would take the files from the previous steps,
    # subtract them, and look at the difference residuals: histogram,
    # quantiles, plots."

    raftDataDelta = md_factory.create(infiles, dtype=dtype)

    # For positions that are in common in the scans evaluate the difference in z
    raftDataDelta.set_ref_plane(raftDataDelta.sensor.xyzPlane_fit(), zoffset=0)
    dzDelta = raftDataDelta.resids
    #
    # Write residual points relative to LSF surface.
    #
    outfile = '%s_flatness_delta_residuals.txt' % raft_id
    raftDataDelta.write_residuals(outfile)
    #
    # Make a histogram of residual heights.
    #
    raftDataDelta.plot_statistics(title='Raft Flatness, %s' % raft_id)
    metData.plot.save('%s_flatness_delta_hist.png' % raft_id)
    #
    # Box and whisker plot of residual heights
    #
    raftDataDelta.resids_boxplot(title='Residual Box Plot, %s' % raft_id)
    metData.plot.save('%s_flatness_delta_boxplot.png' % raft_id)
    #
    # Quantile table
    #
    raftDataDelta.quantile_table(outfile='%s_flatness_delta_quantile_table.txt'
                                 % raft_id)
    #
    # Surface plots
    #
    azims = (10, 45)
    for azim in azims:
        raftDataDelta.flatness_plot(azim=azim, title='Surface Plot (Warm-Cold)')
        metData.plot.save('%s_flatness_delta_point_cloud_azim_%i.png'
                          % (raft_id, azim))

    if pickle_file is not None:
        raftDataDelta.persist(pickle_file)
