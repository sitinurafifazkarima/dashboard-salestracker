# dashboard_salestracker.py
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt


st.set_page_config(page_title="Sales Tracker Dashboard", layout="wide", page_icon="📊")

# Header dengan deskripsi singkat
st.markdown("""
<h1 style='color:#00BFFF; margin-bottom:0;'>📊 Dashboard Analisis Sales Tracker</h1>
<p style='color:#b0b0b0; font-size:16px; margin-top:0;'>Pantau performa sales, konversi, dan insight strategi secara real-time.</p>
""", unsafe_allow_html=True)

# Load data
@st.cache_data
def load_data():
    df = pd.read_csv('sales_visits_enriched_csv.txt', delimiter='\t')
    return df


df = load_data()

# =====================
# FILTER INTERAKTIF
# =====================

with st.sidebar:
    st.header('🔎 Filter Data')
    # Periode (Bulan)
    df['Tanggal'] = pd.to_datetime(df['Tanggal'])
    bulan_opsi = df['Tanggal'].dt.to_period('M').astype(str).unique().tolist()
    bulan_opsi.sort()
    bulan_dipilih = st.selectbox('Pilih Bulan', ['Semua'] + bulan_opsi, index=0)
    # Sales
    sales_opsi = df['Nama_Sales'].dropna().unique().tolist()
    sales_opsi.sort()
    sales_dipilih = st.selectbox('Pilih Sales', ['Semua'] + sales_opsi, index=0)
    # Segmen
    segmen_opsi = df['Segmen'].dropna().unique().tolist()
    segmen_opsi.sort()
    segmen_dipilih = st.selectbox('Pilih Segmen', ['Semua'] + segmen_opsi, index=0)
    # Status Kontrak
    status_opsi = df['Status_Kontrak'].dropna().unique().tolist()
    status_opsi.sort()
    status_dipilih = st.selectbox('Pilih Status Kontrak', ['Semua'] + status_opsi, index=0)
    # Status Customer
    status_cust_opsi = df['Status_Customer'].dropna().unique().tolist()
    status_cust_opsi.sort()
    status_cust_dipilih = st.selectbox('Pilih Status Customer', ['Semua'] + status_cust_opsi, index=0)

# Terapkan filter ke dataframe utama
if bulan_dipilih != 'Semua':
    df = df[df['Tanggal'].dt.to_period('M').astype(str) == bulan_dipilih]
if sales_dipilih != 'Semua':
    df = df[df['Nama_Sales'] == sales_dipilih]
if segmen_dipilih != 'Semua':
    df = df[df['Segmen'] == segmen_dipilih]
if status_dipilih != 'Semua':
    df = df[df['Status_Kontrak'] == status_dipilih]
if status_cust_dipilih != 'Semua':
    df = df[df['Status_Customer'] == status_cust_dipilih]


# =====================
# KPI Cards (Highlight Metrics)
# =====================
st.markdown("---")
st.markdown("<h3 style='color:#00BFFF;'>🔢 Ringkasan Kinerja Utama</h3>", unsafe_allow_html=True)
total_kunjungan = df['ID_Kunjungan'].nunique()
total_deal = df[df['Status_Kontrak'] == 'Deal']['ID_Kunjungan'].nunique()
total_customer = df['ID_Customer'].nunique()
avg_konversi = (total_deal / total_kunjungan * 100) if total_kunjungan else 0

colk1, colk2, colk3, colk4 = st.columns(4)
colk1.metric("Total Kunjungan", f"{total_kunjungan}", help="Jumlah seluruh kunjungan sales")
colk2.metric("Total Deal", f"{total_deal}", help="Jumlah deal yang berhasil")
colk3.metric("Total Customer", f"{total_customer}", help="Jumlah customer unik")
colk4.metric("Rata-rata Konversi", f"{avg_konversi:.1f}%", help="Persentase deal dari total kunjungan")

with st.expander("Tampilkan data mentah (raw data)"):
    st.dataframe(df.head(20))

st.divider()


