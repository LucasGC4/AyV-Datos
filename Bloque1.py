import pandas as pd
import re
from sklearn.linear_model import LinearRegression # para la parte de imputación por regresión

eurocopa_fem_stats_2001 = pd.read_csv("datasetsWC26/2001eurocopa_fem_stats.csv", sep=",")
match_lineups_2026 = pd.read_csv("datasetsWC26/2026match_lineups.csv", sep=";")
match_register_2026 = pd.read_csv("datasetsWC26/2026match_register.csv", sep=";")
nationalteams_2026 = pd.read_csv("datasetsWC26/2026nationalteams.csv", sep=",")
player_stats_2026 = pd.read_csv("datasetsWC26/2026player_stats.csv", sep=";")
squads_players_2026 = pd.read_csv("datasetsWC26/2026squads_and_players.csv", sep=";")
index_referees = pd.read_csv("datasetsWC26/index_referees.csv", sep=";")
matches_mundial202 = pd.read_csv("datasetsWC26/matches_mundial202.csv", sep=",")
matches_mundial2026 = pd.read_csv("datasetsWC26/matches_mundial2026.csv", sep=";")
tournament_stages = pd.read_csv("datasetsWC26/tournament_stages.csv", sep=",")
worldcup_venues = pd.read_csv("datasetsWC26/worldcup_venues.csv", sep=";")


lista_dfs = [
    ("2001eurocopa_fem_stats", eurocopa_fem_stats_2001),
    ("2026match_lineups", match_lineups_2026),
    ("2026match_register", match_register_2026),
    ("2026nationalteams", nationalteams_2026),
    ("2026player_stats", player_stats_2026),
    ("2026squads_and_players", squads_players_2026),
    ("index_referees", index_referees),
    ("matches_mundial202", matches_mundial202),
    ("matches_mundial2026", matches_mundial2026),
    ("tournament_stages", tournament_stages),
    ("worldcup_venues", worldcup_venues),
]

def resumen(df: pd.DataFrame, nombre=""):
    print('\n   '  ,nombre)
    print(f'Tamaño: {df.shape[0]} filas x {df.shape[1]} columnas\n')
    print('Columnas y tipos:')
    print(df.dtypes)
    print('\nValores nulos:')
    print(df.isnull().sum())
    print('\n','-----'*30)


for nombre, df in lista_dfs:
    resumen(df, nombre)

# PARTIDOS
partidos = pd.DataFrame()

# INDEX_PARTIDO
matches_mundial2026 = matches_mundial2026.drop_duplicates().copy()
partidos['index_partido'] = matches_mundial2026['match_id']

# FECHA
#esto lo he tenido que buscar ya que daba error con las fechas en español
s = matches_mundial2026['date'].astype(str).str.strip()
# traducimos los meses en español para poder convertir las fechas
meses = {'junio': 'June', 'julio': 'July'}
def convertir_fecha(fecha):
    fecha = str(fecha).strip()
    for es, en in meses.items():
        fecha = fecha.replace(es, en)
    fecha = fecha.replace(' de ', ' ')

    # identificamos cada formato utilizando expresiones regulares
    if re.fullmatch(r'\d{2}/\d{2}/\d{4}', fecha):
        if fecha in ['06/12/2026', '07/04/2026', '07/11/2026']:
            formato = '%m/%d/%Y'
        else:
            formato = '%d/%m/%Y'
    elif re.fullmatch(r'\d{2}-\d{2}-\d{4}', fecha):
        formato = '%m-%d-%Y'
    elif re.fullmatch(r'\d{2}\.\d{2}\.\d{4}', fecha):
        formato = '%d.%m.%Y'
    elif re.fullmatch(r'\d{8}', fecha):
        formato = '%Y%m%d'
    elif re.fullmatch(r'\d{4}-\d{2}-\d{2}T.*Z', fecha):
        fecha = fecha[:10]
        formato = '%Y-%m-%d'
    elif re.fullmatch(r'\d{2}-[A-Za-z]{3}-\d{2}', fecha):
        formato = '%d-%b-%y'
    elif re.fullmatch(r'\d{1,2} [A-Za-z]+ \d{4}', fecha):
        formato = '%d %B %Y'
    elif re.fullmatch(r'[A-Za-z]+ \d{1,2}, \d{4}', fecha):
        formato = '%B %d, %Y'
    elif re.fullmatch(r'[A-Za-z]+ \d{1,2} \d{4}', fecha):
        formato = '%b %d %Y'
    else:
        return pd.NaT
    return pd.to_datetime(fecha, format=formato, errors='coerce')
partidos['fecha_partido'] = matches_mundial2026['date'].apply(convertir_fecha)

