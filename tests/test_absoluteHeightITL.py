"""
Executes an absolute height analysis for an ITL vendor data set, exercising
code in set_ref_plane that formerly crashed on this data
"""
from __future__ import print_function
import unittest
#import numpy as np
from MetrologyData import md_factory, XyzPlane

class ReferencePlaneITLTestCase(unittest.TestCase):
    "TestCase class for set_ref_plane for ITL absolute height."
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_quantile_table(self):
        """
        Verifies functionality of absolute height analysis for ITL
        sensors by generating a quantile table and comparing it
        with earlier results
        """
        infile = 'ITL_vendor_metrology_data.txt'
        dtype = 'ITL'

        sensorData = md_factory.create(infile, dtype=dtype)

        # Set reference plane at znom=12.992 mm
        #
        sensorData.set_ref_plane(XyzPlane(0, 0, 12992.))

        # Quantile table
        #
        sensorData.quantile_table(outfile='abs_height_quantile_table.txt')

        # Check against previous results for the 1.000 and 0.000 quantiles
        #
        entries = open('abs_height_quantile_table.txt', 'r')
        rows = (row.strip().split() for row in entries)
        quantiles = zip(*rows)
        self.assertAlmostEqual(float(quantiles[1][1]), 1.45)
        self.assertAlmostEqual(float(quantiles[1][11]), -5.19)

if __name__ == '__main__':
    unittest.main()