# =====================
# Distribusi Data Utama
# =====================
st.markdown("<h3 style='color:#00BFFF;'>📊 Distribusi Data Utama</h3>", unsafe_allow_html=True)
st.write("Distribusi status kontrak, segmen, level sales, dan status customer.")

def draw_pie(data, title):
    fig, ax = plt.subplots(figsize=(3.2, 3.2))
    fig.patch.set_alpha(0)
    ax.set_facecolor('none')
    explode = [0.05 if val == data.max() else 0 for val in data]
    wedges, texts, autotexts = ax.pie(
        data,
        labels=data.index,
        autopct='%1.1f%%',
        startangle=140,
        colors=plt.cm.Pastel1.colors,
        explode=explode,
        shadow=False,
        textprops={'fontsize': 9, 'color': '#222'}
    )
    plt.setp(autotexts, color='#222')
    plt.setp(texts, color='#222')
    plt.title(title, fontsize=10, color='#00BFFF')
    return fig

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.pyplot(draw_pie(df['Status_Kontrak'].value_counts(), "Status Kontrak"))
    st.caption(f"<b>Deal terbanyak:</b> {df['Status_Kontrak'].value_counts().idxmax()}", unsafe_allow_html=True)
with col2:
    st.pyplot(draw_pie(df['Segmen'].value_counts(), "Segmen"))
    st.caption(f"<b>Segmen dominan:</b> {df['Segmen'].value_counts().idxmax()}", unsafe_allow_html=True)
with col3:
    st.pyplot(draw_pie(df['Level_Sales'].value_counts(), "Level Sales"))
    st.caption(f"<b>Level terbanyak:</b> {df['Level_Sales'].value_counts().idxmax()}", unsafe_allow_html=True)
with col4:
    st.pyplot(draw_pie(df['Status_Customer'].value_counts(), "Status Customer"))
    st.caption(f"<b>Status dominan:</b> {df['Status_Customer'].value_counts().idxmax()}", unsafe_allow_html=True)

st.divider()
st.markdown("<h3 style='color:#00BFFF;'>📈 Kinerja Sales</h3>", unsafe_allow_html=True)
st.write("Analisis performa sales berdasarkan jumlah kunjungan dan tingkat konversi.")


# Siapkan data terlebih dahulu (digunakan di 2 kolom)
kunjungan_sales = df['Nama_Sales'].value_counts()
kunjungan_per_sales = df.groupby('Nama_Sales')['ID_Kunjungan'].count()
deal_per_sales = df[df['Status_Kontrak'] == 'Deal'].groupby('Nama_Sales')['ID_Kunjungan'].count()

kinerja_sales = pd.concat([kunjungan_per_sales, deal_per_sales], axis=1).fillna(0)
kinerja_sales.columns = ['Total_Kunjungan', 'Jumlah_Deal']
kinerja_sales['Tingkat_Konversi (%)'] = (kinerja_sales['Jumlah_Deal'] / kinerja_sales['Total_Kunjungan'] * 100).round(2)
kinerja_sales = kinerja_sales.sort_values('Tingkat_Konversi (%)', ascending=False)

col1, col2 = st.columns(2)
with col1:
    st.subheader("👥 Total Kunjungan per Sales")
    st.write("Jumlah kunjungan yang dilakukan oleh masing-masing sales.")
    fig_kunjungan, ax = plt.subplots(figsize=(5.5, 3))
    bars = ax.bar(kunjungan_sales.index, kunjungan_sales.values, color='#00BFFF', edgecolor='black')
    ax.set_ylabel("Jumlah", fontsize=8, color='#222')
    ax.set_xlabel("Nama Sales", fontsize=8, color='#222')
    ax.set_title("Total Kunjungan", fontsize=10, color='#00BFFF')
    ax.tick_params(axis='x', labelrotation=45, labelsize=7, colors='#222')
    ax.tick_params(axis='y', labelsize=7, colors='#222')
    ax.set_facecolor('none')
    fig_kunjungan.patch.set_alpha(0)
    plt.tight_layout(pad=0.8)
    for bar in bars:
        yval = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2, yval + 0.5, int(yval), ha='center', fontsize=7, color='#222')
    st.pyplot(fig_kunjungan)
    st.caption(f"<b>Sales teraktif:</b> {kunjungan_sales.idxmax()} ({kunjungan_sales.max()} kunjungan)", unsafe_allow_html=True)
