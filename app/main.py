# -*- coding: utf-8 -*-
"""
Created on Wed Apr 19 09:23:56 2023

@author: zacha
"""
import streamlit as st
import numpy as np
import pandas as pd
import git
import plotly.express as px
import datetime
from PIL import Image

#from datetime import datetime
#from datetime import date

############### PAGE CONFIGURATION ############### 
# Import Chronovet logo
#image = Image.open('C:/Users/zacha/OneDrive/Desktop/Chronovet/App/Streamlit/img/icon.png')
#image_logo = Image.open('C:/Users/zacha/OneDrive/Desktop/Chronovet/App/Streamlit/img/logo.png')
image = Image.open('assets/icon.png')
image_logo = Image.open('assets/logo.png')

#st.set_page_config(layout="wide")
#st.set_page_config(layout="centered")
st.set_page_config(
    layout="centered",
    page_title='Chronovet Analytics',
    page_icon=image_logo
)

col1, col2, col3 = st.columns([2,4,2])
with col1:
    st.write("")
with col2:
    st.image(image, use_column_width=True)
with col3:
    st.write("")



############### FUNCTIONS ############### 
@st.cache
def get_repo():
    try:
        git.Git(".").clone("https://github.com/ZacharieGuibert/c-analytics")
    except git.GitCommandError:
        repo = git.Repo("c-analytics")
        repo.remotes.origin.pull()

def load_data(path):
    dataset = pd.read_excel(path, parse_dates=True)
    return dataset

def static_data(df):
    df_interests = ['ref centravet','nom', 'marque', 'poids']
    refs = df.groupby('id chronovet')[df_interests].agg(['unique'])
    refs.columns = refs.columns.droplevel(-1)
    for item in df_interests:
        refs[item]=refs[item].str[0]
    return refs

    
def ordered_data(df, ID, PV):
    temp_df = df[df['id chronovet']==ID]
    threshold = df.columns.get_loc('poids')
    values = df.columns[threshold+1:]
    #remove = df.columns[:threshold+1]
    ordered_df = temp_df.melt(id_vars=['Date','id chronovet',], value_vars=values,var_name='Reference',value_name='Valeur')
    ordered_df = ordered_df.sort_values(by='Date',ascending=True)
    ordered_df.index = ordered_df.Date
    #ordered_df = ordered_df.drop(['Date'], axis=1)
    if PV == 'Prix':
        ordered_df = ordered_df[(ordered_df['Reference']!='ventes')]
    elif PV == 'Volumes':
        ordered_df = ordered_df[(ordered_df['Reference']=='ventes')]
    ordered_df.index = ordered_df.Date
    return ordered_df

def _max_width_(prcnt_width:int = 75):
    max_width_str = f"max-width: {prcnt_width}%;"
    st.markdown(f""" 
                <style> 
                .reportview-container .main .block-container{{{max_width_str}}}
                </style>    
                """, 
                unsafe_allow_html=True,
    )

def variation_data(df, ID):
    threshold = df.columns.get_loc('poids')
    labs = df.columns[threshold+1:]
    temp_df = df[df['id chronovet']==ID]
    temp_df = temp_df.drop(['ref centravet', 'nom', 'marque', 'poids'], axis=1)
    temp_df.index = temp_df['Date']
    temp_df = temp_df.loc[start_date:end_date]
    variations = []
    for lab in labs:
        variation = temp_df[lab][-1]/temp_df[lab][0] - 1
        variations.append(variation)
    temp_df = temp_df.drop(['Date','id chronovet'], axis=1)
    variation_df = temp_df.T
    variation_df['Variation (in %)'] = variations
    columns_to_keep = [temp_df.index[0], temp_df.index[-1], 'Variation (in %)']
    variation_df = variation_df[columns_to_keep]
    date_cols = pd.Series(temp_df.index.format()).tolist()
    cols = ['Prix '+ datetime.datetime.strptime(date_cols[0], "%Y-%m-%d").strftime("%b %Y"), 'Prix ' + datetime.datetime.strptime(date_cols[-1], "%Y-%m-%d").strftime("%b %Y"), 'Variation (in %)']
    variation_df.columns = cols
    variation_df[cols[0]] = variation_df[cols[0]].apply(lambda x: "€{:.2f}".format((x)))
    variation_df[cols[1]] = variation_df[cols[1]].apply(lambda x: "€{:.2f}".format((x)))
    variation_df = variation_df.replace(['€nan', 'nan', 'nan%'], np.nan)
    
    # Change the format for volumes
    variation_df.loc['ventes'] = variation_df.loc['ventes'].str.replace('€','')    
    variation_df.loc['ventes'] = variation_df.loc['ventes'].apply(lambda x: "{:.0f}".format((float(x))))
    #variation_df.loc[:, "Variation (in %)"] = variation_df["Variation (in %)"].map('{:.2%}'.format)
    variation_df.loc[:, "Variation (in %)"] = variation_df["Variation (in %)"].apply(lambda x: "{:.2%}".format((float(x))))

    variation_df = variation_df.replace(['€nan', 'nan', 'nan%'], np.nan)
    return variation_df

