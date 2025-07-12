import streamlit as st
import requests
import time

# =============================================================================
# FUNGSI-FUNGSI HELPER
# =============================================================================

def shorten_with_ouo(url, api_key):
    """Memperpendek URL menggunakan ouo.io API."""
    if not api_key:
        return url # Kembalikan URL asli jika tidak ada API key
    try:
        api_url = f'https://ouo.io/api/{api_key}?s={url}'
        response = requests.get(api_url)
        if response.status_code == 200:
            # Tambahkan jeda singkat untuk menghindari rate limiting dari API
            time.sleep(0.5) 
            return response.text
        else:
            st.warning(f"Gagal memperpendek {url}. Status: {response.status_code}")
            return url
    except requests.exceptions.RequestException as e:
        st.error(f"Error koneksi saat menghubungi ouo.io: {e}")
        return url

def generate_serial_output(episodes_data, grouping_style, resolutions, shorten_links=False, api_key=""):
    """Menghasilkan output HTML untuk link serial."""
    txt_lines = []
    with st.spinner('Memproses link...'):
        for ep_num in sorted(episodes_data.keys()):
            links = []
            if "Server" in grouping_style:
                for server in sorted(episodes_data[ep_num].keys()):
                    for res in resolutions:
                        if res in episodes_data[ep_num][server]:
                            link_data = episodes_data[ep_num][server][res]
                            url = link_data["url"]
                            if shorten_links:
                                url = shorten_with_ouo(url, api_key)
                            links.append(f'<a href="{url}" rel="nofollow" data-wpel-link="external">{link_data["label"]}</a>')
            elif "Resolusi" in grouping_style:
                for res in resolutions:
                    for server in sorted(episodes_data[ep_num].keys()):
                        if res in episodes_data[ep_num][server]:
                            link_data = episodes_data[ep_num][server][res]
                            url = link_data["url"]
                            if shorten_links:
                                url = shorten_with_ouo(url, api_key)
                            links.append(f'<a href="{url}" rel="nofollow" data-wpel-link="external">{link_data["label"]}</a>')
            txt_lines.append(f'<li><strong>EPISODE {ep_num}</strong> {" ".join(links)}</li>')
    return "\n".join(txt_lines)

def generate_single_output(data, resolutions, servers, shorten_links=False, api_key=""):
    """Menghasilkan output HTML untuk link format Drakor."""
    html_lines = []
    with st.spinner('Memproses dan memperpendek link...'):
        sorted_resolutions = [res for res in resolutions if res in data]
        for res in sorted_resolutions:
            link_parts = []
            for server in servers:
                if server in data[res]:
                    url = data[res][server]
                    if shorten_links:
                        url = shorten_with_ouo(url, api_key)
                    link_parts.append(f'<a href="{url}">{server}</a>')
            if link_parts:
                links_string = " | ".join(link_parts)
                line = f'<p style="text-align: center;"><strong>{res} (Hardsub Indo):</strong> {links_string}</p>'
                html_lines.append(line)
    return "\n".join(html_lines)

def generate_batch_output(data, episode_range, resolutions, server_order, use_uppercase=True, shorten_links=False, api_key=""):
    """Menghasilkan output HTML untuk format batch drakor."""
    html_lines = []
    with st.spinner('Memproses dan memperpendek link...'):
        for ep_num in episode_range:
            if ep_num not in data:
                continue
            html_lines.append(f'<strong>EPISODE {ep_num}</strong>')
            sorted_resolutions = [res for res in resolutions if res in data.get(ep_num, {})]
            for res in sorted_resolutions:
                link_parts = []
                for server in server_order:
                    if server in data.get(ep_num, {}).get(res, {}):
                        url = data[ep_num][res][server]
                        if shorten_links:
                            url = shorten_with_ouo(url, api_key)
                        display_server = server.upper() if use_uppercase else server
                        link_parts.append(f'<a href="{url}">{display_server}</a>')
                if link_parts:
                    links_string = " | ".join(link_parts)
                    line = f'<p>{res} (Hardsub Indo) : {links_string}</p>'
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

