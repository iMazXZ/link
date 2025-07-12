import streamlit as st
import requests
import time

# =============================================================================
# FUNGSI-FUNGSI HELPER (DIPERBARUI DAN DISATUKAN)
# =============================================================================

def shorten_with_ouo(url, api_key):
    """Memperpendek URL menggunakan ouo.io API."""
    if not api_key:
        st.warning("API Key ouo.io tidak ditemukan. Link tidak diperpendek.", icon="🔑")
        return url
    try:
        api_url = f'https://ouo.io/api/{api_key}?s={url}'
        response = requests.get(api_url)
        if response.status_code == 200:
            time.sleep(0.5) 
            return response.text
        else:
            st.warning(f"Gagal memperpendek {url}. Status: {response.status_code}")
            return url
    except requests.exceptions.RequestException as e:
        st.error(f"Error koneksi saat menghubungi ouo.io: {e}")
        return url

def generate_output_ringkas(data, episode_range, resolutions, servers, grouping_style, use_uppercase=True, shorten_servers=[], api_key=""):
    """Menghasilkan output HTML format ringkas dengan opsi grouping dan uppercase."""
    txt_lines = []
    with st.spinner('Memproses link...'):
        for ep_num in episode_range:
            if ep_num not in data: continue
            
            link_parts = []
            display_server = ""
            # Logika pengelompokan
            if "Server" in grouping_style:
                for server in servers:
                    for res in resolutions:
                        if res in data.get(ep_num, {}) and server in data.get(ep_num, {}).get(res, {}):
                            url = data[ep_num][res][server]
                            if server in shorten_servers:
                                url = shorten_with_ouo(url, api_key)
                            display_server = server.upper() if use_uppercase else server
                            link_parts.append(f'<a href="{url}" rel="nofollow" data-wpel-link="external">{display_server} {res}</a>')
            else: # "Resolusi"
                for res in resolutions:
                    for server in servers:
                        if res in data.get(ep_num, {}) and server in data.get(ep_num, {}).get(res, {}):
                            url = data[ep_num][res][server]
                            if server in shorten_servers:
                                url = shorten_with_ouo(url, api_key)
                            display_server = server.upper() if use_uppercase else server
                            link_parts.append(f'<a href="{url}" rel="nofollow" data-wpel-link="external">{display_server} {res}</a>')

            if link_parts:
                txt_lines.append(f'<li><strong>EPISODE {ep_num}</strong> {" ".join(link_parts)}</li>')
    return "\n".join(txt_lines)

def generate_output_drakor(data, episode_range, resolutions, servers, use_uppercase=True, is_centered=False, shorten_servers=[], api_key=""):
    """Menghasilkan output HTML format Drakor (mendukung batch dan single, serta perataan)."""
    html_lines = []
    style_attr = ' style="text-align: center;"' if is_centered else ''
    
    with st.spinner('Memproses dan memperpendek link...'):
        for ep_num in episode_range:
            if ep_num not in data: continue
            
            if len(episode_range) > 1:
                html_lines.append(f'<p{style_attr}><strong>EPISODE {ep_num}</strong></p>')

            for res in resolutions:
                if res not in data.get(ep_num, {}): continue
                link_parts = []
                for server in servers:
                    if server in data.get(ep_num, {}).get(res, {}):
                        url = data[ep_num][res][server]
                        if server in shorten_servers:
                            url = shorten_with_ouo(url, api_key)
                        display_server = server.upper() if use_uppercase else server
                        link_parts.append(f'<a href="{url}">{display_server}</a>')
                if link_parts:
                    links_string = " | ".join(link_parts)
                    line = f'<p{style_attr}><strong>{res} (Hardsub Indo):</strong> {links_string}</p>'
                    html_lines.append(line)
    return "\n".join(html_lines)


# =============================================================================
# STATE INISIALISASI
# =============================================================================
if 'main_data' not in st.session_state:
    st.session_state.main_data = {} # Struktur: {ep: {res: {server: link}}}
if 'server_order' not in st.session_state:
    st.session_state.server_order = []
if 'final_html' not in st.session_state:
    st.session_state.final_html = ""
if 'reset_form' not in st.session_state:
    st.session_state.reset_form = False

# =============================================================================
# UI UTAMA
# =============================================================================

st.set_page_config(layout="wide", page_title="Universal Link Generator")
st.title("Universal Link Generator")

