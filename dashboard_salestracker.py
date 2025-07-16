# dashboard_salestracker.py
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

st.set_page_config(layout="wide")
st.title("📊 Dashboard Analisis Sales Tracker")

# Load data
@st.cache_data
def load_data():
    df = pd.read_csv('sales_visits_enriched_csv.txt', delimiter='\t')
    return df

df = load_data()

# Tampilkan data awal jika diminta
if st.checkbox("Tampilkan data mentah"):
    st.write(df.head())
# --------------------------------------------
# --------------------------------------------
# Fungsi pie chart ringkas dan transparan
def draw_pie(data, title):
    fig, ax = plt.subplots(figsize=(3.2, 3.2))  # Lebih kecil agar muat 4
    fig.patch.set_alpha(0)
    ax.set_facecolor('none')

    explode = [0.05 if val == data.max() else 0 for val in data]

    wedges, texts, autotexts = ax.pie(
        data,
        labels=data.index,
        autopct='%1.1f%%',
        startangle=140,
        colors=plt.cm.Set3.colors,
        explode=explode,
        shadow=True,
        textprops={'fontsize': 9, 'color': 'white'}
    )

    plt.setp(autotexts, color='white')
    plt.setp(texts, color='white')
    plt.title(title, fontsize=10, color='white')

    return fig

# Tampilkan ke Streamlit dalam 4 kolom sejajar
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.pyplot(draw_pie(df['Status_Kontrak'].value_counts(), "Status Kontrak"))

with col2:
    st.pyplot(draw_pie(df['Segmen'].value_counts(), "Segmen"))

with col3:
    st.pyplot(draw_pie(df['Level_Sales'].value_counts(), "Level Sales"))

with col4:
    st.pyplot(draw_pie(df['Status_Customer'].value_counts(), "Status Customer"))

st.markdown("---")
st.header("📈 Kinerja Sales")

# Siapkan data terlebih dahulu (digunakan di 2 kolom)
kunjungan_sales = df['Nama_Sales'].value_counts()
kunjungan_per_sales = df.groupby('Nama_Sales')['ID_Kunjungan'].count()
deal_per_sales = df[df['Status_Kontrak'] == 'Deal'].groupby('Nama_Sales')['ID_Kunjungan'].count()

kinerja_sales = pd.concat([kunjungan_per_sales, deal_per_sales], axis=1).fillna(0)
kinerja_sales.columns = ['Total_Kunjungan', 'Jumlah_Deal']
kinerja_sales['Tingkat_Konversi (%)'] = (kinerja_sales['Jumlah_Deal'] / kinerja_sales['Total_Kunjungan'] * 100).round(2)
kinerja_sales = kinerja_sales.sort_values('Tingkat_Konversi (%)', ascending=False)

# Buat 2 kolom sejajar
col1, col2 = st.columns(2)

# ---------------------
# Kolom 1: Kunjungan
# ---------------------
with col1:
    st.subheader("👥 Total Kunjungan per Sales")
    fig_kunjungan, ax = plt.subplots(figsize=(5.5, 3))
    bars = ax.bar(kunjungan_sales.index, kunjungan_sales.values, color='skyblue', edgecolor='black')
    ax.set_ylabel("Jumlah", fontsize=8, color='white')
    ax.set_xlabel("Nama Sales", fontsize=8, color='white')
    ax.set_title("Total Kunjungan", fontsize=10, color='white')
    ax.tick_params(axis='x', labelrotation=45, labelsize=7, colors='white')
    ax.tick_params(axis='y', labelsize=7, colors='white')
    ax.set_facecolor('none')
    fig_kunjungan.patch.set_alpha(0)
    plt.tight_layout(pad=0.8)
    st.pyplot(fig_kunjungan)

