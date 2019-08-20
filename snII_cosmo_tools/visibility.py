import numpy as np
import matplotlib.pyplot as plt
import astropy.units as u
from astropy.time import Time
from datetime import datetime, timedelta
from ipywidgets import IntSlider, interactive
from astropy.coordinates import (SkyCoord, EarthLocation,
                                 AltAz, get_sun, get_moon)


class Visibility(object):
    def __init__(self, skycoord, utcoffset=(-4 * u.hour),
                 location=None, date_offset=0):
        self.date = datetime.strftime(
            datetime.now() + timedelta(days=date_offset),
            '%Y-%m-%d'
        )
        self._date_offset = date_offset
        if not location:
            location = EarthLocation.of_site('paranal')
        self.location = location
        self.utcoffset = utcoffset
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
        return get_sun(self.time).transform_to(self.frame).alt

    @property
    def moon_alt(self):
        return get_moon(self.time).transform_to(self.frame).alt

    @property
    def moon_distance_midnight(self):
        moon_coord = get_moon(self.midnight)
        return moon_coord.separation(self.skycoord).to(u.deg).value

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

    @property
    def sun_rise(self):
        return self.delta_midnight[self.sun_alt < 0 * u.deg].max()

    @property
    def sun_set(self):
        return self.delta_midnight[self.sun_alt < 0 * u.deg].min()

    def plot(self):
        self.fig = plt.figure()
        self.line_obj = plt.plot(self.delta_midnight, self.alt)[0]
        self.line_moon = plt.plot(self.delta_midnight, self.moon_alt,
                                  linestyle='--', color='black')[0]
        moon_text = "Moon distance: {:.1f}".format(self.moon_distance_midnight)
        self.moon_distance = plt.text(-11.5, 85, moon_text, color='white',
                                      bbox=dict(facecolor='black'))
        plt.xlim(-12, 12)
        plt.xticks(np.arange(13) * 2 - 12)
        plt.ylim(0, 90)
        plt.fill_between([self.sun_rise.value, 12], 0, 90,
                         color='0.5', zorder=0)
        plt.fill_between([-12, self.sun_set.value], 0, 90,
                         color='0.5', zorder=0)
        plt.fill_between([self.end_night.value, self.sun_rise.value], 0, 90,
                         color='0.5', zorder=0, alpha=0.3)
        plt.fill_between([self.sun_set.value, self.start_night.value], 0, 90,
                         color='0.5', zorder=0, alpha=0.3)
        plt.xlabel('Hours from Midnight')
        plt.ylabel('Altitude [deg]')
        return self.fig

    @property
    def date_offset(self):
        return self._date_offset

    @date_offset.setter
    def date_offset(self, offset):
        self._date_offset = offset
        self.date = datetime.strftime(
            datetime.now() + timedelta(days=offset),
            '%Y-%m-%d'
        )
        self.midnight = Time(self.date + ' 23:59:59') - self.utcoffset
        self.frame = AltAz(obstime=self.midnight + self.delta_midnight,
                           location=self.location)

    def update_plot(self, date_offset):
        self.date_offset = date_offset
        self.line_obj.set_ydata(self.alt)
        self.line_moon.set_ydata(self.moon_alt)
        self.fig.canvas.draw_idle()
        self.moon_distance.set_text(
            "Moon distance: {:.1f}".format(self.moon_distance_midnight)
        )


class InteractiveVisibility(Visibility):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.plot()
        self.date_offset_widget = IntSlider(
            value=0,
            min=0,
            max=50,
            step=1,
            description='Days:',
            disabled=False,
            continuous_update=False,
            orientation='horizontal',
            readout=True,
            readout_format='d'
        )
        self.interactive = interactive(self.update_plot,
                                       date_offset=self.date_offset_widget)


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
