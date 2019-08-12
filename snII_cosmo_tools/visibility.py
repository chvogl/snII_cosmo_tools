import numpy as np
import matplotlib.pyplot as plt
import astropy.units as u
from datetime import datetime
from astropy.time import Time
from astropy.coordinates import SkyCoord, EarthLocation, AltAz, get_sun


paranal = EarthLocation.of_site('paranal')


class Visibility(object):
    def __init__(self, skycoord, date=None, utcoffset=(-4 * u.hour),
                 location=None):
        if not date:
            date = datetime.strftime(datetime.now(), '%Y-%m-%d')
        if not location:
            location = paranal
        self.location = location
        self.date = date
        self.midnight = Time(self.date + ' 23:59:59') - utcoffset
        self.skycoord = skycoord
        self.delta_midnight = np.linspace(-12, 12, 100) * u.hour
        self.frame = AltAz(obstime=self.midnight + self.delta_midnight,
                           location=self.location)

    @property
    def alt(self):
        return self.skycoord.transform_to(self.frame).alt

    @property
    def sun_alt(self):
        return get_sun(self.delta_midnight + self.midnight).transform_to(
            self.frame).alt

    @property
    def night_mask(self):
        return self.sun_alt < -18. * u.deg

    @property
    def time(self):
        return self.midnight + self.delta_midnight

    @property
    def max_alt(self):
        return self.alt[self.night_mask].max()

    @property
    def start_night(self):
        return self.delta_midnight[self.sun_alt < -18 * u.deg].min()

    @property
    def end_night(self):
        return self.delta_midnight[self.sun_alt < -18 * u.deg].max()

    def plot(self):
        fig = plt.figure()
        plt.plot(self.delta_midnight, self.alt)
        plt.xlim(-12, 12)
        plt.xticks(np.arange(13) * 2 - 12)
        plt.ylim(0, 90)
        plt.fill_between([self.start_night.value,
                          self.end_night.value], 0, 90,
                         color='0.5', zorder=0)
        plt.xlabel('Hours from Midnight')
        plt.ylabel('Altitude [deg]')
        return fig


def get_max_alt_from_frame(df):
    max_alt = []
    for index, row in df.iterrows():
        coord = SkyCoord(row.RA, row.DEC, unit=(u.hourangle, u.deg))
        vis = Visibility(skycoord=coord)
        max_alt.append(vis.max_alt.value)
    return np.array(max_alt)


def get_gal_latitude_from_frame(df):
    gal_lat = []
    for index, row in df.iterrows():
        coord = SkyCoord(row.RA, row.DEC, unit=(u.hourangle, u.deg))
        gal_lat.append(coord.galactic.b.value)
    return np.array(gal_lat)


def insert_max_alt_in_frame(df):
    max_alt = get_max_alt_from_frame(df)
    df = df.copy()
    df.insert(len(df.columns), 'max_alt', max_alt)
    return df


def insert_gal_lat_in_frame(df):
    gal_lat = get_gal_latitude_from_frame(df)
    df = df.copy()
    df.insert(len(df.columns), 'gal_lat', gal_lat)
    return df
