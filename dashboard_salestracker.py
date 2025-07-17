import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from wordcloud import WordCloud

st.set_page_config(page_title="Sales Tracker Dashboard", layout="wide")
st.title("📊 Sales Tracker Dashboard")
st.markdown("Dashboard interaktif untuk analisis performa sales, pipeline, dan insight actionable.")

# Load data
@st.cache_data
def load_data():
    return pd.read_csv('sales_visits_finalbgt_enriched.csv')
df = load_data()

# Sidebar filter
with st.sidebar:
    st.header("Filter Data")
    sales_list = df['Nama_Sales'].unique()
    selected_sales = st.multiselect("Pilih Sales", sales_list, default=sales_list)
    segmen_list = df['Segmen'].unique() if 'Segmen' in df.columns else []
    selected_segmen = st.multiselect("Pilih Segmen", segmen_list, default=segmen_list)
    status_list = df['Status_Kontrak'].unique()
    selected_status = st.multiselect("Status Kontrak", status_list, default=status_list)

filtered_df = df[
    df['Nama_Sales'].isin(selected_sales) &
    (df['Segmen'].isin(selected_segmen) if 'Segmen' in df.columns else True) &
    df['Status_Kontrak'].isin(selected_status)
]

# KPI Cards
col1, col2, col3, col4 = st.columns(4)
with col1:
    total_deal = filtered_df[filtered_df['Status_Kontrak'].str.lower() == 'deal']['Nilai_Kontrak'].sum()
    st.metric("Total Nilai Deal", f"Rp {total_deal:,.0f}")
with col2:
    conversion = (filtered_df['Status_Kontrak'].str.lower() == 'deal').mean() * 100
    st.metric("Conversion Rate", f"{conversion:.1f}%")
with col3:
    total_prospek = filtered_df['ID_Kunjungan'].nunique()
    st.metric("Total Prospek", f"{total_prospek}")
with col4:
    rata2_durasi = None
    if 'Tanggal' in filtered_df.columns and 'ID_Customer' in filtered_df.columns:
        try:
            filtered_df['Tanggal'] = pd.to_datetime(filtered_df['Tanggal'])
            deal_df = filtered_df[filtered_df['Status_Kontrak'].str.lower() == 'deal']
            durasi_list = []
            for cust in deal_df['ID_Customer'].unique():
                cust_data = filtered_df[filtered_df['ID_Customer'] == cust].sort_values('Tanggal')
                t_awal = cust_data['Tanggal'].min()
                t_deal = cust_data[cust_data['Status_Kontrak'].str.lower() == 'deal']['Tanggal'].min()
                if pd.notnull(t_awal) and pd.notnull(t_deal):
                    durasi = (t_deal - t_awal).days
                    durasi_list.append(durasi)
            if durasi_list:
                rata2_durasi = np.mean(durasi_list)
                st.metric("Rata-rata Durasi Deal (hari)", f"{rata2_durasi:.1f}")
            else:
                st.metric("Rata-rata Durasi Deal (hari)", "-")
        except Exception:
            st.metric("Rata-rata Durasi Deal (hari)", "-")
    else:
        st.metric("Rata-rata Durasi Deal (hari)", "-")

# Ketercapaian Target per Sales
st.subheader("Ketercapaian Target per Sales")
deal_df = filtered_df[filtered_df['Status_Kontrak'].str.lower() == 'deal']
nilai_kontrak_per_sales = deal_df.groupby('Nama_Sales')['Nilai_Kontrak'].sum()
target_sales_per_sales = filtered_df.groupby('Nama_Sales')['Target_Sales'].sum()
ketercapaian_target = (nilai_kontrak_per_sales / target_sales_per_sales).fillna(0)
ketercapaian_target = ketercapaian_target.sort_values(ascending=False)
fig1, ax1 = plt.subplots(figsize=(10,4))
ketercapaian_target.plot(kind='bar', color='skyblue', edgecolor='black', ax=ax1)
ax1.set_ylabel('Rasio Ketercapaian Target')
ax1.set_title('Ketercapaian Target per Sales (Nilai Kontrak Deal / Target Sales)')
ax1.set_xticklabels(ax1.get_xticklabels(), rotation=45)
ax1.grid(axis='y', linestyle='--', alpha=0.5)
st.pyplot(fig1)

