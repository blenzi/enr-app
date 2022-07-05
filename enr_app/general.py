__doc__ = """Fonctions, elements (barre laterale, données, sélections) et définitions 
globales pour l'application"""

import streamlit as st
import pandas as pd
import geopandas as gpd


@st.cache
def load_zones():  # FIXME
    regions = pd.read_json('https://geo.api.gouv.fr/regions').rename(columns={'nom': 'Zone', 'code': 'CodeZone'})
    departements = pd.read_json('https://geo.api.gouv.fr/departements')\
        .rename(columns={'nom': 'Zone', 'code': 'CodeZone'})\
        .merge(regions.rename(columns={'Zone': 'Region', 'CodeZone': 'codeRegion'}), on='codeRegion')
    epcis = pd.read_csv('data/epcis.csv')\
        .merge(departements.rename(columns={'Zone': 'Departement'}), left_on='DEPARTEMENTS_DE_L_EPCI', right_on='CodeZone')\
        .drop(columns=['CodeZone', 'DEPARTEMENTS_DE_L_EPCI'])\
        .rename(columns={'EPCI': 'CodeZone', 'NOM_EPCI': 'Zone'})
    zones = pd.concat([regions, departements, epcis], keys=['Régions', 'Départements', 'Epci']) \
        .reset_index().rename(columns={'level_0': 'TypeZone'})\
        .drop(columns=['level_1', 'codeRegion'])\
        .sort_values(['TypeZone', 'Zone'])
    return zones


zones = load_zones()

@st.cache
def load_installations():
    installations = gpd.read_file('data/installations.gpkg', layer='installations').to_crs(epsg=4326)
    return installations[~installations.geometry.is_empty]

@st.cache
def load_indicateurs():
    indicateurs = pd.read_csv('data/Enedis_com_a_reg_all.csv', index_col=0)\
        .merge(zones, on=['TypeZone', 'CodeZone'])\
        .pivot_table(
            index=['TypeZone', 'Zone', 'Filiere.de.production', 'annee'],
            values='valeur',
            columns='indicateur')

    indicateurs = pd.concat(
        [indicateurs.reset_index(),
         indicateurs.loc['Régions'].reset_index().groupby(
             ['Filiere.de.production', 'annee']).sum().reset_index().assign(TypeZone='Régions', Zone='Toutes')
         #      indicateurs.reset_index().replace('Pays de la Loire', 'Toutes').query('TypeZone == "Régions" and Zone == "Toutes"')
         ]
    ).set_index(['TypeZone', 'Zone', 'Filiere.de.production', 'annee'])
    return indicateurs

filieres = load_indicateurs().index.get_level_values('Filiere.de.production').unique().to_list()

# Defaults
region_default = 'Toutes'
departement_default = 'Tous'
epci_default = 'Tous'

st.session_state['region'] = region_default
st.session_state['departement'] = departement_default
st.session_state['EPCI'] = epci_default

liste_regions = [region_default] + zones.set_index('TypeZone').loc['Régions', 'Zone'].to_list()

st.session_state['filieres'] = {x: True for x in filieres}

def select_zone():
    """
    Sélectionne le territoire (région, département, EPCI) à travers 3 menus déroulants

    Returns: type zone (Régions, Départements ou Epci), zone (nom)
    """
    def on_change_region():
        st.session_state['departement'] = departement_default
        st.session_state['EPCI'] = epci_default

    def on_change_department():
        st.session_state['EPCI'] = epci_default

    st.session_state['region'] = st.sidebar.selectbox('Région', liste_regions,
                                                      liste_regions.index(st.session_state['region']),
                                                      on_change=on_change_region)

    # Restreint les départements et EPCIs à la région / département choisi
    reg = st.session_state['region'] if st.session_state['region'] != region_default else slice(None)
    liste_departements = [departement_default] + \
                         zones.set_index(['TypeZone', 'Region']).loc[('Départements', reg), 'Zone'].to_list()
    st.session_state['departement'] = st.sidebar.selectbox('Département', liste_departements,
                                                           liste_departements.index(st.session_state['departement']),
                                                           on_change=on_change_department)

    dep = st.session_state['departement'] if st.session_state['departement'] != departement_default else slice(None)
    try:
        liste_epcis = [epci_default] + zones.set_index(['TypeZone', 'Region', 'Departement'])\
            .loc[('Epci', reg, dep), 'Zone']\
            .drop_duplicates().to_list()
    except:  # FIXME
        liste_epcis = [epci_default] + zones.set_index('TypeZone').loc['Epci', 'Zone'].to_list()
    st.session_state['EPCI'] = st.sidebar.selectbox('EPCI', liste_epcis,
                                                    liste_epcis.index(st.session_state['EPCI']))

    if st.session_state['EPCI'] != epci_default:
        st.session_state['TypeZone'] = 'Epci'
        st.session_state['Zone'] = st.session_state['EPCI']
    elif st.session_state['departement'] != departement_default:
        st.session_state['TypeZone'] = 'Départements'
        st.session_state['Zone'] = st.session_state['departement']
    else:
        st.session_state['TypeZone'] = 'Régions'
        st.session_state['Zone'] = st.session_state['region']
    return st.session_state['TypeZone'], st.session_state['Zone']

def select_filieres():
    """
    Sélectionne les filières à considérer avec une checkbox par filière

    Returns: un dictionnaire avec filière, True/False
    """
    st.sidebar.write('Filières')
    st.session_state['filieres'] = {fil: st.sidebar.checkbox(fil, st.session_state['filieres'].get(fil, True))
                                    for fil in filieres}
    return [k for k, v in st.session_state['filieres'].items() if v]

def select_installations(type_zone, zone, filiere=None):
    """
    Sélectionne les installations

    Args:
        type_zone: str, (Régions, Départements ou Epci)
        zone: str, nom de la zone
        filiere: list (default: None)

    Returns: DataFrame avec les installations sélectionnées
    """
    installations = load_installations()
    column = {'Régions': 'NOM_REG',
              'Départements': 'NOM_DEP',
              'Epci': 'NOM_EPCI'}[type_zone]
    if type_zone != 'Régions' or zone != region_default:
        installations = installations.query(f'{column} == "{zone}"')
    if len(installations) and filiere is not None:
        selected_filieres = []
        if 'Photovoltaïque' in filiere:
            selected_filieres.extend(['solaire photovoltaïque', 'solaire thermodynamique'])
        if 'Eolien' in filiere:
            selected_filieres.extend(['éolien terrestre', 'éolien marin'])
        if 'Bio Energie' in filiere:
            selected_filieres.extend(['méthanisation'])
        return installations.loc[installations.typo.isin(selected_filieres)]
    return installations

def select_indicateur(type_zone, zone, filiere=slice(None), annee=slice(None), indicateur=slice(None)):
    """
    Sélectionne un ou plusieurs indicateurs

    Args:
        type_zone: str, (Régions, Départements ou Epci)
        zone: str, nom de la zone
        filiere: liste ou valeur (default: toutes)
        annee: liste ou valeur (default: tous)
        indicateur: liste ou valeur (default: tous)

    Returns: DataFrame avec le(s) indicateur(s) sélectionné(s)

    """
    return load_indicateurs().loc[(type_zone, zone, filiere, annee), indicateur]
