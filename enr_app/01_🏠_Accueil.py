import streamlit as st
import folium
from streamlit_folium import folium_static
from enr_app.general import select_zone, select_filieres, select_installations, select_indicateur, \
    get_sources, get_colors, remove_page_items
from enr_app.map_functions import get_map

st.set_page_config('Outil EnR')
remove_page_items()
st.write("# Bienvenu à l'outil EnR")

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
col1.caption(f'Source: {get_sources("puiss_MW", type_zone)}')
col2.metric(f'Énergie produite en {annee}', f'{energie} GWh')
col2.caption(f'Source: {get_sources("energie_GWh", type_zone)}')
col3.metric(f'Nombre de sites en {annee}', nombre)
col3.caption(f'Source: {get_sources("Nombre de sites", type_zone)}')


st.markdown(f"## Installations en France métropolitaine et départements d'outre-mer")
st.write(f'### {type_zone.strip("s")}: {zone}')

if type_zone != 'Régions':
    st.session_state['show_installations'] = True

st.session_state['show_installations'] = st.checkbox('Afficher installations',
                                                     st.session_state.get('show_installations', False))

mapa = get_map(type_zone, zone)
if st.session_state['show_installations']:
    columns = ['nominstallation', 'Filière', 'typo', 'date_inst', 'puiss_MW', 'energie_GWh',
               'NOM_EPCI', 'NOM_DEP', 'NOM_REG']
    installations = select_installations(type_zone, zone, filieres).reset_index()
    mapa.location = [installations.geometry.y.median(), installations.geometry.x.median()]
    n_installations = len(installations)
    subset = installations.iloc[:1000]  # TODO: remove limitation ?
    if n_installations:
        if n_installations > 1000:
            st.write('N.B.: uniquement 1000 installations affichées. Veuillez sélectionner une zone plus restreinte')
        tooltip = folium.GeoJsonTooltip(['nominstallation', 'Filière'])
        popup = folium.GeoJsonPopup(columns)
        # FIXME: marker color not changed
        for (name, group), color in zip(subset.groupby('Filière'), get_colors()):
            tooltip = folium.GeoJsonTooltip(['nominstallation', 'Filière'])
            popup = folium.GeoJsonPopup(columns)
            gjson = folium.GeoJson(subset, name=name, tooltip=tooltip, popup=popup,
                                   style_function=lambda x: {'fillColor': color, 'color': color})
            gjson.add_to(mapa)

folium_static(mapa)
if st.session_state['show_installations']:
    st.caption(f'Source: {get_sources("installations", type_zone)}')
    st.download_button('Exporter au format csv',
                       data=installations[columns].to_csv(index=False),
                       file_name='installations.csv',
                       mime='text/csv',
                       )
    st.dataframe(installations[columns])
    st.caption(f'Source: {get_sources("installations", type_zone)}')
    st.write(f'Installations: {n_installations}')
