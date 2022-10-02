__doc__ = """Fonctions, elements (barre laterale, données, sélections) et définitions
globales pour l'application"""

import os
import s3fs
import streamlit as st
import pandas as pd
import geopandas as gpd


# Defaults
region_default = 'Toutes'
departement_default = 'Tous'
epci_default = 'Tous'
# TODO: récupérer depuis fichier avec données
# N.B.: il faut que ce soit en ordre alphabétique pour que les couleurs et markers correspondent
filieres = ['Eolien', 'Injection de biométhane', 'Méthanisation électrique', 'Photovoltaïque']
sources = {
    'ODRÉ': 'ODRÉ [[1]](https://odre.opendatasoft.com/explore/dataset/registre-national-installation-production-stockage-electricite-agrege-311220/information/?disjunctive.epci&disjunctive.departement&disjunctive.region&disjunctive.filiere&disjunctive.combustible&disjunctive.combustiblessecondaires&disjunctive.technologie&disjunctive.regime&disjunctive.gestionnaire) [[2]](https://odre.opendatasoft.com/explore/dataset/points-dinjection-de-biomethane-en-france/information/?disjunctive.site&disjunctive.nom_epci&disjunctive.departement&disjunctive.region&disjunctive.type_de_reseau&disjunctive.grx_demandeur) [[3]](https://opendata.reseaux-energies.fr/explore/dataset/injection-annuelle-biomethane-pitp-grtgaz)',  # noqa: E501
    'ODRÉ_gaz': 'ODRÉ [[1]](https://odre.opendatasoft.com/explore/dataset/points-dinjection-de-biomethane-en-france/information/?disjunctive.site&disjunctive.nom_epci&disjunctive.departement&disjunctive.region&disjunctive.type_de_reseau&disjunctive.grx_demandeur) [[2]](https://opendata.reseaux-energies.fr/explore/dataset/injection-annuelle-biomethane-pitp-grtgaz)',  # noqa: E501
    'GDRF': '[GRDF](https://opendata.grdf.fr/explore/dataset/capacite-et-quantite-dinjection-de-biomethane)',
    'SDES': 'SDES [[1]](https://www.statistiques.developpement-durable.gouv.fr/tableau-de-bord-solaire-photovoltaique-quatrieme-trimestre-2021?rubrique=21&dossier=172) [[2]](https://www.statistiques.developpement-durable.gouv.fr/tableau-de-bord-eolien-quatrieme-trimestre-2021)',  # noqa: E501
}


def get_sources(indicateur, type_zone):
    """
    Sources des indicateurs et installations

    Args:
        indicateur: str ("installations", "puissance", "production", "nombre")
        type_zone: str (Régions, Départements ou Epci)

    Returns: string
    """
    if indicateur in ("installations", "energie_GWh"):
        return f"{sources['ODRÉ']}, {sources['GDRF']}"
    if indicateur in ("puiss_MW", "Nombre de sites"):
        return f"{sources['SDES']}, {sources['ODRÉ_gaz']}, {sources['GDRF']}" \
            if type_zone in ("Régions", "Départements") \
            else f"{sources['ODRÉ']}, {sources['GDRF']}"
    raise ValueError(f"Indicateur pas connu: {indicateur}")


def remove_page_items(menu=True, footer=True):
    """
    Remove main menu and footer

    Args:
        menu (bool, default=True): remove hamburger menu
        footer (bool, default=True): remove footer "Made with Streamlit"

    Returns: None
    """
    if menu:
        st.markdown(""" <style> #MainMenu {visibility: hidden;} </style> """, unsafe_allow_html=True)
    if footer:
        st.markdown(""" <style> footer {visibility: hidden;} </style> """, unsafe_allow_html=True)


def open_file(filename, mode='r'):
    """
    Return a file object, open with open(data/<filename>, <mode>) or fs.open(projet-connaissance-enr/filename, <mode>)
    for s3, depending if environment variable $AWS_S3_ENDPOINT is set

    Args:
        filename (str): file to open
        mode (str): open mode

    Returns:
        File object
    """
    if 'AWS_S3_ENDPOINT' in os.environ:
        # Create filesystem object
        S3_ENDPOINT_URL = "https://" + os.environ["AWS_S3_ENDPOINT"]
        fs = s3fs.S3FileSystem(client_kwargs={'endpoint_url': S3_ENDPOINT_URL})
        return fs.open(f'projet-connaissance-enr/{filename}', mode=mode)
    else:
        return open(f'data/{filename}', mode=mode)


@st.cache
def load_zones():  # FIXME
    regions = pd.read_json('https://geo.api.gouv.fr/regions').rename(columns={'nom': 'Zone', 'code': 'CodeZone'})
    departements = pd.read_json('https://geo.api.gouv.fr/departements')\
        .rename(columns={'nom': 'Zone', 'code': 'CodeZone'})\
        .merge(regions.rename(columns={'Zone': 'Region', 'CodeZone': 'codeRegion'}), on='codeRegion')
    with open_file('epcis.csv') as file_in:
        epcis = pd.read_csv(file_in)\
            .merge(departements.rename(columns={'Zone': 'Departement'}),
                   left_on='DEPARTEMENTS_DE_L_EPCI', right_on='CodeZone')\
            .drop(columns=['CodeZone', 'DEPARTEMENTS_DE_L_EPCI'])\
            .rename(columns={'EPCI': 'CodeZone', 'NOM_EPCI': 'Zone'})
    zones = pd.concat([regions, departements, epcis], keys=['Régions', 'Départements', 'Epci']) \
        .reset_index().rename(columns={'level_0': 'TypeZone'})\
        .drop(columns=['level_1', 'codeRegion'])\
        .sort_values(['TypeZone', 'Zone'])
    return zones


