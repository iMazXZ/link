import streamlit as st
import pandas as pd

# =============================================================================
# FUNGSI-FUNGSI HELPER
# =============================================================================

def generate_serial_output(episodes_data, grouping_style, resolutions):
    """Menghasilkan output HTML untuk link serial."""
    txt_lines = []
    for ep_num in sorted(episodes_data.keys()):
        links = []
        # Mengelompokkan berdasarkan Server
        if "Server" in grouping_style:
            for server in sorted(episodes_data[ep_num].keys()):
                for res in resolutions:
                    if res in episodes_data[ep_num][server]:
                        link = episodes_data[ep_num][server][res]
                        links.append(f'<a href="{link["url"]}" rel="nofollow" data-wpel-link="external">{link["label"]}</a>')
        # Mengelompokkan berdasarkan Resolusi
        elif "Resolusi" in grouping_style:
            for res in resolutions:
                for server in sorted(episodes_data[ep_num].keys()):
                    if res in episodes_data[ep_num][server]:
                        link = episodes_data[ep_num][server][res]
                        links.append(f'<a href="{link["url"]}" rel="nofollow" data-wpel-link="external">{link["label"]}</a>')
        txt_lines.append(f'<li><strong>EPISODE {ep_num}</strong> {" ".join(links)}</li>')
    return "\n".join(txt_lines)

def generate_single_output(data, resolutions, servers):
    """Menghasilkan output HTML untuk link format Drakor."""
    html_lines = []
    # Memastikan urutan resolusi sesuai dengan yang dipilih pengguna
    sorted_resolutions = [res for res in resolutions if res in data]

    for res in sorted_resolutions:
        if res not in data:
            continue
        link_parts = []
        # Menggunakan urutan server yang sudah di-reorder oleh pengguna
        for server in servers:
            if server in data[res]:
                url = data[res][server]
                link_parts.append(f'<a href="{url}">{server}</a>')
        if link_parts:
            links_string = " | ".join(link_parts)
            line = f'<p style="text-align: center;"><strong>{res} (Hardsub Indo):</strong> {links_string}</p>'
            html_lines.append(line)
    return "\n".join(html_lines)

# =============================================================================
# STATE INISIALISASI
# =============================================================================

if 'serial_data' not in st.session_state:
    st.session_state.serial_data = {}
if 'serial_final_txt' not in st.session_state:
    st.session_state.serial_final_txt = ""
if 'single_data' not in st.session_state:
    st.session_state.single_data = {}
if 'single_server_order' not in st.session_state:
    st.session_state.single_server_order = []
if 'single_final_html' not in st.session_state:
    st.session_state.single_final_html = ""
if 'reset_single' not in st.session_state:
    st.session_state.reset_single = False

# =============================================================================
# UI UTAMA
# =============================================================================

st.set_page_config(layout="wide", page_title="Universal Link Generator")
st.title("Universal Link Generator")

tab1, tab2 = st.tabs([" Bentuk Link Ringkas", "Bentuk Link Drakor"])

# =============================================================================
# TAB 1: LINK SERIAL
# =============================================================================
with tab1:
    st.header("Mode Bentuk Link Ringkas")
    st.info("Gunakan mode ini untuk membuat daftar link dari satu atau lebih server untuk banyak episode sekaligus.")
    
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Masukan Data Disini")
        default_resolutions = ["360p", "480p", "540p", "720p", "1080p"]
        selected_resolutions_serial = st.multiselect("Pilih Resolusi", options=default_resolutions, default=["480p", "720p"], key="res_serial")
        start_episode = st.number_input("Mulai dari Episode", min_value=1, step=1, value=1)
        server_name_serial = st.text_input("Nama Server", placeholder="cth: MR", key="server_serial").strip().upper()
        links_serial = st.text_area("Tempel Link (urut per episode & resolusi)", placeholder="Contoh: Ep1 480p Ep1 720p Ep2 480p Ep2 720p...", height=150)
        
        if st.button("➕ Tambah Data (Serial)"):
            links = [x.strip() for x in links_serial.split() if x.strip()]
            resolutions = selected_resolutions_serial
            if not server_name_serial or not resolutions or not links:
                st.warning("Pastikan semua field terisi.")
            elif len(links) % len(resolutions) != 0:
                st.error(f"Jumlah link harus kelipatan dari jumlah resolusi ({len(resolutions)}).")
            else:
                count = len(links) // len(resolutions)
                for i in range(count):
                    ep = start_episode + i
                    if ep not in st.session_state.serial_data:
                        st.session_state.serial_data[ep] = {}
                    st.session_state.serial_data[ep][server_name_serial] = {}
                    for j, res in enumerate(resolutions):
                        link_index = i * len(resolutions) + j
                        st.session_state.serial_data[ep][server_name_serial][res] = {"url": links[link_index], "label": f"{server_name_serial} {res}"}
                st.success(f"Server '{server_name_serial}' ditambahkan untuk Episode {start_episode} s/d {start_episode + count - 1}.")

    with col2:
        st.subheader("Hasil Generator Data")
        if not st.session_state.serial_data:
            st.write("Belum ada data serial yang ditambahkan.")
        else:
            st.write("**Ringkasan Data:**")
            st.json(st.session_state.serial_data, expanded=False)
            st.divider()
            
            grouping_style = st.radio("Gaya Urutan:", ['Berdasarkan Server', 'Berdasarkan Resolusi'], horizontal=True, key="style_serial")
            
            if st.button("🔨 BUAT KODE"):
                st.session_state.serial_final_txt = generate_serial_output(
                    st.session_state.serial_data,
                    grouping_style,
                    selected_resolutions_serial
                )
            
            st.text_area("Hasil HTML:", value=st.session_state.serial_final_txt, height=200, key="output_serial")
            
            if st.button("🔄 Reset Data Serial"):
                st.session_state.serial_data = {}
                st.session_state.serial_final_txt = ""
                st.rerun()

