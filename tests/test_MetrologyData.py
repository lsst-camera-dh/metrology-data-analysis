from __future__ import print_function
import unittest
import numpy as np
import scipy.stats
import itertools
from MetrologyData import MetrologyData, PointCloud

class PointCloudTestCase(unittest.TestCase):
    "TestCase class for the PointCloud class."
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_xyzPlane_fit(self):
        """
        Test the xyzPlane_fit function.  The 4-sigma clipped value
        should be stable after adding >7-sigma outliers.
        """
        seed = 98029421
        np.random.seed(seed)
        mean = 10
        sigma = 3
        gaussian = scipy.stats.norm(loc=mean, scale=sigma)
        x, y = np.array([xy for xy in
                         itertools.product(range(100), range(100))]).transpose()
        z = gaussian.rvs(size=len(x))
        pc = PointCloud(x, y, z)
        pc.xyzPlane_fit(nsigma=4)

        # Add some >7 sigma points
        xy_sample = lambda: np.random.uniform(0, max(x), size=5)
        xx, yy = np.array([xy for xy in
                           itertools.product(xy_sample(), xy_sample())]).transpose()
        zz = np.array(np.abs(gaussian.rvs(size=len(xx))) + 7*sigma)
        pc_new = pc + PointCloud(xx, yy, zz)
        pc_new.xyzPlane_fit(nsigma=4)
        self.assertAlmostEqual(pc_new.stdev_filt, pc.stdev_filt)

if __name__ == '__main__':
    unittest.main()