def top_down_data(df, labo, vendor, output, nb_products):
    # Get all values
    threshold = df.columns.get_loc('poids')
    vendor_names = df.columns[threshold+1:].unique().tolist()
    vendor_names.remove(vendor)
    temp_df = df[(df['marque']==labo)]
    temp_df = temp_df.drop(vendor_names, axis=1)
    # Get min max values over the period
    min_max_dates = temp_df['Date'].agg(['min', 'max'])
    # Get price variation
    start_end_df = temp_df[temp_df['Date'].isin(min_max_dates)]
    start_df = start_end_df[start_end_df['Date']==min_max_dates[0]]
    start_df.index = start_df['id chronovet']
    end_df = start_end_df[start_end_df['Date']==min_max_dates[1]]
    end_df.index = end_df['id chronovet']
    start_df = start_df[vendor].round(2)
    end_df = end_df[vendor].round(2)
    # Concatenate results
    final_df = pd.concat([start_df, end_df], axis=1)
    final_df.columns=['Prix initial', 'Prix final']
    final_df['Variation'] = final_df['Prix final']/final_df['Prix initial']-1
    final_df = final_df.dropna()
    static_df = static_data(df)
    static_df = static_df.drop(['marque'], axis=1)
    final_df = pd.merge(static_df, final_df, left_index=True, right_index=True)
    final_df['Prix initial'] = final_df['Prix initial'].apply(lambda x: "{:.2f}".format((x)))
    final_df['Prix final'] = final_df['Prix final'].apply(lambda x: "{:.2f}".format((x)))
    # Get final output
    if output == 'Top':
        top_df = final_df.sort_values('Variation', ascending=False)
        top_df = top_df.head(nb_products)
        top_df['Variation'] = top_df['Variation'].apply(lambda x: "{:.2%}".format((x)))
        #top_df.columns = ['Valeur '+ datetime.datetime.strptime(min_max_dates[0], "%Y-%m-%d").strftime("%b %Y"), 'Valeur ' + datetime.datetime.strptime(min_max_dates[1], "%Y-%m-%d").strftime("%b %Y"), 'Variation (in %)']
        return top_df
    elif output == 'Bottom':
        bottom_df = final_df.sort_values('Variation', ascending=True)
        bottom_df = bottom_df.head(nb_products)
        bottom_df['Variation'] = bottom_df['Variation'].apply(lambda x: "{:.2%}".format((x)))
        #bottom_df.columns = ['Valeur '+ datetime.datetime.strptime(min_max_dates[0], "%Y-%m-%d").strftime("%b %Y"), 'Valeur ' + datetime.datetime.strptime(min_max_dates[1], "%Y-%m-%d").strftime("%b %Y"), 'Variation (in %)']
        return bottom_df

############### GET DATA ############### 

#path_file = 'C:/Users/zacha/OneDrive/Desktop/Chronovet/App/Streamlit/data/Historique.xlsx'
path_file = 'data/Historique.xlsx'
historical = load_data(path_file)
refs_data = static_data(historical)
labos = refs_data['marque'].unique().tolist()
# Get vendor names
threshold = historical.columns.get_loc('poids')
vendor_names = historical.columns[threshold+1:].unique().tolist()

############### PRODUCT SPECIFIC ############### 

st.markdown("<h1 style='text-align: center; '>CHRONOVET ANALYTICS</h1>", unsafe_allow_html=True)
st.markdown("<h3 style='text-align: center; '>Suivi des prix et volumes d'un produit Chronovet</h3>", unsafe_allow_html=True)

