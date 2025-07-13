import streamlit as st
import requests
import time
import json
import base64
from datetime import datetime

# =============================================================================
# FUNGSI-FUNGSI HELPER
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

def generate_output_streaming(data, episode_range, resolutions, servers, use_uppercase=True, shorten_servers=[], api_key=""):
    """Menghasilkan output HTML format Streaming."""
    txt_lines = []
    with st.spinner('Memproses link...'):
        for ep_num in episode_range:
            if ep_num not in data: continue
            
            link_parts = []
            # 1. Tambahkan link streaming jika ada
            stream_link = data[ep_num].get('stream_link')
            if stream_link:
                if "Streaming" in shorten_servers: # Gunakan "Streaming" sebagai server virtual
                    stream_link = shorten_with_ouo(stream_link, api_key)
                link_parts.append(f'<a href="{stream_link}">Streaming</a>')

            # 2. Tambahkan link download
            download_links = data[ep_num].get('download_links', {})
            for res in resolutions:
                for server in servers:
                    if res in download_links and server in download_links[res]:
                        url = download_links[res][server]
                        if server in shorten_servers:
                            url = shorten_with_ouo(url, api_key)
                        display_server = server.upper() if use_uppercase else server
                        link_parts.append(f'<a href="{url}">{display_server} {res}</a>')

            if link_parts:
                txt_lines.append(f'EPISODE {ep_num} {" ".join(link_parts)}')
    return "\n".join(txt_lines)


def generate_output_ringkas(data, episode_range, resolutions, servers, grouping_style, use_uppercase=True, shorten_servers=[], api_key=""):
    """Menghasilkan output HTML format ringkas."""
    txt_lines = []
    with st.spinner('Memproses link...'):
        for ep_num in episode_range:
            if ep_num not in data or not data[ep_num].get('download_links'): continue
            
            download_links = data[ep_num]['download_links']
            link_parts = []
            if "Server" in grouping_style:
                for server in servers:
                    for res in resolutions:
                        if res in download_links and server in download_links[res]:
                            url = download_links[res][server]
                            if server in shorten_servers: url = shorten_with_ouo(url, api_key)
                            display_server = server.upper() if use_uppercase else server
                            link_parts.append(f'<a href="{url}" rel="nofollow" data-wpel-link="external">{display_server} {res}</a>')
            else: # "Resolusi"
                for res in resolutions:
                    for server in servers:
                        if res in download_links and server in download_links[res]:
                            url = download_links[res][server]
                            if server in shorten_servers: url = shorten_with_ouo(url, api_key)
                            display_server = server.upper() if use_uppercase else server
                            link_parts.append(f'<a href="{url}" rel="nofollow" data-wpel-link="external">{display_server} {res}</a>')

            if link_parts:
                txt_lines.append(f'<li><strong>EPISODE {ep_num}</strong> {" ".join(link_parts)}</li>')
    return "\n".join(txt_lines)

def generate_output_drakor(data, episode_range, resolutions, servers, use_uppercase=True, is_centered=False, shorten_servers=[], api_key=""):
    """Menghasilkan output HTML format Drakor."""
    html_lines = []
    style_attr = ' style="text-align: center;"' if is_centered else ''
    
    with st.spinner('Memproses dan memperpendek link...'):
        for ep_num in episode_range:
            if ep_num not in data: continue
            
            if len(episode_range) > 1:
                html_lines.append(f'<p{style_attr}><strong>EPISODE {ep_num}</strong></p>')

            download_links = data[ep_num].get('download_links', {})
            for res in resolutions:
                if res not in download_links: continue
                link_parts = []
                for server in servers:
                    if server in download_links[res]:
                        url = download_links[res][server]
                        if server in shorten_servers: url = shorten_with_ouo(url, api_key)
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
    st.session_state.main_data = {} # Struktur: {ep: {'stream_link': '...', 'download_links': {res: {server: link}}}}
if 'server_order' not in st.session_state:
    st.session_state.server_order = []
if 'final_html' not in st.session_state:
    st.session_state.final_html = ""
if 'reset_form' not in st.session_state:
    st.session_state.reset_form = False
if 'resolutions' not in st.session_state:
    st.session_state.resolutions = ["480p", "720p"]
if 'start_ep' not in st.session_state:
    st.session_state.start_ep = 1
