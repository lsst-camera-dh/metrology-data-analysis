import os

# The following is needed so that matplotlib can write to .matplotlib
os.environ['MPLCONFIGDIR'] = os.curdir
import matplotlib
# For batch-processing, use cairo backend to avoid needing an X11 connection.
# (The Agg backend does not work with 3D plots in matplotlib 1.5.1. The cairo
# backend uses vector fonts and does not render Greek letters or some other
# LaTeX math formatting.)
matplotlib.use('cairo')

import sys
import numpy as np
import lsst.eotest.sensor.pylab_plotter as plot
#from matplotlib import dates
#import datetime

def qaPlot(infiles, outfile, title=None):
    # Read the TS5 metrology files specified in infiles, construct time history
    # of the temperature (all four sensors) and pressure

    # The TS5 metrology data are in csv files.  The first three entries on each
    # line are commanded x and y and the measured (summed) z, in mm.
    # The entries of interest here are temp sensors A, B, C, and D, the time (T), and
    # pressure (P)
    data = dict([(key, []) for key in 'ABCDPT'])
        
    for file in infiles:
        for line in open(file):
            if not(line.startswith('#')):
                tokens = line.split(',')
                data['A'].append(float(tokens[9]))
                data['B'].append(float(tokens[10]))
                data['C'].append(float(tokens[11]))
                data['D'].append(float(tokens[12]))
                data['P'].append(float(tokens[13]))
                # Divide the time stamp by 1000 to convert it to seconds
                data['T'].append(float(tokens[14])/1000.)

    #dts = map(datetime.datetime.fromtimestamp, data['T'])
    #fds = dates.date2num(dts)
    #hfmt = dates.DateFormatter('%m/%d %H:%M')

    win = plot.Window()
    plot.pylab.subplot(211)
    plot.pylab.plot(data['T'], data['A'], 'ro', label='A')
    plot.pylab.plot(data['T'], data['B'], 'go', label='B')
    plot.pylab.plot(data['T'], data['C'], 'bo', label='C')
    plot.pylab.plot(data['T'], data['D'], 'ko', label='D')
    plot.pylab.ylabel('Temp. (C)')
    if title is None:
        title = 'QA Plot'
    plot.pylab.title(title)

    #plot.pylab.xaxis.set_major_locator(dates.MinuteLocator())
    #plot.pylab.xaxis.set_major_formatter(hfmt)

    plot.pylab.subplot(212)
    plot.pylab.plot(data['T'], data['P'], 'ro')
    plot.pylab.ylabel('Pres. (torr)')
    plot.pylab.xlabel('Time')

    #plot.pylab.xaxis.set_major_locator(dates.MinuteLocator())
    #plot.pylab.xaxis.set_major_formatter(hfmt)
    plot.pylab.savefig(outfile)


if __name__ == '__main__':
    with open('LCA-10753_RSA-002_files.txt') as f:
        infiles = f.read().splitlines()
        qaPlot(infiles, 'qaPlot.png', title='QA Plot')
