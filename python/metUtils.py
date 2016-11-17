import os
import glob
import fnmatch
import lcatr.schema
from DataCatalog import DataCatalog
import siteUtils

def aggregate_filerefs(producer, testtype, origin=None, dp_mapping=None):
    """
    Aggregate the filerefs for the metrology data products and return
    them as a python list.
    """
    if origin is None:
        origin = siteUtils.getSiteName()

    if dp_mapping is None:
        dp_mapping = dict(BOXPLOT='boxplot',
                          HISTOGRAM='hist',
                          POINT_CLOUD_10='point_cloud_azim_10',
                          POINT_CLOUD_45='point_cloud_azim_45',
                          RESIDUALS='residuals',
                          QUANTILE_TABLE='quantile_table')

    # Common metadata fields for all data products.
    ccd_vendor = siteUtils.getCcdVendor()
    sensor_id = siteUtils.getUnitId()
    md = siteUtils.DataCatalogMetadata(CCD_MANU=ccd_vendor,
                                       LSST_NUM=sensor_id,
                                       PRODUCER=producer,
                                       ORIGIN=origin,
                                       TESTTYPE=testtype,
                                       TEST_CATEGORY='MET')

    # Create filerefs for each data product, adding the file-specific
    # data product metadata.
    tt_ext = testtype.lower()
    results = []
    for dp, ext in dp_mapping.items():
        pattern = '%(sensor_id)s_%(tt_ext)s_*%(ext)s.*'% locals()
        dp_files = glob.glob(pattern)
        results.extend([lcatr.schema.fileref.make(dp_file,
                                                  metadata=md(DATA_PRODUCT=dp))
                        for dp_file in dp_files])

    return results

def aggregate_filerefs_ts5(producer, testtype, origin=None, dp_mapping=None):
    """
    Aggregate the filerefs for the TS5 metrology data products and return
    them as a python list.
    """
    if origin is None:
        origin = siteUtils.getSiteName()

    if dp_mapping is None:
        dp_mapping = dict(BOXPLOT='boxplot',
                          HISTOGRAM='hist',
                          POINT_CLOUD_10='point_cloud_azim_10',
                          POINT_CLOUD_45='point_cloud_azim_45',
                          RESIDUALS='residuals',
                          QUANTILE_TABLE='quantile_table')

    # Common metadata fields for all data products.
    ccd_vendor = siteUtils.getCcdVendor()
    raft_id = siteUtils.getUnitId()
    md = siteUtils.DataCatalogMetadata(CCD_MANU=ccd_vendor,
                                       RAFTNAME = raftname,
                                       LSST_NUM=raft_id,
                                       PRODUCER=producer,
                                       ORIGIN=origin,
                                       TESTTYPE=testtype,
                                       TEST_CATEGORY='MET')

    # Create filerefs for each data product, adding the file-specific
    # data product metadata.
    tt_ext = testtype.lower()
    results = []
    for dp, ext in dp_mapping.items():
        pattern = '%(raft_id)s_%(tt_ext)s_*%(ext)s.*'% locals()
        dp_files = glob.glob(pattern)
        results.extend([lcatr.schema.fileref.make(dp_file,
                                                  metadata=md(DATA_PRODUCT=dp))
                        for dp_file in dp_files])

    return results

def _folder(sensor_id, root_folder='LSST/vendorData'):
    # CCD manufacturer is specified differently in the LSST/vendorData
    # and LSST/mirror/SLAC-prod/prod folders, e.g., 'ITL' vs
    # 'ITL-CCD', so append a wildcard: 'ITL*'.
    ccd_manu = sensor_id.split('-')[0] + '*'
    my_folder = os.path.join(root_folder, ccd_manu, sensor_id)
    return my_folder

def get_met_scan_data(sensor_id, pattern, root_folder='LSST/vendorData',
                      site='slac.lca.archive', sort=False,
                      description='Metrology Scan Files:'):
    try:
        folder = os.environ['LCATR_DATACATALOG_FOLDER']
    except KeyError:
        folder = _folder(sensor_id, root_folder=root_folder)

    dc = DataCatalog(folder=folder, site=site)

    query = '&&'.join(('DATA_PRODUCT=="MET_SCAN"',
                       'TEST_CATEGORY=="MET"',
                       'LSST_NUM=="%(sensor_id)s"'))
    query = query % locals()

    datasets = dc.find_datasets(query)
    file_list = []
    for item in datasets.full_paths():
        if fnmatch.fnmatch(os.path.basename(item), pattern):
            file_list.append(item)
    if sort:
        file_list = sorted(file_list)
    siteUtils.print_file_list(description, file_list)
    return file_list

if __name__ == '__main__':
#    get_met_scan_data('e2v-CCD250-11093-10-04', '*.csv')
    get_met_scan_data('ITL-3800C-033', '*.txt')
