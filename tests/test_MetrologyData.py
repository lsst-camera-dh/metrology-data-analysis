"""
Unit tests for MetrologyData class.
"""
from __future__ import print_function
import unittest
import numpy as np
import scipy.stats
import itertools
from MetrologyData import PointCloud, XyzPlane

class PointCloudTestCase(unittest.TestCase):
    "TestCase class for the PointCloud class."
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_xyzPlane_fit(self):
        """
        Test the xyzPlane_fit function.  The 4-sigma clipped value and
        plane fit parameters should be stable after adding >7-sigma
        outliers.
        """
        seed = 98029421
        np.random.seed(seed)
        a, b, c = 5, 2, -1
        xyz_plane = XyzPlane(a, b, c)
        mean = 10
        sigma = 3
        gaussian = scipy.stats.norm(loc=mean, scale=sigma)
        positions = np.array([xy for xy in
                              itertools.product(range(100), range(100))])
        x, y = positions.transpose()
        z = xyz_plane(positions) + gaussian.rvs(size=len(x))
        pc = PointCloud(x, y, z)
        fitted_plane = pc.xyzPlane_fit(nsigma=4)

        # Add some >7 sigma points
        xy_sample = lambda: np.random.uniform(0, max(x), size=5)
        new_positions = np.array([xy for xy in
                                  itertools.product(xy_sample(), xy_sample())])
        xx, yy = new_positions.transpose()
        zz = np.array(xyz_plane(new_positions) +
                      np.abs(gaussian.rvs(size=len(xx))) + 7*sigma)
        pc_new = pc + PointCloud(xx, yy, zz)
        fitted_plane_new = pc_new.xyzPlane_fit(nsigma=4)

        self.assertAlmostEqual(pc_new.stdev_filt, pc.stdev_filt)
        for i in range(len(fitted_plane.pars)):
            self.assertAlmostEqual(fitted_plane.pars[0],
                                   fitted_plane_new.pars[0])

if __name__ == '__main__':
    unittest.main()
