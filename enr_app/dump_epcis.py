__doc__ = """Dump la liste d'EPCIs avec départements dans epcis.csv"""

import geopandas as gpd


installations = gpd.read_file('data/installations.gpkg', layer='installations').to_crs(epsg=4326)
installations = installations[~installations.geometry.is_empty]

def fcn(x):
    "Converti 'DEPARTEMENTS_DE_L_EPCI' en liste"
    return x.replace('\"', '').strip('c()').split(', ')

multi = installations['DEPARTEMENTS_DE_L_EPCI'].str.contains('c')
epcis = installations.loc[:, ['EPCI', 'NOM_EPCI', 'DEPARTEMENTS_DE_L_EPCI']]
epcis.loc[multi, 'DEPARTEMENTS_DE_L_EPCI'] = epcis.loc[multi, 'DEPARTEMENTS_DE_L_EPCI'].apply(fcn)
epcis.explode('DEPARTEMENTS_DE_L_EPCI').drop_duplicates().to_csv('epcis.csv', index=False)
