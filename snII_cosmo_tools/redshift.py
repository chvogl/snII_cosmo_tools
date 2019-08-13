import pandas as pd
import astropy.units as units
from astropy.cosmology import Planck15
from astropy.coordinates import SkyCoord
from astropy.table import Table, hstack


class GladeRedshiftCatalogue(object):
    comp_repr = ['z', 'flag1', 'd_proj[kpc]', 'PGC', 'GWGC name',
                 'HyperLEDA name', '2MASS name', 'SDSS-DR12 name', 'dist',
                 'dist_err', 'flag2', 'mu', 'abs_mag']

    def __init__(self, fname, min_z=1e-3, max_z=0.5):
        self.data = pd.HDFStore(fname, mode='r').data
        self.data_description = pd.HDFStore(fname, mode='r').description
        self.data = self.data[self.data.z > min_z]
        self.data = self.data[self.data.z < max_z]
        self.coords = SkyCoord(self.data.RA, self.data.dec,
                               frame="icrs", unit=units.deg)
        self.arcsec_per_kpc = Planck15.arcsec_per_kpc_proper(self.data.z)

    def find_host_z(self, target_coords, mag=0.0, max_dist_kpc=20.):
        sep = self.coords.separation(target_coords).to(units.arcsec).value
        sep /= self.arcsec_per_kpc.value
        matches = self.data[sep < max_dist_kpc]
        matches.insert(0, 'd_proj[kpc]', sep[sep < max_dist_kpc])
        if len(matches) > 0:
            mu = Planck15.distmod(matches.z.values).value
            abs_mag = mag - mu
            matches.insert(1, 'mu', mu)
            matches.insert(2, 'abs_mag', abs_mag)

        matches = matches.sort_values('d_proj[kpc]')
        return matches

    # TODO: improve logic
    def generate_aladin_table(self, m):
        coords = SkyCoord(m.RA, m.dec, unit=units.deg)
        ra = coords.ra.to_string(units.hourangle, sep=':')
        dec = [coord.split(' ')[1] for coord in coords.to_string('hmsdms')]
        dec = [
            dec1.replace('d', ':').replace(
                'm', ':').replace('s', '') for dec1 in dec
        ]
        coord_table = Table([ra, dec], names=['RA', 'DEC'])
        host_info_table = Table.from_pandas(m[self.comp_repr])
        return hstack([coord_table, host_info_table])

    def find_host_z_from_row(self, row, max_dist_kpc=20.):
        target_coords = SkyCoord(row.RA, row.DEC, unit=(units.hourangle,
                                                        units.deg))

        return self.find_host_z(target_coords, mag=row['Discovery Mag'],
                                max_dist_kpc=max_dist_kpc)
