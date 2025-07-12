import streamlit as st
import requests
import time

# =============================================================================
# FUNGSI-FUNGSI HELPER (TIDAK BERUBAH)
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

def generate_output_ringkas(data, episode_range, resolutions, servers, shorten_servers=[], api_key=""):
    """Menghasilkan output HTML format ringkas (seperti Tab 1 lama)."""
    txt_lines = []
    with st.spinner('Memproses link...'):
        for ep_num in episode_range:
            if ep_num not in data: continue
            link_parts = []
            for server in servers:
                if server not in data[ep_num]: continue
                for res in resolutions:
                    if res in data[ep_num][server]:
                        url = data[ep_num][server][res]
                        if server in shorten_servers:
                            url = shorten_with_ouo(url, api_key)
                        link_parts.append(f'<a href="{url}" rel="nofollow" data-wpel-link="external">{server.upper()} {res}</a>')
            txt_lines.append(f'<li><strong>EPISODE {ep_num}</strong> {" ".join(link_parts)}</li>')
    return "\n".join(txt_lines)

def generate_output_drakor_center(data, resolutions, servers, shorten_servers=[], api_key=""):
    """Menghasilkan output HTML format drakor center (seperti Tab 2 lama)."""
    html_lines = []
    with st.spinner('Memproses dan memperpendek link...'):
        for res in resolutions:
            link_parts = []
            for server in servers:
                if res in data and server in data[res]:
                    url = data[res][server]
                    if server in shorten_servers:
                        url = shorten_with_ouo(url, api_key)
                    link_parts.append(f'<a href="{url}">{server}</a>')
            if link_parts:
                links_string = " | ".join(link_parts)
                line = f'<p style="text-align: center;"><strong>{res} (Hardsub Indo):</strong> {links_string}</p>'
                html_lines.append(line)
    return "\n".join(html_lines)

def generate_output_batch_drakor(data, episode_range, resolutions, servers, use_uppercase=True, shorten_servers=[], api_key=""):
    """Menghasilkan output HTML format batch drakor (seperti Tab 3 lama)."""
    html_lines = []
    with st.spinner('Memproses dan memperpendek link...'):
        for ep_num in episode_range:
            if ep_num not in data: continue
            html_lines.append(f'<strong>EPISODE {ep_num}</strong>')
            for res in resolutions:
                if res not in data[ep_num]: continue
                link_parts = []
                for server in servers:
                    if server in data[ep_num][res]:
                        url = data[ep_num][res][server]
                        if server in shorten_servers:
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
if 'main_data' not in st.session_state:
    st.session_state.main_data = {}
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

    # --- Pilihan Mode Input ---
    input_mode = st.radio("Pilih Mode Input", ["Batch Episode", "Single Link"], horizontal=True, key="input_mode")
    
    start_ep, end_ep = 1, 1
    if input_mode == "Batch Episode":
        c1, c2 = st.columns(2)
        start_ep = c1.number_input("Mulai dari Episode", min_value=1, value=1, step=1, key="start_ep")
        end_ep = c2.number_input("Sampai Episode", min_value=start_ep, value=start_ep, step=1, key="end_ep")

    # --- Input Umum ---
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
                episode_range = range(start_ep, end_ep + 1) if input_mode == "Batch Episode" else [1] # Gunakan [1] sebagai placeholder untuk single link

                for ep in episode_range:
                    if ep not in st.session_state.main_data: st.session_state.main_data[ep] = {}
                    for res in resolutions:
                        if server_name not in st.session_state.main_data[ep]: st.session_state.main_data[ep][server_name] = {}
                        st.session_state.main_data[ep][server_name][res] = links[link_idx]
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
                        if server_to_delete in ep_data: del ep_data[server_to_delete]
                    st.rerun()
            with st.expander(f"Edit detail untuk server: {s_name}"):
                # ... (Logika edit tetap sama, hanya disesuaikan untuk struktur data baru)
                pass # Untuk sementara, logika edit bisa ditambahkan kembali jika diperlukan
        
        st.divider()

        # --- Pilihan Format Output ---
        st.subheader("Pilih Format Output")
        output_format = st.radio(
            "Pilih format HTML yang akan dihasilkan:",
            ["Format Batch Drakor (Default)", "Format Drakor - Center", "Format Ringkas"],
            key="output_format"
        )
        
        use_uppercase = True
        if output_format == "Format Batch Drakor (Default)":
            use_uppercase = st.toggle("Jadikan nama server uppercase", value=True, key="uppercase_toggle")

        if st.button("🚀 Generate HTML", type="primary"):
            final_html = ""
            episode_range = range(st.session_state.get('start_ep', 1), st.session_state.get('end_ep', 1) + 1)
            
            if output_format == "Format Ringkas":
                # Untuk format ringkas, kita asumsikan data yang relevan adalah dari episode batch
                final_html = generate_output_ringkas(st.session_state.main_data, episode_range, st.session_state.resolutions, st.session_state.server_order, servers_to_shorten, ouo_api_key)
            elif output_format == "Format Drakor - Center":
                # Ambil data dari episode pertama sebagai representasi single link
                single_data_for_gen = st.session_state.main_data.get(1, {})
                # Balik strukturnya agar sesuai dengan format yang diharapkan fungsi
                formatted_single_data = {}
                for server, res_links in single_data_for_gen.items():
                    for res, link in res_links.items():
                        if res not in formatted_single_data: formatted_single_data[res] = {}
                        formatted_single_data[res][server] = link
                final_html = generate_output_drakor_center(formatted_single_data, st.session_state.resolutions, st.session_state.server_order, servers_to_shorten, ouo_api_key)
            else: # "Format Batch Drakor (Default)"
                final_html = generate_output_batch_drakor(st.session_state.main_data, episode_range, st.session_state.resolutions, st.session_state.server_order, use_uppercase, servers_to_shorten, ouo_api_key)
            
            st.session_state.final_html = final_html

        if st.session_state.final_html:
            st.code(st.session_state.final_html, language="html")
            st.markdown("---")
            st.markdown("### 👀 Live Preview")
            st.components.v1.html(st.session_state.final_html, height=300, scrolling=True)
