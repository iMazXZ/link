import streamlit as st
import requests
import time
import json
import base64
from datetime import datetime

# =============================================================================
# CUSTOM CSS STYLING
# =============================================================================

def load_custom_css():
    st.markdown("""
    <style>
    /* Import Google Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    /* Global Styles */
    .stApp {
        font-family: 'Inter', sans-serif;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        min-height: 100vh;
    }
    
    /* Main Container */
    .main-container {
        background: rgba(255, 255, 255, 0.95);
        border-radius: 20px;
        padding: 2rem;
        margin: 1rem 0;
        box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.2);
    }
    
    /* Header Styles */
    .header-title {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        font-size: 2.5rem;
        font-weight: 700;
        text-align: center;
        margin-bottom: 0.5rem;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.1);
    }
    
    .header-subtitle {
        text-align: center;
        color: #666;
        font-size: 1.1rem;
        margin-bottom: 2rem;
        font-weight: 400;
    }
    
    /* Section Headers */
    .section-header {
        background: linear-gradient(90deg, #667eea, #764ba2);
        color: white;
        padding: 1rem 1.5rem;
        border-radius: 15px;
        margin: 1rem 0;
        font-weight: 600;
        font-size: 1.2rem;
        display: flex;
        align-items: center;
        gap: 0.5rem;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
    }
    
    /* Card Styles */
    .info-card {
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
        border-radius: 15px;
        padding: 1.5rem;
        margin: 1rem 0;
        border: 1px solid rgba(255, 255, 255, 0.3);
        box-shadow: 0 8px 25px rgba(0, 0, 0, 0.1);
    }
    
    .success-card {
        background: linear-gradient(135deg, #a8edea 0%, #fed6e3 100%);
        border-radius: 15px;
        padding: 1rem;
        margin: 1rem 0;
        border-left: 4px solid #10b981;
    }
    
    .warning-card {
        background: linear-gradient(135deg, #ffeaa7 0%, #fab1a0 100%);
        border-radius: 15px;
        padding: 1rem;
        margin: 1rem 0;
        border-left: 4px solid #f59e0b;
    }
    
    /* Button Styles */
    .stButton > button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 25px;
        padding: 0.75rem 2rem;
        font-weight: 600;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(102, 126, 234, 0.4);
    }
    
    /* Input Styles */
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea,
    .stSelectbox > div > div > select {
        border-radius: 10px;
        border: 2px solid #e2e8f0;
        transition: all 0.3s ease;
        font-family: 'Inter', sans-serif;
    }
    
    .stTextInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus,
    .stSelectbox > div > div > select:focus {
        border-color: #667eea;
        box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
    }
    
    /* Sidebar Styles */
    .css-1d391kg {
        background: linear-gradient(180deg, #667eea 0%, #764ba2 100%);
    }
    
    .css-1d391kg .stMarkdown {
        color: white;
    }
    
    /* Server Control Cards */
    .server-control-card {
        background: white;
        border-radius: 12px;
        padding: 1rem;
        margin: 0.5rem 0;
        border: 1px solid #e2e8f0;
        box-shadow: 0 2px 10px rgba(0, 0, 0, 0.05);
        transition: all 0.3s ease;
    }
    
    .server-control-card:hover {
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
        transform: translateY(-2px);
    }
    
    /* Code Block Styles */
    .stCode {
        border-radius: 15px;
        background: linear-gradient(135deg, #2d3748 0%, #4a5568 100%);
        border: 1px solid #4a5568;
    }
    
    /* Progress and Status */
    .status-badge {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        border-radius: 20px;
        font-size: 0.875rem;
        font-weight: 500;
        margin: 0.25rem;
    }
    
    .status-success {
        background: #d1fae5;
        color: #065f46;
    }
    
    .status-warning {
        background: #fef3c7;
        color: #92400e;
    }
    
    .status-info {
        background: #dbeafe;
        color: #1e40af;
    }
    
    /* Animation Classes */
    .fade-in {
        animation: fadeIn 0.5s ease-in;
    }
    
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(20px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    .pulse {
        animation: pulse 2s infinite;
    }
    
    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.7; }
    }
    
    /* Responsive Design */
    @media (max-width: 768px) {
        .main-container {
            padding: 1rem;
            margin: 0.5rem;
        }
        
        .header-title {
            font-size: 2rem;
        }
        
        .section-header {
            font-size: 1rem;
            padding: 0.75rem 1rem;
        }
    }
    
    /* Custom Scrollbar */
    ::-webkit-scrollbar {
        width: 8px;
    }
    
    ::-webkit-scrollbar-track {
        background: #f1f1f1;
        border-radius: 10px;
    }
    
    ::-webkit-scrollbar-thumb {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 10px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: linear-gradient(135deg, #5a67d8 0%, #6b46c1 100%);
    }
    </style>
    """, unsafe_allow_html=True)