# --- Pengaturan API Key Global ---
st.sidebar.header("Pengaturan Global")
ouo_api_key = st.sidebar.text_input("API Key ouo.io", value="8pHuHRq5", type="password", help="Masukkan API Key Anda dari ouo.io untuk menggunakan fitur perpendek link.")
SERVER_OPTIONS = ["(Ketik Manual)", "Mirrored", "TeraBox", "UpFiles", "BuzzHeav", "AkiraBox", "SendNow", "KrakrnFl", "Vidguard", "StreamHG"]

# --- Layout Utama ---
col1, col2 = st.columns(2)

# =============================================================================
# KOLOM KIRI: INPUT DATA
# =============================================================================
with col1:
    st.header("1. Input Data")

    if st.session_state.get('reset_form', False):
        st.session_state.update({"sb_server": SERVER_OPTIONS[0], "txt_server": "", "links_text": "", "reset_form": False})

    input_mode = st.radio("Pilih Mode Input", ["Batch Episode", "Single Link"], horizontal=True, key="input_mode")
    
    start_ep, end_ep = 1, 1
    if input_mode == "Batch Episode":
        c1, c2 = st.columns(2)
        start_ep = c1.number_input("Mulai dari Episode", min_value=1, value=1, step=1, key="start_ep")
        end_ep = c2.number_input("Sampai Episode", min_value=start_ep, value=start_ep, step=1, key="end_ep")

    default_resolutions = ["360p", "480p", "540p", "720p", "1080p"]
    resolutions = st.multiselect("Pilih Resolusi (sesuai urutan link)", options=default_resolutions, default=["480p", "720p"], key="resolutions")
    
    server_choice = st.selectbox("Pilih Nama Server", options=SERVER_OPTIONS, key="sb_server")
    server_name = st.text_input("Nama Server Manual", key="txt_server").strip() if server_choice == SERVER_OPTIONS[0] else server_choice
    
    links_text = st.text_area("Tempel link untuk server ini (1 link per baris)", key="links_text", height=200)

    if st.button("+ Tambah Data", type="primary"):
        links = [link.strip() for link in links_text.splitlines() if link.strip()]
        num_eps = (end_ep - start_ep) + 1 if input_mode == "Batch Episode" else 1
        
        if not all([server_name, links, resolutions]):
            st.warning("Pastikan Nama Server, Resolusi, dan Link terisi.")
        else:
            expected_links = num_eps * len(resolutions)
            if len(links) != expected_links:
                st.error(f"Jumlah link tidak sesuai. Diperlukan: {expected_links}, Disediakan: {len(links)}.")
            else:
                link_idx = 0
                episode_range = range(start_ep, end_ep + 1) if input_mode == "Batch Episode" else [1]
                for ep in episode_range:
                    if ep not in st.session_state.main_data: st.session_state.main_data[ep] = {}
                    for res in resolutions:
                        if res not in st.session_state.main_data[ep]: st.session_state.main_data[ep][res] = {}
                        st.session_state.main_data[ep][res][server_name] = links[link_idx]
                        link_idx += 1
                
                if server_name not in st.session_state.server_order:
                    st.session_state.server_order.append(server_name)
                
                st.success(f"Server '{server_name}' berhasil ditambahkan!"); st.session_state.reset_form = True; st.rerun()

    if st.button("🔄 Reset Semua Data & Pengaturan"):
        st.session_state.main_data = {}; st.session_state.server_order = []; st.session_state.final_html = ""; st.rerun()

