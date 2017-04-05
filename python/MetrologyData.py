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
import pickle
import numpy as np
import scipy.optimize
import scipy.stats
from mpl_toolkits.mplot3d import Axes3D
import lsst.eotest.sensor.pylab_plotter as plot

class XyzPlane(object):
    """
    Function object class to represent a plane as a function
    of x, y coordinates, where z = a*x + b*y + c.
    """
    def __init__(self, a, b, c):
        self.pars = a, b, c
    def __call__(self, positions):
        a, b, c = self.pars
        return np.array([a*x + b*y + c for x, y in positions])

def xyz_plane(positions, a, b, c):
    "Function wrapping XyzPlane for passing to scipy.optimize.curve_fit"
    my_plane = XyzPlane(a, b, c)
    return my_plane(positions)

class PointCloud(object):
    """
    Abstraction for x, y, z points representing a metrology scan of a
    surface.
    """
    def __init__(self, x, y, z):
        self.x = np.array(x)
        self.y = np.array(y)
        self.z = np.array(z)
        self.stdev_filt = None
        self.mean_filt = None

    def data(self):
        """
        Return the xyz data repackaged in a format appropriate for
        fitting using scipy.optimize.curve_fit and the xyz_plane function.
        """
        return np.array(zip(self.x, self.y)), self.z

    def __add__(self, other):
        result = PointCloud([], [], [])
        result.x = np.concatenate((self.x, other.x))
        result.y = np.concatenate((self.y, other.y))
        result.z = np.concatenate((self.z, other.z))
        return result

    def xyzPlane_fit(self, nsigma=4, p0=(0, 0, 0)):
        """
        Fit a plane to the xyz data, clipping the initial fit at the
        nsigma level to remove outlier points.  Return an XyzPlane
        functor set to the fit parameters.
        """
        positions = np.array(zip(self.x, self.y))

        # Initial fit
        pars, _ = scipy.optimize.curve_fit(xyz_plane, positions, self.z, p0=p0)
        dz = xyz_plane(positions, *pars) - self.z
        mean, stdev = np.mean(dz), np.std(dz)
        # Refit iteratively until the standard deviation of residuals does not
        # change
        stdev_last = -1
        stdev_new = stdev
        index = np.where((dz > mean-nsigma*stdev) & (dz < mean+nsigma*stdev))
        while stdev_new != stdev_last:
            stdev_last = stdev_new
            # Refit the reference data within nsigma*stdev of the mean.
            pars, _ = scipy.optimize.curve_fit(xyz_plane, positions[index],
                                               self.z[index], p0=pars)
            dz = xyz_plane(positions, *pars) - self.z
            mean, stdev_new = np.mean(dz[index]), np.std(dz[index])
            index = np.where((dz > mean-nsigma*stdev_new) &
                             (dz < mean+nsigma*stdev_new))

        # Make the standard deviation and mean of the filtered residuals
        # available, along with the fit parameters
        self.stdev_filt = stdev_new
        self.mean_filt = mean
        self.pars = pars

        # Return a XyzPlane functor initialized with the fitted parameters.
        return XyzPlane(*pars)

