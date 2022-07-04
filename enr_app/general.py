__doc__ = """Fonctions, elements (barre laterale, données, sélections) et définitions 
globales pour l'application"""

import streamlit as st
import pandas as pd
import geopandas as gpd


@st.cache
def load_zones():  # FIXME
    return pd.read_csv('data/liste_zone_complete.csv', index_col=0)

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
    # Toutes -> Pays de la Loire, FIXME: remove
    indicateurs = pd.concat(
        [indicateurs.reset_index(),
         indicateurs.reset_index().replace('Pays de la Loire', 'Toutes').query(
             'TypeZone == "Régions" and Zone == "Toutes"')]
    ).set_index(['TypeZone', 'Zone', 'Filiere.de.production', 'annee'])

    return indicateurs

regions = pd.read_json('https://geo.api.gouv.fr/regions')
departements = pd.read_json('https://geo.api.gouv.fr/departements')\
    .merge(regions.rename(columns={'nom': 'region', 'code': 'codeRegion'}), on='codeRegion')
epcis = pd.read_csv('data/liste_zones_dep.csv', index_col=0)\
    .rename(columns={'Zone': 'nom', 'CodeZone': 'code'})
    # .merge(departements.rename(columns={'nom': 'departement'}), left_on='dep', right_on='code')  # TODO: index as character
zones = pd.concat([regions, departements, epcis], keys=['Régions', 'Départements', 'Epci'])\
    .reset_index().rename(columns={'level_0': 'TypeZone', 'nom': 'Zone', 'code': 'CodeZone'})

filieres = load_indicateurs().index.get_level_values('Filiere.de.production').unique().to_list()

# Defaults
region_default = 'Toutes'
departement_default = 'Tous'
epci_default = 'Tous'

st.session_state['TypeZone'] = 'Régions'
st.session_state['Zone'] = 'Pays de la Loire'

st.session_state['region'] = region_default
st.session_state['departement'] = departement_default
st.session_state['EPCI'] = epci_default

liste_regions = [region_default] + regions['nom'].sort_values().to_list()
liste_departements = [departement_default] + departements['nom'].sort_values().to_list()
liste_epcis = [epci_default] + zones.set_index('TypeZone').loc['Epci', 'Zone'].to_list()

st.session_state['filieres'] = filieres

def select_zone():
    """
    Sélectionne le territoire (région, département, EPCI) à travers 3 menus déroulants

    TODO: sélectionner automatiquement région quand on choisi départment ?
    TODO: changer departement/epci à default quand on choisi région/département

    :return:
    """
    st.session_state['region'] = st.sidebar.selectbox('Région', liste_regions)
    # TODO: restreindre les départements et EPCIs à la région / département choisi
    st.session_state['departement'] = st.sidebar.selectbox('Département', liste_departements)
    st.session_state['EPCI'] = st.sidebar.selectbox('EPCI', liste_epcis)

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

    :return: Un dictionnaire avec filière, True/False
    """
    st.sidebar.write('Filières')
    st.session_state['filieres'] = {fil: st.sidebar.checkbox(fil, True) for fil in filieres}
    return [k for k, v in st.session_state['filieres'].items() if v]

def select_installations(type_zone=st.session_state['TypeZone'],
                         zone=st.session_state['Zone'],
                         filieres=None):
    installations = load_installations()
    column = {'Régions': 'NOM_REG',
              'Départements': 'NOM_DEP',
              'Epci': 'NOM_EPCI'}[type_zone]
    if type_zone != 'Régions' or zone != region_default:
        installations = installations.set_index(column).loc[zone].reset_index()
    if filieres is not None:
        selected_filieres = []
        if 'Photovoltaïque' in filieres:
            selected_filieres.extend(['solaire photovoltaïque', 'solaire thermodynamique'])
        if 'Eolien' in filieres:
            selected_filieres.extend(['éolien terrestre', 'éolien marin'])
        if 'Bio Energie' in filieres:
            selected_filieres.extend(['méthanisation'])
        st.write(f'Filières sélectionnées: {selected_filieres}')
        return installations.loc[installations.typo.isin(selected_filieres)]
    return installations

def select_indicateur(type_zone=st.session_state['TypeZone'],
                      zone=st.session_state['Zone'],
                      filiere=slice(None),
                      annee=slice(None),
                      indicateur=slice(None)):
    return load_indicateurs().loc[(type_zone, zone, filiere, annee), indicateur]
