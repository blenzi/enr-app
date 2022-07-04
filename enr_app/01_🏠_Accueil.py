import streamlit as st
from enr_app.general import select_zone, select_filieres, select_installations, select_indicateur
import folium
from streamlit_folium import folium_static


type_zone, zone = select_zone()
filieres = select_filieres()

st.write("# Bienvenu à l'outil EnR")

annee = 2020
puissance = int(select_indicateur(type_zone, zone, filieres, annee, 'Puissance.totale.en.kW').sum()/1e3)
energie = int(select_indicateur(type_zone, zone, filieres, annee, 'Energie.totale.en.kWh').sum()/1e6)
nombre = int(select_indicateur(type_zone, zone, filieres, annee, 'Nombre de sites').sum())


col1, col2, col3 = st.columns(3)
col1.metric(f'Puissance maximum installée en {annee}', f'{puissance} GWh')
col2.metric(f'Énergie produite en {annee}', f'{energie} GWh')
col3.metric(f'Nombre de sites en {annee}', nombre)


st.markdown(f'### Installations en France métropolitaine: {st.session_state["Zone"]}')
installations = select_installations(type_zone, zone, filieres)
n_installations = len(installations)
installations = installations.iloc[:1000]  # TODO: remove limitation


# FIXME: median -> mean after filtering on metropole ?
map = folium.Map(location=[installations.geometry.y.median(), installations.geometry.x.median()], zoom_start=5)
tooltip = folium.GeoJsonTooltip(['nominstallation', 'typo'])
gjson = folium.GeoJson(installations, tooltip=tooltip, name="Installations")
gjson.add_to(map)
folium_static(map)

columns = ['nominstallation', 'date_inst', 'puiss_MW', 'typo', 'NOM_EPCI', 'NOM_DEP', 'NOM_REG']
st.dataframe(installations[columns])
st.write(f'Installations: {n_installations}')
