__doc__ = """Fonctions, elements (barre laterale, données, sélections) et définitions 
globales pour l'application"""

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
    'ODRE': 'ODRE [[1]](https://odre.opendatasoft.com/explore/dataset/registre-national-installation-production-stockage-electricite-agrege-311220/information/?disjunctive.epci&disjunctive.departement&disjunctive.region&disjunctive.filiere&disjunctive.combustible&disjunctive.combustiblessecondaires&disjunctive.technologie&disjunctive.regime&disjunctive.gestionnaire) [[2]](https://odre.opendatasoft.com/explore/dataset/points-dinjection-de-biomethane-en-france/information/?disjunctive.site&disjunctive.nom_epci&disjunctive.departement&disjunctive.region&disjunctive.type_de_reseau&disjunctive.grx_demandeur) [[3]](https://opendata.reseaux-energies.fr/explore/dataset/injection-annuelle-biomethane-pitp-grtgaz)',  #noqa
    'GDRF': '[GRDF](https://opendata.grdf.fr/explore/dataset/capacite-et-quantite-dinjection-de-biomethane)',
    'SDES': 'SDES [[1]](https://www.statistiques.developpement-durable.gouv.fr/tableau-de-bord-solaire-photovoltaique-quatrieme-trimestre-2021?rubrique=21&dossier=172) [[2]](https://www.statistiques.developpement-durable.gouv.fr/tableau-de-bord-solaire-photovoltaique-quatrieme-trimestre-2021?rubrique=21&dossier=172)',  #noqa
}

def get_sources(indicateur, type_zone, zone=None):
    """
    Sources des indicateurs et installations

    Args:
        indicateur: str ("installations", "puissance", "production", "nombre")
        type_zone: str (Régions, Départements ou Epci)
        zone: str, default=None

    Returns: string
    """
    if indicateur in ("installations", "production"):
        return f"{sources['ODRE']}, {sources['GDRF']}"
    if indicateur in ("puissance", "nombre"):
        return sources["SDES"] if type_zone in ("Régions", "Départements") else f"{sources['ODRE']}, {sources['GDRF']}"
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

@st.cache
def load_installations():
    filiere = {'solaire photovoltaïque': 'Photovoltaïque', 
               'éolien terrestre': 'Eolien',
               'éolien marin': 'Eolien',
               'méthanisation': 'Méthanisation électrique'
               }

    installations = gpd.read_file('data/installations.gpkg', layer='installations').to_crs(epsg=4326)\
        .assign(Filière=lambda x: x['typo'].replace(filiere), energie_GWh=lambda x: x['prod_MWh_an'] * 1e-3)

    inst = pd.concat([installations, load_installations_biogaz()])
    return inst[~inst.geometry.is_empty]

@st.cache
def load_installations_biogaz():
    return gpd.read_file('data/installations.gpkg', layer='installations_biogaz')\
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
    Enedis = pd.read_csv('data/Enedis_com_a_reg_all.csv', index_col=0) \
        .merge(load_zones(), on=['TypeZone', 'CodeZone']) \
        .rename(columns={'Filiere.de.production': 'Filière'}) \
        .replace({'Bio Energie': 'Méthanisation électrique'})

    sdes = pd.read_csv('data/SDES_indicateurs_depts_regions_France.csv') \
        .set_index('Zone').drop('Total DOM').reset_index() \
        .replace({'Total France': 'Toutes', 'Somme': 'Régions'}) \
        .rename(columns={'Filiere.de.production': 'Filière'}) \
        .assign(type_estimation='SDES')

    France = Enedis.query("TypeZone == 'Régions'") \
        .groupby(['indicateur', 'Filière', 'annee']).sum().reset_index() \
        .assign(TypeZone='Régions', Zone='Toutes', type_estimation='Somme')

    indicateurs = pd.concat([Enedis, France, sdes]) \
        .drop_duplicates(['TypeZone', 'Zone', 'annee', 'Filière', 'indicateur'], keep='last') \
        .pivot_table(index=['TypeZone', 'Zone', 'Filière', 'annee'],
                     values='valeur', 
                     columns='indicateur') \
        .assign(puiss_MW=lambda x: x['Puissance.totale.en.kW'] / 1e3,
                energie_GWh=lambda x: x['Energie.totale.en.kWh'] / 1e6) \
        .drop(columns=['Puissance.totale.en.kW', 'Energie.totale.en.kWh'])

    return pd.concat([indicateurs, *get_indicateurs_biogaz()])

