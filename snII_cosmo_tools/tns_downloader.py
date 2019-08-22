import io
import re
import webbrowser
import requests
import pandas as pd
import matplotlib.pyplot as plt
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

    def __init__(self, number_of_days=1.):
        self._search = None
        self.start_date = datetime.strftime(
            datetime.now() - timedelta(number_of_days), '%Y-%m-%d')
        self.query_dict = query_dict.copy()
        self.query_dict['date_start[date]'] = self.start_date

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
