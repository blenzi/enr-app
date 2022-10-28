import altair as alt
import pandas as pd
import streamlit as st

from enr_app.general import (
    get_colors,
    get_markers,
    get_sources,
    open_file,
    remove_page_items,
    select_filieres,
    select_indicateur,
    select_zone,
)

remove_page_items()
type_zone, zone = select_zone()
filieres = select_filieres()

st.write("# Production")
st.write(f'### {type_zone.strip("s")}: {zone}')

indicateur = "energie_GWh"
add_sraddet = False
df = (
    select_indicateur(type_zone, zone, filiere=filieres, indicateur=indicateur)
    .reset_index()
    .rename(columns={"energie_GWh": "Énergie produite (GWh)"})
    .drop(columns=["TypeZone", "Zone"])
)

if type_zone == "Régions" and zone == "Grand Est" and st.checkbox("Objectifs SRADDET"):
    add_sraddet = True
    with open_file("objectifs_SRADDET_GrandEst.csv") as file_in:
        sraddet = (
            pd.read_csv(file_in, sep=";")
            .set_index("Filière")
            .stack()
            .rename("Objectif")
            .rename_axis(index={None: "annee"})
            .reset_index()
            .astype({"annee": int})
        )

    df = (
        pd.merge(
            df,
            sraddet.loc[sraddet["Filière"].isin(filieres)],
            on=["Filière", "annee"],
            how="outer",
        )
        .sort_values(["Filière", "annee"])
        .reset_index(drop=True)
    )

line = (
    alt.Chart(df, width=600)
    .mark_line()
    .encode(
        x="annee:O",
        y="Énergie produite (GWh)",
        color=alt.Color("Filière", scale=alt.Scale(range=get_colors()), legend=None),
        tooltip=["annee", "Filière", "Énergie produite (GWh)"],
    )
)

points = line.mark_point(filled=True).encode(
    color=alt.Color("Filière", scale=alt.Scale(range=get_colors())),
    shape=alt.Shape("Filière", scale=alt.Scale(range=get_markers())),
)

layers = [line, points]
if add_sraddet:
    # lf = df.dropna(subset='Objectif')['Filière'].unique()
    # st.write(lf, get_colors(lf) )
    line_sraddet = line.mark_line(strokeDash=[1.0], point=True).encode(
        x="annee:O",
        y="Objectif",
        color=alt.Color("Filière", scale=alt.Scale(range=get_colors()), legend=None),
        tooltip=["annee", "Filière", "Objectif"],
    )
    # FIXME: Colors and markers are wrong because not all Filières are present ?
    points_sraddet = line_sraddet.mark_point(filled=False).encode(
        color=alt.Color("Filière", scale=alt.Scale(range=get_colors(df)), legend=None),
        shape=alt.Shape("Filière", scale=alt.Scale(range=get_markers(df)), legend=None),
    )
    layers.extend([line_sraddet])  # , points_sraddet])

c = alt.layer(*layers).resolve_scale(color="independent", shape="independent")

st.altair_chart(c)
st.caption(f'Source: {get_sources("energie_GWh", type_zone)}')


st.download_button(
    "Exporter au format csv",
    data=df.to_csv(index=False),
    file_name="production.csv",
    mime="text/csv",
)
st.dataframe(df)
st.caption(f"Source: {get_sources(indicateur, type_zone)}")