# =============================================================================
# TAB 2: LINK DRAKOR
# =============================================================================
with tab2:
    st.header("Mode Bentuk Link Drakor")
    st.info("Gunakan mode ini untuk membuat daftar link dengan format Drakor berdasarkan resolusi dan server.")

    # Reset form input jika diperlukan
    if st.session_state.reset_single:
        st.session_state.update({
            "server_single": "",
            "link_single": "",
            "reset_single": False
        })
        # Tidak perlu me-rerun di sini agar tidak mengganggu alur

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Masukkan Data Link")
        default_resolutions = ["360p", "480p", "540p", "720p", "1080p"]

        selected_resolutions = st.multiselect(
            "Pilih Resolusi (Urutan ini akan digunakan di hasil akhir)",
            options=default_resolutions,
            default=["360p", "480p", "540p", "720p"],
            key="res_single"
        )

        server_name_single = st.text_input(
            "Nama Server",
            placeholder="contoh: TeraBox",
            key="server_single"
        ).strip()

        links_single = st.text_area(
            "Link (1 link per baris sesuai urutan resolusi)",
            height=150,
            key="link_single"
        )

        if st.button("➕ Tambah Data", type="primary"):
            links = [l.strip() for l in links_single.strip().splitlines() if l.strip()]
            if not selected_resolutions:
                st.warning("Pilih minimal satu resolusi.")
            elif not server_name_single:
                st.warning("Nama server tidak boleh kosong.")
            elif len(selected_resolutions) != len(links):
                st.error(f"Jumlah link ({len(links)}) tidak cocok dengan jumlah resolusi yang dipilih ({len(selected_resolutions)}).")
            else:
                for i, res in enumerate(selected_resolutions):
                    if res not in st.session_state.single_data:
                        st.session_state.single_data[res] = {}
                    st.session_state.single_data[res][server_name_single] = links[i]

                if server_name_single not in st.session_state.single_server_order:
                    st.session_state.single_server_order.append(server_name_single)

                st.success(f"Server '{server_name_single}' berhasil ditambahkan.")
                
                # Set flag untuk reset input dan rerun
                st.session_state.reset_single = True
                st.rerun()

        if st.button("🔄 Reset Semua Data"):
            st.session_state.single_data = {}
            st.session_state.single_server_order = []
            st.session_state.single_final_html = ""
            st.rerun()

    with col2:
        st.subheader("Pengaturan Hasil")
        if not st.session_state.single_data:
            st.write("Belum ada data yang dimasukkan.")
        else:
            # --- BLOK BARU UNTUK RE-ORDER ---
            st.markdown("**Atur Ulang Urutan Server**")
            st.info("Seret dan lepas baris untuk mengubah urutan server pada link yang akan dihasilkan.", icon="↕️")
            
            # Buat DataFrame dari urutan server saat ini
            df = pd.DataFrame({"Server": st.session_state.single_server_order})

            # Gunakan st.data_editor untuk memungkinkan re-ordering
            edited_df = st.data_editor(
                df,
                hide_index=True,
                use_container_width=True,
                num_rows="dynamic", # Memungkinkan penghapusan server jika diperlukan
                key="server_order_editor"
            )

            # Ambil urutan baru dari editor
            new_server_order = edited_df["Server"].tolist()
            
            # Perbarui urutan di session state
            st.session_state.single_server_order = new_server_order
            # --- AKHIR BLOK BARU ---
            
            st.divider()

            if st.button("🚀 Generate HTML"):
                st.session_state.single_final_html = generate_single_output(
                    st.session_state.single_data,
                    selected_resolutions, # Menggunakan urutan resolusi dari multiselect
                    st.session_state.single_server_order # Menggunakan urutan server yang sudah diatur
                )

            if st.session_state.single_final_html:
                st.code(st.session_state.single_final_html, language="html")
                st.markdown("---")
                st.markdown("### 👀 Live Preview")
                st.components.v1.html(st.session_state.single_final_html, height=300, scrolling=True)
            else:
                st.write("Klik tombol 'Generate HTML' untuk melihat hasil.")