with col2:
    st.subheader("📊 Tingkat Konversi (Deal) per Sales")
    st.write("Persentase deal yang berhasil dicapai oleh masing-masing sales.")
    fig_konversi, ax = plt.subplots(figsize=(5.5, 3))
    bars = ax.barh(kinerja_sales.index, kinerja_sales['Tingkat_Konversi (%)'],
                   color='#32CD32', edgecolor='black')
    ax.set_xlabel("Tingkat Konversi (%)", fontsize=8, color='#222')
    ax.set_title("Tingkat Konversi", fontsize=10, color='#32CD32')
    ax.tick_params(axis='x', labelsize=7, colors='#222')
    ax.tick_params(axis='y', labelsize=7, colors='#222')
    ax.set_facecolor('none')
    fig_konversi.patch.set_alpha(0)
    plt.tight_layout(pad=0.8)
    for i, val in enumerate(kinerja_sales['Tingkat_Konversi (%)']):
        ax.text(val + 0.5, i, f"{val}%", va='center', fontsize=7, color='#222')
    st.pyplot(fig_konversi)
    st.caption(f"<b>Konversi tertinggi:</b> {kinerja_sales.index[0]} ({kinerja_sales['Tingkat_Konversi (%)'].iloc[0]}%)", unsafe_allow_html=True)

st.divider()

# =====================
# Analisis Customer Baru & Efektivitas Penarikan
# =====================
st.markdown("---")
st.header("🆕 Analisis Customer Baru & Efektivitas Penarikan")

# Asumsi: Customer baru = Status_Customer == 'Baru' (atau bisa disesuaikan)
df_baru = df[df['Status_Customer'].str.lower().str.contains('baru', na=False)]
total_cust_baru = df_baru['ID_Customer'].nunique()
deal_cust_baru = df_baru[df_baru['Status_Kontrak'] == 'Deal']['ID_Customer'].nunique()
deal_rate_baru = (deal_cust_baru / total_cust_baru * 100) if total_cust_baru else 0

colb1, colb2, colb3 = st.columns(3)
colb1.metric("Total Customer Baru", f"{total_cust_baru}")
colb2.metric("Customer Baru Deal", f"{deal_cust_baru}")
colb3.metric("Deal Rate Customer Baru", f"{deal_rate_baru:.1f}%")

# Breakdown status deal customer baru
st.subheader("📊 Status Deal Customer Baru")
status_baru = df_baru['Status_Kontrak'].value_counts()
fig_sb, ax = plt.subplots(figsize=(4.5, 3))
bars = ax.bar(status_baru.index, status_baru.values, color=['#32CD32' if s=='Deal' else '#FF7F50' for s in status_baru.index], edgecolor='black')
for bar in bars:
    yval = bar.get_height()
    ax.text(bar.get_x() + bar.get_width()/2, yval + 0.5, int(yval), ha='center', fontsize=8, color='#222')
ax.set_ylabel("Jumlah Customer Baru", fontsize=8, color='#222')
ax.set_xlabel("Status Kontrak", fontsize=8, color='#222')
ax.set_title("Distribusi Status Deal Customer Baru", fontsize=10, color='#00BFFF')
ax.tick_params(axis='x', labelsize=8, colors='#222')
ax.tick_params(axis='y', labelsize=8, colors='#222')
ax.set_facecolor('none')
fig_sb.patch.set_alpha(0)
plt.tight_layout(pad=0.5)
st.pyplot(fig_sb)
st.caption(f"<b>Insight:</b> Dari total {total_cust_baru} customer baru, {deal_cust_baru} berhasil deal ({deal_rate_baru:.1f}%).", unsafe_allow_html=True)

# =====================
# Analisis Aktivitas Sales
# =====================
st.markdown("---")
st.header("🚀 Analisis Aktivitas Sales")