@st.cache
def load_installations():
    with open_file('app.gpkg', 'rb') as file_in:
        return gpd.read_file(file_in, layer='installations')


@st.cache
def load_installations_biogaz():
    with open_file('installations.gpkg', 'rb') as file_in:
        return gpd.read_file(file_in, layer='installations_biogaz')\
            .to_crs(epsg=4326)\
            .rename(columns={'nom_du_projet': 'nominstallation',
                             'date_de_mes': 'date_inst',
                             'quantite_annuelle_injectee_en_mwh': 'prod_MWh_an',
                             'type': 'typo'}) \
            .assign(Filière='Injection de biométhane',
                    puiss_MW=lambda x: x['capacite_de_production_gwh_an'] / (365 * 24) * 1e3,
                    energie_GWh=lambda x: x['prod_MWh_an'] * 1e-3
                    )


@st.cache
def load_indicateurs():
    with open_file('indicateurs.csv') as file_in:
        return pd.read_csv(file_in).set_index(['TypeZone', 'Zone', 'Filière', 'annee'])


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

    liste_regions = [region_default] + load_zones().set_index('TypeZone').loc['Régions', 'Zone'].to_list()
    if 'region' not in st.session_state:
        st.session_state['region'] = region_default
        index = 0
    else:
        index = liste_regions.index(st.session_state['region'])
    st.sidebar.selectbox('Région', liste_regions, index, on_change=on_change_region, key='region')

    # Restreint les départements et EPCIs à la région / département choisi
    reg = st.session_state['region'] if st.session_state['region'] != region_default else slice(None)
    liste_departements = load_zones().set_index(['TypeZone', 'Region']).loc[('Départements', reg), 'Zone'].to_list()
    liste_departements = [departement_default] + liste_departements
    if 'departement' not in st.session_state:
        st.session_state['departement'] = departement_default
        index = 0
    else:
        index = liste_departements.index(st.session_state['departement'])
    st.sidebar.selectbox('Département', liste_departements, index, key='departement', on_change=on_change_department)

    dep = st.session_state['departement'] if st.session_state['departement'] != departement_default else slice(None)
    try:
        liste_epcis = [epci_default] + load_zones().set_index(['TypeZone', 'Region', 'Departement'])\
            .loc[('Epci', reg, dep), 'Zone']\
            .drop_duplicates().to_list()
    except KeyError:
        liste_epcis = [epci_default] + load_zones().set_index('TypeZone').loc['Epci', 'Zone'].to_list()

    if 'EPCI' not in st.session_state:
        st.session_state['EPCI'] = epci_default
        index = 0
    else:
        index = liste_epcis.index(st.session_state['EPCI'])
    st.sidebar.selectbox('EPCI', liste_epcis, index, key='EPCI')

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
    values = {x: st.session_state.get(x, True) for x in filieres}
    st.session_state['filieres'] = {k: st.sidebar.checkbox(k, v, key=k) for k, v in values.items()}
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
        return installations.loc[installations['Filière'].isin(filiere)]
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
    try:
        return load_indicateurs().loc[(type_zone, zone, filiere, annee), indicateur]
    except KeyError:
        return pd.DataFrame(columns=['TypeZone', 'Zone', 'Filière', 'annee', indicateur], dtype=str)


def get_colors(liste_filieres=None):
    """
    Returns: liste de couleurs à utiliser selon les filières sélectionnées, pour garder la même couleur par filière
    """
    # colors from category10 in https://vega.github.io/vega/docs/schemes/#categorical
    colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd']
    d = st.session_state['filieres'] if liste_filieres is None \
        else {fil: fil in liste_filieres for fil in filieres}
    return [x for fil, x in zip(filieres, colors) if d.get(fil)]


def get_icon_colors(liste_filieres=None):
    """
    Returns: liste de couleurs à utiliser pour les markers selon les filières sélectionnées,
    pour garder la même couleur par filière
    """
    colors = ['blue', 'orange', 'green', 'red', 'purple']
    d = st.session_state['filieres'] if liste_filieres is None \
        else {fil: fil in liste_filieres for fil in filieres}
    return [x for fil, x in zip(filieres, colors) if d.get(fil)]


def get_markers(liste_filieres=None):
    """
    Returns: liste de symboles à utiliser selon les filières sélectionnées, pour garder le même symbole par filière
    """
    # https://vega.github.io/vega/docs/marks/symbol/
    markers = ['circle', 'square', 'triangle', 'cross', 'diamond']
    d = st.session_state['filieres'] if liste_filieres is None \
        else {fil: fil in liste_filieres for fil in filieres}
    return [x for fil, x in zip(filieres, markers) if d.get(fil)]
