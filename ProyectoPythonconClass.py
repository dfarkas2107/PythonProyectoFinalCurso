# Empiezo con un TRY para el manejo de excepciones
try:
    import sys # top of your code 
    import pandas as pd
    import krakenex
    import requests
    import streamlit as st
    from pykrakenapi import KrakenAPI
    import plotly.graph_objects as go
    import datetime as dt
    import plotly.express as px
    import altair as alt
    from datetime import date
    from datetime import datetime

# Cheqeo todos los pares con el dolar con los que podriamos trabajar  en KRAKEN

    resp = requests.get('https://api.kraken.com/0/public/AssetPairs')
    resp = resp.json()

    euro_pairs = []
    for pair in resp['result']:
            if pair.endswith('USD'):
                euro_pairs.append(pair)

# Defino las caracteristicas de theme de la interfaz:

# Creo una funcion para determinar las caracteristicas de las graficas.Algunas de ellas son iguales para todas,por eso es mas eficiente haer una funcion.
    today = datetime.now()
    st.set_page_config(layout="wide")


    def white_marks():
        return {
            'config': {
                'background': 'white',
                'view': {
                    'width': 900,
                    'height': 300}},
            'mark': {
                'type':  'line'}
                }


# Registro el theme de las graficas
    alt.themes.register('white_marks', white_marks)

# Llamo al theme que elegi
    alt.themes.enable('white_marks')

# Creo un titulo para al app mediante markdown que es mas flexible que hacerlo mediante st.title
    st.markdown("<h1 style='text-align: center; color: grey;'>Cripto Journal</h1>",
                unsafe_allow_html=True)

# Genero en streamlit un sidebar que permite elegir 5 pares de monedas.Es posible elegir todas,pero no creemos que sea util para este trabajo.
    input_lista = st.sidebar.selectbox(
        'Elige una moneda:',
        ('BITUSD',
         'EWTUSD',
         'ACAUSD',
         'ACHUSD',
         'ADAUSD')
    )
# Creo encabezados y sub encabezados segnn el dia y segun la moneda que el usuario eligio:
    subtitulo = st.write('Evolucion de ' + input_lista)
    Horadia = st.text(today)

# Genero la request a la API de Kraken para que busque la informacion de las monedas que el usuario haya seleccionado:
    resp = requests.get('https://api.kraken.com/0/public/OHLC?pair=' +
                        input_lista+'&amp;since=1647625329&amp;interval=60')

# Por medio de la libreria pandas creo un dataframe en donde guardo la informacion que me trae la API de Kraken,tambien defino el nombre de las columnas.
    df = pd.DataFrame(resp.json()['result'][input_lista])
    df.columns = ['unixtimestap', 'open', 'high',
                  'low', 'close', 'vwap', 'volume', 'count']

# Tengo que definir que tipo de variable seran cada columna,en este caso se transforman a variables numericas
    columnas = ['open', 'high', 'low', 'close', 'vwap', 'volume', 'count']
    df[columnas] = df[columnas].apply(pd.to_numeric)

# La variable unixtimestap es necesario convertirla tambien,en este caso a una variable de tiempo
    df['unixtimestap'] = pd.to_datetime(df['unixtimestap'], unit="s")

# Creo un sidebar nuevo que permite elegir que tipo de grafico mostrar,si es con media movil o normal
    Grafico = st.sidebar.selectbox(
        'Elige un grafico nuevo:',
        (["Sin Media Movil", "Media Movil"]))

    sidebarra = st.sidebar.slider("Periodo:", min_value=0, max_value=50)

# Graficamos  el precio de #cierre con respecto a la unidad de tiempo #unixtimestap

    df2 = df[['unixtimestap', 'close']]

    df2['close'] = df2['close'].apply(pd.to_numeric)

    fig = alt.Chart(df).mark_line(color="red").encode(alt.X('unixtimestap', scale=alt.Scale(zero=False),
                                                            axis=alt.Axis(title='', grid=False)),
                                                      alt.Y("close", scale=alt.Scale(zero=False),
                                                            axis=alt.Axis(title='', grid=False)))


# Creo los datos necesario para hacer el grafico de media movil

    dfpromedio = df.close.rolling(sidebarra).mean()
    dfmeunixtimestapmovil = df.assign(meunixtimestapmovil=dfpromedio)

    mediamovil = alt.Chart(dfmeunixtimestapmovil).mark_line().encode(alt.X('unixtimestap', scale=alt.Scale(zero=False),
                                                                           axis=alt.Axis(grid=False)),
                                                                     alt.Y("meunixtimestapmovil", scale=alt.Scale(zero=False),
                                                                           axis=alt.Axis(grid=False)))

    dosgraficos = (mediamovil + fig)
# Creo un grafico que muestra la evolucion del precio y la media movil para utilizar luego

# Creo un grafico que muestra la evolucion del precio y la media movil para utilizar luego
    total = (fig + mediamovil).interactive()
    if Grafico == "Media Movil":
        st.write(total)

    else:
        st.write(fig)


# RSI
# calculo la diferencia entre cada periodo del DF2
    dfmediamovil = df2.assign(mediamovil=dfpromedio)
    df2_diff = dfmediamovil['close'].diff()
    df2_diff = df2_diff.apply(pd.to_numeric)

# defino df2_diff_negativo con las perdidas

    df2_diff_negativo = df2_diff.copy()
    df2_diff_negativo[df2_diff_negativo > 0] = 0

# defino df2_diff_positivo con todas las ganancias

    df2_diff_positivo = df2_diff.copy()
    df2_diff_positivo[df2_diff_negativo < 0] = 0

# Agrego las columnas  a mi dataframe
    df_gain_loss = dfmediamovil.assign(
        Diff=df2_diff, Gain=df2_diff_positivo, Loss=df2_diff_negativo)

# calculo  avg_gain-avg_loss de 14 periodos

    avg_gain = df_gain_loss.Gain.rolling(14).mean()
    avg_loss = df_gain_loss.Loss.abs().rolling(14).mean()
    df_gain_loss_avg = df_gain_loss.assign(Ganprom=avg_gain, Perprom=avg_loss)

# calculo el RS

    RS = avg_gain/avg_loss

# Calculo el RSI

    RSI = 100-100/(1+RS)

# AGREGO RS Y RSI AL Dataframe

    df_gain_loss_avg_rs = df_gain_loss_avg.assign(rs=RS, rsi=RSI)

    fig2 = alt.Chart(df_gain_loss_avg_rs).mark_line(color='green').encode(alt.X('unixtimestap', scale=alt.Scale(zero=False),
                                                                                axis=alt.Axis(title='', grid=False)),
                                                                          alt.Y("rsi", scale=alt.Scale(zero=False),
                                                                                axis=alt.Axis(title='', grid=False))).properties(width=900, height=150).interactive()

# Definimos el benchmark en 70 y 30  para el analis.

    line1 = alt.Chart(pd.DataFrame({'y': [70]})).mark_rule(strokeDash=[
        10, 10]).encode(y='y').properties(width=900, height=150).interactive()
    line2 = alt.Chart(pd.DataFrame({'y': [30]})).mark_rule(strokeDash=[
        10, 10]).encode(y='y').properties(width=900, height=150).interactive()

    fig3 = (fig2 + line1+line2)

    st.write(fig3)
#Creo una exception al final para que me triga en un print cual fue la excepcion que causa la ejecucion:
   
except Exception as err:
       print("imprimir excepcion capturada",err)