# 1. Breakdown Jenis Kunjungan
st.subheader("🔍 Distribusi Jenis Kunjungan Sales")
jenis_kunjungan = df['Jenis_Kunjungan'].value_counts()
fig_jk, ax = plt.subplots(figsize=(4.5, 3))
bars = ax.bar(jenis_kunjungan.index, jenis_kunjungan.values, color='#FF7F50', edgecolor='black')
for bar in bars:
    yval = bar.get_height()
    ax.text(bar.get_x() + bar.get_width()/2, yval + 0.5, int(yval), ha='center', fontsize=8, color='#222')
ax.set_ylabel("Jumlah", fontsize=8, color='#222')
ax.set_xlabel("Jenis Kunjungan", fontsize=8, color='#222')
ax.set_title("Breakdown Jenis Kunjungan", fontsize=10, color='#FF7F50')
ax.tick_params(axis='x', labelrotation=15, labelsize=8, colors='#222')
ax.tick_params(axis='y', labelsize=8, colors='#222')
ax.set_facecolor('none')
fig_jk.patch.set_alpha(0)
plt.tight_layout(pad=0.5)
st.pyplot(fig_jk)
st.caption(f"<b>Jenis kunjungan terbanyak:</b> {jenis_kunjungan.idxmax()} ({jenis_kunjungan.max()} aktivitas)", unsafe_allow_html=True)



# 3. Leaderboard Sales Paling Aktif
st.subheader("🏆 Leaderboard Sales Paling Aktif (Top 10)")
leaderboard = kunjungan_sales.head(10).reset_index()
leaderboard.columns = ['Nama Sales', 'Jumlah Kunjungan']
st.dataframe(leaderboard, use_container_width=True)
st.caption(f"<b>Total sales aktif:</b> {kunjungan_sales.count()} | <b>Rata-rata kunjungan/sales:</b> {kunjungan_sales.mean():.1f}", unsafe_allow_html=True)




# Tabel Detail
with st.expander("📋 Lihat detail kinerja sales"):
    st.dataframe(kinerja_sales.reset_index(), use_container_width=True)



st.markdown("---")
st.header("🎯 Perbandingan Target Sales")

# Hitung rata-rata target sales per Level dan Status_Kontrak
target_avg = df.groupby(['Status_Kontrak', 'Level_Sales'])['Target_Sales'].mean().unstack().fillna(0)

st.subheader("📊 Rata-rata Target Sales per Status Kontrak dan Level Sales")
fig, ax = plt.subplots(figsize=(6.2, 3.2))
colors = ['#00BFFF', '#32CD32', '#FF7F50', '#9370DB', '#A9A9A9']
target_avg.plot(kind='bar', ax=ax, edgecolor='black', color=colors, width=0.65)
ax.set_title("Rata-rata Target Sales per Status Kontrak", fontsize=10, color='#00BFFF')
ax.set_xlabel("Status Kontrak", fontsize=8, color='#222')
ax.set_ylabel("Rata-rata Target (Rp)", fontsize=8, color='#222')
ax.tick_params(axis='x', labelrotation=0, labelsize=7, colors='#222')
ax.tick_params(axis='y', labelsize=7, colors='#222')
ax.set_facecolor('none')
fig.patch.set_alpha(0)
plt.legend(title='Level Sales', fontsize=7, title_fontsize=8, labelcolor='#222')
plt.tight_layout(pad=0.5)
st.pyplot(fig)


# Ambil kunjungan terakhir tiap customer
df['Tanggal'] = pd.to_datetime(df['Tanggal'])
df_last = df.sort_values(by='Tanggal').groupby('ID_Customer').last().reset_index()






# Hitung jumlah customer unik per tahap funnel (cumulative, filtering minimal tahap)
tahapan_order = ['Inisiasi', 'Presentasi', 'Penawaran Harga', 'Negosiasi']
progress_cat = pd.Categorical(df_last['Progress'], categories=tahapan_order, ordered=True)
tahapan_summary = []
for i, tahap in enumerate(tahapan_order):
    # Filter customer yang progres terakhirnya minimal di tahap ini
    mask = progress_cat.codes >= i
    jumlah = df_last[mask]['ID_Customer'].nunique()
    tahapan_summary.append({'Tahap_Progres': tahap, 'Jumlah_Customer': jumlah})