# Conversion Rate per Sales
st.subheader("Conversion Rate per Sales")
prospek_per_sales = filtered_df.groupby('Nama_Sales')['ID_Kunjungan'].nunique()
deal_per_sales = deal_df.groupby('Nama_Sales')['ID_Kunjungan'].nunique()
conversion_rate_sales = (deal_per_sales / prospek_per_sales * 100).fillna(0)
fig2, ax2 = plt.subplots(figsize=(10,4))
conversion_rate_sales.sort_values(ascending=False).plot(kind='bar', color='orange', edgecolor='black', ax=ax2)
ax2.set_ylabel('Conversion Rate (%)')
ax2.set_title('Conversion Rate per Sales')
ax2.set_xticklabels(ax2.get_xticklabels(), rotation=45)
ax2.grid(axis='y', linestyle='--', alpha=0.5)
st.pyplot(fig2)

# Heatmap Tahap Berhenti per Sales
st.subheader("Heatmap Tahap Berhenti per Sales")
if 'Progress' in filtered_df.columns:
    last_progress = filtered_df.sort_values('Tanggal').groupby('ID_Customer').last().reset_index()
    non_deal = last_progress[last_progress['Status_Kontrak'].str.lower() != 'deal']
    if not non_deal.empty:
        pivot_berhenti = non_deal.pivot_table(index='Nama_Sales', columns='Progress', values='ID_Customer', aggfunc='count', fill_value=0)
        fig3, ax3 = plt.subplots(figsize=(10,6))
        sns.heatmap(pivot_berhenti, annot=True, fmt='d', cmap='Reds', ax=ax3)
        ax3.set_title('Jumlah Customer Berhenti di Setiap Tahap per Sales')
        ax3.set_ylabel('Nama Sales')
        ax3.set_xlabel('Tahap Progress')
        st.pyplot(fig3)
    else:
        st.info('Tidak ada data non-deal untuk heatmap.')
else:
    st.info('Kolom Progress tidak tersedia.')

# Wordcloud Lost Reason
st.subheader("Wordcloud Alasan Lost")
if 'Catatan' in filtered_df.columns and 'Status_Kontrak' in filtered_df.columns:
    last_progress = filtered_df.sort_values('Tanggal').groupby('ID_Customer').last().reset_index()
    lost_notes = last_progress[last_progress['Status_Kontrak'].str.lower() != 'deal']['Catatan'].dropna().astype(str)
    text = ' '.join(lost_notes)
    import re
    from collections import Counter
    stopwords = set([
        'yang','dan','dalam','untuk','dengan','pada','di','ke','dari','sebagai','ada','ini','itu',
        'karena','sudah','belum','tidak','jadi','akan','oleh','atau','masih','saja','hanya','sangat','lebih','kurang','klien'
    ])
    words = re.findall(r'\b\w+\b', text.lower())
    filtered = [w for w in words if w not in stopwords and len(w) > 2]
    freq = Counter(filtered)
    if freq:
        wc = WordCloud(width=700, height=300, background_color='white', colormap='cool').generate_from_frequencies(freq)
        fig4, ax4 = plt.subplots(figsize=(8,3))
        ax4.imshow(wc, interpolation='bilinear')
        ax4.axis('off')
        st.pyplot(fig4)
    else:
        st.info('Tidak ada alasan lost yang cukup dominan.')
else:
    st.info('Kolom Catatan tidak tersedia.')

# Tabel Prioritas & Rekomendasi (dummy, bisa diisi dari model prediksi jika ada)
st.subheader("Prioritas & Rekomendasi Follow-up")
st.dataframe(filtered_df[['Nama_Customer','Nama_Sales','Progress','Status_Kontrak','Nilai_Kontrak']].head(30))

# Insight Box
st.info("""
**Insight Otomatis:**
- Sales dengan aktivitas rendah cenderung tidak capai target.
- Tahap bottleneck dapat diidentifikasi dari heatmap.
- Conversion rate dan pipeline value dapat digunakan untuk menentukan prioritas follow-up.
- Analisis lost reason membantu perbaikan proses sales.
""")

# Download Data
st.download_button("Download Data Filtered", filtered_df.to_csv(index=False), "filtered_data.csv")

st.caption("© 2025 Tim Data Analytics")