class MetrologyData(object):
    """
    Base class for metrology data.
    """
    def __init__(self, infile):
        self.infile = infile
        self._read_data()
        self.resids = None
        self.resids_filt = None
        self.pars = None

    def set_ref_plane(self, plane_functor, zoffset=0, nsigma=5):
        self.plane_functor = plane_functor
        pos, z = self.sensor.data()
        dz = z - plane_functor(pos) + zoffset
        self.resids = dz

        # Also define residuals with outliers removed (nsigma clipping)
        if self.sensor.mean_filt is None:
            # For absolute height analysis for ITL sensors no plane will
            # have been fit at this point, so the mean and standard 
            # deviations of residuals with outliers filtered will not 
            # have been evaluated.  No plane needs to be fit here, but
            # the code expects to be able to reference the mean and
            # standard deviations of the filtered residuals.
            mean, stdev = np.mean(dz), np.std(dz)
            index = np.where((dz > mean-nsigma*stdev) &
                             (dz < mean+nsigma*stdev))
            self.sensor.mean_filt = np.mean(dz[index])
            self.sensor.stdev_filt = np.std(dz[index])

        mean, stdev = self.sensor.mean_filt, self.sensor.stdev_filt
        index = np.where((dz > mean-nsigma*stdev) & (dz < mean+nsigma*stdev))
        self.resids_filt = dz[index]

    def flatness_plot(self, elev=10, azim=30, title=None,
                      sensor_color='r', ref_color='b'):
        win = plot.Window()
        ax = Axes3D(win.fig)

        ax.scatter(self.sensor.x, self.sensor.y, self.resids, c=sensor_color)

        x = np.linspace(min(self.sensor.x), max(self.sensor.x), 100)
        y = np.linspace(min(self.sensor.y), max(self.sensor.y), 100)

        xx, yy, zz = [], [], []
        for xval in x:
            for yval in y:
                xx.append(xval)
                yy.append(yval)
                zz.append(0)

        xx = np.array(xx).reshape(len(y), len(x))
        yy = np.array(yy).reshape(len(y), len(x))
        zz = np.array(zz).reshape(len(y), len(x))

        ax.plot_wireframe(xx, yy, zz, rstride=5, cstride=5)

        index = np.where(self.resids > 0)
        ax.scatter(self.sensor.x[index], self.sensor.y[index],
                   self.resids[index], c=sensor_color)

        plot.pylab.xlabel('x (mm)')
        plot.pylab.ylabel('y (mm)')
        ax.set_zlabel('z (micron)')
        ax.view_init(elev=elev, azim=azim)
        if title is None:
            title = self.infile
        ax.set_title(title)
        return win, ax

    def absolute_height_plot(self, elev=10, azim=30, title=None,
                             sensor_color='r', ref_color='b',
                             refpoint_color='b'):
        win = plot.Window()
        ax = Axes3D(win.fig)
        ax.scatter(self.sensor.x, self.sensor.y, self.sensor.z,
                   c=sensor_color)
        try:
            ax.scatter(self.reference.x, self.reference.y, self.reference.z,
                       c=refpoint_color)
            y = np.linspace(min(self.reference.y), max(self.reference.y), 100)
        except AttributeError:
            # Vendor data may not have data from the reference plane
            # scans, so there are not reference points to plot.
            #
            # Use the sensor points to set the grid points in y.
            y = np.linspace(min(self.sensor.y), max(self.sensor.y), 100)

        x = np.linspace(min(self.sensor.x), max(self.sensor.x), 100)

        xx, yy, zz = [], [], []
        for xval in x:
            for yval in y:
                xx.append(xval)
                yy.append(yval)
                zz.append(self.plane_functor([(xval, yval)]))

        xx = np.array(xx).reshape(len(y), len(x))
        yy = np.array(yy).reshape(len(y), len(x))
        zz = np.array(zz).reshape(len(y), len(x))

        ax.plot_wireframe(xx, yy, zz, rstride=5, cstride=5)

        index = np.where(self.resids > 0)
        ax.scatter(self.sensor.x[index], self.sensor.y[index],
                   self.sensor.z[index], c=sensor_color)

        plot.pylab.xlabel('x (mm)')
        plot.pylab.ylabel('y (mm)')
        ax.set_zlabel('z (micron)')
        ax.view_init(elev=elev, azim=azim)
        if title is None:
            title = self.infile
        ax.set_title(title)
        return win, ax

    def quantile_table(self, outfile=None,
                       quantiles=(1, 0.995, 0.990, 0.975, 0.75, 0.5,
                                  0.25, 0.025, 0.01, 0.005, 0)):
        self.quantiles = {}
        if self.resids is None:
            raise RuntimeError("Reference plane not set")
        if outfile is None:
            output = sys.stdout
        else:
            output = open(outfile, 'w')
        sorted_resids = sorted(self.resids)
        npts = len(sorted_resids)
        output.write('quantile     z (micron)\n')
        for quantile in quantiles:
            index = min(int(npts*quantile), npts-1)
            output.write(' %.3f   %12.6f\n' % (quantile, sorted_resids[index]))
            self.quantiles['%.3f' % quantile] = sorted_resids[index]
        if outfile is not None:
            output.close()

        # Also evaluate quantiles with outliers filtered
        self.quantiles_filt = {}
        sorted_resids_filt = sorted(self.resids_filt)
        npts = len(sorted_resids_filt)
        for quantile in quantiles:
            index = min(int(npts*quantile), npts-1)
            self.quantiles_filt['%.3f' % quantile] = sorted_resids_filt[index]

    def write_residuals(self, outfile, contour_id=1):
        if self.resids is None:
            raise RuntimeError("Reference plane not set")
        pos, z = self.sensor.data()
        output = open(outfile, 'w')
        output.write('Contour %i\n' % contour_id)
        for my_pos, my_z in zip(pos, self.resids):
            output.write('%.6f  %.6f  %.6f mm\n' % (my_pos[0], my_pos[1], my_z))
        output.close()

    def resids_boxplot(self, yrange=None, title=None):
        win = plot.Window()
        plot.pylab.boxplot(self.resids)
        plot.pylab.ylabel('micron')
        plot.setAxis(yrange=yrange)
        if title is None:
            title = self.infile
        win.set_title(title)
        return win

    def plot_statistics(self, nsigma=5, title=None, zoffset=0, bins=60):
        """
        Plot summary statistics of z-value residuals relative to the
        provided XyzPlane functor.  The sensor data are used if
        plane_data is None.
        """
        if self.resids is None:
            raise RuntimeError("Reference plane not set")
        dz = self.resids_filt
        # Define the axis range relative to the mean of the residuals
        xrange = [self.sensor.mean_filt - 5*self.sensor.stdev_filt,
                  self.sensor.mean_filt + 5*self.sensor.stdev_filt]
        win = plot.histogram(dz,
                             xname=r'z - $z_{\rm model}$ (micron)',
                             yname='entries/bin',
                             bins=bins,
                             xrange=xrange)
        plot.pylab.annotate('mean=%.3f\nstdev=%.3f\n%i-sigma clip'
                            % (self.sensor.mean_filt, self.sensor.stdev_filt,
                               nsigma), (0.05, 0.8), xycoords='axes fraction')

        # Overlay a Gaussian with the same sigma and correct normalization
        binsz = np.abs(xrange[1] - xrange[0])/float(bins)
        x = np.linspace(np.min(dz), np.max(dz), 100)
        gaussian = scipy.stats.norm(loc=self.sensor.mean_filt,
                                    scale=self.sensor.stdev_filt)
        plot.pylab.plot(x, np.size(dz)*binsz*gaussian.pdf(x), color='b',
                        linestyle='-')

        if title is None:
            title = self.infile
        win.set_title(title)
        return win

    def persist(self, outfile):
        output = open(outfile, 'w')
        pickle.dump(self, output)
        output.close()