tahapan_summary = pd.DataFrame(tahapan_summary)


st.markdown("---")
st.header("🔁 Funnel Progres Kunjungan")
st.subheader("� Funnel Analytics: Jumlah Customer di Setiap Tahapan")

# Funnel diagram dengan matplotlib patches
import matplotlib.patches as patches


funnel_labels = tahapan_summary['Tahap_Progres'].astype(str).tolist()
funnel_values = tahapan_summary['Jumlah_Customer'].tolist()
colors_funnel = ['#FFD700', '#00BFFF', '#32CD32', '#FF7F50']

fig_funnel, ax = plt.subplots(figsize=(7, 4))
width_top = 5.5
height = 0.7
gap = 0.18
min_width = 1.5
for i, (label, value) in enumerate(zip(funnel_labels, funnel_values)):
    # Lebar proporsional
    if funnel_values[0] == 0:
        width = min_width
    else:
        width = min_width + (width_top - min_width) * (value / funnel_values[0])
    left = (width_top - width) / 2
    bottom = (len(funnel_labels) - i - 1) * (height + gap)
    rect = patches.FancyBboxPatch((left, bottom), width, height,
                                  boxstyle="round,pad=0.08", ec="black", fc=colors_funnel[i], alpha=0.85)
    ax.add_patch(rect)
    ax.text(width_top/2, bottom + height/2, f"{label}\n{value} Customer", ha='center', va='center', fontsize=11, color='#222', weight='bold')

ax.set_xlim(0, width_top)
ax.set_ylim(0, (height+gap)*len(funnel_labels))
ax.axis('off')
fig_funnel.patch.set_alpha(0)
st.pyplot(fig_funnel)

# Konversi per Segmen
kunjungan_segmen = df.groupby('Segmen')['ID_Kunjungan'].count().rename('Total_Kunjungan')
deal_segmen = df[df['Status_Kontrak'] == 'Deal'].groupby('Segmen')['ID_Kunjungan'].count().rename('Jumlah_Deal')

analisis_segmen = pd.concat([kunjungan_segmen, deal_segmen], axis=1).fillna(0)
analisis_segmen['Jumlah_Deal'] = analisis_segmen['Jumlah_Deal'].astype(int)
analisis_segmen['Tingkat_Konversi (%)'] = (analisis_segmen['Jumlah_Deal'] / analisis_segmen['Total_Kunjungan'] * 100).round(2)

# Konversi per Status Customer
kunjungan_status = df.groupby('Status_Customer')['ID_Kunjungan'].count().rename('Total_Kunjungan')
deal_status = df[df['Status_Kontrak'] == 'Deal'].groupby('Status_Customer')['ID_Kunjungan'].count().rename('Jumlah_Deal')

analisis_status = pd.concat([kunjungan_status, deal_status], axis=1).fillna(0)
analisis_status['Jumlah_Deal'] = analisis_status['Jumlah_Deal'].astype(int)
analisis_status['Tingkat_Konversi (%)'] = (analisis_status['Jumlah_Deal'] / analisis_status['Total_Kunjungan'] * 100).round(2)

st.markdown("---")
st.header("🏷️ Konversi Berdasarkan Segmen dan Status Customer")


