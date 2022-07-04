import altair as alt
import streamlit as st
from enr_app.general import select_zone, select_filieres, select_indicateur

type_zone, zone = select_zone()
filieres = select_filieres()

st.write("# Production")
st.write(f'Zone: {zone}')
st.write(f'Filières: {st.session_state["filieres"]}')
st.write(f'Filières sélectionnées: {filieres}')

df = select_indicateur(type_zone, zone, filiere=filieres, indicateur='Energie.totale.en.kWh')\
  .reset_index()\
  .assign(energie_GWh=lambda x: x['Energie.totale.en.kWh']/1e6)\
  .rename(columns={'Filiere.de.production': 'Filière', 'energie_GWh': 'Énergie produite (GWh)'})\
  .drop(columns=['TypeZone', 'Zone', 'Energie.totale.en.kWh'])

c = alt.Chart(df, width=600).mark_line().encode(
  x='annee:O',
  y='Énergie produite (GWh):Q',
  color='Filière:N'
)

    # color=alt.Color('color', scale=None)

st.altair_chart(c)
st.dataframe(df)
