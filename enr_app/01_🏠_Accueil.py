import streamlit as st
import folium
from streamlit_folium import folium_static


st.set_page_config('Outil EnR')
st.write("# Bienvenu à l'outil EnR")
from enr_app.general import select_zone, select_filieres, select_installations, select_indicateur, get_zoom, sources


type_zone, zone = select_zone()
filieres = select_filieres()

annee = 2020
try:
    puissance = int(select_indicateur(type_zone, zone, filieres, annee, 'puiss_MW').sum())
except KeyError:
    puissance = 'N/A'
try:
    energie = int(select_indicateur(type_zone, zone, filieres, annee, 'energie_GWh').sum())
except KeyError:
    energie = 'N/A'
try:
    nombre = int(select_indicateur(type_zone, zone, filieres, annee, 'Nombre de sites').sum())
except KeyError:
    nombre = 'N/A'


col1, col2, col3 = st.columns(3)
col1.metric(f'Puissance maximum installée en {annee}', f'{puissance} MW')
col1.caption(f'Source: {sources["SDES" if type_zone in ("Régions", "Départements") else "ODRE"]}')
col2.metric(f'Énergie produite en {annee}', f'{energie} GWh')
col2.caption(f'Source: {sources["ODRE"]}')
col3.metric(f'Nombre de sites en {annee}', nombre)
col3.caption(f'Source: {sources["SDES" if type_zone in ("Régions", "Départements") else "ODRE"]}')


st.markdown(f"### Installations en France métropolitaine et départements d'outre-mer: {st.session_state['Zone']}")
installations = select_installations(type_zone, zone, filieres)
n_installations = len(installations)

# FIXME: median -> mean after filtering on metropole ?
if n_installations:
    subset = installations.iloc[:1000]  # TODO: remove limitation
    if n_installations > 1000:
        st.write('N.B.: uniquement 1000 installations affichées. Veuillez sélectionner une zone plus restreinte')
    ign = 'https://wxs.ign.fr/essentiels/geoportail/wmts?REQUEST=GetTile&SERVICE=WMTS&VERSION=1.0.0&STYLE=normal&TILEMATRIXSET=PM&FORMAT=image/png&LAYER=GEOGRAPHICALGRIDSYSTEMS.PLANIGNV2&TILEMATRIX={z}&TILEROW={y}&TILECOL={x}' # noqa
    map = folium.Map(tiles=ign,
                     attr='<a target="_blank" href="https://www.geoportail.gouv.fr/">Geoportail France</a>',
                     min_zoom=2,
                     max_zoom=18,
                     location=[installations.geometry.y.median(), installations.geometry.x.median()],
                     zoom_start=get_zoom(type_zone, zone)
                     )
    tooltip = folium.GeoJsonTooltip(['nominstallation', 'Filière'])
    columns = ['nominstallation', 'Filière', 'typo', 'date_inst', 'puiss_MW', 'energie_GWh', 'NOM_EPCI', 'NOM_DEP',
               'NOM_REG']
    popup = folium.GeoJsonPopup(columns)
    gjson = folium.GeoJson(subset, tooltip=tooltip, popup=popup, name="Installations")
    gjson.add_to(map)
    folium_static(map)
    st.caption(f'Source: {sources["ODRE"]}')
    st.dataframe(installations[columns])
st.write(f'Installations: {n_installations}')