# Dua kolom: Konversi per Segmen & Status Customer
col1, col2 = st.columns(2)
with col1:
    st.subheader("📊 Konversi per Segmen")
    fig_segmen, ax = plt.subplots(figsize=(5.5, 3))
    sorted_segmen = analisis_segmen.sort_values('Tingkat_Konversi (%)', ascending=True)
    bars = ax.barh(sorted_segmen.index, sorted_segmen['Tingkat_Konversi (%)'],
                   color='#32CD32', edgecolor='black')
    for i, val in enumerate(sorted_segmen['Tingkat_Konversi (%)']):
        ax.text(val + 0.5, i, f"{val}%", va='center', fontsize=8, color='#222')
    ax.set_xlabel("Tingkat Konversi (%)", fontsize=8, color='#222')
    ax.set_title("Deal Rate per Segmen", fontsize=10, color='#32CD32')
    ax.tick_params(axis='x', labelsize=8, colors='#222')
    ax.tick_params(axis='y', labelsize=8, colors='#222')
    ax.set_facecolor('none')
    fig_segmen.patch.set_alpha(0)
    plt.tight_layout(pad=0.5)
    st.pyplot(fig_segmen)
    st.caption(f"<b>Segmen konversi tertinggi:</b> {sorted_segmen['Tingkat_Konversi (%)'].idxmax()} ({sorted_segmen['Tingkat_Konversi (%)'].max()}%)", unsafe_allow_html=True)
with col2:
    st.subheader("👥 Konversi per Status Customer")
    fig_status, ax = plt.subplots(figsize=(5.5, 3))
    sorted_status = analisis_status.sort_values('Tingkat_Konversi (%)', ascending=True)
    bars = ax.barh(sorted_status.index, sorted_status['Tingkat_Konversi (%)'],
                   color='#00BFFF', edgecolor='black')
    for i, val in enumerate(sorted_status['Tingkat_Konversi (%)']):
        ax.text(val + 0.5, i, f"{val}%", va='center', fontsize=8, color='#222')
    ax.set_xlabel("Tingkat Konversi (%)", fontsize=8, color='#222')
    ax.set_title("Deal Rate per Status Customer", fontsize=10, color='#00BFFF')
    ax.tick_params(axis='x', labelsize=8, colors='#222')
    ax.tick_params(axis='y', labelsize=8, colors='#222')
    ax.set_facecolor('none')
    fig_status.patch.set_alpha(0)
    plt.tight_layout(pad=0.5)
    st.pyplot(fig_status)
    st.caption(f"<b>Status konversi tertinggi:</b> {sorted_status['Tingkat_Konversi (%)'].idxmax()} ({sorted_status['Tingkat_Konversi (%)'].max()}%)", unsafe_allow_html=True)


# Pastikan Tanggal sudah dalam datetime
df['Tanggal'] = pd.to_datetime(df['Tanggal'])

# Buat kolom bulan
df['Bulan'] = df['Tanggal'].dt.to_period('M').astype(str)

# Hitung jumlah kunjungan dan deal per bulan
kunjungan_per_bulan = df.groupby('Bulan')['ID_Kunjungan'].count()
deal_per_bulan = df[df['Status_Kontrak'] == 'Deal'].groupby('Bulan')['ID_Kunjungan'].count()

# Gabungkan ke satu DataFrame
tren_bulanan = pd.concat([kunjungan_per_bulan, deal_per_bulan], axis=1).fillna(0)
tren_bulanan.columns = ['Total_Kunjungan', 'Jumlah_Deal']

st.markdown("---")
st.header("📅 Tren Kunjungan & Deal per Bulan")

st.subheader("📈 Jumlah Kunjungan & Deal")



fig_tren, ax = plt.subplots(figsize=(6.2, 3.2))
ax.plot(tren_bulanan.index, tren_bulanan['Total_Kunjungan'],
        marker='o', color='#00BFFF', label='Total Kunjungan', linewidth=2)
ax.plot(tren_bulanan.index, tren_bulanan['Jumlah_Deal'],
        marker='s', color='#32CD32', label='Jumlah Deal', linewidth=2)
ax.set_title("Tren Kunjungan & Deal per Bulan", fontsize=10, color='#00BFFF')
ax.set_xlabel("Bulan", fontsize=8, color='#222')
ax.set_ylabel("Jumlah", fontsize=8, color='#222')
ax.tick_params(axis='x', rotation=45, labelsize=8, colors='#222')
ax.tick_params(axis='y', labelsize=8, colors='#222')
ax.set_facecolor('none')
fig_tren.patch.set_alpha(0)
ax.legend(fontsize=7)
plt.tight_layout(pad=0.5)
st.pyplot(fig_tren)