# =============================================================================
# KOLOM KANAN: PENGATURAN & HASIL
# =============================================================================
with col2:
    st.header("2. Pengaturan & Hasil")
    if not st.session_state.main_data:
        st.info("Belum ada data yang ditambahkan.")
    else:
        st.markdown("**Daftar & Pengaturan Server**")
        servers_to_shorten = []
        server_list = list(st.session_state.server_order)
        for i, s_name in enumerate(server_list):
            control_cols = st.columns([0.2, 0.5, 0.1, 0.1, 0.1])
            with control_cols[0]:
                if st.checkbox("ouo.io", key=f"shorten_{i}", help=f"Perpendek link untuk {s_name}"):
                    servers_to_shorten.append(s_name)
            with control_cols[1]:
                st.text_input("Server", value=s_name, key=f"display_name_{i}", disabled=True, label_visibility="collapsed")
            with control_cols[2]:
                if st.button("↑", key=f"up_{i}", use_container_width=True, help="Naikkan urutan", disabled=(i == 0)):
                    st.session_state.server_order.insert(i - 1, st.session_state.server_order.pop(i)); st.rerun()
            with control_cols[3]:
                if st.button("↓", key=f"down_{i}", use_container_width=True, help="Turunkan urutan", disabled=(i == len(server_list) - 1)):
                    st.session_state.server_order.insert(i + 1, st.session_state.server_order.pop(i)); st.rerun()
            with control_cols[4]:
                if st.button("⌦", key=f"del_{i}", use_container_width=True, help=f"Hapus server {s_name}"):
                    server_to_delete = st.session_state.server_order.pop(i)
                    for ep_data in st.session_state.main_data.values():
                        for res_data in ep_data.values():
                            if server_to_delete in res_data: del res_data[server_to_delete]
                    st.rerun()
            with st.expander(f"Edit detail untuk server: {s_name}"):
                new_server_name = st.text_input("Edit Nama Server", value=s_name, key=f"edit_name_{i}")
                st.write("**Edit Link:**")
                for ep_num, res_data in st.session_state.main_data.items():
                    for res, server_links in res_data.items():
                        if s_name in server_links:
                            st.text_input(label=f"Ep {ep_num} - {res}", value=server_links[s_name], key=f"link_edit_{i}_{ep_num}_{res}")
                
                if st.button("Simpan Perubahan", key=f"save_changes_{i}", use_container_width=True):
                    for ep_num, res_data in st.session_state.main_data.items():
                        for res, server_links in res_data.items():
                            if s_name in server_links:
                                link_key = f"link_edit_{i}_{ep_num}_{res}"
                                if link_key in st.session_state:
                                    st.session_state.main_data[ep_num][res][s_name] = st.session_state[link_key]
                    if new_server_name != s_name and new_server_name:
                        st.session_state.server_order[i] = new_server_name
                        for ep_data in st.session_state.main_data.values():
                            for res, res_data_inner in ep_data.items():
                                if s_name in res_data_inner:
                                    res_data_inner[new_server_name] = res_data_inner.pop(s_name)
                    st.success(f"Perubahan untuk server '{s_name}' telah disimpan!"); st.rerun()

        st.divider()

        st.subheader("Pilih Format Output")
        output_format = st.radio("Pilih format HTML:", ["Format Drakor", "Format Ringkas"], key="output_format")
        
        # Opsi kondisional berdasarkan format yang dipilih
        if output_format == "Format Drakor":
            c1, c2 = st.columns(2)
            use_uppercase_drakor = c1.toggle("Server Uppercase", value=True, key="uppercase_drakor_toggle")
            is_centered = c2.toggle("Rata Tengah", value=False, key="center_align_toggle")
        else: # Format Ringkas
            c1, c2 = st.columns(2)
            grouping_style = c1.radio("Urutkan berdasarkan:", ["Server", "Resolusi"], key="grouping_style")
            use_uppercase_ringkas = c2.toggle("Server Uppercase", value=True, key="uppercase_ringkas_toggle")

        if st.button("🚀 Generate HTML", type="primary"):
            final_html = ""
            active_resolutions = st.session_state.get('resolutions', [])
            
            if output_format == "Format Ringkas":
                episode_keys = sorted(st.session_state.main_data.keys())
                episode_range = range(episode_keys[0], episode_keys[-1] + 1)
                final_html = generate_output_ringkas(st.session_state.main_data, episode_range, active_resolutions, st.session_state.server_order, grouping_style, use_uppercase=use_uppercase_ringkas, shorten_servers=servers_to_shorten, api_key=ouo_api_key)
            else: # Format Drakor
                input_mode = st.session_state.get('input_mode')
                episode_range = [1] if input_mode == "Single Link" else range(st.session_state.start_ep, st.session_state.end_ep + 1)
                final_html = generate_output_drakor(st.session_state.main_data, episode_range, active_resolutions, st.session_state.server_order, use_uppercase_drakor, is_centered, servers_to_shorten, ouo_api_key)
            
            st.session_state.final_html = final_html

        if st.session_state.final_html:
            st.code(st.session_state.final_html, language="html")
            st.markdown("---")
            st.markdown("### 👀 Live Preview")
            st.components.v1.html(st.session_state.final_html, height=300, scrolling=True)
