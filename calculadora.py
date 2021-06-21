import streamlit as st
import pickle
import pandas as pd
import numpy as np
from sklearn.metrics import roc_curve

import bokeh.io as bk_io
import bokeh.models as bk_m
import bokeh.layouts as bk_l
import bokeh.plotting as bk_plt

modelo = pickle.load( open( "calculadora.p", "rb" ) )

y_test = pickle.load( open( "dfTest_Etiqueta.p", "rb" ) )

y_pred_test = pickle.load( open( "dfTest_Proba.p", "rb" ) )


html = """
<div style="background-color:royalblue;padding:10px">
<h1 style="color:white;text-align:center;">Calculadora de riesgo de HTA</h1>
<h2 style="color:white;text-align:center;">Rellene las siguientes preguntas</h2>
</div>
"""

st.markdown(html, unsafe_allow_html=True)



with st.form("calculator"):

    col1, col2 = st.beta_columns(2)

    with col1:
    

        edad = st.number_input('Indique su edad:', min_value=18, max_value=120)

        frecCard = st.number_input('Indique su frecuencia cardiaca habitual en reposo:', min_value=45, max_value=120)

        talla = st.number_input('Indique su talla (en cm):', min_value=130, max_value=250)

        peso = st.number_input('Indique su peso (en kg):', min_value=40, max_value=200)

    with col2:
        dislipemia = st.radio(
                            "¿Padece usted dislipemia?",
                            ('SI', 'NO'))

        diabetes = st.radio("¿Padece usted diabetes?",
                            ('SI', 'NO'))

        cafe = st.radio(
                            "¿Toma usted al menos, una taza de café al día?",
                            ('SI', 'NO'))
    
        text = st.write("Pulse aquí para calcular:")
        submit = st.form_submit_button(label='Comprobar riesgo')



if submit==True:



    edad = (edad - 56.201163) / 16.589871

    frecCard = (frecCard - 68.255780) / 10.644211

    imc = peso / ((talla/100)*(talla/100))
    imc = (imc - 26.402428) / 4.540184


    if dislipemia == 'SI':
        dislipemia = 1
    else:
        dislipemia = 0
    

    if diabetes == 'SI':
        diabetes = 1
    else:
        diabetes = 0


    if cafe == 'SI':
        cafe = 1
    else:
        cafe = 0


    X = np.array([edad, frecCard, imc, dislipemia, diabetes, cafe])

    prob_HTA = modelo.predict_proba([X])

    if (prob_HTA[0,1]*100) > 50:
        st.error('Su probabilidad de padecer HTA es ' + str(round((prob_HTA[0,1]*100),2)) + '%, debería medirse la tensión en una farmacia o acudir a su consulta de Atencion Primaria')

    elif (prob_HTA[0,1]*100) > 35 and (prob_HTA[0,1]*100) < 50:
        st.warning('Su probabilidad de padecer HTA es ' + str(round((prob_HTA[0,1]*100),2)) + '%, su riesgo no es elevado aún, pero debería vigilar sus hábitos. Recuerde llevar una vida sana y activa')

    else:
        st.success('Su probabilidad de padecer HTA es ' + str(round((prob_HTA[0,1]*100),2)) + '%, su riesgo es bajo. Recuerde llevar una vida sana y activa')



    fig = bk_plt.figure(plot_width=500, plot_height=500, title="Riesgo de padecer HTA",
               x_axis_label="1 - Specifity" , y_axis_label = "Sensitivity",
               x_range=[-0.01,1.01], y_range=[-0.01,1.01], toolbar_location=None, tools = "")
    

    x,y,thr = roc_curve(y_test, y_pred_test)

    data = pd.DataFrame(zip(x,y,thr), columns = ['FPR','TPR','THR'])

    
    patchx = []
    patchy_el = [0, 0 ,1, 1]
    patchy =  []


    id1 = data.loc[data['THR']>0.52,'THR'].idxmin()
    id2 = data.loc[data['THR']<0.52,'THR'].idxmax()
    x_t = (data.loc[id1,'FPR']+data.loc[id2,'FPR'])/2


    thresholds = [0,x_t,1]
    colors = ['red','green']


    for i in range(1, len(thresholds), 1):
            patchx = patchx + [[thresholds[i-1], thresholds[i], thresholds[i], thresholds[i-1]]]
            patchy = patchy + [patchy_el]


    for i in range(len(patchx)):
            fig.patch(patchx[i], patchy[i], fill_color = colors[i], alpha = 0.3, line_width = 0)


    id1 = data.loc[data['THR']>prob_HTA[0,1],'THR'].idxmin()
    id2 = data.loc[data['THR']<prob_HTA[0,1],'THR'].idxmax()

    x_p = (data.loc[id1,'FPR']+data.loc[id2,'FPR'])/2
    y_p = (data.loc[id1,'TPR']+data.loc[id2,'TPR'])/2


    linea = fig.line(source=data, x='FPR', y='TPR', line_width = 3, legend_label = "Curva ROC", name = 'CURVA')


    punto = fig.x(x_p, y_p, size = 10, line_width = 6,  alpha = 1, color = 'black',
                legend_label = f'POINT: FPR = {x_p:.2f} TPR {y_p:.2f}',
                name = 'POINT')


    fig.add_tools(bk_m.HoverTool(tooltips=[("FPR", '@{FPR}{0.00}'), ("TPR", '@{TPR}{0.00}'), ("PROBABILITY", "@{THR}{0.00}")], renderers = [linea], mode='vline'))


    fig.legend.location = "bottom_right"
    fig.legend.border_line_width = 3
    fig.legend.border_line_color = "navy"
    fig.legend.border_line_alpha = 0.5

    
    st.bokeh_chart(fig)