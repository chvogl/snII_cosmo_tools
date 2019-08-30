import os
import bs4
import gspread
import getpass
import datetime
import warnings
import pandas as pd
from ipywidgets import Textarea, Button, Dropdown
from oauth2client.service_account import ServiceAccountCredentials


class TargetArchiver(object):
    def __init__(self, row):
        self.row = row
        self.name = row.name
        self.button = Button(description='Archive object!')
        self.button.style.button_color = 'orange'
        self.text = Textarea(
            value='',
            placeholder='Add comment on object!',
            description='Comment:',
            disabled=False
        )
        self.destination = Dropdown(
            options=['classification targets', 'misc'],
            value='classification targets',
            description='Archive as:',
            disabled=False,
        )
        self.check_if_archived()
        self.button.on_click(self.on_button_clicked)

    def on_button_clicked(self, b):
        self.deactivate_button()
        self.archive()

    def deactivate_button(self):
        self.button.style.button_color = 'green'
        self.button.disabled = True
        self.button.description = u"Archived \u2713"

    @property
    def row_with_comment(self):
        row_with_comment = self.row.append(
            pd.Series({'Comment': self.text.value})
        )
        row_with_comment = row_with_comment.append(
            pd.Series({'Time archived': self.time_now})
        )
        row_with_comment = row_with_comment.append(
            pd.Series({'Archived by': getpass.getuser()})
        )
        return row_with_comment

    @property
    def row_with_comment_frame(self):
        return pd.DataFrame(
            self.row_with_comment.values.reshape(1, -1),
            columns=self.row_with_comment.index,
            index=[self.row.name]
        )

    def archive(self):
        pass

    def check_if_archived(self):
        pass

    @property
    def time_now(self):
        return datetime.datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        )


class LocalTargetArchiver(TargetArchiver):
    def __init__(self, row, archive_path='data/targets_archive.hdf'):
        self.archive_path = archive_path
        super().__init__(row)

    def archive(self):
        with pd.HDFStore(self.archive_path) as hdf:
            if '/archived_targets' not in hdf.keys():
                archived_targets = self.row_with_comment_frame
            else:
                archived_targets = pd.concat(
                    [hdf.archived_targets, self.row_with_comment_frame]
                )
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                hdf.put('archived_targets', archived_targets)

    def check_if_archived(self):
        if os.path.isfile(self.archive_path):
            with pd.HDFStore(self.archive_path) as hdf:
                if self.name in hdf['/archived_targets'].index:
                    self.deactivate_button()


class GspreadTargetArchiver(TargetArchiver):
    json_keyfile_name = None  # is set in __init__.py
    scope = ['https://spreadsheets.google.com/feeds',
             'https://www.googleapis.com/auth/drive']

    def __init__(self, row):
        self.credentials = ServiceAccountCredentials.from_json_keyfile_name(
            self.json_keyfile_name, self.scope
        )
        self.client = gspread.authorize(self.credentials)
        self.sheet = self.client.open('snII_cosmo_targets_archive')
        self._gspread_columns = None
        super().__init__(row)

    def archive(self):
        row = self.row_with_comment.astype(str).to_list()
        self.sheet.worksheet(self.destination.value).insert_row(row, 2)

    @property
    def archived_objects(self):
        archived_objects = pd.DataFrame(self.sheet.sheet1.get_all_records(),
                                        columns=self.gspread_columns)
        archived_objects.index = self.get_name_from_href(archived_objects.Name)
        archived_objects.index.name = 'Name'
        return archived_objects

    @property
    def gspread_columns(self):
        if not self._gspread_columns:
            self._gspread_columns = self.sheet.sheet1.row_values(1)
        return self._gspread_columns

    @staticmethod
    def get_name_from_href(html_refs):
        names = [
            bs4.BeautifulSoup(html_ref,
                              'html.parser').text for html_ref in html_refs
        ]
        return names
