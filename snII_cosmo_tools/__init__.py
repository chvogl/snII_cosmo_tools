import glob
from .style import (highlight_dec_cut, highlight_visibility,
                    insert_tns_links_into_df,
                    insert_survey_links_into_df,
                    highlight_gal_lat, get_styled_html_table,
                    highlight_general_traffic_light)
from .tns_downloader import (TNSDownloader, TNSSpectrum,
                             TNSDownloadError, ZtfLightCurveDownloader)
from .filter_targets import TargetFilter, InteractiveTargetFilter
from .visibility import insert_max_alt_in_frame, insert_gal_lat_in_frame
from .visualization import TargetVisualizer
from .visibility import Visibility, InteractiveVisibility
from .redshift import GladeRedshiftCatalogue, TwodFRedshiftCatalogue
from .ob_generation import OBGenerator

json_keyfile_names = glob.glob('auth/*.json')
if json_keyfile_names:
    from .archive_targets import GspreadTargetArchiver as TargetArchiver
    TargetArchiver.json_keyfile_name = json_keyfile_names[0]
    print('Logging to google spreadsheet!')
else:
    print('There is no JSON keyfile in the auth folder!\nLogging to hdf file!')
    from .archive_targets import LocalTargetArchiver as TargetArchiver