# RONDA
tournament_stages = tournament_stages.drop_duplicates().copy()
matches_mundial2026['index_partido'] = matches_mundial2026['match_id']
matches_mundial2026 = matches_mundial2026.merge(tournament_stages[['stage_name', 'stage_id']],how = 'left', on='stage_id' )
partidos = partidos.merge(matches_mundial2026[['stage_name', 'index_partido']],how = 'left', on='index_partido')
partidos = partidos.rename(columns={'stage_name': 'ronda'})

# ESTADIO
worldcup_venues = worldcup_venues.drop_duplicates().copy()
matches_mundial2026 = matches_mundial2026.merge(worldcup_venues[['stadium_name', 'venue_id', 'city', 'country']],how = 'left', on='venue_id' )
partidos = partidos.merge(matches_mundial2026[['stadium_name', 'index_partido', 'city', 'country']],how = 'left', on='index_partido')
partidos = partidos.rename(columns={'stadium_name': 'estadio'})

# CIUDAD_PARTIDO
partidos = partidos.rename(columns={'city': 'ciudad_partido'})

# PAIS_PARTIDO
partidos = partidos.rename(columns={'country': 'pais_partido'})
partidos['pais_partido'] = partidos['pais_partido'].str.upper()

# SELECCIÓN_LOCAL
nationalteams_2026 = nationalteams_2026.drop_duplicates().copy()
matches_mundial2026 = matches_mundial2026.merge(
    nationalteams_2026[['team_id','team_name']], 
    left_on='home_team_id', 
    right_on='team_id', 
    how='left'
)
matches_mundial2026 = matches_mundial2026.rename(columns={'team_name': 'seleccion_local'})
partidos = partidos.merge(matches_mundial2026[['index_partido', 'seleccion_local']],how = 'left', on='index_partido')


# SELECCIÓN_VISITANTE
matches_mundial2026 = matches_mundial2026.merge(
    nationalteams_2026[['team_id','team_name']], 
    left_on='away_team_id', 
    right_on='team_id', 
    how='left'
)

partidos = partidos.merge(matches_mundial2026[['index_partido', 'team_name']],how = 'left', on='index_partido')
partidos = partidos.rename(columns={'team_name': 'seleccion_visitante'})

# MARCADOR_LOCAL
partidos = partidos.merge(matches_mundial2026[['index_partido', 'home_score', 'away_score', 'home_penalty_score', 'away_penalty_score', 'result_type']],how = 'left', on='index_partido')
partidos = partidos.rename(columns={'home_score': 'marcador_local'})

# MARCADOR_VISITANTE
partidos = partidos.rename(columns={'away_score': 'marcador_visitante'})

# PRÓRROGA
partidos = partidos.rename(columns={'result_type': 'prorroga'})
partidos['prorroga'] = partidos['prorroga'].map({'Regular':'NO','AET':'SI','Penalties':'SI'})

# PENALTY_LOCAL
partidos = partidos.rename(columns={'home_penalty_score': 'penalty_local'})
partidos['penalty_local'] = (partidos['penalty_local'].fillna(0)/10).astype(int)

# PENALTY_VISITANTE
partidos = partidos.rename(columns={'away_penalty_score': 'penalty_visitante'})
partidos['penalty_visitante'] = (partidos['penalty_visitante'].fillna(0)/10).astype(int)

# ÁRBITRO_PARTIDO
index_referees = index_referees.drop_duplicates().copy()
matches_mundial2026 = matches_mundial2026.merge(index_referees[['referee_id', 'name']], how='left', on='referee_id')
partidos = partidos.merge(matches_mundial2026[['index_partido', 'name']], how='left', on='index_partido')
partidos = partidos.rename(columns={'name': 'arbitro_partido'})
partidos = partidos.set_index('index_partido') # establecemos index_partido como índice, según el enunciado
print(partidos.isnull().sum()) # comprobamos los valores nulos de partidos antes de la limpieza
print(partidos[partidos['arbitro_partido'].isnull()]) # identificamos los partidos que tienen un árbitro sin registrar
# sustituimos el árbitro nulo por un valor que indique que no está disponible
# conservamos el partido para no perder información del mundial
partidos['arbitro_partido'] = partidos['arbitro_partido'].fillna('Desconocido')
print(partidos.index.duplicated().sum()) # comprobamos que no existan identificadores de partidos duplicados
print(partidos.isnull().sum()) # comprobamos que no queden valores nulos después de la limpieza
print(partidos.shape) # comprobamos que el dataframe tiene las dimensiones exigidas
print(partidos.dtypes) # comprobamos que los tipos de datos sean correctos
# comprobamos que no existan marcadores ni penaltis negativos
print((partidos[['marcador_local', 'marcador_visitante','penalty_local', 'penalty_visitante']] < 0).sum())

# JUGADORES
# creamos el dataframe jugadores a partir de los datasets originales
jugadores = pd.DataFrame()
#index inicial, ya que hay jugadores que comparten nombre (Ali Ahmed)
jugadores['player_id'] = player_stats_2026['player_id']

