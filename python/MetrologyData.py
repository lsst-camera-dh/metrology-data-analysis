import sys
import numpy as np
import scipy.optimize
from mpl_toolkits.mplot3d import Axes3D
import pylab_plotter as plot

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

    def point_cloud_plot(self, elev=10, azim=30, title=None, 
                         sensor_color='r', ref_color='b', refpoint_color='b'):
        win = plot.Window()
        ax = Axes3D(win.fig)
        ax.scatter(self.sensor.x, self.sensor.y, self.sensor.z,
                   c=sensor_color)
        ax.scatter(self.reference.x, self.reference.y, self.reference.z,
                   c=refpoint_color)

        x = np.linspace(min(self.sensor.x), max(self.sensor.x), 100)
        y = np.linspace(min(self.reference.y), max(self.reference.y), 100)

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
        if len(data) != 3:
            raise RuntimeError("Expected exactly 3 Contour data blocks in the OGP data. %i found." % len(data))
        # Identify sensor and reference point clouds by mean y-values.
        # The sensor dataset is in the middle.
        yavgs = sorted([np.mean(cloud.y) for cloud in data.values()])
        ref_clouds = []
        for cloud in data.values():
            if np.mean(cloud.y) == yavgs[1]:
                self.sensor = cloud
            else:
                ref_clouds.append(cloud)
        self.reference = ref_clouds[0] + ref_clouds[1]

    def _xyz(self, line):
        # Unpack a line and convert z values from mm to microns.
        data = [float(x) for x in line.split()[:3]]
        return data[0], data[1], 1e3*data[2]

    def sensorPlane_fit(self, nsigma=3, p0=(0, 0, 0)):
        "Return XyzPlane functor fit to the sensor data."
        return self.sensor.xyzPlane_fit(nsigma=nsigma, p0=p0)

    def refPlane_fit(self, nsigma=3, p0=(0, 0, 0)):
        "Return XyzPlane functor fit to the gauge block data."
        return self.reference.xyzPlane_fit(nsigma=nsigma, p0=p0)

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
        # Convert x, y from micron to mm
        self.sensor.x /= 1e3
        self.sensor.y /= 1e3

class MetrologyDataFactory(object):
    _prototypes = dict([(dtype, metDataClass) for dtype, metDataClass in 
                        zip('OGP ITL e2v'.split(),
                            (OgpData, ItlData, E2vData))])
    def __init__(self):
        pass

    def create(self, infile, dtype='OGP'):
        try:
            return self._prototypes[dtype](infile)
        except KeyError:
            raise RuntimeError("Unrecognized metrology data type: " + dtype)

md_factory = MetrologyDataFactory()
