import astropy.units as u
from IPython.display import HTML
from astropy.coordinates import SkyCoord
from ipywidgets import Layout
import ipyaladin.aladin_widget as ipal


class TargetVisualizer(object):
    def __init__(self, coords, name, fov=0.0333, layout=None):
        if not layout:
            layout = Layout(width='40.00%')
            layout.margin = '87.5px 0px 0px 75px'
        self.coords = coords
        self.name = name
        self.aladin = ipal.Aladin(
            target=self.coords.to_string('hmsdms', sep=' '),
            layout=layout, fov=fov, survey=self.survey
        )

    @classmethod
    def from_row(cls, row, fov=0.0333, layout=None):
        coords = SkyCoord(row.RA, row.DEC, unit=(u.hourangle, u.deg))
        return cls(coords, row.name, layout=layout)

    @property
    def survey(self):
        if self.coords.dec < -30. * u.deg:
            survey = 'P/DSS2/color'  # 'P/SDSS9/color'
        else:
            survey = 'P/PanSTARRS/DR1/color-z-zg-g'
        return survey

    @property
    def html_label(self):
        return HTML("""<div style="background-color: black ;
                    padding: 10px; border: 1px solid black;">
                    <b> <font color="white">{}
                    </font> <b> </div>""".format(self.name))