# --- Pengaturan API Key Global ---
st.sidebar.header("Pengaturan Global")
ouo_api_key = st.sidebar.text_input("API Key ouo.io", value="8pHuHRq5", type="password", help="Masukkan API Key Anda dari ouo.io untuk menggunakan fitur perpendek link.")

SERVER_OPTIONS = ["(Ketik Manual)", "Mirrored", "TeraBox", "UpFiles", "BuzzHeav", "AkiraBox", "SendNow", "KrakrnFl", "Vidguard", "StreamHG"]
tab1, tab2, tab3 = st.tabs(["Bentuk Link Ringkas", "Bentuk Link Drakor", "Link Batch Drakor"])

# =============================================================================
# TAB 1: LINK SERIAL
# =============================================================================
with tab1:
    st.header("Mode Bentuk Link Ringkas")
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Masukan Data Disini")
        default_resolutions = ["360p", "480p", "540p", "720p", "1080p"]
        selected_resolutions_serial = st.multiselect("Pilih Resolusi", options=default_resolutions, default=["480p", "720p"], key="res_serial")
        start_episode = st.number_input("Mulai dari Episode", min_value=1, step=1, value=1)
        server_name_serial = st.text_input("Nama Server", placeholder="cth: MR", key="server_serial").strip().upper()
        links_serial = st.text_area("Tempel Link (urut per episode & resolusi)", placeholder="Contoh: Ep1 480p Ep1 720p Ep2 480p Ep2 720p...", height=150)
        
        if st.button("+ Tambah Data (Serial)"):
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
        if st.session_state.get('serial_data'):
            st.write("**Ringkasan Data:**")
            st.json(st.session_state.serial_data, expanded=False)
            st.divider()
            grouping_style = st.radio("Gaya Urutan:", ['Berdasarkan Server', 'Berdasarkan Resolusi'], horizontal=True, key="style_serial")
            
            shorten_serial = st.checkbox("Perpendek link dengan ouo.io", key="shorten_serial")
            if shorten_serial and not ouo_api_key:
                st.warning("Masukkan API Key ouo.io di sidebar untuk memperpendek link.")

            if st.button("Buat Kode"):
                st.session_state.serial_final_txt = generate_serial_output(
                    st.session_state.serial_data,
                    grouping_style,
                    selected_resolutions_serial,
                    shorten_links=shorten_serial,
                    api_key=ouo_api_key
                )
            
            st.text_area("Hasil HTML:", value=st.session_state.serial_final_txt, height=200, key="output_serial")
            if st.button("Reset Data Serial"):
                st.session_state.serial_data = {}; st.session_state.serial_final_txt = ""; st.rerun()
        else:
            st.write("Belum ada data serial yang ditambahkan.")