# ---------------------
# Kolom 2: Konversi
# ---------------------
with col2:
    st.subheader("📊 Tingkat Konversi (Deal) per Sales")
    fig_konversi, ax = plt.subplots(figsize=(5.5, 3))
    bars = ax.barh(kinerja_sales.index, kinerja_sales['Tingkat_Konversi (%)'],
                   color='mediumseagreen', edgecolor='black')
    ax.set_xlabel("Tingkat Konversi (%)", fontsize=8, color='white')
    ax.set_title("Tingkat Konversi", fontsize=10, color='white')
    ax.tick_params(axis='x', labelsize=7, colors='white')
    ax.tick_params(axis='y', labelsize=7, colors='white')
    ax.set_facecolor('none')
    fig_konversi.patch.set_alpha(0)
    plt.tight_layout(pad=0.8)
    st.pyplot(fig_konversi)

# ---------------------
# Tabel Detail
# ---------------------
with st.expander("📋 Lihat detail kinerja sales"):
    styled_table = kinerja_sales.reset_index().style.set_properties(**{
        'background-color': '#0e1117',
        'color': 'white',
        'border-color': 'white'
    })
    st.dataframe(styled_table)


st.markdown("---")
st.header("🎯 Perbandingan Target Sales")

# Hitung rata-rata target sales per Level dan Status_Kontrak
target_avg = df.groupby(['Status_Kontrak', 'Level_Sales'])['Target_Sales'].mean().unstack().fillna(0)

# Plot bar chart: status di sumbu X, Level_Sales sebagai batang
st.subheader("📊 Rata-rata Target Sales per Status Kontrak dan Level Sales")

fig, ax = plt.subplots(figsize=(6.2, 3.2))  # Lebih kecil dan ramping

colors = ['skyblue', 'mediumseagreen', 'salmon', 'mediumpurple', 'gray']
target_avg.plot(kind='bar', ax=ax, edgecolor='black', color=colors, width=0.65)

ax.set_title("Rata-rata Target Sales per Status Kontrak", fontsize=10, color='white')
ax.set_xlabel("Status Kontrak", fontsize=8, color='white')
ax.set_ylabel("Rata-rata Target (Rp)", fontsize=8, color='white')
ax.tick_params(axis='x', labelrotation=0, labelsize=7, colors='white')
ax.tick_params(axis='y', labelsize=7, colors='white')
ax.set_facecolor('none')
fig.patch.set_alpha(0)

plt.legend(title='Level Sales', fontsize=7, title_fontsize=8, labelcolor='white')
plt.tight_layout(pad=0.5)

st.pyplot(fig)


# Ambil kunjungan terakhir tiap customer
df['Tanggal'] = pd.to_datetime(df['Tanggal'])
df_last = df.sort_values(by='Tanggal').groupby('ID_Customer').last().reset_index()

# Hitung jumlah customer per tahap progres terakhir
tahapan_summary = df_last['Progress'].value_counts().rename_axis('Tahap_Progres').reset_index(name='Jumlah_Customer')

# Urutkan tahapan sesuai alur funnel
tahapan_order = ['Inisiasi', 'Presentasi', 'Penawaran Harga', 'Negosiasi', 'Paska Deal']
tahapan_summary['Tahap_Progres'] = pd.Categorical(tahapan_summary['Tahap_Progres'], categories=tahapan_order, ordered=True)
tahapan_summary = tahapan_summary.sort_values('Tahap_Progres')

st.markdown("---")
st.header("🔁 Funnel Progres Kunjungan")

st.subheader("📊 Jumlah Customer di Tiap Tahapan Progres (Terakhir)")

fig, ax = plt.subplots(figsize=(6, 3.2))  # Kecil dan ramping

bars = ax.bar(tahapan_summary['Tahap_Progres'], tahapan_summary['Jumlah_Customer'],
              color='steelblue', edgecolor='black')

# Tambahkan angka di atas batang
for bar in bars:
    yval = bar.get_height()
    ax.text(bar.get_x() + bar.get_width()/2, yval + 1, int(yval), ha='center', fontsize=8, color='white')

ax.set_title("Distribusi Tahapan Progres Kunjungan Terakhir", fontsize=10, color='white')
ax.set_xlabel("Tahapan Progres", fontsize=8, color='white')
ax.set_ylabel("Jumlah Customer", fontsize=8, color='white')
ax.tick_params(axis='x', labelsize=8, colors='white')
ax.tick_params(axis='y', labelsize=8, colors='white')
ax.set_facecolor('none')
fig.patch.set_alpha(0)
plt.tight_layout(pad=0.6)

