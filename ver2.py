import streamlit as st

# Custom CSS for light theme redesign with layout fixes
st.markdown("""
    <style>
    /* General body styling */
    body {
        background-color: #f5f7fa;
        color: #2d3748;
        font-family: 'Inter', sans-serif;
    }
    
    /* Main container */
    .stApp {
        background-color: #ffffff;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        padding: 2rem;
        max-width: 1200px;
        margin: 0 auto;
    }
    
    /* Title styling */
    h1 {
        color: #1a73e8;
        font-weight: 700;
        text-align: center;
        margin-bottom: 1.5rem;
    }
    
    /* Header styling */
    h2 {
        color: #2d3748;
        font-weight: 600;
        border-bottom: 2px solid #e2e8f0;
        padding-bottom: 0.5rem;
    }
    
    /* Subheader styling */
    h3 {
        color: #4a5568;
        font-weight: 500;
    }
    
    /* Tabs styling */
    .stTabs [data-baseweb="tab-list"] {
        background-color: #e2e8f0;
        border-radius: 8px;
        padding: 0.5rem;
        justify-content: center;
    }
    .stTabs [data-baseweb="tab"] {
        background-color: #ffffff;
        color: #4a5568;
        border-radius: 6px;
        margin: 0.2rem;
        padding: 0.5rem 1rem;
        font-weight: 500;
        min-width: 150px;
        text-align: center;
    }
    .stTabs [data-baseweb="tab"][aria-selected="true"] {
        background-color: #1a73e8;
        color: #ffffff;
        font-weight: 600;
    }
    
    /* Buttons */
    .stButton>button {
        background-color: #1a73e8;
        color: white;
        border-radius: 6px;
        padding: 0.5rem 1rem;
        border: none;
        font-weight: 500;
        transition: background-color 0.2s;
    }
    .stButton>button:hover {
        background-color: #1557b0;
        color: white;
    }
    
    /* Reset button specific styling */
    .stButton>button[kind="secondary"] {
        background-color: #e53e3e;
        color: white;
    }
    .stButton>button[kind="secondary"]:hover {
        background-color: #c53030;
    }
    
    /* Text inputs and text areas */
    .stTextInput input, .stTextArea textarea {
        background-color: #f7fafc;
        border: 1px solid #e2e8f0;
        border-radius: 6px;
        color: #2d3748;
        padding: 0.5rem;
    }
    
    /* Multiselect */
    .stMultiSelect [data-baseweb="select"] {
        background-color: #f7fafc;
        border-radius: 6px;
        border: 1px solid #e2e8f0;
        padding: 0.25rem;
    }
    .stMultiSelect [data-baseweb="tag"] {
        background-color: #e2e8f0;
        color: #2d3748;
        border-radius: 4px;
        padding: 0.1rem 0.5rem;
        margin: 0.1rem;
    }
    
    /* Info and warning boxes */
    .stAlert {
        border-radius: 6px;
        background-color: #e6f3ff;
        color: #2d3748;
        border: 1px solid #bfdbfe;
        padding: 0.75rem;
    }
    .stAlert[kind="warning"] {
        background-color: #fefcbf;
        border: 1px solid #f6e05e;
    }
    .stAlert[kind="success"] {
        background-color: #c6f6d5;
        border: 1px solid #68d391;
    }
    .stAlert[kind="error"] {
        background-color: #fed7d7;
        border: 1px solid #f56565;
    }
    
    /* Divider */
    .stDivider {
        background-color: #e2e8f0;
        margin: 1rem 0;
    }
    
    /* Code block */
    .stCodeBlock {
        background-color: #f7fafc;
        border: 1px solid #e2e8f0;
        border-radius: 6px;
        padding: 1rem;
    }
    
    /* JSON viewer */
    .stJson {
        background-color: #f7fafc;
        border: 1px solid #e2e8f0;
        border-radius: 6px;
        padding: 1rem;
    }
    
    /* Live preview section */
    .stMarkdown h3 {
        color: #1a73e8;
        font-weight: 600;
    }
    
    /* Columns */
    .stColumn {
        padding: 1rem;
        display: flex;
        flex-direction: column;
        gap: 1rem;
    }
    
    /* Ensure consistent spacing and alignment */
    .stApp > div {
        margin: 0 auto;
        width: 100%;
    }
    .element-container {
        margin-bottom: 1rem;
    }
    </style>
""", unsafe_allow_html=True)