# =============================================================================
# FUNGSI-FUNGSI HELPER (TIDAK DIUBAH)
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
    """Menghasilkan output HTML format ringkas."""
    txt_lines = []
    with st.spinner('Memproses link...'):
        for ep_num in episode_range:
            if ep_num not in data: continue
            
            link_parts = []
            display_server = ""
            if "Server" in grouping_style:
                for server in servers:
                    for res in resolutions:
                        if res in data.get(ep_num, {}) and server in data.get(ep_num, {}).get(res, {}):
                            url = data[ep_num][res][server]
                            if server in shorten_servers: url = shorten_with_ouo(url, api_key)
                            display_server = server.upper() if use_uppercase else server
                            link_parts.append(f'<a href="{url}" rel="nofollow" data-wpel-link="external">{display_server} {res}</a>')
            else: # "Resolusi"
                for res in resolutions:
                    for server in servers:
                        if res in data.get(ep_num, {}) and server in data.get(ep_num, {}).get(res, {}):
                            url = data[ep_num][res][server]
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

            for res in resolutions:
                if res not in data.get(ep_num, {}): continue
                link_parts = []
                for server in servers:
                    if server in data.get(ep_num, {}).get(res, {}):
                        url = data[ep_num][res][server]
                        if server in shorten_servers: url = shorten_with_ouo(url, api_key)
                        display_server = server.upper() if use_uppercase else server
                        link_parts.append(f'<a href="{url}">{display_server}</a>')
                if link_parts:
                    links_string = " | ".join(link_parts)
                    line = f'<p{style_attr}><strong>{res} (Hardsub Indo):</strong> {links_string}</p>'
                    html_lines.append(line)
    return "\n".join(html_lines)

# =============================================================================
# STATE INISIALISASI (TIDAK DIUBAH)
# =============================================================================
if 'main_data' not in st.session_state:
    st.session_state.main_data = {}
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
# UI UTAMA - REDESIGNED
# =============================================================================

st.set_page_config(
    layout="wide", 
    page_title="Universal Link Generator",
    page_icon="🚀",
    initial_sidebar_state="expanded"
)

# Load Custom CSS
load_custom_css()

# Header dengan styling modern
st.markdown("""
<div class="main-container fade-in">
    <h1 class="header-title">🚀 Universal Link Generator</h1>
    <p class="header-subtitle">Generate HTML links with style and efficiency</p>
</div>
""", unsafe_allow_html=True)

