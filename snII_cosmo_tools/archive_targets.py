import os
import datetime
import warnings
import pandas as pd
from ipywidgets import Textarea, Button


class TargetArchiver(object):
    def __init__(self, row, archive_path='data/targets_archive.hdf'):
        self.row = row
        self.name = row.name
        self.archive_path = archive_path
        self.button = Button(description='Archive object!')
        self.button.style.button_color = 'orange'
        self.text = Textarea(
            value='',
            placeholder='Add comment on object!',
            description='Comment:',
            disabled=False
        )
        self.check_if_archived()
        self.button.on_click(self.on_button_clicked)

    def check_if_archived(self):
        if os.path.isfile(self.archive_path):
            with pd.HDFStore(self.archive_path) as hdf:
                if self.name in hdf['/archived_targets'].index:
                    self.deactivate_button()

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
        return row_with_comment

    @property
    def row_with_comment_frame(self):
        return pd.DataFrame(
            self.row_with_comment.values.reshape(1, -1),
            columns=self.row_with_comment.index,
            index=[self.row.name]
        )

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

    @property
    def time_now(self):
        return datetime.datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        )
