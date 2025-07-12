import streamlit as st

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

def generate_batch_output(data, episode_range, resolutions, server_order, use_uppercase=True):
    """Menghasilkan output HTML untuk format batch drakor."""
    html_lines = []
    for ep_num in episode_range:
        if ep_num not in data:
            continue
        
        html_lines.append(f'<strong>Episode {ep_num}</strong>')
        
        # Urutkan resolusi sesuai dengan input pengguna
        sorted_resolutions = [res for res in resolutions if res in data.get(ep_num, {})]

        for res in sorted_resolutions:
            link_parts = []
            # Gunakan urutan server yang sudah diatur
            for server in server_order:
                if server in data.get(ep_num, {}).get(res, {}):
                    url = data[ep_num][res][server]
                    display_server = server.upper() if use_uppercase else server
                    link_parts.append(f'<a href="{url}">{display_server}</a>')
            
            if link_parts:
                links_string = " | ".join(link_parts)
                line = f'<p>{res} (HARDSUB INDO) : {links_string}</p>'
                html_lines.append(line)
    
    return "\n".join(html_lines)


# =============================================================================
# STATE INISIALISASI
# =============================================================================

# State untuk Tab 1
if 'serial_data' not in st.session_state:
    st.session_state.serial_data = {}
if 'serial_final_txt' not in st.session_state:
    st.session_state.serial_final_txt = ""

# State untuk Tab 2
if 'single_data' not in st.session_state:
    st.session_state.single_data = {}
if 'single_server_order' not in st.session_state:
    st.session_state.single_server_order = []
if 'single_final_html' not in st.session_state:
    st.session_state.single_final_html = ""
if 'reset_single' not in st.session_state:
    st.session_state.reset_single = False

# State untuk Tab 3 (Batch Drakor)
if 'batch_data' not in st.session_state:
    st.session_state.batch_data = {}
if 'batch_server_order' not in st.session_state:
    st.session_state.batch_server_order = []
if 'batch_final_html' not in st.session_state:
    st.session_state.batch_final_html = ""
if 'reset_batch' not in st.session_state:
    st.session_state.reset_batch = False


# =============================================================================
# UI UTAMA
# =============================================================================

st.set_page_config(layout="wide", page_title="Universal Link Generator")
st.title("Universal Link Generator")

tab1, tab2, tab3 = st.tabs(["Bentuk Link Ringkas", "Bentuk Link Drakor", "Link Batch Drakor"])

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
    st.info("Gunakan mode ini untuk membuat daftar link dengan format Drakor untuk satu episode.")

    if st.session_state.reset_single:
        st.session_state.update({
            "server_single": "",
            "link_single": "",
            "reset_single": False
        })

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
            st.markdown("**Atur Urutan Server**")
            server_list = st.session_state.single_server_order
            for i, server_name in enumerate(server_list):
                r_col1, r_col2, r_col3, r_col4 = st.columns([0.6, 0.15, 0.15, 0.1])
                with r_col1:
                    st.text_input(label="Server", value=server_name, key=f"server_name_{i}", disabled=True, label_visibility="collapsed")
                with r_col2:
                    if st.button("⬆️", key=f"up_{i}", use_container_width=True, disabled=(i == 0)):
                        server_list.insert(i - 1, server_list.pop(i)); st.rerun()
                with r_col3:
                    if st.button("⬇️", key=f"down_{i}", use_container_width=True, disabled=(i == len(server_list) - 1)):
                        server_list.insert(i + 1, server_list.pop(i)); st.rerun()
                with r_col4:
                    if st.button("🗑️", key=f"del_{i}", use_container_width=True):
                        server_to_delete = server_list.pop(i)
                        for res_key in st.session_state.single_data:
                            if server_to_delete in st.session_state.single_data[res_key]:
                                del st.session_state.single_data[res_key][server_to_delete]
                        st.rerun()
            st.divider()

            if st.button("🚀 Generate HTML"):
                st.session_state.single_final_html = generate_single_output(
                    st.session_state.single_data, selected_resolutions, st.session_state.single_server_order)

            if st.session_state.single_final_html:
                st.code(st.session_state.single_final_html, language="html")
                st.markdown("---")
                st.markdown("### 👀 Live Preview")
                st.components.v1.html(st.session_state.single_final_html, height=300, scrolling=True)
            else:
                st.write("Klik tombol 'Generate HTML' untuk melihat hasil.")

