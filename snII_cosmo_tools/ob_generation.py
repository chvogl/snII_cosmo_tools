import re
import os
from astropy import units as u
from astropy.coordinates import SkyCoord


class OBGenerator(object):
    value_regex = re.compile('(?<=\")(?P<name>\S*)(?=\")') # noqa

    def __init__(self, target_name, coords,
                 template_ob='data/template_obs/ob2508588.obx',
                 prefix='TOO_', dest_path='data/generated_obs'):
        self.target_name = target_name
        self.coords = coords
        self.prefix = prefix
        self.dest_path = dest_path
        self.template_ob = template_ob

    @classmethod
    def from_row(cls, row):
        target_name = row.name
        coords = SkyCoord(row.RA, row.DEC, unit=(u.hourangle, u.deg))
        return cls(target_name, coords)

    @property
    def ra(self):
        return self.coords.to_string('hmsdms', sep=':').split(' ')[0]

    @property
    def dec(self):
        dec = self.coords.to_string('hmsdms', sep=':').split(' ')[1]
        return dec.replace('+', '')

    @classmethod
    def set_value(cls, ob, key, value):
        return [
            re.sub(cls.value_regex,
                   value, line) if re.match(key + '\s+',
                                            line) else line for line in ob
        ]

    @property
    def ob_fname(self):
        return self.prefix + self.target_name.replace(' ', '') + '.obx'

    def generate_ob(self):
        with open(self.template_ob) as f:
            ob = f.readlines()

        ob = self.set_value(ob, 'TARGET.NAME', self.target_name)
        ob = self.set_value(ob, 'ra', self.ra)
        ob = self.set_value(ob, 'dec', self.dec)

        if not os.path.isdir(self.dest_path):
            os.mkdir(self.dest_path)

        with open(os.path.join(self.dest_path, self.ob_fname), 'w+') as f:
            f.writelines(ob)

    def __call__(self, button):
        self.generate_ob()
