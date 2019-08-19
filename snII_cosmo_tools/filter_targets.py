import numpy as np
from ipywidgets import ToggleButtons, FloatSlider, interactive
from snII_cosmo_tools.style import get_styled_html_table
from IPython.display import display, HTML


class TargetFilter(object):
    def __init__(self, targets):
        self.targets = targets

    def filter_targets(self, obj_type, max_alt, mag_cut):
        mask_alt = self.targets.max_alt > max_alt
        mask_mag = self.targets['Discovery Mag'] > mag_cut
        mask_classified = [
            isinstance(obj_type, str) for obj_type in self.targets['Obj. Type']
        ]
        if obj_type != 'unclassified':
            mask_obj = self.targets['Obj. Type'] == obj_type
        else:
            mask_obj = np.logical_not(mask_classified)

        mask = np.logical_and(mask_alt, mask_mag)
        mask = np.logical_and(mask, mask_obj)

        N_alt = np.logical_not(mask_alt).sum()
        N_mag = np.logical_not(mask_mag).sum()
        N_obj = np.logical_not(mask_obj).sum()
        N_tot = N_alt + N_mag + N_obj

        print('Discarding {} objects: {} based on mag, {} based on alt, {} based on type'.format(
            N_tot, N_mag, N_alt, N_obj)
        )

        display(HTML(get_styled_html_table(self.targets[mask])))

        return self.targets[mask]


class InteractiveTargetFilter(TargetFilter):
    def __init__(self, targets):
        super().__init__(targets)
        self.obj_type = ToggleButtons(
            options=['unclassified', 'SN II', 'SN IIP', 'SN Ia'],
            description='Type:', disabled=False, button_style=''
        )
        self.max_alt = FloatSlider(
            value=30.,
            min=0.,
            max=90.,
            step=2.,
            description='Max alt cut:',
            disabled=False,
            continuous_update=False,
            orientation='horizontal',
            readout=True,
            readout_format='.1f',
        )
        self.mag_cut = FloatSlider(
            value=17.,
            min=10.,
            max=22.,
            step=0.25,
            description='Max mag cut:',
            disabled=False,
            continuous_update=False,
            orientation='horizontal',
            readout=True,
            readout_format='.1f',
        )

        self.interactive = interactive(self.filter_targets,
                                       obj_type=self.obj_type,
                                       max_alt=self.max_alt,
                                       mag_cut=self.mag_cut)
