import io
import re
import json
import webbrowser
import requests
import pandas as pd
import numpy as np
from jinja2 import Template
from bs4 import BeautifulSoup
import matplotlib.pyplot as plt
from bokeh.plotting import figure
from bokeh.models.sources import ColumnDataSource
from bokeh.models import Arrow, Label, HoverTool
from datetime import datetime, timedelta

# http://astronotes.co.uk/blog/2016/01/28/Parsing-The-Transient-Name-Server.html
query_dict = {"date_start[date]": None,
              "date_end[date]": "2100-01-01",
              "num_page": "1000"}


class TNSDownloadError(Exception):
    pass


class TNSDownloader(object):
    url = "https://wis-tns.weizmann.ac.il/search"

    compact_repr = ['Name', 'RA', 'DEC', 'Obj. Type', 'Redshift',
                    'Host Name', 'Host Redshift', 'Discovering Group/s',
                    'Classifying Group/s', 'Disc. Internal Name',
                    'Discovery Mag', 'Discovery Mag Filter',
                    'Discovery Date (UT)']

    obj_type_keys = {'SN II': 10, 'SN Ia': 3, 'SN IIP': 11}

    def __init__(self, number_of_days=1., obj_type=None,
                 only_classified_sne=False):
        self._search = None
        self.obj_type = obj_type
        self.start_date = datetime.strftime(
            datetime.now() - timedelta(number_of_days), '%Y-%m-%d')
        self.query_dict = query_dict.copy()
        self.query_dict['date_start[date]'] = self.start_date
        if self.obj_type:
            self.query_dict['objtype[]'] = self.obj_type_keys[self.obj_type]
        if only_classified_sne:
            self.query_dict["classified_sne"] = "1"

    def query(self):
        print("Making a query!")
        self._search = requests.get(url=self.url, params=self.query_dict)
        csv_query = requests.get(self._search.url + "&format=csv")
        buff = io.StringIO(csv_query.content.decode("utf-8"))
        self._result = pd.read_csv(buff)

    def open_in_browser(self):
        webbrowser.open(self._search.url)

    def open_object_in_browser(self, name):
        webbrowser.open(self.get_object_link(name))

    @staticmethod
    def get_object_link(name):
        name = name.strip('AT ').strip('SN ')
        name = "https://wis-tns.weizmann.ac.il/object/" + name
        return name

    @property
    def result(self):
        if not hasattr(self, '_result'):
            self.query()
        return self._result

    @property
    def result_compact(self):
        return self.result[self.compact_repr]


class TNSSpectrum(object):
    spec_regex = re.compile('https:\S*\.ascii*')
    base_url = 'https://wis-tns.weizmann.ac.il/object/'

    def __init__(self, name):
        self.name = name.strip('AT').strip('SN').strip(' ')
        self._spec = None
        self._spec_url = None

    @property
    def url(self):
        return self.base_url + self.name

    @property
    def spec_url(self):
        if not self._spec_url:
            print('Retrieving spec url')
            html = requests.get(self.url)
            possible_urls = re.findall(self.spec_regex, html.text)
            N_urls = len(possible_urls)
            if N_urls != 1:
                print(possible_urls)
                raise TNSDownloadError('Found {} possible urls'.format(N_urls))
            else:
                self._spec_url = possible_urls[0]
        return self._spec_url

    @property
    def spec(self):
        if self._spec is None:
            print('Downloading spectrum')
            spec_raw = requests.get(self.spec_url)
            with io.StringIO(spec_raw.text) as spec_buff:
                if 'ePESSTO' in self.spec_url:
                    names = ['wave', 'flux']
                    sep = '\t'
                else:
                    names = ['wave', 'flux', 'idk']
                    sep = ' '
                self._spec = pd.read_csv(spec_buff, comment='#',
                                         names=names,
                                         header=None, sep=sep)
        return self._spec

    def plot(self):
        fig = plt.figure()
        plt.plot(self.spec.wave, self.spec.flux)
        plt.ylabel('Flux')
        plt.xlabel('Wavelength $[\AA]$')
        plt.title('Classification spectrum')
        return fig


