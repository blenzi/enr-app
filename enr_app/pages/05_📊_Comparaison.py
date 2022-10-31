import altair as alt
import streamlit as st

from enr_app.general import (
    get_colors,
    get_sources,
    load_zones,
    remove_page_items,
    select_filieres,
    select_indicateur,
)

remove_page_items()
st.title("Comparer les territoires")

n_max = 10
st.sidebar.write(f"Maximum {n_max} options")


def limit_choices(key):
    if len(st.session_state[key]) > n_max:
        st.session_state[key] = st.session_state[key][:n_max]


liste_regions = load_zones().set_index("TypeZone").loc["Régions", "Zone"].to_list()
regions = st.sidebar.multiselect(
    "Régions", liste_regions, key="regions", on_change=limit_choices, args=("regions",)
)

reg = regions or slice(None)
liste_departements = (
    load_zones()
    .set_index(["TypeZone", "Region"])
    .loc[("Départements", reg), "Zone"]
    .to_list()
)
departements = st.sidebar.multiselect(
    "Départements",
    liste_departements,
    key="departements",
    on_change=limit_choices,
    args=("departements",),
)

type_zone = "Départements" if departements else "Régions"
zone = departements or regions

indicateurs = select_indicateur(type_zone, zone).reset_index()

cols = indicateurs.columns.drop(
    ["TypeZone", "Zone", "annee", "Filière", "type_estimation"]
)
indicateur = st.sidebar.selectbox("Indicateur", cols)

annees = sorted(indicateurs["annee"].unique())
annee = st.sidebar.selectbox("Année", annees)

filieres = select_filieres()


if zone:
    try:
        df = select_indicateur(
            type_zone, zone, filieres, annee, indicateur
        ).reset_index()
        colors = get_colors(liste_filieres=df["Filière"].unique())
        c = (
            alt.Chart(df, width=700, height=100 * len(zone))
            .mark_bar()
            .encode(
                x=indicateur,
                y="Zone:O",
                color=alt.Color("Filière:N", scale=alt.Scale(range=colors)),
                tooltip=["Zone", "Filière", indicateur],
            )
        )
        st.altair_chart(c)
        st.caption(f"Source: {get_sources(indicateur, type_zone)}")

        st.download_button(
            "Exporter au format csv",
            data=df.to_csv(index=False),
            file_name="nombre_installations.csv",
            mime="text/csv",
        )
        st.dataframe(df)
        st.caption(f"Source: {get_sources(indicateur, type_zone)}")
    except KeyError:
        st.write("Pas de donnée pour la zone et année sélectionnées")
else:
    st.write(
        "Veuillez sélectionner des régions ou départements, ainsi que l'année, l'indicateur et les filières"
    )
