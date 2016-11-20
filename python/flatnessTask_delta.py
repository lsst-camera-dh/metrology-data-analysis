import numpy as np
import MetrologyData as metData
from MetrologyData import md_factory

def flatnessTask_delta(raft_id, infiles, dtype='OGP', pickle_file=None):
    # This is modified from flatnessTask to accept a list of data files as
    # input.  # The script processes each file to evaluate the temperature
    # and standard deviation of the residuals, # then look the differences
    # of the results for warm, cold, and warm again
    # This routine implicitly assumes that the scan grids are exactly
    # the same for the different data sets.  It does keep track of
    # which scan points are missing in the various data sets.

    # From Peter:  "This step would take the files from the previous steps, subtract them, and look at the difference residuals: histogram, quantiles, plots. "

    # Process each file, evaluating temperature, time, and standard
    # deviation of flatness

    stdev = [] 
    temperature = []
    datestr = []
    nsigma = 4

    for infile in infiles:
        raftData = md_factory.create([infile], dtype=dtype)
        # Fit and set the reference plane to the LSF to the raft surface
        # points.
        #
        raftData.set_ref_plane(raftData.sensor.xyzPlane_fit(), zoffset=0)
        dz = raftData.resids

        # Apply nsigma clipping to evaluate the standard deviation
        mean = np.mean(dz)
        std = np.std(dz)
        index = np.where((dz > mean-nsigma*std) & (dz < mean+nsigma*std))
        stdev.append(np.std(dz[index]))

        # Parse the file name to get the temperature and time stamp
        pieces = infile.split('_')
        datestr.append(pieces[6])
        loc = pieces[7].find('C')
        temperature.append(pieces[7][0:loc])

    # Find the 'best' (least standard deviation, after clipping) scans at the warmest and
    # coldest temperatures
    temp = np.array(temperature).astype(float)
    loc = np.where((temp == np.max(temp)))[0]
    std = np.array(stdev)
    pos = np.where(std[loc] == np.min(std[loc]))[0]
    locWarm = loc[pos[0]]
    loc = np.where((temp == np.min(temp)))[0]
    pos = np.where(std[loc] == np.min(std[loc]))[0]
    locCold = loc[pos[0]]

    # print("locWarm:  ", locWarm)
    # print("locCold:  ", locCold)

    raftDataDelta = md_factory.create([infiles[locWarm], infiles[locCold]], dtype=dtype)

    # For positions that are in common in the scans evaluate the difference in z
    raftDataDelta.set_ref_plane(raftDataDelta.sensor.xyzPlane_fit(), zoffset=0)
    dzDelta = raftDataDelta.resids
    print("flatness resid:  ", np.std(dzDelta))
        
    #
    #
    # Write residual points relative to LSF surface.
    #
    outfile = '%s_flatness_residuals_%s_delta.txt' % (raft_id, pieces[2])
    raftDataDelta.write_residuals(outfile)
    #
    # Make a histogram of residual heights.
    #
    raftDataDelta.plot_statistics(title='Raft Flatness, %s' % infile)
    metData.plot.save('%s_flatness_hist_%s_delta.png' % (raft_id, pieces[2]))
    #
    # Box and whisker plot of residual heights
    #
    raftDataDelta.resids_boxplot()
    metData.plot.save('%s_flatness_boxplot_%s_delta.png' % (raft_id, pieces[2]))
    #
    # Quantile table
    #
    raftDataDelta.quantile_table(outfile='%s_flatness_quantile_table_%s_delta.txt'
                          % (raft_id, pieces[2]))
    #
    # Surface plots
    #
    azims = (10, 45)
    for azim in azims:
        raftDataDelta.flatness_plot(azim=azim,title=infiles[locWarm] + ' ' + infiles[locCold])
        metData.plot.save('%s_flatness_delta_point_cloud_azim_%i_%s.png'
                      % (raft_id, azim, pieces[2]))

    if pickle_file is not None:
        raftDataDelta.persist(pickle_file)

if __name__ == '__main__':
    with open('ETU01_file_list.txt') as f:
        infiles = f.read().splitlines()

    print(infiles)

    flatnessTask_delta('ETU01', infiles, dtype='TS5', pickle_file=None)