class ZtfLightCurveDownloader(object):
    base_url = 'https://lasair.roe.ac.uk/object/'
    bands = ['g', 'r']
    cutout_template = Template(
        'https://lasair.roe.ac.uk/lasair/static/ztf/stamps/jpg/{{id[:3]}}/candid{{id}}.jpg'
    )

    def __init__(self, name):
        self.name = name
        self._json = None
        self._non_detections = None
        self._detections = None

    @property
    def url(self):
        return self.base_url + self.name.replace(' ', '') + '/json'

    @property
    def json(self):
        if not self._json:
            self._json = json.loads(requests.get(self.url).text)
        return self._json

    @property
    def non_detections(self):
        if not self._non_detections:
            non_detections = []
            for candidate in self.json['candidates']:
                if 'candid' not in candidate:
                    non_detections.append(candidate)
            non_detections = pd.DataFrame(non_detections)
            self._non_detections = {
                'g': non_detections[non_detections.fid == 1],
                'r': non_detections[non_detections.fid == 2]
            }
        return self._non_detections

    @property
    def detections(self):
        if not self._detections:
            detections = []
            for candidate in self.json['candidates']:
                if 'candid' in candidate:
                    detections.append(candidate)
            detections = pd.DataFrame(detections)
            self._detections = {
                'g': detections[detections.fid == 1],
                'r': detections[detections.fid == 2]
            }
        return self._detections

    def plot(self):
        hover = HoverTool(
            tooltips="""
                <img
                    src="@imgs" height="380" alt="@imgs" width="380"
                    style="float: left; margin: 15px 15px 15px 15px;"
                    border="2"
                ></img>
        """
        )

        f = figure(x_axis_label='MJD', y_axis_label='Difference Magnitude',
                   width=400, height=130)
        f.add_tools(hover)

        if self.best_non_detection is not None:
            y_arrow = 0.5 * (self.best_non_detection.magpsf + self.first_detection.magpsf)
            delta_non = str(round(self.delta_non_detection, 2)) + ' d'
            label = Label(x=self.best_non_detection.mjd,
                          y=y_arrow, text=delta_non, level='glyph',
                          x_offset=10, y_offset=20, render_mode='canvas')
            arrow = Arrow(x_start=self.first_detection.mjd,
                          y_start=y_arrow,
                          x_end=self.best_non_detection.mjd,
                          y_end=y_arrow)
            f.add_layout(arrow)
            f.add_layout(label)

        for col, band in zip(['green', 'red'], ['g', 'r']):
            f.scatter(x=self.non_detections[band].mjd,
                      y=self.non_detections[band].magpsf, legend='non-' + band,
                      color=col, alpha=0.6, size=7)
            if len(self.detections[band]) > 0:
                source = ColumnDataSource(
                    data=dict(x=self.detections[band].mjd,
                              y=self.detections[band].magpsf,
                              imgs=self.cutout_urls[band])
                )
                f.diamond(x='x', y='y', source=source, legend=band,
                          color=col, size=14)
        f.legend.click_policy = "hide"
        f.sizing_mode = 'scale_width'
        f.legend.location = "top_left"
        f.y_range.flipped = True
        return f

    @property
    def first_detection(self):
        return pd.concat(
            [self.detections[band] for band in self.bands]).sort_values(
                'mjd', ascending=True).iloc[0]

    @property
    def best_non_detection(self):
        non_detections = pd.concat(
            [self.non_detections[band] for band in self.bands]
        )
        deep_mask = non_detections.magpsf > (self.first_detection.magpsf + 0.4)
        earlier_mask = non_detections.mjd < self.first_detection.mjd
        non_detections = non_detections[np.logical_and(deep_mask,
                                                       earlier_mask)]
        if len(non_detections) > 0:
            i = np.argmin(
                (self.first_detection.mjd - non_detections.mjd).values
            )
            best_non_detection = non_detections.iloc[i]
        else:
            best_non_detection = None
        return best_non_detection

    @property
    def cutout_urls(self):
        cutout_urls = {}
        for band in self.bands:
            ids = self.detections[band].candid
            cutout_urls[band] = [
                self.cutout_template.render(id=str(id)) for id in ids
            ]
        return cutout_urls

    @property
    def delta_non_detection(self):
        return self.first_detection.mjd - self.best_non_detection.mjd