# NOMBRE_JUGADOR
# obtenemos los nombres desde el dataset de plantillas utilizando player_id para evitar los problemas de codificación presentes en el dataset de estadísticas
jugadores = jugadores.merge(squads_players_2026[['player_id', 'player_name']],on='player_id',how='left')
jugadores = jugadores.rename(columns={'player_name':'nombre_jugador'})

# SELECCIÓN_NACIONAL
# asociamos cada jugador con su selección nacional mediante los identificadores de jugador y selección
nationalteams_2026 = nationalteams_2026.drop_duplicates().copy()
player_stats_2026 = player_stats_2026.merge(nationalteams_2026[['team_id', 'team_name']], how='left', on='team_id')
jugadores['seleccion_nacional'] = player_stats_2026['team_name']

# CLUB_JUGADOR
# incorporamos el club de cada jugador utilizando su identificador
jugadores = jugadores.merge(squads_players_2026[['player_id', 'club_team']], on='player_id', how='left')
jugadores = jugadores.rename(columns={'club_team':'club_jugador'})

# PARTIDOS_SELECCIÓN
# calculamos los partidos disputados por cada selección en el mundial contando sus apariciones como local y visitante
conteo_partidos = pd.concat([partidos['seleccion_local'],partidos['seleccion_visitante']]).value_counts()
jugadores['partidos_seleccion'] = jugadores['seleccion_nacional'].map(conteo_partidos)

# POSICIÓN
jugadores['posicion'] = player_stats_2026['position']

# VALOR_MERCADO
# incorporamos el valor de mercado de cada jugador
jugadores = jugadores.merge(squads_players_2026[['player_id', 'market_value_eur']], on='player_id', how='left')
jugadores = jugadores.rename(columns={'market_value_eur':'valor_mercado'})
# imputamos los valores de mercado nulos con la media de los jugadores de la misma selección nacional
jugadores['valor_mercado'] = jugadores['valor_mercado'].fillna(jugadores.groupby('seleccion_nacional')['valor_mercado'].transform('mean'))

# PARTIDOS_JUGADOS
jugadores['partidos_jugados'] = player_stats_2026['matches_played']

# MINUTOS_JUGADOS
jugadores['minutos_jugados'] = player_stats_2026['minutes_played']

# GOLES
jugadores['goles'] = player_stats_2026['goals'].fillna(0).astype(int)

# ASISTENCIAS
jugadores['asistencias'] = player_stats_2026['assists'].fillna(0).astype(int)

# TIROS
jugadores['tiros'] = player_stats_2026['shots'].fillna(0).astype(int)

# TARJETAS_AMARILLAS
jugadores['tarjetas_amarillas'] = player_stats_2026['yellow_cards'].fillna(0).astype(int)

# TARJETAS_ROJAS
jugadores['tarjetas_rojas'] = player_stats_2026['red_cards'].fillna(0).astype(int)

# PARADAS
jugadores['paradas'] = player_stats_2026['saves'].fillna(0).astype(int)

# GOLES_CONCEDIDOS
jugadores['goles_concedidos'] = player_stats_2026['goals_conceded'].fillna(0).astype(int)

# CALIFICACIÓN_MEDIA
# incorporamos las calificaciones originales, conservando los valores nulos para imputarlos posteriormente mediante regresión
jugadores['calificacion_media'] = player_stats_2026['average_rating']

# PARTE HECHA CON IA -----
# imputamos las calificaciones faltantes mediante regresión lineal diferenciando porteros y jugadores de campo según sus estadísticas
# variables utilizadas para predecir la calificación
variables_campo = ['goles', 'asistencias','tarjetas_amarillas', 'tarjetas_rojas']
variables_portero = ['paradas', 'goles_concedidos','tarjetas_amarillas', 'tarjetas_rojas']

# separamos porteros y jugadores de campo
for es_portero, variables in [(True, variables_portero), (False, variables_campo)]:
    if es_portero:
        grupo = jugadores['posicion'] == 'GK'
    else:
        grupo = jugadores['posicion'] != 'GK'

    # jugadores con calificación conocida
    entrenamiento = jugadores[grupo & jugadores['calificacion_media'].notna()]

    # jugadores con calificación desconocida
    imputar = jugadores[grupo & jugadores['calificacion_media'].isna()]
    modelo = LinearRegression()
    modelo.fit(entrenamiento[variables],entrenamiento['calificacion_media'])
    # predecimos las calificaciones faltantes a partir del modelo entrenado
    predicciones = modelo.predict(imputar[variables])

    # la calificación debe estar entre 0 y 10
    jugadores.loc[imputar.index, 'calificacion_media'] = (predicciones.clip(0, 10))
# ----------

