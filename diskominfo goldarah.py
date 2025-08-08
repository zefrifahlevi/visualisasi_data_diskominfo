import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import datetime
import json # Import json for potential debugging display

# --- Konfigurasi Halaman ---
st.set_page_config(page_title="Visualisasi Data Statistik Garut", layout="wide")

# --- Fungsi untuk mengambil data dari API dengan caching ---
@st.cache_data(ttl=3600)  # Cache data selama 1 jam (misalnya 1 jam)
def get_data_from_api(api_url):
    """
    Mengambil data JSON dari URL API yang diberikan dan menerapkan caching.
    """
    try:
        response = requests.get(api_url)
        response.raise_for_status()  # Akan memunculkan HTTPError untuk respons status kode yang buruk (4xx atau 5xx)
        data = response.json()
        return data
    except requests.exceptions.RequestException as e:
        st.error(f"Error saat mengambil data dari API: {e}")
        return None

# --- Bagian Utama Aplikasi ---
st.title("Visualisasi Data Penduduk Kabupaten Garut Berdasarkan Golongan Darah, Kecamatan & Jenis Kelamin")
st.markdown("Data bersumber dari [Garut Satu Data](https://satudata.garutkab.go.id/)")

# URL API yang akan digunakan (sudah diperbarui untuk data golongan darah)
API_URL = "https://satudata-api.garutkab.go.id/api/datasets/jumlah-penduduk-kabupaten-garut-berdasarkan-golongan-darah-4167/"
raw_api_response = get_data_from_api(API_URL)

