__doc__ = "Fonctions pour produire une carte des installations"

import geopandas as gpd
import streamlit as st
import folium
from enr_app.general import region_default, load_zones, open_file


@st.cache
def load_contour_regions():
    with open_file('installations.gpkg', 'rb') as file_in:
        return gpd.read_file(file_in, layer='regions').to_crs(epsg=4326)


@st.cache
def load_contour_departements():
    with open_file('installations.gpkg', 'rb') as file_in:
        return gpd.read_file(file_in, layer='departements').to_crs(epsg=4326)


@st.cache
def load_contour_EPCIs():
    with open_file('installations.gpkg', 'rb') as file_in:
        return gpd.read_file(file_in, layer='EPCIs').to_crs(epsg=4326)


def get_zoom(type_zone, zone):
    """
    Retourne le zoom pour la carte, selon le type de zone (EPCI, département, région, toute la France)
    Args:
        type_zone: str ('Epci', 'départements', 'régions')
        zone: str

    Returns:

    """
    if type_zone == 'Epci':
        return 8
    elif type_zone == 'Départements':
        return 7
    elif zone != region_default:
        return 6
    return 5


def get_map(type_zone, zone):
    if type_zone == 'Régions' and zone == region_default:
        contour = load_contour_regions().query("REG > '10'")
    elif type_zone == 'Régions':
        contour = load_contour_regions().query(f'NOM_REG == "{zone}"')
        # location = [contour_zone.centroid.y, contour_zone.centroid.x]
    elif type_zone == 'Départements':
        contour = load_contour_departements().query(f'NOM_DEP == "{zone}"')
        # location = [contour_zone.centroid.y, contour_zone.centroid.x]
    elif type_zone == 'Epci':
        contour = load_contour_EPCIs().query(f'Zone == "{zone}"')
        if not len(contour):  # FIXME: entrées manquantes ?
            dep = load_zones().set_index(['TypeZone', 'Zone']).loc[(type_zone, zone), 'Departement'].values[0]
            contour = load_contour_departements().query(f'NOM_DEP == "{dep}"')
    else:
        raise ValueError(f'Invalid type_zone: {type_zone}')
    location = [contour.geometry.apply(lambda g: g.centroid.y).mean(),
                contour.geometry.apply(lambda g: g.centroid.x).mean()]

    ign = 'https://wxs.ign.fr/essentiels/geoportail/wmts?REQUEST=GetTile&SERVICE=WMTS&VERSION=1.0.0&STYLE=normal&TILEMATRIXSET=PM&FORMAT=image/png&LAYER=GEOGRAPHICALGRIDSYSTEMS.PLANIGNV2&TILEMATRIX={z}&TILEROW={y}&TILECOL={x}' # noqa
    mapa = folium.Map(tiles=ign,
                      attr='<a target="_blank" href="https://www.geoportail.gouv.fr/">Geoportail France</a>',
                      min_zoom=2,
                      max_zoom=18,
                      location=location,
                      zoom_start=get_zoom(type_zone, zone)
                      )
    gjson = folium.GeoJson(contour, name=type_zone)
    gjson.add_to(mapa)
    return mapa
