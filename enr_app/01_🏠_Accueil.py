import folium
import streamlit as st
from streamlit_folium import folium_static

from enr_app.general import (
    get_icon_colors,
    get_sources,
    remove_page_items,
    select_filieres,
    select_indicateur,
    select_installations,
    select_zone,
)
from enr_app.map_functions import get_map

st.set_page_config("Outil EnR")
remove_page_items()
st.write("# Bienvenu à l'outil EnR")

type_zone, zone = select_zone()
filieres = select_filieres()

annee = 2021
tuiles = {
    "puiss_MW": {
        "texte": f"Puissance maximum installée en {annee}",
        "valeur": lambda x: f"{int(x)} MW",
    },
    "energie_GWh": {
        "texte": f"Énergie produite en {annee}",
        "valeur": lambda x: f"{int(x)} GWh",
    },
    "Nombre de sites": {
        "texte": f"Nombre de sites en {annee}",
        "valeur": lambda x: f"{int(x)}",
    },
}

for col, (indicateur, tuile) in zip(st.columns(3), tuiles.items()):
    df = select_indicateur(type_zone, zone, filieres, annee, indicateur)
    if df.empty:
        col.metric(tuile["texte"], "N/A")
    else:
        col.metric(tuile["texte"], tuile["valeur"](df.sum()))
    col.caption(f"Source: {get_sources(indicateur, type_zone)}")

# Carte
st.markdown("## Installations en France métropolitaine et départements d'outre-mer")
st.write(f'### {type_zone.strip("s")}: {zone}')

if type_zone != "Régions":
    st.session_state["show_installations"] = True

st.session_state["show_installations"] = st.checkbox(
    "Afficher installations", st.session_state.get("show_installations", False)
)

mapa = get_map(type_zone, zone)
if st.session_state["show_installations"]:
    columns = [
        "nominstallation",
        "Filière",
        "typo",
        "date_inst",
        "puiss_MW",
        "energie_GWh",
        "NOM_EPCI",
        "NOM_DEP",
        "NOM_REG",
    ]
    installations = select_installations(type_zone, zone, filieres).reset_index()
    mapa.location = [
        installations.geometry.y.median(),
        installations.geometry.x.median(),
    ]
    n_installations = len(installations)
    max_installations = 1000
    subset = installations.iloc[:max_installations]  # TODO: remove limitation ?
    if n_installations:
        if n_installations > max_installations:
            st.write(
                f"N.B.: uniquement {max_installations} installations affichées. "
                "Veuillez sélectionner une zone plus restreinte"
            )
        tooltip = folium.GeoJsonTooltip(["nominstallation", "Filière"])
        popup = folium.GeoJsonPopup(columns)
        for (name, group), color in zip(subset.groupby("Filière"), get_icon_colors()):
            tooltip = folium.GeoJsonTooltip(["nominstallation", "Filière"])
            popup = folium.GeoJsonPopup(columns)
            marker = folium.Marker(icon=folium.Icon(color=color))
            gjson = folium.GeoJson(
                group, name=name, tooltip=tooltip, popup=popup, marker=marker
            )
            gjson.add_to(mapa)

folium.LayerControl().add_to(mapa)
folium_static(mapa)
if st.session_state["show_installations"]:
    st.caption(f'Source: {get_sources("installations", type_zone)}')
    st.download_button(
        "Exporter au format csv",
        data=installations[columns].to_csv(index=False),
        file_name="installations.csv",
        mime="text/csv",
    )
    st.dataframe(installations[columns])
    st.caption(f'Source: {get_sources("installations", type_zone)}')
    st.write(f"Installations: {n_installations}")