# =============================================================================
# TAB 2: LINK DRAKOR
# =============================================================================
with tab2:
    st.header("Mode Bentuk Link Drakor")
    if st.session_state.get('reset_single', False):
        st.session_state.update({"sb_server_single": SERVER_OPTIONS[0], "txt_server_single": "", "link_single": "", "reset_single": False})
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Masukkan Data Link")
        default_resolutions = ["360p", "480p", "540p", "720p", "1080p"]
        selected_resolutions = st.multiselect("Pilih Resolusi (Urutan ini akan digunakan di hasil akhir)", options=default_resolutions, default=["360p", "480p", "540p", "720p"], key="res_single")
        server_choice_single = st.selectbox("Pilih Nama Server", options=SERVER_OPTIONS, key="sb_server_single")
        server_name_single_input = st.text_input("Nama Server Manual", key="txt_server_single").strip() if server_choice_single == SERVER_OPTIONS[0] else server_choice_single
        links_single = st.text_area("Link (1 link per baris sesuai urutan resolusi)", height=150, key="link_single")
        if st.button("+ Tambah Data", type="primary"):
            links = [l.strip() for l in links_single.strip().splitlines() if l.strip()]
            if not selected_resolutions: st.warning("Pilih minimal satu resolusi.")
            elif not server_name_single_input: st.warning("Nama server tidak boleh kosong.")
            elif len(selected_resolutions) != len(links): st.error(f"Jumlah link ({len(links)}) tidak cocok dengan jumlah resolusi ({len(selected_resolutions)}).")
            else:
                for i, res in enumerate(selected_resolutions):
                    if res not in st.session_state.single_data: st.session_state.single_data[res] = {}
                    st.session_state.single_data[res][server_name_single_input] = links[i]
                if server_name_single_input not in st.session_state.single_server_order: st.session_state.single_server_order.append(server_name_single_input)
                st.success(f"Server '{server_name_single_input}' berhasil ditambahkan."); st.session_state.reset_single = True; st.rerun()
        if st.button("Reset Semua Data"): st.session_state.single_data = {}; st.session_state.single_server_order = []; st.session_state.single_final_html = ""; st.rerun()

    with col2:
        st.subheader("Pengaturan & Hasil")
        if st.session_state.get('single_data'):
            st.markdown("**Daftar & Pengaturan Server**")
            server_list = list(st.session_state.single_server_order)
            for i, s_name in enumerate(server_list):
                control_cols = st.columns([0.7, 0.1, 0.1, 0.1])
                with control_cols[0]: st.text_input("Server", value=s_name, key=f"single_display_name_{i}", disabled=True, label_visibility="collapsed")
                with control_cols[1]:
                    if st.button("↑", key=f"single_up_{i}", use_container_width=True, help="Naikkan urutan", disabled=(i == 0)): st.session_state.single_server_order.insert(i - 1, st.session_state.single_server_order.pop(i)); st.rerun()
                with control_cols[2]:
                    if st.button("↓", key=f"single_down_{i}", use_container_width=True, help="Turunkan urutan", disabled=(i == len(server_list) - 1)): st.session_state.single_server_order.insert(i + 1, st.session_state.single_server_order.pop(i)); st.rerun()
                with control_cols[3]:
                    if st.button("⌦", key=f"single_del_{i}", use_container_width=True, help=f"Hapus server {s_name}"):
                        server_to_delete = st.session_state.single_server_order.pop(i)
                        for res_data in st.session_state.single_data.values():
                            if server_to_delete in res_data: del res_data[server_to_delete]
                        st.rerun()
                with st.expander(f"Edit detail untuk server: {s_name}"):
                    new_server_name = st.text_input("Edit Nama Server", value=s_name, key=f"single_edit_name_{i}")
                    st.write("**Edit Link:**")
                    for res in st.session_state.get('res_single', []):
                        if res in st.session_state.single_data and s_name in st.session_state.single_data[res]:
                            st.text_input(label=res, value=st.session_state.single_data[res][s_name], key=f"single_link_edit_{i}_{res}")
                    if st.button("Simpan Perubahan", key=f"single_save_changes_{i}", use_container_width=True):
                        for res in st.session_state.get('res_single', []):
                            if f"single_link_edit_{i}_{res}" in st.session_state: st.session_state.single_data[res][s_name] = st.session_state[f"single_link_edit_{i}_{res}"]
                        if new_server_name != s_name:
                            st.session_state.single_server_order[i] = new_server_name
                            for res_data in st.session_state.single_data.values():
                                if s_name in res_data: res_data[new_server_name] = res_data.pop(s_name)
                        st.success(f"Perubahan untuk server '{s_name}' telah disimpan!"); st.rerun()
            st.divider()
            
            shorten_single = st.checkbox("Perpendek link dengan ouo.io", key="shorten_single")
            if shorten_single and not ouo_api_key:
                st.warning("Masukkan API Key ouo.io di sidebar untuk memperpendek link.")

            if st.button("Generate HTML"):
                st.session_state.single_final_html = generate_single_output(
                    st.session_state.single_data, selected_resolutions, st.session_state.single_server_order,
                    shorten_links=shorten_single, api_key=ouo_api_key)

            if st.session_state.single_final_html:
                st.code(st.session_state.single_final_html, language="html")
                st.markdown("---"); st.markdown("### Live Preview"); st.components.v1.html(st.session_state.single_final_html, height=300, scrolling=True)
        else:
            st.write("Belum ada data yang dimasukkan.")