st.pyplot(fig)

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

# Buat dua kolom sejajar
col1, col2 = st.columns(2)

# ------------------------
# Kolom 1: Konversi per Segmen
# ------------------------
with col1:
    st.subheader("📊 Konversi per Segmen")
    fig_segmen, ax = plt.subplots(figsize=(5.5, 3))
    sorted_segmen = analisis_segmen.sort_values('Tingkat_Konversi (%)', ascending=True)

    bars = ax.barh(sorted_segmen.index, sorted_segmen['Tingkat_Konversi (%)'],
                   color='mediumseagreen', edgecolor='black')

    for i, val in enumerate(sorted_segmen['Tingkat_Konversi (%)']):
        ax.text(val + 0.5, i, f"{val}%", va='center', fontsize=8, color='white')

    ax.set_xlabel("Tingkat Konversi (%)", fontsize=8, color='white')
    ax.set_title("Deal Rate per Segmen", fontsize=10, color='white')
    ax.tick_params(axis='x', labelsize=8, colors='white')
    ax.tick_params(axis='y', labelsize=8, colors='white')
    ax.set_facecolor('none')
    fig_segmen.patch.set_alpha(0)
    plt.tight_layout(pad=0.5)

    st.pyplot(fig_segmen)

# ------------------------
# Kolom 2: Konversi per Status Customer
# ------------------------
with col2:
    st.subheader("👥 Konversi per Status Customer")
    fig_status, ax = plt.subplots(figsize=(5.5, 3))
    sorted_status = analisis_status.sort_values('Tingkat_Konversi (%)', ascending=True)

    bars = ax.barh(sorted_status.index, sorted_status['Tingkat_Konversi (%)'],
                   color='steelblue', edgecolor='black')

    for i, val in enumerate(sorted_status['Tingkat_Konversi (%)']):
        ax.text(val + 0.5, i, f"{val}%", va='center', fontsize=8, color='white')

    ax.set_xlabel("Tingkat Konversi (%)", fontsize=8, color='white')
    ax.set_title("Deal Rate per Status Customer", fontsize=10, color='white')
    ax.tick_params(axis='x', labelsize=8, colors='white')
    ax.tick_params(axis='y', labelsize=8, colors='white')
    ax.set_facecolor('none')
    fig_status.patch.set_alpha(0)
    plt.tight_layout(pad=0.5)

    st.pyplot(fig_status)


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

fig_tren, ax = plt.subplots(figsize=(6.2, 3.2))  # Ringkas

ax.plot(tren_bulanan.index, tren_bulanan['Total_Kunjungan'],
        marker='o', color='skyblue', label='Total Kunjungan', linewidth=2)
ax.plot(tren_bulanan.index, tren_bulanan['Jumlah_Deal'],
        marker='s', color='mediumseagreen', label='Jumlah Deal', linewidth=2)

ax.set_title("Tren Kunjungan & Deal per Bulan", fontsize=10, color='white')
ax.set_xlabel("Bulan", fontsize=8, color='white')
ax.set_ylabel("Jumlah", fontsize=8, color='white')
ax.tick_params(axis='x', rotation=45, labelsize=8, colors='white')
ax.tick_params(axis='y', labelsize=8, colors='white')
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
    background_color=None,
    mode='RGBA',
    colormap='tab20',
    max_words=100
).generate_from_frequencies(word_freq_dict)

# Tampilkan di Streamlit
fig_wc, ax = plt.subplots(figsize=(6.5, 3.5))
ax.imshow(wordcloud, interpolation='bilinear')
ax.axis('off')
fig_wc.patch.set_alpha(0)
st.pyplot(fig_wc)

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

# Ambil kunjungan terakhir masing-masing customer
latest_visits = df.sort_values(by='Tanggal').groupby('ID_Customer').last().reset_index()

# Prediksi probabilitas deal
X_pred = pd.get_dummies(latest_visits[features], drop_first=True)
X_pred = X_pred.reindex(columns=X.columns, fill_value=0)
latest_visits['Prob_Deal'] = model.predict_proba(X_pred)[:, 1]

# Strategi follow-up berdasarkan progress dan probabilitas
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