# --- Sidebar Modern ---
with st.sidebar:
    st.markdown("""
    <div class="section-header">
        ⚙️ Pengaturan Global
    </div>
    """, unsafe_allow_html=True)
    
    ouo_api_key = st.text_input(
        "🔑 API Key ouo.io", 
        value="8pHuHRq5", 
        type="password", 
        help="Masukkan API Key Anda dari ouo.io untuk memperpendek link"
    )
    
    if ouo_api_key:
        st.markdown('<div class="status-badge status-success">✅ API Key Ready</div>', unsafe_allow_html=True)
    
    st.markdown("---")
    
    # --- Fitur Simpan & Muat Sesi ---
    st.markdown("""
    <div class="section-header">
        💾 Simpan & Muat Sesi
    </div>
    """, unsafe_allow_html=True)
    
    # Tombol Simpan dengan styling
    if st.button("💾 Simpan Sesi Saat Ini", use_container_width=True):
        session_data = {
            'main_data': st.session_state.main_data,
            'server_order': st.session_state.server_order,
            'resolutions': st.session_state.resolutions,
            'start_ep': st.session_state.start_ep,
            'end_ep': st.session_state.end_ep,
        }
        session_json = json.dumps(session_data, indent=4)
        b64 = base64.b64encode(session_json.encode()).decode()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        href = f'<a href="data:file/json;base64,{b64}" download="link_generator_session_{timestamp}.json">📥 Unduh File Sesi</a>'
        st.markdown(f'<div class="success-card">{href}</div>', unsafe_allow_html=True)
        st.success("✅ File sesi siap diunduh!")
    
    # Fitur Muat dari Teks
    st.markdown("**📋 Muat dari File JSON**")
    json_text_to_load = st.text_area(
        "Tempel konten file .json di sini", 
        height=120,
        placeholder="Paste JSON content here..."
    )
    
    if st.button("📤 Muat dari Teks", use_container_width=True):
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
                    st.session_state.final_html = ""
                    st.success("🎉 Sesi berhasil dimuat!")
                    st.rerun()
                else:
                    st.error("❌ Format JSON tidak valid!")
            except json.JSONDecodeError:
                st.error("❌ Format teks bukan JSON yang valid!")
            except Exception as e:
                st.error(f"❌ Gagal memuat data: {e}")
        else:
            st.warning("⚠️ Area teks kosong!")

SERVER_OPTIONS = ["(Ketik Manual)", "Mirrored", "TeraBox", "UpFiles", "BuzzHeav", "AkiraBox", "SendNow", "KrakrnFl", "Vidguard", "StreamHG"]

# Layout utama dengan kolom
col1, col2 = st.columns([1, 1], gap="large")

