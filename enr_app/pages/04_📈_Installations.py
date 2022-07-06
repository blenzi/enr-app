import altair as alt
import streamlit as st
from enr_app.general import select_zone, select_filieres, select_indicateur, get_colors

type_zone, zone = select_zone()
filieres = select_filieres()

st.write("# Nombre d'installations")
st.write(f'Zone: {zone}')
st.write(f'Filières sélectionnées: {", ".join(filieres)}')

df = select_indicateur(type_zone, zone, filiere=filieres, indicateur='Nombre de sites')\
  .reset_index()\
  .rename(columns={'Filiere.de.production': 'Filière'})\
  .drop(columns=['TypeZone', 'Zone']).astype({'Nombre de sites': int})

c = alt.Chart(df, width=600).mark_bar().encode(
  x='annee:O',
  y='Nombre de sites:Q',
  color=alt.Color('Filière:N', scale=alt.Scale(range=get_colors()))
)

st.altair_chart(c)
st.dataframe(df, width=600)