# =============================================================================
# TAB 3: LINK BATCH DRAKOR
# =============================================================================
with tab3:
    st.header("Mode Link Batch Drakor")
    st.info("Gunakan mode ini untuk menambahkan server satu per satu untuk rentang episode.")

    if st.session_state.get('reset_batch', False):
        st.session_state.update({
            "batch_server_name": "",
            "batch_links_text": "",
            "reset_batch": False
        })

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("1. Atur Episode & Resolusi")
        c1, c2 = st.columns(2)
        start_ep = c1.number_input("Mulai dari Episode", min_value=1, value=1, step=1, key="batch_start")
        end_ep = c2.number_input("Sampai Episode", min_value=start_ep, value=start_ep, step=1, key="batch_end")

        default_resolutions = ["360p", "480p", "540p", "720p", "1080p"]
        resolutions = st.multiselect(
            "Pilih Resolusi (sesuai urutan link)",
            options=default_resolutions,
            default=["480p", "720p"],
            key="batch_res"
        )
        st.divider()

        st.subheader("2. Tambah Server & Link")
        server_name = st.text_input("Nama Server", placeholder="MIRRORED", key="batch_server_name").strip()
        
        links_text = st.text_area(
            "Tempel link untuk server ini (1 link per baris)",
            placeholder=f"Link Ep{start_ep} {resolutions[0] if resolutions else ''}\nLink Ep{start_ep} {resolutions[1] if len(resolutions)>1 else ''}\n...",
            key="batch_links_text",
            height=200
        )

        if st.button("➕ Tambah Data Batch", type="primary"):
            links = [link.strip() for link in links_text.splitlines() if link.strip()]
            num_eps = (end_ep - start_ep) + 1
            
            if not all([server_name, links, resolutions, num_eps > 0]):
                st.warning("Pastikan Nama Server, Resolusi, dan Link terisi dengan benar.")
            else:
                expected_links = num_eps * len(resolutions)
                if len(links) != expected_links:
                    st.error(f"Jumlah link tidak sesuai. Diperlukan: {expected_links}, Disediakan: {len(links)}.")
                else:
                    link_idx = 0
                    for ep in range(start_ep, end_ep + 1):
                        if ep not in st.session_state.batch_data:
                            st.session_state.batch_data[ep] = {}
                        for res in resolutions:
                            if res not in st.session_state.batch_data[ep]:
                                st.session_state.batch_data[ep][res] = {}
                            st.session_state.batch_data[ep][res][server_name] = links[link_idx]
                            link_idx += 1
                    
                    if server_name not in st.session_state.batch_server_order:
                        st.session_state.batch_server_order.append(server_name)
                    
                    st.success(f"Server '{server_name}' berhasil ditambahkan untuk Episode {start_ep}-{end_ep}!")
                    st.session_state.reset_batch = True
                    st.rerun()

        if st.button("🔄 Reset Semua Data Batch"):
            st.session_state.batch_data = {}
            st.session_state.batch_server_order = []
            st.session_state.batch_final_html = ""
            st.rerun()

    with col2:
        st.subheader("Pengaturan & Hasil")
        if not st.session_state.batch_data:
            st.write("Belum ada data batch yang ditambahkan.")
        else:
            st.markdown("**Daftar & Pengaturan Server**")
            
            server_list = list(st.session_state.batch_server_order)
            for i, s_name in enumerate(server_list):
                # --- Baris Kontrol Utama (di luar expander) ---
                control_cols = st.columns([0.6, 0.1, 0.1, 0.2])
                with control_cols[0]:
                    st.text_input("Server", value=s_name, key=f"display_name_{i}", disabled=True, label_visibility="collapsed")
                with control_cols[1]:
                    if st.button("⬆️", key=f"batch_up_{i}", use_container_width=True, help="Naikkan urutan", disabled=(i == 0)):
                        st.session_state.batch_server_order.insert(i - 1, st.session_state.batch_server_order.pop(i)); st.rerun()
                with control_cols[2]:
                    if st.button("⬇️", key=f"batch_down_{i}", use_container_width=True, help="Turunkan urutan", disabled=(i == len(server_list) - 1)):
                        st.session_state.batch_server_order.insert(i + 1, st.session_state.batch_server_order.pop(i)); st.rerun()
                with control_cols[3]:
                    if st.button("🗑️ Hapus", key=f"batch_del_{i}", use_container_width=True, help=f"Hapus server {s_name}"):
                        server_to_delete = st.session_state.batch_server_order.pop(i)
                        for ep_data in st.session_state.batch_data.values():
                            for res_data in ep_data.values():
                                if server_to_delete in res_data:
                                    del res_data[server_to_delete]
                        st.rerun()

                # --- Expander untuk Edit Detail ---
                with st.expander(f"Edit detail untuk server: {s_name}"):
                    new_server_name = st.text_input("Edit Nama Server", value=s_name, key=f"edit_name_{i}")
                    st.write("**Edit Link:**")

                    for ep_num in range(st.session_state.get('batch_start', 1), st.session_state.get('batch_end', 1) + 1):
                        for res in st.session_state.get('batch_res', []):
                            if ep_num in st.session_state.batch_data and res in st.session_state.batch_data[ep_num] and s_name in st.session_state.batch_data[ep_num][res]:
                                st.text_input(
                                    label=f"Ep {ep_num} - {res}", 
                                    value=st.session_state.batch_data[ep_num][res][s_name],
                                    key=f"link_edit_{i}_{ep_num}_{res}"
                                )
                    
                    if st.button("💾 Simpan Perubahan", key=f"save_changes_{i}", use_container_width=True):
                        # Update Links
                        for ep_num in range(st.session_state.get('batch_start', 1), st.session_state.get('batch_end', 1) + 1):
                            for res in st.session_state.get('batch_res', []):
                                link_key = f"link_edit_{i}_{ep_num}_{res}"
                                if link_key in st.session_state:
                                    st.session_state.batch_data[ep_num][res][s_name] = st.session_state[link_key]

                        # Update Name (Lakukan setelah update link untuk menjaga referensi)
                        if new_server_name != s_name:
                            st.session_state.batch_server_order[i] = new_server_name
                            for ep_data in st.session_state.batch_data.values():
                                for res_data in ep_data.values():
                                    if s_name in res_data:
                                        res_data[new_server_name] = res_data.pop(s_name)
                        
                        st.success(f"Perubahan untuk server '{s_name}' telah disimpan!")
                        st.rerun()
            
            st.divider()
            
            # --- Pengaturan Output Final ---
            use_uppercase_output = st.toggle("Jadikan nama server uppercase", value=True, key="batch_uppercase_output_toggle")

            if st.button("🚀 Generate Batch HTML"):
                episode_range = range(
                    st.session_state.get('batch_start', 1), 
                    st.session_state.get('batch_end', 1) + 1
                )
                st.session_state.batch_final_html = generate_batch_output(
                    st.session_state.batch_data,
                    episode_range,
                    st.session_state.get('batch_res', []),
                    st.session_state.batch_server_order,
                    use_uppercase=use_uppercase_output
                )

            if st.session_state.batch_final_html:
                st.code(st.session_state.batch_final_html, language="html")
                st.markdown("---")
                st.markdown("### 👀 Live Preview")
                st.components.v1.html(st.session_state.batch_final_html, height=300, scrolling=True)
            else:
                st.info("Klik tombol 'Generate Batch HTML' untuk melihat hasil.")