# =============================================================================
# KOLOM KIRI: INPUT DATA - REDESIGNED
# =============================================================================
with col1:
    st.markdown("""
    <div class="section-header">
        📝 Input Data
    </div>
    """, unsafe_allow_html=True)
    
    if st.session_state.get('reset_form', False):
        st.session_state.update({"sb_server": SERVER_OPTIONS[0], "txt_server": "", "links_text": "", "reset_form": False})
    
    # Mode Input dengan styling
    st.markdown("**📊 Mode Input**")
    input_mode = st.radio(
        "Pilih mode input data", 
        ["Batch Episode", "Single Link"], 
        horizontal=True, 
        key="input_mode"
    )
    
    # Episode Range Input
    if input_mode == "Batch Episode":
        st.markdown("**📺 Range Episode**")
        c1, c2 = st.columns(2)
        with c1:
            st.session_state.start_ep = st.number_input(
                "Mulai dari Episode", 
                min_value=1, 
                value=st.session_state.start_ep, 
                step=1
            )
        with c2:
            st.session_state.end_ep = st.number_input(
                "Sampai Episode", 
                min_value=st.session_state.start_ep, 
                value=st.session_state.end_ep, 
                step=1
            )
        
        episode_count = st.session_state.end_ep - st.session_state.start_ep + 1
        st.markdown(f'<div class="status-badge status-info">📊 Total: {episode_count} episode</div>', unsafe_allow_html=True)
    
    # Resolution Selection
    st.markdown("**🎬 Resolusi Video**")
    default_resolutions = ["360p", "480p", "540p", "720p", "1080p"]
    st.session_state.resolutions = st.multiselect(
        "Pilih resolusi (sesuai urutan link)", 
        options=default_resolutions, 
        default=st.session_state.resolutions,
        help="Pilih resolusi sesuai urutan link yang akan diinput"
    )
    
    if st.session_state.resolutions:
        res_badges = " ".join([f'<span class="status-badge status-success">{res}</span>' for res in st.session_state.resolutions])
        st.markdown(f'<div>Selected: {res_badges}</div>', unsafe_allow_html=True)
    
    # Server Selection
    st.markdown("**🖥️ Server Configuration**")
    server_choice = st.selectbox(
        "Pilih nama server", 
        options=SERVER_OPTIONS, 
        key="sb_server"
    )
    
    server_name = st.text_input(
        "Nama Server Manual", 
        key="txt_server",
        placeholder="Masukkan nama server custom..."
    ).strip() if server_choice == SERVER_OPTIONS[0] else server_choice
    
    # Links Input
    st.markdown("**🔗 Input Links**")
    links_text = st.text_area(
        "Tempel link untuk server ini", 
        key="links_text", 
        height=150,
        placeholder="Paste links here (one per line)...",
        help="Masukkan satu link per baris sesuai urutan episode dan resolusi"
    )
    
    # Calculate expected links
    if st.session_state.resolutions:
        if input_mode == "Batch Episode":
            expected_links = (st.session_state.end_ep - st.session_state.start_ep + 1) * len(st.session_state.resolutions)
        else:
            expected_links = len(st.session_state.resolutions)
        
        current_links = len([link for link in links_text.splitlines() if link.strip()])
        
        if current_links > 0:
            if current_links == expected_links:
                st.markdown(f'<div class="status-badge status-success">✅ {current_links}/{expected_links} links ready</div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="status-badge status-warning">⚠️ {current_links}/{expected_links} links</div>', unsafe_allow_html=True)
    
    # Action Buttons
    st.markdown("**⚡ Actions**")
    button_col1, button_col2 = st.columns(2)
    
    with button_col1:
        if st.button("➕ Tambah Data", type="primary", use_container_width=True):
            links = [link.strip() for link in links_text.splitlines() if link.strip()]
            num_eps = (st.session_state.end_ep - st.session_state.start_ep) + 1 if input_mode == "Batch Episode" else 1
            
            if not all([server_name, links, st.session_state.resolutions]):
                st.markdown('<div class="warning-card">⚠️ Pastikan Nama Server, Resolusi, dan Link terisi.</div>', unsafe_allow_html=True)
            else:
                expected_links = num_eps * len(st.session_state.resolutions)
                if len(links) != expected_links:
                    st.markdown(f'<div class="warning-card">❌ Jumlah link tidak sesuai. Diperlukan: {expected_links}, Disediakan: {len(links)}.</div>', unsafe_allow_html=True)
                else:
                    link_idx = 0
                    episode_range = range(st.session_state.start_ep, st.session_state.end_ep + 1) if input_mode == "Batch Episode" else [1]
                    for ep in episode_range:
                        if ep not in st.session_state.main_data: st.session_state.main_data[ep] = {}
                        for res in st.session_state.resolutions:
                            if res not in st.session_state.main_data[ep]: st.session_state.main_data[ep][res] = {}
                            st.session_state.main_data[ep][res][server_name] = links[link_idx]
                            link_idx += 1
                    
                    if server_name not in st.session_state.server_order:
                        st.session_state.server_order.append(server_name)
                    
                    st.markdown(f'<div class="success-card">🎉 Server "{server_name}" berhasil ditambahkan!</div>', unsafe_allow_html=True)
                    st.session_state.reset_form = True
                    st.rerun()
    
    with button_col2:
        if st.button("🔄 Reset Semua", use_container_width=True):
            st.session_state.main_data = {}
            st.session_state.server_order = []
            st.session_state.final_html = ""
            st.rerun()