if raw_api_response:
    st.write(f"Data diperbarui terakhir pada: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    try:
        # PENTING: Mengambil data dari kunci 'data.pivot_data'
        if 'data' in raw_api_response and 'pivot_data' in raw_api_response['data'] and \
           isinstance(raw_api_response['data']['pivot_data'], list):
            df_raw = pd.DataFrame(raw_api_response['data']['pivot_data'])
            st.success("Data berhasil diambil dari kunci 'data.pivot_data'.")
        else:
            st.error("Struktur data API tidak seperti yang diharapkan. Pastikan ada kunci 'data.pivot_data' yang berisi list.")
            st.info("Berikut adalah respons API mentah untuk membantu debugging:")
            st.json(raw_api_response) # Tampilkan respons API mentah untuk debugging
            st.stop()  # Hentikan eksekusi jika data tidak dapat diproses

        # --- Memastikan Kolom yang Dibutuhkan Ada ---
        # Kolom yang dibutuhkan untuk visualisasi golongan darah DAN kecamatan/jenis kelamin
        required_cols_gol_darah = ['tahun', 'gol_drh', 'jumlah']
        required_cols_kecamatan_jk = ['tahun', 'nama_kecamatan', 'jumlah', 'jenis_kelamin']
        
        # Gabungkan semua kolom yang dibutuhkan
        all_required_cols = list(set(required_cols_gol_darah + required_cols_kecamatan_jk))

        existing_cols = df_raw.columns.tolist()

        missing_cols = [col for col in all_required_cols if col not in existing_cols]
        if missing_cols:
            st.error(f"Kolom yang dibutuhkan tidak ditemukan: {', '.join(missing_cols)}")
            st.warning(f"Kolom yang tersedia dalam data: {', '.join(existing_cols)}")
            st.info("Silakan periksa kembali struktur 'pivot_data' di API atau sesuaikan nama kolom di script.")
            st.stop() # Hentikan eksekusi jika kolom tidak lengkap

        # Drop baris dengan nilai NaN pada kolom kunci dan ubah tipe data
        df_raw = df_raw.dropna(subset=all_required_cols)
        df_raw['tahun'] = df_raw['tahun'].astype(int)
        df_raw['jumlah'] = pd.to_numeric(df_raw['jumlah']) # Pastikan kolom 'jumlah' adalah numerik

        with st.expander("Lihat Data Mentah yang Sudah Diproses"):
            st.dataframe(df_raw)

        # Buat dropdown untuk memilih tahun
        list_tahun = sorted(df_raw['tahun'].unique(), reverse=True)
        selected_tahun = st.selectbox("Pilih Tahun:", list_tahun)
        df_filtered = df_raw[df_raw['tahun'] == selected_tahun]

        # --- Tab untuk Visualisasi ---
        if not df_filtered.empty:
            tab1, tab2 = st.tabs(["Berdasarkan Golongan Darah", "Berdasarkan Kecamatan & Jenis Kelamin"])

            with tab1:
                st.markdown(f"### Jumlah Penduduk Berdasarkan Golongan Darah Tahun {selected_tahun}")

                # Buat dua kolom untuk Bar Chart dan Pie Chart
                col1_tab1, col2_tab1 = st.columns(2)

                with col1_tab1:
                    # Visualisasi Bar Chart Golongan Darah
                    df_bar_gol_darah_data = df_filtered.groupby('gol_drh')['jumlah'].sum().reset_index()
                    fig_bar_gol_darah = px.bar(
                        df_bar_gol_darah_data,
                        x='gol_drh',
                        y='jumlah',
                        title=f'Jumlah Penduduk per Golongan Darah',
                        labels={'gol_drh': 'Golongan Darah', 'jumlah': 'Jumlah Penduduk'},
                        color='gol_drh'
                    )
                    fig_bar_gol_darah.update_layout(
                        xaxis={'categoryorder':'total descending'},
                        yaxis_tickformat=".2s" # Format angka menjadi SI-prefix (e.g., 10K, 1M)
                    )
                    st.plotly_chart(fig_bar_gol_darah, use_container_width=True)

                with col2_tab1:
                    # Visualisasi Pie Chart Golongan Darah
                    # st.markdown(f"### Proporsi Penduduk Berdasarkan Golongan Darah") # Judul lebih singkat karena di kolom
                    fig_pie_gol_darah = px.pie(
                        df_bar_gol_darah_data, # Menggunakan data yang sudah diagregasi dari bar chart
                        values='jumlah',
                        names='gol_drh',
                        title=f'Proporsi Penduduk Berdasarkan Golongan Darah Tahun {selected_tahun}',
                        labels={'gol_drh': 'Golongan Darah', 'jumlah': 'Jumlah Penduduk'}
                    )
                    fig_pie_gol_darah.update_traces(textposition='inside', textinfo='percent+label') # Menampilkan persentase dan label di dalam pie
                    st.plotly_chart(fig_pie_gol_darah, use_container_width=True)

                st.markdown("---") # Garis pemisah setelah kolom

                # Visualisasi Line Chart Golongan Darah (tetap full width)
                st.markdown("### Tren Jumlah Penduduk Berdasarkan Golongan Darah dari Tahun ke Tahun")
                df_grouped_gol_darah = df_raw.groupby(['tahun', 'gol_drh']).agg({'jumlah': 'sum'}).reset_index()
                fig_line_gol_darah = px.line(
                    df_grouped_gol_darah,
                    x='tahun',
                    y='jumlah',
                    color='gol_drh',
                    markers=True,
                    title='Tren Jumlah Penduduk Berdasarkan Golongan Darah',
                    labels={'tahun': 'Tahun', 'jumlah': 'Jumlah Penduduk', 'gol_drh': 'Golongan Darah'}
                )
                fig_line_gol_darah.update_layout(
                    hovermode="x unified",
                    yaxis_tickformat=".2s" # Format angka menjadi SI-prefix (e.g., 10K, 1M)
                )
                st.plotly_chart(fig_line_gol_darah, use_container_width=True)

            with tab2:
                st.markdown(f"### Jumlah Penduduk Berdasarkan Kecamatan dan Jenis Kelamin Tahun {selected_tahun}")

                # Buat dua kolom untuk Bar Chart Total dan Stacked Bar Chart
                col1_tab2, col2_tab2 = st.columns(2)

                with col1_tab2:
                    # Visualisasi Bar Chart Jumlah Penduduk per Kecamatan (Total)
                    df_bar_kecamatan_total = df_filtered.groupby('nama_kecamatan')['jumlah'].sum().reset_index()
                    fig_bar_kecamatan_total = px.bar(
                        df_bar_kecamatan_total,
                        x='nama_kecamatan',
                        y='jumlah',
                        title=f'Total Jumlah Penduduk per Kecamatan',
                        labels={'nama_kecamatan': 'Kecamatan', 'jumlah': 'Total Jumlah Penduduk'},
                        color='nama_kecamatan'
                    )
                    fig_bar_kecamatan_total.update_layout(
                        xaxis={'categoryorder':'total descending'},
                        yaxis_tickformat=".2s" # Format angka menjadi SI-prefix (e.g., 10K, 1M)
                    )
                    st.plotly_chart(fig_bar_kecamatan_total, use_container_width=True)

                with col2_tab2:
                    # Visualisasi Stacked Bar Chart Jumlah Penduduk per Kecamatan berdasarkan Jenis Kelamin
                    # st.markdown(f"### Penduduk per Kecamatan (Jenis Kelamin)") # Judul lebih singkat
                    df_stacked_kecamatan_jk = df_filtered.groupby(['nama_kecamatan', 'jenis_kelamin'])['jumlah'].sum().reset_index()
                    fig_stacked_kecamatan_jk = px.bar(
                        df_stacked_kecamatan_jk,
                        x='nama_kecamatan',
                        y='jumlah',
                        color='jenis_kelamin',
                        title=f'Jumlah Penduduk per Kecamatan Berdasarkan Jenis Kelamin',
                        labels={'nama_kecamatan': 'Kecamatan', 'jumlah': 'Jumlah Penduduk', 'jenis_kelamin': 'Jenis Kelamin'},
                        barmode='group' # Menggunakan 'group' untuk bar berdampingan, atau 'stack' untuk bertumpuk
                    )
                    fig_stacked_kecamatan_jk.update_layout(
                        xaxis={'categoryorder':'total descending'},
                        yaxis_tickformat=".2s" # Format angka menjadi SI-prefix (e.g., 10K, 1M)
                    )
                    st.plotly_chart(fig_stacked_kecamatan_jk, use_container_width=True)

                st.markdown("---") # Garis pemisah setelah kolom

                # Visualisasi Line Chart Tren Jumlah Penduduk per Kecamatan dari Tahun ke Tahun
                st.markdown("### Tren Total Jumlah Penduduk per Kecamatan dari Tahun ke Tahun")
                df_grouped_kecamatan_total = df_raw.groupby(['tahun', 'nama_kecamatan']).agg({'jumlah': 'sum'}).reset_index()
                fig_line_kecamatan_total = px.line(
                    df_grouped_kecamatan_total,
                    x='tahun',
                    y='jumlah',
                    color='nama_kecamatan',
                    markers=True,
                    title='Tren Total Jumlah Penduduk per Kecamatan',
                    labels={'tahun': 'Tahun', 'jumlah': 'Total Jumlah Penduduk', 'nama_kecamatan': 'Kecamatan'}
                )
                fig_line_kecamatan_total.update_layout(
                    hovermode="x unified",
                    yaxis_tickformat=".2s" # Format angka menjadi SI-prefix (e.g., 10K, 1M)
                )
                st.plotly_chart(fig_line_kecamatan_total, use_container_width=True)
        else:
            st.info("Tidak ada data yang tersedia untuk tahun yang dipilih.")

    except (KeyError, TypeError, ValueError) as e:
        st.error(f"Terjadi kesalahan saat memproses data: {e}")
        st.info("Berikut adalah respons API mentah untuk membantu debugging:")
        st.json(raw_api_response)
else:
    st.info("Gagal mengambil data dari API. Pastikan URL API benar dan koneksi internet stabil.")