class OgpData(MetrologyData):
    """
    Abstraction for single sensor metrology scan, including gauge
    block data, using the OGP machine at BNL.
    """
    def __init__(self, infile):
        super(OgpData, self).__init__(infile)

    def _read_data(self):
        # Read the "Contour" data blocks into a local dict, convert
        # each to a PointCloud object, sort by mean y-value, and
        # finally, set the sensor and reference datasets.
        data = dict()
        key = None
        for line in open(self.infile):
            if line.startswith('Contour'):
                key = line.strip()
                data[key] = []
            if line.strip() and key is not None:
                try:
                    coords = self._xyz(line)
                    data[key].append(coords)
                except ValueError:
                    pass
            else:
                key = None
        # Convert to PointCloud objects.
        for key in data:
            data[key] = PointCloud(*zip(*tuple(data[key])))

        # Identify sensor and reference point clouds by mean y-values:
        # The sensor Contours are all in the range [0,42] and the reference
        # point clouds are outside this range.  The test below is based
        # on the mean y coordinates of the Contours, so the implicit
        # assumption is that no single Contour will cross between reference
        # blocks.
        yavgs = sorted([np.mean(cloud.y) for cloud in data.values()])
        ref_clouds = []

        for cloud in data.values():
            if np.mean(cloud.y) >= 0. and np.mean(cloud.y) <= 42.:
                self.sensor = cloud
            else:
                ref_clouds.append(cloud)
        if len(yavgs) > 1:
            # Add all the reference point clouds together, explicitly
            # setting the 'start' value in the sum function.
            self.reference = sum(ref_clouds[1:], ref_clouds[0])

    def _xyz(self, line):
        # Unpack a line and convert z values from mm to microns.
        data = [float(x) for x in line.split()[:3]]
        return data[0], data[1], 1e3*data[2]