from wordcloud import WordCloud
from collections import Counter
import re

st.markdown("---")
st.header("☁️ WordCloud Alasan Kegagalan (Catatan Non-Deal)")

st.subheader("💭 Kata yang Sering Muncul dalam Catatan")

# Filter hanya kunjungan non-deal
df_gagal = df[df['Status_Kontrak'].isin(['Tidak Deal', 'Batal', 'Cancel'])]
catatan_text = ' '.join(df_gagal['Catatan'].astype(str).tolist())

# Tokenisasi dan filter stopwords
words = re.findall(r'\b\w+\b', catatan_text.lower())
stopwords_umum = {
    'yang', 'dan', 'dalam', 'untuk', 'dengan', 'pada', 'di',
    'ke', 'dari', 'sebagai', 'ada', 'ini', 'itu', 'karena',
    'sudah', 'belum', 'tidak', 'jadi', 'akan', 'oleh', 'atau'
}
filtered_words = [word for word in words if word not in stopwords_umum and len(word) > 2]

# Hitung frekuensi
word_freq = Counter(filtered_words).most_common(100)

# Buat dictionary untuk WordCloud
word_freq_dict = dict(word_freq)


# Buat WordCloud
wordcloud = WordCloud(
    width=800,
    height=300,
    background_color='white',
    colormap='cool',
    max_words=100
).generate_from_frequencies(word_freq_dict)

# Tampilkan di Streamlit
fig_wc, ax = plt.subplots(figsize=(6.5, 3.5))
ax.imshow(wordcloud, interpolation='bilinear')
ax.axis('off')
fig_wc.patch.set_alpha(0)
st.pyplot(fig_wc)
st.caption("<b>Insight:</b> Kata yang sering muncul dapat menjadi fokus perbaikan strategi sales.", unsafe_allow_html=True)

import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import OneHotEncoder


st.markdown("---")
st.header("🤖 Prediksi Deal & Rekomendasi Strategi")

# Konversi label
df['Is_Deal'] = (df['Status_Kontrak'] == 'Deal').astype(int)
df['Tanggal'] = pd.to_datetime(df['Tanggal'])

# Fitur kategorikal penting
features = ['Progress', 'Segmen', 'Status_Customer', 'Jenis_Kunjungan', 'Level_Sales']
X = pd.get_dummies(df[features], drop_first=True)
y = df['Is_Deal']

# Latih model Logistic Regression
X_train, X_test, y_train, y_test = train_test_split(X, y, random_state=42, test_size=0.2)
model = LogisticRegression(max_iter=1000)
model.fit(X_train, y_train)

# --- Analisis Prediktif Interaktif ---
st.subheader("🔮 Analisis Prediktif Interaktif")
st.write("Pilih fitur di bawah untuk melihat prediksi peluang deal dan rekomendasi strategi follow-up.")

# Ambil opsi unik dari data
opsi_segmen = df['Segmen'].dropna().unique().tolist()
opsi_status_cust = df['Status_Customer'].dropna().unique().tolist()
opsi_progress = df['Progress'].dropna().unique().tolist()
opsi_jenis_kunj = df['Jenis_Kunjungan'].dropna().unique().tolist()
opsi_level_sales = df['Level_Sales'].dropna().unique().tolist()

colf1, colf2 = st.columns(2)
with colf1:
    segmen_input = st.selectbox('Pilih Segmen', opsi_segmen)
    status_cust_input = st.selectbox('Pilih Status Customer', opsi_status_cust)
    progress_input = st.selectbox('Pilih Tahapan/Progress', opsi_progress)
with colf2:
    jenis_kunj_input = st.selectbox('Pilih Jenis Kunjungan', opsi_jenis_kunj)
    level_sales_input = st.selectbox('Pilih Level Sales', opsi_level_sales)

# Buat DataFrame 1 baris dari input user
input_dict = {
    'Progress': progress_input,
    'Segmen': segmen_input,
    'Status_Customer': status_cust_input,
    'Jenis_Kunjungan': jenis_kunj_input,
    'Level_Sales': level_sales_input
}
input_df = pd.DataFrame([input_dict])
input_X = pd.get_dummies(input_df, drop_first=True)
input_X = input_X.reindex(columns=X.columns, fill_value=0)

