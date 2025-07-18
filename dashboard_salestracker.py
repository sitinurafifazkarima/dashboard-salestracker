# 📊 DASHBOARD SALES TRACKER

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import pickle
import streamlit as st

# =======================
# 📅 DATA LOADING
# =======================
df = pd.read_csv('sales_visits_finalbgt_enriched.csv')
df['Tanggal'] = pd.to_datetime(df['Tanggal'])

# =======================
# 📌 LAYER 1 - FUNNEL OVERVIEW PER SALES
# =======================
st.title("Sales Funnel per Sales")

sales_funnel = df.groupby(['Nama_Sales', 'Progress']).size().unstack(fill_value=0)

# Reindex agar semua tahap funnel muncul walau belum ada datanya
tahapan_funnel = ['Awal', 'Follow Up', 'Penawaran', 'Negosiasi', 'Paska Deal']
sales_funnel = sales_funnel.reindex(columns=tahapan_funnel, fill_value=0)

st.dataframe(sales_funnel)

# =======================
# 📌 LAYER 2 - PERFORMANSI SALES
# =======================
st.header("Performa Sales")

if 'Level_Sales' not in df.columns:
    df['Level_Sales'] = 'Unknown'

sales_performance = df.groupby('Nama_Sales').agg(
    Total_Kunjungan=('ID_Customer', 'count'),
    Jumlah_Customer=('ID_Customer', 'nunique'),
    Level_Sales=('Level_Sales', lambda x: x.mode().iloc[0] if not x.mode().empty else 'Unknown')
)

all_sales = sales_performance.index
sales_performance['Nilai_Kontrak_Aktual'] = 0
sales_performance['Prospek_Nilai_Kontrak'] = 0

latest_contracts = df.sort_values('Tanggal').groupby(['ID_Customer']).last()

for sales in all_sales:
    sales_contracts = latest_contracts[latest_contracts['Nama_Sales'] == sales]
    aktual = sales_contracts[sales_contracts['Progress'] == 'Paska Deal']['Nilai_Kontrak'].sum()
    prospek = sales_contracts[sales_contracts['Progress'] != 'Paska Deal']['Nilai_Kontrak'].sum()
    sales_performance.at[sales, 'Nilai_Kontrak_Aktual'] = aktual
    sales_performance.at[sales, 'Prospek_Nilai_Kontrak'] = prospek

sales_performance['Total_Nilai_Kontrak'] = sales_performance['Nilai_Kontrak_Aktual'] + sales_performance['Prospek_Nilai_Kontrak']

jumlah_deal = latest_contracts[latest_contracts['Progress'] == 'Paska Deal'].groupby('Nama_Sales').size()
sales_performance['Jumlah_Deal'] = pd.Series(0, index=all_sales).add(jumlah_deal, fill_value=0).astype(int)

sales_performance['Closing_Rate'] = (sales_performance['Jumlah_Deal'] / sales_performance['Jumlah_Customer'] * 100).fillna(0).round(2)
sales_performance['Efektivitas'] = (sales_performance['Jumlah_Deal'] / sales_performance['Total_Kunjungan'] * 100).fillna(0).round(2)

progress_mapping = {'Awal':0, 'Follow Up':1, 'Penawaran':2, 'Negosiasi':3, 'Paska Deal':4}
df['Progress_Score'] = df['Progress'].map(progress_mapping)

sales_progress = df.groupby('Nama_Sales')['Progress_Score'].mean()
sales_performance['Rata_Rata_Progress'] = sales_progress.reindex(all_sales).fillna(0).round(2)

sales_performance = sales_performance.sort_values(['Jumlah_Deal', 'Total_Nilai_Kontrak'], ascending=False)

st.dataframe(sales_performance)

fig, axes = plt.subplots(2, 2, figsize=(18, 10))

sales_performance['Total_Kunjungan'].plot(kind='bar', ax=axes[0, 0], alpha=0.6, label='Kunjungan')
sales_performance['Jumlah_Deal'].plot(kind='bar', ax=axes[0, 0], alpha=0.6, label='Deal')
axes[0, 0].set_title('Jumlah Kunjungan vs Deal')
axes[0, 0].legend()

sales_performance['Closing_Rate'].plot(kind='bar', ax=axes[0, 1], color='green')
axes[0, 1].set_title('Closing Rate per Sales')

sales_performance[['Nilai_Kontrak_Aktual', 'Prospek_Nilai_Kontrak']].plot(kind='bar', stacked=True, ax=axes[1, 0])
axes[1, 0].set_title('Nilai Kontrak Aktual vs Prospek')

fig.tight_layout()
st.pyplot(fig)

low_performers = sales_performance[
    (sales_performance['Closing_Rate'] < sales_performance['Closing_Rate'].median()) &
    (sales_performance['Total_Kunjungan'] > sales_performance['Total_Kunjungan'].median())
]

if not low_performers.empty:
    st.warning("Sales yang perlu pendampingan:")
    st.dataframe(low_performers[['Total_Kunjungan', 'Closing_Rate']])

performa_data = {
    'sales_performance': sales_performance,
    'low_performers': low_performers,
    'top_performer': sales_performance.index[0]
}

with open('performa_sales.pkl', 'wb') as f:
    pickle.dump(performa_data, f)
