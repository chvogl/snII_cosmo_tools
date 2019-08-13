import io
import webbrowser
import requests
import pandas as pd
from datetime import datetime, timedelta

# http://astronotes.co.uk/blog/2016/01/28/Parsing-The-Transient-Name-Server.html
query_dict = {"date_start[date]": None,
              "date_end[date]": "2100-01-01",
              "num_page": "1000"}


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