# Prediksi probabilitas deal
prob_deal = model.predict_proba(input_X)[0, 1]

# Rekomendasi strategi
def strategi(progress, prob):
    if prob >= 0.8:
        return "Dorong ke tahap akhir kontrak"
    elif prob >= 0.6:
        if 'Negosiasi' in progress:
            return "Follow-up intensif minggu ini"
        elif 'Presentasi' in progress:
            return "Lanjut ke Penawaran Harga"
        else:
            return "Percepat follow-up"
    elif prob >= 0.4:
        return "Evaluasi Ulang"
    else:
        return "Pertimbangkan drop atau ubah pendekatan"

rekomendasi = strategi(progress_input, prob_deal)

st.markdown(f"**Prediksi Peluang Deal:** <span style='color:#00BFFF;font-size:22px'><b>{prob_deal*100:.1f}%</b></span>", unsafe_allow_html=True)
st.markdown(f"**Rekomendasi Strategi:** <span style='color:#32CD32;font-size:18px'><b>{rekomendasi}</b></span>", unsafe_allow_html=True)

# --- Analisis batch customer tetap ditampilkan di bawah ---
# Ambil kunjungan terakhir masing-masing customer
latest_visits = df.sort_values(by='Tanggal').groupby('ID_Customer').last().reset_index()

# Prediksi probabilitas deal untuk seluruh customer
X_pred = pd.get_dummies(latest_visits[features], drop_first=True)
X_pred = X_pred.reindex(columns=X.columns, fill_value=0)
latest_visits['Prob_Deal'] = model.predict_proba(X_pred)[:, 1]

latest_visits['Rekomendasi_Strategi'] = latest_visits.apply(
    lambda row: strategi(row['Progress'], row['Prob_Deal']), axis=1
)

# Format hasil
output = latest_visits[['Nama_Customer', 'Nama_Sales', 'Progress', 'Segmen', 'Kunjungan_Ke', 'Prob_Deal', 'Rekomendasi_Strategi']]
output['Probabilitas_Deal'] = (output['Prob_Deal'] * 100).round(0).astype(int).astype(str) + '%'
output = output.drop(columns='Prob_Deal')
output.columns = ['Customer', 'Nama_Sales', 'Progress', 'Segmen', 'Kunjungan_Ke', 'Rekomendasi Strategi', 'Probabilitas Deal']

st.subheader("📋 Rekomendasi Strategi Follow-Up per Customer")
st.dataframe(output.sort_values('Probabilitas Deal', ascending=False).reset_index(drop=True))

# Tambahkan kolom Segmentasi Prioritas
def segment_prioritas(prob):
    if prob >= 0.8:
        return "🔥 Prioritas Tinggi"
    elif prob >= 0.6:
        return "⚠️ Perlu Follow-up Segera"
    elif prob >= 0.4:
        return "🧊 Potensi Rendah"
    else:
        return "❌ Tidak Disarankan"

latest_visits['Segmentasi_Prioritas'] = latest_visits['Prob_Deal'].apply(segment_prioritas)

# Rekomendasi strategi tambahan berdasarkan prioritas
segmentasi_output = latest_visits[['Nama_Customer', 'Segmen', 'Progress', 'Prob_Deal', 'Segmentasi_Prioritas', 'Rekomendasi_Strategi']]
segmentasi_output['Probabilitas_Deal'] = (segmentasi_output['Prob_Deal'] * 100).round(0).astype(int).astype(str) + '%'
segmentasi_output = segmentasi_output.drop(columns='Prob_Deal')
segmentasi_output.columns = ['Customer', 'Segmen', 'Progress', 'Segmentasi Prioritas', 'Rekomendasi Strategi', 'Probabilitas Deal']

st.subheader("📊 Segmentasi Prioritas Customer Berdasarkan Prediksi")
st.dataframe(segmentasi_output.sort_values('Probabilitas Deal', ascending=False).reset_index(drop=True))
