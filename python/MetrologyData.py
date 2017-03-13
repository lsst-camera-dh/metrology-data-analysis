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
        #self.resids_model = None

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

        print(pars)
        # For this set of 'good' points, model the expected distribution of
        # residuals based on fitting planes to the individual CCD surfaces.
        # This involves stepping through the CCDs (S00 -> S22), selecting the
        # data points 'owned' by a given sensor, fitting a plane to them,
        # and evaluating the plane at each of the data points owned by the CCD.
        # An array with the model residuals with respect to the overall
        # best-fitting plane is accumulated
        x = self.x
        y = self.y
        # Construct an 'ideal' list of x, y grid points spanning the sensor, so that
        # positions excluded from the fits as outliers are not excluded from the
        # evaluation of the fitted sensor surface height
        x1 = np.arange(np.min(x), np.max(x)+4, 4)
        y1 = np.arange(np.min(y), np.max(y)+4, 4)
        xmodel = []
        ymodel = []
        for xi in x1:
            for yi in y1:
                xmodel.append(xi)
                ymodel.append(yi)

        xmodel = np.asarray(xmodel)
        ymodel = np.asarray(ymodel)

        for ccd in range(0, 9):
            xmin = 123 + 40*(ccd / 3)
            xmax = xmin + 40
            ymin = 27 + 40*np.mod(ccd, 3)
            ymax = ymin + 40
            print(xmin,xmax,ymin,ymax)
            #include = np.where((x[index] >= xmin) & (x[index] < xmax) &
            #                   (y[index] >= ymin) & (y[index] < ymax))
            include = np.where((x >= xmin) & (x < xmax) &
                               (y >= ymin) & (y < ymax) &
                               (dz > mean-nsigma*stdev_new) &
                               (dz < mean+nsigma*stdev_new))
            pars_temp, _ = scipy.optimize.curve_fit(xyz_plane, positions[include],
                                               self.z[include], p0=pars)
            print(ccd, pars_temp)
            # Evaluate difference between the plane fit and the overall fit
            pars_diff = pars_temp - pars
            print(ccd, pars_diff)
            #dzmodel.append(x[include]*pars_diff[0] + y[include]*pars_diff[1] +
                          #pars_diff[2])
            #if ccd == 0:
                #dzmodel = np.array(x[include]*pars_diff[0] + y[include]*pars_diff[1] +
                #          pars_diff[2])
            #else:
                #dzmodel = np.append(dzmodel, x[include]*pars_diff[0] + y[include]*pars_diff[1] +
                #          pars_diff[2])
            # Construct an 'ideal' list of x, y grid points spanning the sensor, so that
            # positions excluded from the fits as outliers are not excluded from the
            # evaluation of the fitted sensor surface height
            include = np.where((xmodel >= xmin) & (xmodel < xmax) &
                               (ymodel >= ymin) & (ymodel < ymax) )

            if ccd == 0:
                dzmodel = np.array(xmodel[include]*pars_diff[0] + ymodel[include]*pars_diff[1] +
                          pars_diff[2])
            else:
                dzmodel = np.append(dzmodel, xmodel[include]*pars_diff[0] + ymodel[include]*pars_diff[1] +
                          pars_diff[2])

        import pickle
        pickle.dump( dzmodel, open("dzmodel.pickle", "wb") )

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
        self.resids_model = None
        self.pars = None

    def set_ref_plane(self, plane_functor, zoffset=0, nsigma=5):
        self.plane_functor = plane_functor
        pos, z = self.sensor.data()
        dz = z - plane_functor(pos) + zoffset
        self.resids = dz
        # Also define residuals with outliers removed (nsigma clipping)
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

        index = np.where(self.resids_filt > 0)
        ax.scatter(self.sensor.x[index], self.sensor.y[index],
                   self.resids_filt[index], c=sensor_color)

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

    def plot_statistics(self, nsigma=5, title=None, zoffset=0):
        """
        Plot summary statistics of z-value residuals relative to the
        provided XyzPlane functor.  The sensor data are used if
        plane_data is None.
        """
        if self.resids is None:
            raise RuntimeError("Reference plane not set")
        dz = self.resids_filt

        lim = np.round(self.sensor.stdev_filt)
        xrange = [-5*lim, 5*lim]
        win = plot.histogram(dz,
                             xname=r'z - $z_{\rm model}$ (micron)',
                             yname='entries/bin',
                             bins=60,
                             xrange=xrange)
        plot.pylab.annotate('mean=%.3f\nstdev=%.3f\n%i-sigma clip'
                            % (self.sensor.mean_filt, self.sensor.stdev_filt,
                               nsigma), (0.05, 0.8), xycoords='axes fraction')

        # Overlay a Gaussian with the same sigma and correct normalization
        x = np.arange(np.min(dz), np.max(dz), 0.1)
        binsz = 10*lim/60
        y = np.exp(-0.5*np.square(x/self.sensor.stdev_filt))
        y = y/np.sum(y)*np.size(dz)*binsz/0.1
        plot.pylab.plot(x, y, color='b', linestyle='-')

        # Overlay the model residuals
        #plot.pylab.hist(self.resids_model, bins=60, range=xrange, color='r',
                             #linestyle='-')
        resids_model = pickle.load( open( "dzmodel.pickle", "rb") )
        #print(resids_model)
        print('relative sizes:')
        print(dz.size, resids_model.size)
        hist, bin_edges = np.histogram(resids_model, range=(-5*lim, 5*lim), bins=60)
        #print(hist)
        # Smooth the histogram by an approximate resolution function
        filter = np.exp(-(bin_edges[1:]*bin_edges[1:])/2./(3.*3.))
        filter = filter/np.sum(filter)
        hist2 = np.convolve(hist, filter, mode='same')
        print(xrange)
        print(bin_edges)
        print(hist2)
        print(bin_edges.size, hist.size, hist2.size)
        print(bin_edges.shape, hist.shape, hist2.shape)
        #print(resids_model)
        plot.pylab.plot(bin_edges[1:], hist2, color='r', linestyle='-')

        plot.pylab.plot(bin_edges[1:], hist, color='g', linestyle='-')

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