@st.cache
def get_indicateurs_biogaz():
    """
    Returns: liste de tableaux contenant les indicateurs pour le biogaz aux niveaux des EPCI, départements, régions
    et toute la France
    """
    # FIXME: évolution au cours des années. 2020 c'est peut-être même pas la bonne année
    installations_biogaz = load_installations_biogaz()

    France = installations_biogaz.agg({'puiss_MW': 'sum', "energie_GWh": 'sum', 'NOM_REG': 'count'}) \
        .to_frame().T \
        .assign(Zone=region_default, TypeZone='Régions') \
        .rename(columns={'NOM_REG': 'Nombre de sites'})

    # Indicateurs aux niveaux EPCI, départements, régions
    ind = [installations_biogaz.groupby(column).agg(
        puiss_MW=("puiss_MW", 'sum'),
        energie_GWh=("energie_GWh", 'sum'),
        N=("puiss_MW", 'count')
    ).reset_index().rename(columns={'N': 'Nombre de sites', column: 'Zone'}) \
               .assign(TypeZone=type_zone)
           for type_zone, column in {'Epci': 'NOM_EPCI', 'Départements': 'NOM_DEP', 'Régions': 'NOM_REG'}.items()]

    return [df.assign(annee=2020, Filière='Injection de biométhane')
              .set_index(['TypeZone', 'Zone', 'Filière', 'annee'])
               for df in [France] + ind]

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
    index = liste_regions.index(st.session_state['region']) if 'region' in st.session_state else 0
    st.session_state['region'] = st.sidebar.selectbox('Région', liste_regions, index, on_change=on_change_region)

    # Restreint les départements et EPCIs à la région / département choisi
    reg = st.session_state['region'] if st.session_state['region'] != region_default else slice(None)
    liste_departements = [departement_default] + \
                         load_zones().set_index(['TypeZone', 'Region']).loc[('Départements', reg), 'Zone'].to_list()
    index = liste_departements.index(st.session_state['departement']) if 'department' in st.session_state else 0
    st.session_state['departement'] = st.sidebar.selectbox('Département', liste_departements,
                                                           index,
                                                           on_change=on_change_department)

    dep = st.session_state['departement'] if st.session_state['departement'] != departement_default else slice(None)
    try:
        liste_epcis = [epci_default] + load_zones().set_index(['TypeZone', 'Region', 'Departement'])\
            .loc[('Epci', reg, dep), 'Zone']\
            .drop_duplicates().to_list()
    except:  # FIXME
        liste_epcis = [epci_default] + load_zones().set_index('TypeZone').loc['Epci', 'Zone'].to_list()

    index = liste_epcis.index(st.session_state['EPCI']) if 'EPCI' in st.session_state else 0
    st.session_state['EPCI'] = st.sidebar.selectbox('EPCI', liste_epcis, index)

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
    if 'filieres' not in st.session_state:
        st.session_state['filieres'] = {x: True for x in filieres}
    st.session_state['filieres'] = {k: st.sidebar.checkbox(k, v) for k, v in st.session_state['filieres'].items()}
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
    return load_indicateurs().loc[(type_zone, zone, filiere, annee), indicateur]

def get_colors(liste_filieres=None):
    """
    Returns: liste de couleurs à utiliser selon les filières sélectionnées, pour garder la même couleur par filière
    """
    # colors from category10 in https://vega.github.io/vega/docs/schemes/#categorical
    colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd']
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
