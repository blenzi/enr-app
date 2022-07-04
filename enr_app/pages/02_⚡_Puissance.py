import altair as alt
import streamlit as st
from enr_app.general import select_zone, select_filieres, select_indicateur

type_zone, zone = select_zone()
filieres = select_filieres()

st.write("# Puissance maximum")
st.write(f'Zone: {zone}')
st.write(f'Filières: {st.session_state["filieres"]}')
st.write(f'Filières sélectionnées: {filieres}')

df = select_indicateur(type_zone, zone, filiere=filieres, indicateur='Puissance.totale.en.kW')\
  .reset_index()\
  .assign(puiss_MW=lambda x: x['Puissance.totale.en.kW']/1e3)\
  .rename(columns={'Filiere.de.production': 'Filière', 'puiss_MW': 'Puissance maximum (MW)'})\
  .drop(columns=['TypeZone', 'Zone', 'Puissance.totale.en.kW'])

c = alt.Chart(df, width=600).mark_bar().encode(
  x='annee:O',
  y='Puissance maximum (MW):Q',
  color='Filière:N'
)

    # color=alt.Color('color', scale=None)

st.altair_chart(c)
st.dataframe(df, width=600)
