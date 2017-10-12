"""
Evaluates the fraction of a sensor surface outside the nominal allowed range, using
absolute height quantiles
"""
from __future__ import print_function
import os
import unittest
from MetrologyData import md_factory, XyzPlane
import metUtils

class fracOutsideITLTestCase(unittest.TestCase):
    "TestCase class for frac_outside for ITL absolute height."
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_frac_outside(self):
        """
        Verifies evaluation of the fraction of a sensor surface outside the
        allowed range (+/-9 microns from Znom)
        """
        infile = os.path.join(os.environ['METROLOGYDATAANALYSISDIR'], 'tests',
                                         'ITL_vendor_metrology_data.txt')
        dtype = 'ITL'

        sensorData = md_factory.create(infile, dtype=dtype)

        # Set reference plane at Znom=12.992 mm
        #
        sensorData.set_ref_plane(XyzPlane(0, 0, 12992.))

        sensorData.quantile_table()

        frac_outside = metUtils.frac_outside(sensorData.quantiles)

        # Check against previous result
        #
        self.assertAlmostEqual(frac_outside, 0.0)

        # Shift down so middle of distribution is right at -9
        shift = 9 + sensorData.quantiles['0.500']
        for key in sensorData.quantiles:
            sensorData.quantiles[key] -= shift

        frac_outside = metUtils.frac_outside(sensorData.quantiles)
        # Check against expected result
        #
        self.assertAlmostEqual(frac_outside, 0.5)

        # Shift up so middle of distribution is right at +9
        for key in sensorData.quantiles:
            sensorData.quantiles[key] += 18

        frac_outside = metUtils.frac_outside(sensorData.quantiles)
        # Check against expected result
        #
        self.assertAlmostEqual(frac_outside, 0.5)

if __name__ == '__main__':
    unittest.main()
