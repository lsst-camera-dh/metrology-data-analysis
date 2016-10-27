import os

# The following is needed so that matplotlib can write to .matplotlib
os.environ['MPLCONFIGDIR'] = os.curdir
import matplotlib
# For batch-processing, use cairo backend to avoid needing an X11 connection.
# (The Agg backend does not work with 3D plots in matplotlib 1.5.1)
matplotlib.use('cairo')

import sys
import pickle
import numpy as np
import scipy.optimize
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

    def xyzPlane_fit(self, nsigma=3, p0=(0, 0, 0)):
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

        # Refit the reference data within nsigma*stdev of the mean.
        index = np.where((dz > mean-nsigma*stdev) & (dz < mean+nsigma*stdev))
        pars, _ = scipy.optimize.curve_fit(xyz_plane, positions[index],
                                           self.z[index], p0=pars)

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

    def set_ref_plane(self, plane_functor, zoffset=0):
        self.plane_functor = plane_functor
        pos, z = self.sensor.data()
        self.resids = z - plane_functor(pos) + zoffset

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
        output.write('quantile     z (um)\n')
        for quantile in quantiles:
            index = min(int(npts*quantile), npts-1)
            output.write( ' %.3f   %12.6f\n' % (quantile, sorted_resids[index]))
            self.quantiles['%.3f' % quantile] = sorted_resids[index]
        if outfile is not None:
            output.close()

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
        plot.pylab.ylabel(r'$\mu$m')
        plot.setAxis(yrange=yrange)
        if title is None:
            title = self.infile
        win.set_title(title)
        return win

    def plot_statistics(self, nsigma=4, title=None, zoffset=0):
        """
        Plot summary statistics of z-value residuals relative to the 
        provided XyzPlane functor.  The sensor data are used if
        plane_data is None.
        """
        if self.resids is None:
            raise RuntimeError("Reference plane not set")
        dz = self.resids
        mean, stdev = np.mean(dz), np.std(dz)

        # Trim outliers at nsigma and recompute mean and stdev.
        index = np.where((dz > mean-nsigma*stdev) & (dz < mean+nsigma*stdev))
        mean, stdev = np.mean(dz[index]), np.std(dz[index])

        win = plot.histogram(dz[index],
                             xname=r'$z - z_{\rm model}$ $(\mu{\rm m})$',
                             yname='entries/bin')
        plot.pylab.annotate('mean=%.3f\nstdev=%.3f\n%i-sigma clip'
                            % (mean, stdev, nsigma),
                            (0.05, 0.8), xycoords='axes fraction')
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
    _prototypes = dict(OGP=OgpData, ITL=ItlData, e2v=E2vData)

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
