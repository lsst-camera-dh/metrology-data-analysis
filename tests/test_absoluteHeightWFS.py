"""
Executes an absolute height analysis for an ITL Wavefront Sensor vendor data set,
exercising code in plot_statistics that formerly crashed on this data
"""
from __future__ import print_function
import os
import unittest
from MetrologyData import md_factory, XyzPlane
import MetrologyData as metData

class ReferencePlaneWFSTestCase(unittest.TestCase):
    "TestCase class for plot_statistics for Wavefront Sensor absolute height."
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_plot_statistics(self):
        """
        Verifies functionality of the generation of the histogram of absolute
        height residuals for Wavefront Sensors.  The code previously crashed
        if the entire range of residuals was more than 5 sigma from zero, as
        is normally the case for Wavefront Sensors
        """
        infile = os.path.join(os.environ['METROLOGYDATAANALYSISDIR'], 'tests',
                                         'WFS_vendor_metrology_data.txt')
        dtype = 'ITL'
        sensor_id = 'ITL-4400C-033'

        sensorData = md_factory.create(infile, dtype=dtype)

        # Set reference plane at znom=12.992 mm
        #
        sensorData.set_ref_plane(XyzPlane(0, 0, 12992.))

        # Make a histogram of residual heights.  (Do not save the plot output.)
        #
        sensorData.plot_statistics(title='Sensor Absolute Height, %s' % infile)

if __name__ == '__main__':
    unittest.main()