class Ts5Data(MetrologyData):
    """
    Abstraction for raft (RSA and RTM) metrology scans with TS5.
    """
    def __init__(self, infile):
        super(Ts5Data, self).__init__(infile)

    def _read_data(self):
        # The TS5 metrology data are in csv files.  The first three entries on each
        # line are commanded x and y and the measured (summed) z, in mm.
        # Here to allow option of differencing two data sets, infile is
        # assumed to be a list of 1 or 2 elements
        data = dict([(key, []) for key in 'XYZ'])
        # Test to see whether a single string or a list of two files has been
        # passed for infile
        if isinstance(self.infile, str):
            filename = self.infile
        else:
            filename = self.infile[0]
 
        for line in open(filename):
            if not line.startswith('#'):
                tokens = line.split(',')
                data['X'].append(float(tokens[0]))
                data['Y'].append(float(tokens[1]))
                data['Z'].append(float(tokens[2]))

        # If a second file has been provided (for evaluating differential
        # flatness) read it and subtract the z measurements, keeping
        # in mind that the grid points included may not be the same
        # in both files
        data2 = dict([(key, []) for key in 'XYZ'])
        if len(self.infile) == 2:
            for line in open(self.infile[1]):
                if not line.startswith('#'):
                    tokens = line.split(',')
                    data2['X'].append(float(tokens[0]))
                    data2['Y'].append(float(tokens[1]))
                    data2['Z'].append(float(tokens[2]))

            # Convert to ndarrays so the where function can be used
            x = np.array(data['X'])
            y = np.array(data['Y'])
            z = np.array(data['Z'])
            x2 = np.array(data2['X'])
            y2 = np.array(data2['Y'])
            z2 = np.array(data2['Z'])

            data3 = dict([(key, []) for key in 'XYZ'])
            for i in np.arange(len(x)):
                loc = np.where((x2 == x[i]) & (y2 == y[i]))[0]
                if len(loc):
                    data3['X'].append(x[i])
                    data3['Y'].append(y[i])
                    data3['Z'].append(z[i] - z2[loc[0]])

            data = data3

        self.sensor = PointCloud(data['X'], data['Y'], data['Z'])
        # Convert z from mm to micron
        self.sensor.z *= 1e3


    def _xyz(self, line):
        # Unpack a line and convert z values from mm to microns.
        data = [float(x) for x in line.split()[:3]]
        return data[0], data[1], 1e3*data[2]

class ItlData(MetrologyData):
    def __init__(self, infile):
        super(ItlData, self).__init__(infile)

    def _read_data(self):
        # The ITL metrology data just comprises x, y, z points scanned
        # over the sensor. The piston and tilt relative to the 13mm
        # ZNOM has presumably been subtracted off.
        data = dict([(key, []) for key in 'XYZ'])
        for line in open(self.infile):
            if line.startswith('ImagePoint'):
                tokens = line.split()
                if len(tokens) > 5:
                    # Omit this line since it is part of the scan
                    # summary data and not a scan point.
                    continue
                data[tokens[1]].append(float(tokens[3]))
        self.sensor = PointCloud(data['X'], data['Y'], data['Z'])
        # Convert z from mm to micron
        self.sensor.z *= 1e3

class E2vData(MetrologyData):
    def __init__(self, infile):
        super(E2vData, self).__init__(infile)

    def _read_data(self):
        data = dict([(key, []) for key in 'XYZ'])
        for line in open(self.infile):
            tokens = line.split(',')
            data['X'].append(float(tokens[0]))
            data['Y'].append(float(tokens[1]))
            data['Z'].append(float(tokens[2]))
        self.sensor = PointCloud(data['X'], data['Y'], data['Z'])
        # Convert z from mm to micron
        self.sensor.z *= 1e3

class MetrologyDataFactory(object):
    _prototypes = dict(OGP=OgpData, ITL=ItlData, e2v=E2vData, TS5=Ts5Data)

    def __init__(self):
        pass

    def create(self, infile, dtype='OGP'):
        try:
            return self._prototypes[dtype](infile)
        except KeyError:
            raise RuntimeError("Unrecognized metrology data type: " + dtype)

    def load(self, pickle_file):
        "Unpersist a MetrologyData object from a pickle file."
        return pickle.load(open(pickle_file))

md_factory = MetrologyDataFactory()
