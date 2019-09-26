import numpy as np
from snII_cosmo_tools.tns_downloader import TNSDownloader

survey_link_dict = {
    'ALeRCE': 'http://alerce.online/vue/object/',
    'ZTF': 'http://alerce.online/vue/object/',
    'ATLAS': 'https://star.pst.qub.ac.uk/sne/atlas4/',
    'Pan-STARRS1': 'https://star.pst.qub.ac.uk/sne/ps13pi/psdb/',
    'GaiaAlerts': 'http://gsaweb.ast.cam.ac.uk/alerts/alert/'
}


def highlight_dec_cut(s):
    dec = [float(s1.split(':')[0]) for s1 in s]
    above_cut = np.array(dec) >= 25.
    return ['background-color: red' if v else '' for v in above_cut]


def highlight_visibility(s):
    vis = []
    for s1 in s:
        if s1 < 30.:
            vis.append('background-color: red')
        elif s1 < 45:
            vis.append('background-color: orange')
        else:
            vis.append('background-color: green')
    return vis


def highlight_general_traffic_light(s, levels=[30., 45., 90.]):
    prop = []
    for s1 in s:
        if s1 < levels[0]:
            prop.append('background-color: red')
        elif np.logical_and(s1 < levels[1], s1 < levels[2]):
            prop.append('background-color: orange')
        else:
            prop.append('background-color: green')
    return prop


def highlight_gal_lat(s):
    vis = []
    for s1 in s:
        s1 = np.abs(s1)
        if s1 < 20.:
            vis.append('background-color: red')
        elif s1 < 30:
            vis.append('background-color: orange')
        else:
            vis.append('background-color: green')
    return vis


def insert_tns_links_into_df(targets):
    links = []
    for name in targets.Name:
        link = TNSDownloader.get_object_link(name)
        links.append('<a href="{1}" target="_blank">{0}</a>'.format(
            name, link))
    names = targets.Name.copy()
    targets['Name'] = links
    return targets, names


def insert_survey_links_into_df(targets):
    links = []
    for groups, name in zip(targets['Discovering Group/s'],
                            targets['Disc. Internal Name']):
        groups = groups.split(',')
        group = groups[0]
        if group in survey_link_dict and type(name) is str:
            link = survey_link_dict[group]
            if group not in ['ATLAS', 'Pan-STARRS1']:
                link += name
            link = '<a href="{1}" target="_blank">{0}</a>'.format(name, link)
        else:
            link = name
        links.append(link)
    targets['Disc. Internal Name'] = links
    return targets


def get_styled_html_table(targets):
    return targets.style.apply(
        highlight_visibility, subset=['max_alt']).apply(
            highlight_gal_lat, subset=['gal_lat']).hide_index().render()