with st.form ('info'):
    st.subheader('Informations à completer')
    col1,col2,col3 = st.columns(3)
    with col1:
        selected_id_chronovet = st.selectbox(label='Identifiant Chronovet', options=refs_data.index)
    with col2:
        start_date = st.date_input(
            "Date de début",
            datetime.date(2023,1,1)
            )
    with col3:
        end_date = st.date_input(
            "Date de fin",
            #datetime.date(2022,1,1)
            )
            
    submitted = st.form_submit_button('Submit')
    if submitted:
    
        static_data = pd.DataFrame(
            {
             'Reference Centravet': [refs_data.loc[selected_id_chronovet][0]],
             'Nom produit': [refs_data.loc[selected_id_chronovet][1]],
             'Laboratoire': [refs_data.loc[selected_id_chronovet][2]],
             'Poids': [refs_data.loc[selected_id_chronovet][3]]
            })
        st.subheader('Informations sur le produit')
        st.dataframe(static_data)
        
        st.subheader('Evolution des prix')
        filtered_prices = ordered_data(historical, selected_id_chronovet, 'Prix')
        line_fig = px.line(filtered_prices.loc[start_date:end_date],
                           x='Date', y='Valeur',
                           color='Reference')
                           #title = 'Evolution des prix')
        st.plotly_chart(line_fig)
        
        st.subheader('Evolution des volumes')
        filtered_volumes = ordered_data(historical, selected_id_chronovet, 'Volumes')
        bar_fig = px.line(filtered_volumes.loc[start_date:end_date],
                           x='Date', y='Valeur',
                           color='Reference')
                           #title = 'Evolution des prix')
        st.plotly_chart(bar_fig)

        st.subheader('Evolution relatives des prix et volumes')
        variation_df = variation_data(historical, selected_id_chronovet)
        variation_df = variation_df.style.highlight_null(props="color: transparent;")  # hide NaNs
        st.table(variation_df)


############### GENERAL - Augmentations ############### 

st.markdown("<h3 style='text-align: center; '>Plus fortes augmentations par laboratoire et vendeur</h3>", unsafe_allow_html=True)

with st.form ('suivi augmentations'):
    st.subheader('Informations à completer')
    col1,col2,col3,col4, col5 = st.columns(5)
    with col1:
        selected_lab_top = st.selectbox(label='Laboratoire', options=labos)
    with col2:
        selected_vendor_top = st.selectbox(label='Vendeur', options=vendor_names)
    with col3:
        start_date_top = st.date_input(
            "Date de début",
            datetime.date(2023,1,1)
            )
    with col4:
        end_date_top = st.date_input(
            "Date de fin",
            #datetime.date(2022,1,1)
            )
    with col5:
        top_number = st.number_input('Quantité', min_value=5, max_value=20, step=1)
            
    submitted_top = st.form_submit_button('Submit')
    
    if submitted_top:
        st.markdown("La première colonne du tableau est l'identifiant chronovet")
        top_df = top_down_data(historical, selected_lab_top, selected_vendor_top, 'Top', top_number)
        top_df = top_df.style.highlight_null(props="color: transparent;")  # hide NaNs
        st.table(top_df)

############### GENERAL - Baisses ############### 

st.markdown("<h3 style='text-align: center; '>Plus fortes baisses par laboratoire et vendeur</h3>", unsafe_allow_html=True)

with st.form ('suivi baisses'):
    st.subheader('Informations à completer')
    col1,col2,col3,col4, col5 = st.columns(5)
    with col1:
        selected_lab_bottom = st.selectbox(label='Laboratoire', options=labos)
    with col2:
        selected_vendor_bottom = st.selectbox(label='Vendeur', options=vendor_names)
    with col3:
        start_date_bottom = st.date_input(
            "Date de début",
            datetime.date(2023,1,1)
            )
    with col4:
        end_date_bottom = st.date_input(
            "Date de fin",
            #datetime.date(2022,1,1)
            )
    with col5:
        bottom_number = st.number_input('Quantité', min_value=5, max_value=20, step=1)
            
    submitted_bottom = st.form_submit_button('Submit')
    
    if submitted_bottom:
        st.markdown("La première colonne du tableau est l'identifiant chronovet")
        bottom_df = top_down_data(historical, selected_lab_bottom, selected_vendor_bottom, 'Bottom', bottom_number)
        bottom_df = bottom_df.style.highlight_null(props="color: transparent;")  # hide NaNs
        st.table(bottom_df)

############### SIDE BAR ###############

with st.sidebar:
    st.subheader('A propos')
    st.markdown("Cette page permet de:")
    st.write(
                """    
        - **Visualiser l'évolution des prix appliqués par la concurrence** pour chaque produit Chronovet
        - Obtenir la **liste des produits avec les plus fortes augmentations et diminutions de prix ou de volume**, par laboratoire et par vendeur
                """
            )
    #st.markdown("pour l'ensemble des produits vendus sur **Chronovet**")
    
    st.markdown("**Les informations suivantes sont nécessaires**:")
    st.write(
                """    
        - l'identifiant Chronovet
        - la date de début et de fin d'observation
        - la quantité d'observations maximale que l'on souhaite voir (minimum:5, maximum:20'
                """
            )

#st.sidebar.image(image_side)
#st.sidebar.image('https://streamlit.io/images/brand/streamlit-mark-color.png', width=50)