# =============================================================================
# FUNGSI-FUNGSI HELPER
# =============================================================================

def generate_serial_output(episodes_data, grouping_style, resolutions):
    txt_lines = []
    for ep_num in sorted(episodes_data.keys()):
        links = []
        if "Server" in grouping_style:
            for server in sorted(episodes_data[ep_num].keys()):
                for res in resolutions:
                    if res in episodes_data[ep_num][server]:
                        link = episodes_data[ep_num][server][res]
                        links.append(f'<a href="{link["url"]}" rel="nofollow" data-wpel-link="external">{link["label"]}</a>')
        elif "Resolusi" in grouping_style:
            for res in resolutions:
                for server in sorted(episodes_data[ep_num].keys()):
                    if res in episodes_data[ep_num][server]:
                        link = episodes_data[ep_num][server][res]
                        links.append(f'<a href="{link["url"]}" rel="nofollow" data-wpel-link="external">{link["label"]}</a>')
        txt_lines.append(f'<li><strong>EPISODE {ep_num}</strong> {" ".join(links)}</li>')
    return "\n".join(txt_lines)

def generate_single_output(data, resolutions, servers):
    html_lines = []
    for res in resolutions:
        if res not in data:
            continue
        link_parts = []
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

    # ✅ Reset form input jika diperlukan
    if st.session_state.reset_single:
        st.session_state.update({
            "server_single": "",
            "link_single": "",
            "res_single": st.session_state.get("res_single", ["360p", "540p", "720p"]),
            "reset_single": False
        })
        st.rerun()

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Masukkan Data Link")
        default_resolutions = ["360p", "480p", "540p", "720p", "1080p"]

        selected_resolutions = st.multiselect(
            "Pilih Resolusi",
            options=default_resolutions,
            default=["360p", "480p", "540p", "720p"],
            key="res_single"
        )

        server_name_single = st.text_input(
            "Nama Server",
            placeholder="contoh: TeraBox",
            key="server_single"
        )

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
                for res in selected_resolutions:
                    if res not in st.session_state.single_data:
                        st.session_state.single_data[res] = {}
                    st.session_state.single_data[res][server_name_single] = links[selected_resolutions.index(res)]

                if server_name_single not in st.session_state.single_server_order:
                    st.session_state.single_server_order.append(server_name_single)

                st.success(f"Server '{server_name_single}' berhasil ditambahkan.")

                st.session_state.reset_single = True
                st.rerun()

        if st.button("🔄 Reset Data Konten Tunggal"):
            st.session_state.single_data = {}
            st.session_state.single_server_order = []
            st.session_state.single_final_html = ""
            st.rerun()

    with col2:
        st.subheader("Hasil HTML")
        if not st.session_state.single_data:
            st.write("Belum ada data yang dimasukkan.")
        else:
            st.write("**Urutan Server Ditambahkan:**")
            st.write(" → ".join(f"`{s}`" for s in st.session_state.single_server_order))
            st.divider()

            if st.button("🚀 Generate HTML"):
                st.session_state.single_final_html = generate_single_output(
                    st.session_state.single_data,
                    list(st.session_state.single_data.keys()),
                    st.session_state.single_server_order
                )

            if st.session_state.single_final_html:
                st.code(st.session_state.single_final_html, language="html")
                st.markdown("---")
                st.markdown("### 👀 Live Preview")
                st.components.v1.html(st.session_state.single_final_html, height=300, scrolling=True)
            else:
                st.write("Klik tombol 'Generate HTML' untuk melihat hasil.")
