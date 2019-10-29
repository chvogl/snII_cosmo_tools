import numpy as np
import pandas as pd
import astropy.units as units
import matplotlib.pyplot as plt
from astropy.cosmology import Planck15
from astropy.coordinates import SkyCoord
from astropy.table import Table, hstack


class RedshiftCatalogue(object):
    comp_repr = slice(None)

    def __init__(self, fname, min_z=1e-2, max_z=0.5):
        self.data = pd.HDFStore(fname, mode='r').data
        self.data_description = pd.HDFStore(fname, mode='r').description
        self.data = self.data[self.data.z > min_z]
        self.data = self.data[self.data.z < max_z]
        self.coords = self.get_sky_coords(self.data)
        self.arcsec_per_kpc = Planck15.arcsec_per_kpc_proper(self.data.z)

    @staticmethod
    def get_sky_coords(data):
        return SkyCoord(data.RA, data.dec,
                        frame="icrs", unit=units.deg)

    def find_host_z(self, target_coords, mag=0.0, max_dist_kpc=20.):
        sep = self.coords.separation(target_coords).to(units.arcsec).value
        sep /= self.arcsec_per_kpc.value
        matches = self.data[sep < max_dist_kpc]
        matches.insert(0, 'd_proj[kpc]', sep[sep < max_dist_kpc])
        if len(matches) > 0:
            self.insert_mu_absmag_in_frame(matches, matches.z.values, mag)

        matches = matches.sort_values('d_proj[kpc]')
        return matches

    @staticmethod
    def insert_mu_absmag_in_frame(frame, z, mag):
        mu = Planck15.distmod(z).value
        abs_mag = mag - mu
        frame.insert(1, 'mu', mu)
        frame.insert(2, 'abs_mag', abs_mag)

    @classmethod
    def get_tns_host_from_row(cls, row):
        redshift_table = None
        if np.isfinite(row['Host Redshift']):
            redshift_table = pd.DataFrame(row.values[np.newaxis, :],
                                          columns=row.index)
            redshift_table = redshift_table[['Host Name', 'Host Redshift']]
            cls.insert_mu_absmag_in_frame(
                redshift_table, z=row.loc['Host Redshift'],
                mag=row['Discovery Mag']
            )
            redshift_table = redshift_table.rename(
                columns={'Host Redshift': 'z'}
            )
            return redshift_table[["z", "Host Name", "mu", "abs_mag"]]

    # TODO: improve logic
    def generate_aladin_table(self, m):
        coords = self.get_sky_coords(m)
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

    def plot(self, fig=None):
        ra_rad = self.coords.ra.wrap_at(180 * units.deg).radian
        dec_rad = self.coords.dec.radian
        if not fig:
            fig = plt.figure()
        plt.subplot(111, projection="aitoff")
        plt.grid(True)
        plt.scatter(ra_rad, dec_rad, s=1.5, alpha=0.1)
        plt.subplots_adjust(top=0.95, bottom=0.0)
        return fig


class GladeRedshiftCatalogue(RedshiftCatalogue):
    short_name = 'glade'
    comp_repr = ['z', 'flag1', 'd_proj[kpc]', 'PGC', 'GWGC name',
                 'HyperLEDA name', '2MASS name', 'SDSS-DR12 name', 'dist',
                 'dist_err', 'flag2', 'mu', 'abs_mag']


class TwodFRedshiftCatalogue(RedshiftCatalogue):
    short_name = '2dF'
    comp_repr = ['z', 'name', 'spectra', 'ra2000',
                 'dec2000', 'BJG', 'BJSEL', 'GALEXT',
                 'SB_BJ', 'z_helio', 'quality', 'abemma',
                 'Z_ABS', 'Z_EMI', 'NMBEST', 'SNR', 'mu', 'abs_mag']

    @staticmethod
    def get_sky_coords(data):
        return SkyCoord(data.ra2000, data.dec2000,
                        unit=(units.hourangle, units.deg))


class SixdFRedshiftCatalogue(RedshiftCatalogue):
    short_name = '6dF'
    comp_repr = ['z', 'TARGETNAME', 'ra', 'dec', 'mu', 'abs_mag']

    @staticmethod
    def get_sky_coords(data):
        return SkyCoord(data.ra, data.dec,
                        unit=(units.hourangle, units.deg))


class SDSSRedshiftCatalogue(RedshiftCatalogue):
    short_name = 'sdss'

    @staticmethod
    def get_sky_coords(data):
        return SkyCoord(data.ra, data.dec, frame="icrs", unit=units.deg)