# COMPROBACIONES FINALES
# comprobamos el número de jugadores, los valores nulos y los identificadores duplicados
# verificamos también que las calificaciones estén dentro del intervalo de 0 a 10
print("Número de jugadores:", len(jugadores))
print("\nValores nulos:")
print(jugadores.isnull().sum())
print("\nIDs duplicados:")
print(jugadores['player_id'].duplicated().sum())
print("\nCalificaciones fuera del rango 0-10:")
print((~jugadores['calificacion_media'].between(0, 10)).sum())

# establecemos nombre_jugador como índice, según el enunciado eliminamos player_id porque no forma parte de las columnas finales requeridas
jugadores = jugadores.set_index('nombre_jugador')

# eliminamos el identificador auxiliar
jugadores = jugadores.drop(columns=['player_id'])

# comprobación del resultado
print(jugadores.shape)
print(jugadores.head())

# EVENTOS
eventos = pd.DataFrame()

# INDEX_EVENTO
eventos['index_evento'] = match_register_2026['event_id']

# MINUTO_EVENTO
eventos['minuto_evento'] = match_register_2026['minute']

# INDEX_PARTIDO
eventos['index_partido'] = match_register_2026['match_id']

# NOMBRE_JUGADOR
eventos = eventos.merge(
    squads_players_2026[['player_id', 'player_name']],
    left_on=match_register_2026['player_id'],
    right_on='player_id',
    how='left'
)
eventos = eventos.rename(columns={'player_name': 'nombre_jugador'})
eventos = eventos.drop(columns=['player_id'])

# TIPO_EVENTO
eventos['tipo_evento'] = match_register_2026['event_type']

# SELECCION_EVENTO
eventos = eventos.merge(
    nationalteams_2026[['team_id', 'team_name']].drop_duplicates('team_id'),
    left_on=match_register_2026['team_id'],
    right_on='team_id',
    how='left'
)
eventos = eventos.rename(columns={'team_name': 'seleccion_evento'})
eventos = eventos.drop(columns=['team_id'])

# comprobamos las dimensiones y los valores nulos
print(eventos.shape)
print(eventos.isnull().sum())
print(eventos.head())

# eliminamos los eventos sin partido, jugador o tipo de evento ya que no se pueden asociar a un evento válido del mundial
eventos = eventos.dropna(subset=['index_partido', 'nombre_jugador', 'tipo_evento'])
print(eventos.shape)

# comprobamos y eliminamos los eventos duplicados
print("duplicados:", eventos.duplicated().sum())
eventos = eventos.drop_duplicates()
print("eventos restantes:", eventos.shape)

print(eventos['tipo_evento'].value_counts())

# unificamos los nombres de los eventos de revisión del VAR
eventos['tipo_evento'] = eventos['tipo_evento'].replace('Review VAR', 'VAR Review')
print(eventos['tipo_evento'].value_counts())

# identificamos los eventos con minutos negativos o superiores a 130
print(eventos[(eventos['minuto_evento'] < 0) |(eventos['minuto_evento'] > 130)])

# eliminamos los eventos con minutos anómalos
# conservamos los minutos nulos para imputarlos posteriormente
eventos = eventos[eventos['minuto_evento'].isna() |eventos['minuto_evento'].between(0, 130)].copy()
print(eventos.shape)

# ordenamos los eventos por partido y por su orden original
eventos = eventos.sort_values(['index_partido', 'index_evento'])

# imputamos los minutos nulos mediante interpolación dentro de cada partido, hemos necesitado ayuda de la IA para interpolarlos
eventos['minuto_evento'] = (eventos.groupby('index_partido')['minuto_evento'].transform(lambda x: x.interpolate(method='linear', limit_area='inside')))

# comprobamos cuántos minutos siguen sin completar
print(eventos['minuto_evento'].isnull().sum())

# identificamos los eventos cuyos minutos no se han podido interpolar, ya que pone que hay 22
print(eventos[eventos['minuto_evento'].isnull()])

# completamos los minutos que no tienen dos eventos vecinos conocidos utilizando el minuto disponible más cercano del mismo partido
eventos['minuto_evento'] = (eventos.groupby('index_partido')['minuto_evento'].transform(lambda x: x.ffill().bfill()).round().astype(int))

# comprobamos los minutos nulos restantes
print(eventos['minuto_evento'].isnull().sum())

# establecemos index_evento como índice del dataframe
eventos = eventos.set_index('index_evento')
eventos['index_partido'] = eventos['index_partido'].astype(int)
print(eventos.shape)
print(eventos.index.duplicated().sum())

# comprobamos los tipos de datos de los eventos
print(eventos.dtypes)

# exportamos los tres dataframes a archivos excel
partidos.to_excel('partidosWC26.xlsx')
eventos.to_excel('eventosWC26.xlsx')
jugadores.to_excel('jugadoresWC2026.xlsx')
