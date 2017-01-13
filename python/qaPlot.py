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
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import datetime

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
                # Multiply the pressure by 1E6 to convert it to micro-torr
                data['P'].append(float(tokens[13])*1E6)
                # Divide the time stamp by 1000 to convert it to seconds
                data['T'].append(float(tokens[14])/1000.)

    win, axarr = plt.subplots(2, sharex=True)
    times = [datetime.datetime.fromtimestamp(t) for t in data['T']]

    axarr[0].plot(times, data['A'], 'ro', label='A')
    axarr[0].plot(times, data['B'], 'go', label='B')
    axarr[0].plot(times, data['C'], 'bo', label='C')
    axarr[0].plot(times, data['D'], 'ko', label='D')
    axarr[0].set_ylabel('Temp. (C)')
    if title is None:
        title = 'QA Plot'
    axarr[0].set_title(title)

    axarr[1].plot(times, data['P'], 'ro')
    hfmt = mdates.DateFormatter('%H:%M')
    axarr[1].xaxis.set_major_formatter(hfmt)
    axarr[1].set_ylabel('Pres. (micro-torr)')
    axarr[1].set_xlabel('Time')

    plt.savefig(outfile)