class OgpRsaData(MetrologyData):
    """
    Abstraction for an RSA metrology scan using the OGP machine at BNL.
    """
    def __init__(self, infile):
        super(OgpRsaData, self).__init__(infile)

    def _read_data(self):
        # Read the "Contour" data blocks into a local dict, convert
        # each to a PointCloud object, sort by mean y-value, and
        # finally, set the sensor and reference datasets.
        data = dict()
        key = None
        for line in open(self.infile):
            if line.startswith('Contour'):
                # take the number after 'Contour' as the index key
                key = line.strip().split()[1]
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

        # Identify RSA surface and ball scans by mean z values
        # and x, y ranges
        zavgs = sorted([np.mean(cloud.z) for cloud in data.values()])
        ref_clouds1 = []
        ref_clouds2 = []
        ref_clouds3 = []

        for cloud in data.values():
            if np.mean(cloud.y) >= 0. and np.mean(cloud.y) <= 42.:
                self.sensor = cloud
            else:
                # Figure out which ball it belongs to
                if (np.mean(cloud.x) > 220  and np.mean(cloud.x) < 320
                    and np.mean(cloud.y) > 160 and np.mean(cloud.y) < 190):
                    ref_clouds1.append(cloud)
                if (np.mean(cloud.x) > 220  and np.mean(cloud.x) < 320
                    and np.mean(cloud.y) > 240 and np.mean(cloud.y) < 280):
                    ref_clouds2.append(cloud)
                if (np.mean(cloud.x) > 110  and np.mean(cloud.x) < 140
                    and np.mean(cloud.y) > 200 and np.mean(cloud.y) < 240):
                    ref_clouds3.append(cloud)

        #if len(yavgs) > 1:
            # Add all the reference point clouds together, explicitly
            # setting the 'start' value in the sum function.
        #    self.reference = sum(ref_clouds[1:], ref_clouds[0])
        print(size(ref_clouds1))

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
 
        lastx = -999
        toggle = 1
        for line in open(filename):
            # read the 1st, 3rd, etc. scan lines
            if not line.startswith('#'):
                tokens = line.split(',')
                if float(tokens[0]) <> lastx:
                    lastx = float(tokens[0])
                    toggle = 1 - toggle

                toggle = 0  # read every line
                if toggle == 0:
                    data['X'].append(float(tokens[0]))
                    data['Y'].append(float(tokens[1]))
                    data['Z'].append(float(tokens[2]))

#        for line in open(filename):
#            if not line.startswith('#'):
#                tokens = line.split(',')
#                data['X'].append(float(tokens[0]))
#                data['Y'].append(float(tokens[1]))
#                data['Z'].append(float(tokens[2]))

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
    _prototypes = dict(OGP=OgpData, OGPRSA = OgpRsaData, ITL=ItlData,
                       e2v=E2vData, TS5=Ts5Data)

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