# =============================================================================
# KOLOM KANAN: PENGATURAN & HASIL - REDESIGNED
# =============================================================================
with col2:
    st.markdown("""
    <div class="section-header">
        🎛️ Pengaturan & Hasil
    </div>
    """, unsafe_allow_html=True)
    
    if not st.session_state.main_data:
        st.markdown("""
        <div class="info-card">
            <h3>📋 Belum ada data</h3>
            <p>Silakan tambahkan data server dan link terlebih dahulu menggunakan form di sebelah kiri.</p>
        </div>
        """, unsafe_allow_html=True)
    else:
        # Server Management Section
        st.markdown("**🖥️ Manajemen Server**")
        servers_to_shorten = []
        server_list = list(st.session_state.server_order)
        
        for i, s_name in enumerate(server_list):
            with st.container():
                st.markdown(f'<div class="server-control-card">', unsafe_allow_html=True)
                
                # Server control row
                control_cols = st.columns([0.15, 0.45, 0.1, 0.1, 0.1, 0.1])
                
                with control_cols[0]:
                    if st.checkbox("🔗", key=f"shorten_{i}", help=f"Perpendek link untuk {s_name}"):
                        servers_to_shorten.append(s_name)
                
                with control_cols[1]:
                    st.markdown(f"**{s_name}**")
                
                with control_cols[2]:
                    if st.button("⬆️", key=f"up_{i}", help="Naikkan urutan", disabled=(i == 0)):
                        st.session_state.server_order.insert(i - 1, st.session_state.server_order.pop(i))
                        st.rerun()
                
                with control_cols[3]:
                    if st.button("⬇️", key=f"down_{i}", help="Turunkan urutan", disabled=(i == len(server_list) - 1)):
                        st.session_state.server_order.insert(i + 1, st.session_state.server_order.pop(i))
                        st.rerun()
                
                with control_cols[4]:
                    if st.button("✏️", key=f"edit_{i}", help="Edit server"):
                        st.session_state[f"edit_mode_{i}"] = True
                
                with control_cols[5]:
                    if st.button("🗑️", key=f"del_{i}", help=f"Hapus server {s_name}"):
                        server_to_delete = st.session_state.server_order.pop(i)
                        for ep_data in st.session_state.main_data.values():
                            for res_data in ep_data.values():
                                if server_to_delete in res_data: del res_data[server_to_delete]
                        st.rerun()
                
                # Edit mode
                if st.session_state.get(f"edit_mode_{i}", False):
                    st.markdown("**✏️ Edit Server**")
                    new_server_name = st.text_input("Nama Server", value=s_name, key=f"edit_name_{i}")
                    
                    st.markdown("**Edit Links:**")
                    for ep_num, res_data in st.session_state.main_data.items():
                        for res, server_links in res_data.items():
                            if s_name in server_links:
                                st.text_input(
                                    f"Episode {ep_num} - {res}", 
                                    value=server_links[s_name], 
                                    key=f"link_edit_{i}_{ep_num}_{res}"
                                )
                    
                    edit_col1, edit_col2 = st.columns(2)
                    with edit_col1:
                        if st.button("💾 Simpan", key=f"save_changes_{i}"):
                            # Save changes logic (sama seperti original)
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
                            st.session_state[f"edit_mode_{i}"] = False
                            st.success(f"✅ Perubahan untuk server '{s_name}' telah disimpan!")
                            st.rerun()
                    
                    with edit_col2:
                        if st.button("❌ Batal", key=f"cancel_edit_{i}"):
                            st.session_state[f"edit_mode_{i}"] = False
                            st.rerun()
                
                st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Output Format Selection
        st.markdown("**🎨 Format Output**")
        output_format = st.radio(
            "Pilih format HTML:", 
            ["Format Drakor", "Format Ringkas"], 
            key="output_format",
            horizontal=True
        )
        
        # Format-specific settings
        if output_format == "Format Drakor":
            st.markdown("**⚙️ Pengaturan Drakor**")
            c1, c2 = st.columns(2)
            with c1:
                use_uppercase_drakor = st.toggle("📝 Server Uppercase", value=True, key="uppercase_drakor_toggle")
            with c2:
                is_centered = st.toggle("🎯 Rata Tengah", value=False, key="center_align_toggle")
            
            # Preview badges
            preview_badges = []
            if use_uppercase_drakor:
                preview_badges.append('<span class="status-badge status-info">UPPERCASE</span>')
            if is_centered:
                preview_badges.append('<span class="status-badge status-info">CENTERED</span>')
            
            if preview_badges:
                st.markdown(f'<div>Preview: {" ".join(preview_badges)}</div>', unsafe_allow_html=True)
        
        else:  # Format Ringkas
            st.markdown("**⚙️ Pengaturan Ringkas**")
            c1, c2 = st.columns(2)
            with c1:
                grouping_style = st.radio("📋 Urutkan berdasarkan:", ["Server", "Resolusi"], key="grouping_style")
            with c2:
                use_uppercase_ringkas = st.toggle("📝 Server Uppercase", value=True, key="uppercase_ringkas_toggle")
            
            # Preview badges
            preview_badges = [f'<span class="status-badge status-info">BY {grouping_style.upper()}</span>']
            if use_uppercase_ringkas:
                preview_badges.append('<span class="status-badge status-info">UPPERCASE</span>')
            
            st.markdown(f'<div>Preview: {" ".join(preview_badges)}</div>', unsafe_allow_html=True)
        
        # Generate Button
        st.markdown("**🚀 Generate**")
        if st.button("🎯 Generate HTML", type="primary", use_container_width=True):
            with st.spinner("🔄 Generating HTML..."):
                final_html = ""
                active_resolutions = st.session_state.get('resolutions', [])
                input_mode = st.session_state.get('input_mode')
                episode_range = [1] if input_mode == "Single Link" else range(st.session_state.start_ep, st.session_state.end_ep + 1)
                
                if output_format == "Format Ringkas":
                    final_html = generate_output_ringkas(
                        st.session_state.main_data, 
                        episode_range, 
                        active_resolutions, 
                        st.session_state.server_order, 
                        grouping_style, 
                        use_uppercase_ringkas, 
                        servers_to_shorten, 
                        ouo_api_key
                    )
                else:  # Format Drakor
                    final_html = generate_output_drakor(
                        st.session_state.main_data, 
                        episode_range, 
                        active_resolutions, 
                        st.session_state.server_order, 
                        use_uppercase_drakor, 
                        is_centered, 
                        servers_to_shorten, 
                        ouo_api_key
                    )
                
                st.session_state.final_html = final_html
                st.success("🎉 HTML berhasil di-generate!")
        
        # Output Results
        if st.session_state.final_html:
            st.markdown("**📋 Hasil HTML**")
            
            # Stats
            line_count = len(st.session_state.final_html.splitlines())
            char_count = len(st.session_state.final_html)
            
            stats_col1, stats_col2, stats_col3 = st.columns(3)
            with stats_col1:
                st.markdown(f'<div class="status-badge status-info">📊 {line_count} lines</div>', unsafe_allow_html=True)
            with stats_col2:
                st.markdown(f'<div class="status-badge status-info">🔤 {char_count} chars</div>', unsafe_allow_html=True)
            with stats_col3:
                st.markdown(f'<div class="status-badge status-success">✅ Ready</div>', unsafe_allow_html=True)
            
            # Code output
            st.code(st.session_state.final_html, language="html")
            
            # Preview
            st.markdown("**👀 Preview**")
            with st.expander("Lihat Preview HTML", expanded=False):
                st.components.v1.html(st.session_state.final_html, height=300, scrolling=True)
            
            # Copy button simulation
            st.markdown("""
            <div class="success-card">
                <h4>📋 Siap untuk dicopy!</h4>
                <p>Klik pada code block di atas, lalu gunakan Ctrl+A untuk select all dan Ctrl+C untuk copy.</p>
            </div>
            """, unsafe_allow_html=True)

# =============================================================================
# FOOTER
# =============================================================================
st.markdown("---")
st.markdown("""
<div style="text-align: center; padding: 2rem; color: #666;">
    <p>🚀 <strong>Universal Link Generator</strong> - Built with ❤️ using Streamlit</p>
    <p>Modern UI • Fast Processing • Multiple Formats</p>
</div>
""", unsafe_allow_html=True)
