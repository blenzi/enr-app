import altair as alt
import streamlit as st
from enr_app.general import select_zone, select_filieres, select_indicateur, get_colors, get_markers

type_zone, zone = select_zone()
filieres = select_filieres()

st.write("# Production")
st.write(f'Zone: {zone}')
st.write(f'Filières sélectionnées: {", ".join(filieres)}')

df = select_indicateur(type_zone, zone, filiere=filieres, indicateur='Energie.totale.en.kWh')\
  .reset_index()\
  .assign(energie_GWh=lambda x: x['Energie.totale.en.kWh']/1e6)\
  .rename(columns={'Filiere.de.production': 'Filière', 'energie_GWh': 'Énergie produite (GWh)'})\
  .drop(columns=['TypeZone', 'Zone', 'Energie.totale.en.kWh'])

line = alt.Chart(df, width=600).mark_line().encode(
    x='annee:O',
    y='Énergie produite (GWh)',
    color=alt.Color('Filière', scale=alt.Scale(range=get_colors()), legend=None)
)

points = line.mark_point(filled=True).encode(
    color=alt.Color('Filière', scale=alt.Scale(range=get_colors())),
    shape=alt.Shape('Filière', scale=alt.Scale(range=get_markers()))
)

c = alt.layer(
    line,
    points
).resolve_scale(
    color='independent',
    shape='independent'
)

st.altair_chart(c)
st.dataframe(df)