if 'end_ep' not in st.session_state:
    st.session_state.end_ep = 1


# =============================================================================
# UI UTAMA
# =============================================================================

st.set_page_config(layout="wide", page_title="Universal Link Generator")
st.title("Universal Link Generator")

# --- Pengaturan Sidebar ---
st.sidebar.header("Pengaturan Global")
ouo_api_key = st.sidebar.text_input("API Key ouo.io", value="8pHuHRq5", type="password", help="Masukkan API Key Anda dari ouo.io.")
st.sidebar.divider()
st.sidebar.header("Simpan & Muat Sesi")
if st.sidebar.button("Simpan Sesi Saat Ini"):
    session_data = {'main_data': st.session_state.main_data, 'server_order': st.session_state.server_order, 'resolutions': st.session_state.resolutions, 'start_ep': st.session_state.start_ep, 'end_ep': st.session_state.end_ep}
    session_json = json.dumps(session_data, indent=4)
    b64 = base64.b64encode(session_json.encode()).decode()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    href = f'<a href="data:file/json;base64,{b64}" download="link_generator_session_{timestamp}.json">Unduh File Sesi</a>'
    st.sidebar.markdown(href, unsafe_allow_html=True)
    st.sidebar.success("File sesi siap diunduh.")
json_text_to_load = st.sidebar.text_area("Tempel konten file .json di sini untuk memuat sesi", height=150)
if st.sidebar.button("Muat dari Teks"):
    if json_text_to_load:
        try:
            loaded_data = json.loads(json_text_to_load)
            required_keys = ['main_data', 'server_order', 'resolutions', 'start_ep', 'end_ep']
            if all(key in loaded_data for key in required_keys):
                st.session_state.main_data = {int(k): v for k, v in loaded_data['main_data'].items()}
                st.session_state.server_order = loaded_data['server_order']
                st.session_state.resolutions = loaded_data['resolutions']
                st.session_state.start_ep = loaded_data['start_ep']
                st.session_state.end_ep = loaded_data['end_ep']
                st.session_state.final_html = ""; st.sidebar.success("Sesi berhasil dimuat!"); st.rerun()
            else: st.sidebar.error("Teks JSON tidak valid.")
        except Exception as e: st.sidebar.error(f"Gagal memuat: {e}")
    else: st.sidebar.warning("Area teks kosong.")

SERVER_OPTIONS = ["(Ketik Manual)", "Mirrored", "TeraBox", "UpFiles", "BuzzHeav", "AkiraBox", "SendNow", "KrakrnFl", "Vidguard", "StreamHG"]
col1, col2 = st.columns(2)

