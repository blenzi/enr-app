import altair as alt
import streamlit as st

from enr_app.general import (
    get_colors,
    get_sources,
    remove_page_items,
    select_filieres,
    select_indicateur,
    select_zone,
)

remove_page_items()
type_zone, zone = select_zone()
filieres = select_filieres()

st.write("# Nombre d'installations")
st.write(f'### {type_zone.strip("s")}: {zone}')

indicateur = "Nombre de sites"
df = (
    select_indicateur(type_zone, zone, filiere=filieres, indicateur=indicateur)
    .reset_index()
    .drop(columns=["TypeZone", "Zone"])
    .dropna()
    .astype({indicateur: int})
)
colors = get_colors(liste_filieres=df["Filière"].unique())

c = (
    alt.Chart(df, width=600)
    .mark_bar()
    .encode(
        x="annee:O",
        y="Nombre de sites:Q",
        color=alt.Color("Filière:N", scale=alt.Scale(range=colors)),
        tooltip=["annee", "Filière", indicateur],
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
st.dataframe(df, width=600)
st.caption(f"Source: {get_sources(indicateur, type_zone)}")