# =============================================================================
# TAB 3: LINK BATCH DRAKOR
# =============================================================================
with tab3:
    st.header("Mode Link Batch Drakor")
    if st.session_state.get('reset_batch', False):
        st.session_state.update({"sb_server_batch": SERVER_OPTIONS[0], "txt_server_batch": "", "batch_links_text": "", "reset_batch": False})
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("1. Atur Episode & Resolusi")
        c1, c2 = st.columns(2)
        start_ep = c1.number_input("Mulai dari Episode", min_value=1, value=1, step=1, key="batch_start")
        end_ep = c2.number_input("Sampai Episode", min_value=start_ep, value=start_ep, step=1, key="batch_end")
        default_resolutions = ["360p", "480p", "540p", "720p", "1080p"]
        resolutions = st.multiselect("Pilih Resolusi (sesuai urutan link)", options=default_resolutions, default=["480p", "720p"], key="batch_res")
        st.divider()
        st.subheader("2. Tambah Server & Link")
        server_choice_batch = st.selectbox("Pilih Nama Server", options=SERVER_OPTIONS, key="sb_server_batch")
        server_name = st.text_input("Nama Server Manual", key="txt_server_batch").strip() if server_choice_batch == SERVER_OPTIONS[0] else server_choice_batch
        links_text = st.text_area("Tempel link untuk server ini (1 link per baris)", placeholder=f"Link Ep{start_ep} {resolutions[0] if resolutions else ''}\n...", key="batch_links_text", height=200)
        if st.button("+ Tambah Data Batch", type="primary"):
            links = [link.strip() for link in links_text.splitlines() if link.strip()]
            num_eps = (end_ep - start_ep) + 1
            if not all([server_name, links, resolutions, num_eps > 0]): st.warning("Pastikan Nama Server, Resolusi, dan Link terisi dengan benar.")
            else:
                expected_links = num_eps * len(resolutions)
                if len(links) != expected_links: st.error(f"Jumlah link tidak sesuai. Diperlukan: {expected_links}, Disediakan: {len(links)}.")
                else:
                    link_idx = 0
                    for ep in range(start_ep, end_ep + 1):
                        if ep not in st.session_state.batch_data: st.session_state.batch_data[ep] = {}
                        for res in resolutions:
                            if res not in st.session_state.batch_data[ep]: st.session_state.batch_data[ep][res] = {}
                            st.session_state.batch_data[ep][res][server_name] = links[link_idx]; link_idx += 1
                    if server_name not in st.session_state.batch_server_order: st.session_state.batch_server_order.append(server_name)
                    st.success(f"Server '{server_name}' berhasil ditambahkan untuk Episode {start_ep}-{end_ep}!"); st.session_state.reset_batch = True; st.rerun()
        if st.button("Reset Semua Data Batch"): st.session_state.batch_data = {}; st.session_state.batch_server_order = []; st.session_state.batch_final_html = ""; st.rerun()

    with col2:
        st.subheader("Pengaturan & Hasil")
        if st.session_state.get('batch_data'):
            st.markdown("**Daftar & Pengaturan Server**")
            server_list = list(st.session_state.batch_server_order)
            for i, s_name in enumerate(server_list):
                control_cols = st.columns([0.7, 0.1, 0.1, 0.1])
                with control_cols[0]: st.text_input("Server", value=s_name, key=f"display_name_{i}", disabled=True, label_visibility="collapsed")
                with control_cols[1]:
                    if st.button("↑", key=f"batch_up_{i}", use_container_width=True, help="Naikkan urutan", disabled=(i == 0)): st.session_state.batch_server_order.insert(i - 1, st.session_state.batch_server_order.pop(i)); st.rerun()
                with control_cols[2]:
                    if st.button("↓", key=f"batch_down_{i}", use_container_width=True, help="Turunkan urutan", disabled=(i == len(server_list) - 1)): st.session_state.batch_server_order.insert(i + 1, st.session_state.batch_server_order.pop(i)); st.rerun()
                with control_cols[3]:
                    if st.button("⌦", key=f"batch_del_{i}", use_container_width=True, help=f"Hapus server {s_name}"):
                        server_to_delete = st.session_state.batch_server_order.pop(i)
                        for ep_data in st.session_state.batch_data.values():
                            for res_data in ep_data.values():
                                if server_to_delete in res_data: del res_data[server_to_delete]
                        st.rerun()
                with st.expander(f"Edit detail untuk server: {s_name}"):
                    new_server_name = st.text_input("Edit Nama Server", value=s_name, key=f"edit_name_{i}")
                    st.write("**Edit Link:**")
                    for ep_num in range(st.session_state.get('batch_start', 1), st.session_state.get('batch_end', 1) + 1):
                        for res in st.session_state.get('batch_res', []):
                            if ep_num in st.session_state.batch_data and res in st.session_state.batch_data[ep_num] and s_name in st.session_state.batch_data[ep_num][res]:
                                st.text_input(label=f"Ep {ep_num} - {res}", value=st.session_state.batch_data[ep_num][res][s_name], key=f"link_edit_{i}_{ep_num}_{res}")
                    if st.button("Simpan Perubahan", key=f"save_changes_{i}", use_container_width=True):
                        for ep_num in range(st.session_state.get('batch_start', 1), st.session_state.get('batch_end', 1) + 1):
                            for res in st.session_state.get('batch_res', []):
                                if f"link_edit_{i}_{ep_num}_{res}" in st.session_state: st.session_state.batch_data[ep_num][res][s_name] = st.session_state[f"link_edit_{i}_{ep_num}_{res}"]
                        if new_server_name != s_name:
                            st.session_state.batch_server_order[i] = new_server_name
                            for ep_data in st.session_state.batch_data.values():
                                for res_data in ep_data.values():
                                    if s_name in res_data: res_data[new_server_name] = res_data.pop(s_name)
                        st.success(f"Perubahan untuk server '{s_name}' telah disimpan!"); st.rerun()
            st.divider()
            
            use_uppercase_output = st.toggle("Jadikan nama server uppercase", value=True, key="batch_uppercase_output_toggle")
            shorten_batch = st.checkbox("Perpendek link dengan ouo.io", key="shorten_batch")
            if shorten_batch and not ouo_api_key:
                st.warning("Masukkan API Key ouo.io di sidebar untuk memperpendek link.")

            if st.button("Generate Batch HTML"):
                episode_range = range(st.session_state.get('batch_start', 1), st.session_state.get('batch_end', 1) + 1)
                st.session_state.batch_final_html = generate_batch_output(
                    st.session_state.batch_data, episode_range, st.session_state.get('batch_res', []),
                    st.session_state.batch_server_order, use_uppercase=use_uppercase_output,
                    shorten_links=shorten_batch, api_key=ouo_api_key)

            if st.session_state.batch_final_html:
                st.code(st.session_state.batch_final_html, language="html")
                st.markdown("---"); st.markdown("### Live Preview"); st.components.v1.html(st.session_state.batch_final_html, height=300, scrolling=True)
        else:
            st.write("Belum ada data batch yang ditambahkan.")