# =============================================================================
# KOLOM KIRI: INPUT DATA
# =============================================================================
with col1:
    st.header("1. Input Data")
    if st.session_state.get('reset_form', False):
        st.session_state.update({"sb_server": SERVER_OPTIONS[0], "txt_server": "", "links_text": "", "stream_links_text": "", "reset_form": False})

    input_mode = st.radio("Pilih Mode Input", ["Batch Episode", "Single Link"], horizontal=True, key="input_mode")
    
    stream_links_text = ""
    if input_mode == "Batch Episode":
        c1, c2 = st.columns(2)
        st.session_state.start_ep = c1.number_input("Mulai dari Episode", min_value=1, value=st.session_state.start_ep, step=1)
        st.session_state.end_ep = c2.number_input("Sampai Episode", min_value=st.session_state.start_ep, value=st.session_state.end_ep, step=1)
        stream_links_text = st.text_area("Link Streaming (1 per baris, opsional)", key="stream_links_text", height=100)

    default_resolutions = ["360p", "480p", "540p", "720p", "1080p"]
    st.session_state.resolutions = st.multiselect("Pilih Resolusi Download", options=default_resolutions, default=st.session_state.resolutions)
    
    server_choice = st.selectbox("Pilih Nama Server Download", options=SERVER_OPTIONS, key="sb_server")
    server_name = st.text_input("Nama Server Manual", key="txt_server").strip() if server_choice == SERVER_OPTIONS[0] else server_choice
    
    links_text = st.text_area("Tempel Link Download (1 per baris)", key="links_text", height=150)

    if st.button("+ Tambah Data", type="primary"):
        download_links = [link.strip() for link in links_text.splitlines() if link.strip()]
        stream_links = [link.strip() for link in stream_links_text.splitlines() if link.strip()]
        num_eps = (st.session_state.end_ep - st.session_state.start_ep) + 1 if input_mode == "Batch Episode" else 1
        
        if not server_name and download_links:
            st.warning("Nama Server Download tidak boleh kosong.")
        elif download_links and not st.session_state.resolutions:
             st.warning("Pilih minimal satu resolusi download.")
        elif input_mode == "Batch Episode" and stream_links and len(stream_links) != num_eps:
            st.error(f"Jumlah link streaming ({len(stream_links)}) tidak cocok dengan jumlah episode ({num_eps}).")
        else:
            expected_links = num_eps * len(st.session_state.resolutions)
            if download_links and len(download_links) != expected_links:
                st.error(f"Jumlah link download tidak sesuai. Diperlukan: {expected_links}, Disediakan: {len(download_links)}.")
            else:
                link_idx, stream_idx = 0, 0
                episode_range = range(st.session_state.start_ep, st.session_state.end_ep + 1) if input_mode == "Batch Episode" else [1]
                for ep in episode_range:
                    if ep not in st.session_state.main_data: st.session_state.main_data[ep] = {}
                    if 'download_links' not in st.session_state.main_data[ep]: st.session_state.main_data[ep]['download_links'] = {}
                    
                    if stream_links and stream_idx < len(stream_links):
                        st.session_state.main_data[ep]['stream_link'] = stream_links[stream_idx]
                        stream_idx += 1
                    
                    if download_links:
                        for res in st.session_state.resolutions:
                            if res not in st.session_state.main_data[ep]['download_links']: st.session_state.main_data[ep]['download_links'][res] = {}
                            st.session_state.main_data[ep]['download_links'][res][server_name] = download_links[link_idx]
                            link_idx += 1
                
                        if server_name not in st.session_state.server_order: st.session_state.server_order.append(server_name)
                
                st.success(f"Data berhasil ditambahkan!"); st.session_state.reset_form = True; st.rerun()

    if st.button("🔄 Reset Semua Data"):
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
        server_list_with_stream = ["Streaming"] + st.session_state.server_order
        for s_name in server_list_with_stream:
            is_stream = s_name == "Streaming"
            
            # Jangan tampilkan 'Streaming' jika tidak ada link streaming sama sekali
            if is_stream and not any(d.get('stream_link') for d in st.session_state.main_data.values()):
                continue

            control_cols = st.columns([0.2, 0.5, 0.1, 0.1, 0.1]) if not is_stream else st.columns([0.2, 0.8])
            with control_cols[0]:
                if st.checkbox("ouo.io", key=f"shorten_{s_name}", help=f"Perpendek link untuk {s_name}"):
                    servers_to_shorten.append(s_name)
            with control_cols[1]:
                st.text_input("Server", value=s_name, key=f"display_name_{s_name}", disabled=True, label_visibility="collapsed")
            
            if not is_stream:
                idx = st.session_state.server_order.index(s_name)
                with control_cols[2]:
                    if st.button("↑", key=f"up_{s_name}", use_container_width=True, help="Naikkan urutan", disabled=(idx == 0)):
                        st.session_state.server_order.insert(idx - 1, st.session_state.server_order.pop(idx)); st.rerun()
                with control_cols[3]:
                    if st.button("↓", key=f"down_{s_name}", use_container_width=True, help="Turunkan urutan", disabled=(idx == len(st.session_state.server_order) - 1)):
                        st.session_state.server_order.insert(idx + 1, st.session_state.server_order.pop(idx)); st.rerun()
                with control_cols[4]:
                    if st.button("⌦", key=f"del_{s_name}", use_container_width=True, help=f"Hapus server {s_name}"):
                        server_to_delete = st.session_state.server_order.pop(idx)
                        for ep_data in st.session_state.main_data.values():
                            if 'download_links' in ep_data:
                                for res_data in ep_data['download_links'].values():
                                    if server_to_delete in res_data: del res_data[server_to_delete]
                        st.rerun()
            
            with st.expander(f"Edit detail untuk {s_name}"):
                if is_stream:
                    st.write("**Edit Link Streaming:**")
                    for ep_num, ep_data in st.session_state.main_data.items():
                        if 'stream_link' in ep_data:
                            st.text_input(label=f"Ep {ep_num} - Streaming", value=ep_data['stream_link'], key=f"edit_stream_link_{ep_num}")
                else:
                    new_server_name = st.text_input("Edit Nama Server", value=s_name, key=f"edit_name_{s_name}")
                    st.write("**Edit Link Download:**")
                    for ep_num, ep_data in st.session_state.main_data.items():
                        if s_name in ep_data.get('download_links', {}).get(st.session_state.resolutions[0], {}):
                             for res in st.session_state.resolutions:
                                if res in ep_data.get('download_links', {}) and s_name in ep_data['download_links'][res]:
                                    st.text_input(label=f"Ep {ep_num} - {res}", value=ep_data['download_links'][res][s_name], key=f"link_edit_{s_name}_{ep_num}_{res}")

                if st.button("Simpan Perubahan", key=f"save_changes_{s_name}", use_container_width=True):
                    if is_stream:
                        for ep_num in st.session_state.main_data:
                            st.session_state.main_data[ep_num]['stream_link'] = st.session_state[f"edit_stream_link_{ep_num}"]
                    else:
                        idx = st.session_state.server_order.index(s_name)
                        for ep_num, ep_data in st.session_state.main_data.items():
                            if s_name in ep_data.get('download_links', {}).get(st.session_state.resolutions[0], {}):
                                for res in st.session_state.resolutions:
                                    link_key = f"link_edit_{s_name}_{ep_num}_{res}"
                                    if link_key in st.session_state: st.session_state.main_data[ep_num]['download_links'][res][s_name] = st.session_state[link_key]
                        if new_server_name != s_name and new_server_name:
                            st.session_state.server_order[idx] = new_server_name
                            for ep_data in st.session_state.main_data.values():
                                for res_data in ep_data.get('download_links', {}).values():
                                    if s_name in res_data: res_data[new_server_name] = res_data.pop(s_name)
                    st.success(f"Perubahan untuk '{s_name}' telah disimpan!"); st.rerun()

        st.divider()
        st.subheader("Pilih Format Output")
        output_format = st.radio("Pilih format HTML:", ["Format Streaming", "Format Drakor", "Format Ringkas"], key="output_format")
        
        if output_format == "Format Drakor":
            c1, c2 = st.columns(2); use_uppercase_drakor = c1.toggle("Server Uppercase", value=True, key="uppercase_drakor_toggle"); is_centered = c2.toggle("Rata Tengah", value=False, key="center_align_toggle")
        elif output_format == "Format Ringkas":
            c1, c2 = st.columns(2); grouping_style = c1.radio("Urutkan berdasarkan:", ["Server", "Resolusi"], key="grouping_style", horizontal=True); use_uppercase_ringkas = c2.toggle("Server Uppercase", value=True, key="uppercase_ringkas_toggle")
        else: # Format Streaming
            use_uppercase_stream = st.toggle("Server Uppercase", value=True, key="uppercase_stream_toggle")

        if st.button("🚀 Generate HTML", type="primary"):
            active_resolutions = st.session_state.get('resolutions', [])
            input_mode = st.session_state.get('input_mode')
            episode_range = [1] if input_mode == "Single Link" else range(st.session_state.start_ep, st.session_state.end_ep + 1)
            
            if output_format == "Format Ringkas":
                st.session_state.final_html = generate_output_ringkas(st.session_state.main_data, episode_range, active_resolutions, st.session_state.server_order, grouping_style, use_uppercase_ringkas, servers_to_shorten, ouo_api_key)
            elif output_format == "Format Drakor":
                st.session_state.final_html = generate_output_drakor(st.session_state.main_data, episode_range, active_resolutions, st.session_state.server_order, use_uppercase_drakor, is_centered, servers_to_shorten, ouo_api_key)
            else: # Format Streaming
                st.session_state.final_html = generate_output_streaming(st.session_state.main_data, episode_range, active_resolutions, st.session_state.server_order, use_uppercase_stream, servers_to_shorten, ouo_api_key)

        if st.session_state.final_html:
            st.code(st.session_state.final_html, language="html")
            st.components.v1.html(st.session_state.final_html, height=300, scrolling=True)
