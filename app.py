import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore

# =============================================================================
# BAGIAN 0: KONEKSI KE DATABASE FIREBASE
# =============================================================================

# Fungsi untuk menginisialisasi koneksi ke Firebase
# Menggunakan @st.cache_resource agar koneksi hanya dibuat sekali
@st.cache_resource
def initialize_firebase():
    try:
        # Mengambil kredensial dari Streamlit Secrets
        creds_dict = dict(st.secrets["firebase_credentials"])
        
        # PERBAIKAN: Mengganti literal '\n' dengan karakter newline yang sebenarnya
        creds_dict["private_key"] = creds_dict["private_key"].replace('\\n', '\n')
        
        cred = credentials.Certificate(creds_dict)
        firebase_admin.initialize_app(cred)
        print("Firebase Initialized.")
    except ValueError as e:
        # Mencegah error jika aplikasi sudah diinisialisasi (karena Streamlit rerun)
        if "The default Firebase app already exists" not in str(e):
            raise e
    return firestore.client()

# Inisialisasi DB di awal
db = initialize_firebase()

# =============================================================================
# BAGIAN 1: FUNGSI-FUNGSI HELPER
# =============================================================================

# Fungsi dari Skrip #1 (Mode Serial)
def generate_serial_output(episodes_data, grouping_style, resolutions):
    txt_lines = []
    # Mengonversi key episode ke integer untuk sorting yang benar
    sorted_keys = sorted([int(k) for k in episodes_data.keys()])
    for ep_num in sorted_keys:
        ep_num_str = str(ep_num) # Gunakan string lagi untuk akses dictionary
        links = []
        if "Server" in grouping_style:
            for server in sorted(episodes_data[ep_num_str].keys()):
                for res in resolutions:
                    if res in episodes_data[ep_num_str][server]:
                        link = episodes_data[ep_num_str][server][res]
                        links.append(f'<a href="{link["url"]}" rel="nofollow" data-wpel-link="external">{link["label"]}</a>')
        elif "Resolusi" in grouping_style:
            for res in resolutions:
                for server in sorted(episodes_data[ep_num_str].keys()):
                    if res in episodes_data[ep_num_str][server]:
                        link = episodes_data[ep_num_str][server][res]
                        links.append(f'<a href="{link["url"]}" rel="nofollow" data-wpel-link="external">{link["label"]}</a>')
        txt_lines.append(f'<li><strong>EPISODE {ep_num}</strong> {" ".join(links)}</li>')
    return "\n".join(txt_lines)

# Fungsi dari Skrip #2 (Mode Konten Tunggal)
def generate_single_output(data, resolutions, servers):
    html_lines = []
    for res in resolutions:
        if res not in data: continue
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
# BAGIAN 2: FUNGSI UNTUK MEMUAT DATA DARI FIREBASE
# =============================================================================

def load_data_from_firestore():
    # Hanya muat data jika session state kosong untuk menghindari load berulang
    if 'data_loaded' not in st.session_state:
        # Load data untuk Mode Serial
        serial_ref = db.collection("link_generator").document("serial_data").get()
        if serial_ref.exists:
            st.session_state.serial_data = serial_ref.to_dict()
        else:
            st.session_state.serial_data = {}

        # Load data untuk Mode Konten Tunggal
        single_ref = db.collection("link_generator").document("single_data").get()
        if single_ref.exists:
            data = single_ref.to_dict()
            st.session_state.single_data = data.get('data', {})
            st.session_state.single_server_order = data.get('order', [])
        else:
            st.session_state.single_data = {}
            st.session_state.single_server_order = []

        st.session_state.serial_final_txt = ""
        st.session_state.single_final_html = ""
        st.session_state.data_loaded = True # Tandai bahwa data sudah dimuat

# Panggil fungsi load data di awal
load_data_from_firestore()

# =============================================================================
# BAGIAN 3: TAMPILAN UTAMA APLIKASI
# =============================================================================

st.set_page_config(layout="wide", page_title="Universal Link Generator")
st.title("Universal Link Generator")

tab1, tab2 = st.tabs([" Bentuk Link Ringkas", "Bentuk Link Drakor"])

# --- KONTEN UNTUK TAB 1: MODE SERIAL ---
with tab1:
    st.header("Mode Bentuk Link Ringkas")
    st.info("Gunakan mode ini untuk membuat daftar link dari satu atau lebih server untuk banyak episode sekaligus.")
    
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Masukan Data Disini")
        with st.form("serial_form"): # Hapus clear_on_submit
            resolutions_serial = st.text_input("Resolusi (pisahkan spasi)", value="480p 720p", key="res_serial")
            start_episode = st.number_input("Mulai dari Episode", min_value=1, step=1, value=1)
            server_name_serial = st.text_input("Nama Server", placeholder="cth: MR", key="server_serial").strip().upper()
            links_serial = st.text_area("Tempel Link (urut per episode & resolusi)", placeholder="Contoh: Ep1 480p Ep1 720p...", height=150)
            
            submitted_serial = st.form_submit_button("➕ Tambah Data")

            if submitted_serial:
                links = [x.strip() for x in links_serial.split() if x.strip()]
                resolutions = [res.strip() for res in resolutions_serial.strip().split() if res.strip()]
                if not server_name_serial or not resolutions or not links:
                    st.warning("Pastikan semua field terisi.")
                elif len(links) % len(resolutions) != 0:
                    st.error(f"Jumlah link harus kelipatan dari jumlah resolusi ({len(resolutions)}).")
                else:
                    count = len(links) // len(resolutions)
                    for i in range(count):
                        ep = str(start_episode + i) # Firestore key harus string
                        if ep not in st.session_state.serial_data:
                            st.session_state.serial_data[ep] = {}
                        st.session_state.serial_data[ep][server_name_serial] = {}
                        for j, res in enumerate(resolutions):
                            link_index = i * len(resolutions) + j
                            st.session_state.serial_data[ep][server_name_serial][res] = {"url": links[link_index], "label": f"{server_name_serial} {res}"}
                    # Simpan ke Firestore
                    db.collection("link_generator").document("serial_data").set(st.session_state.serial_data)
                    st.success(f"Server '{server_name_serial}' ditambahkan dan disimpan ke database.")
    
    with col2:
        st.subheader("Hasil Generator Data")
        if not st.session_state.get('serial_data'):
            st.write("Belum ada data serial yang ditambahkan.")
        else:
            st.write("**Ringkasan Data (dari Database):**")
            st.json(st.session_state.serial_data, expanded=False)
            st.divider()
            
            grouping_style = st.radio("Gaya Urutan:", ['Berdasarkan Server', 'Berdasarkan Resolusi'], horizontal=True, key="style_serial")
            
            if st.button("🔨 BUAT KODE"):
                resolutions = [res.strip() for res in resolutions_serial.strip().split() if res.strip()]
                st.session_state.serial_final_txt = generate_serial_output(st.session_state.serial_data, grouping_style, resolutions)
            
            st.text_area("Hasil HTML:", value=st.session_state.serial_final_txt, height=200, key="output_serial")
            
            if st.button("🔄 Reset Data Serial"):
                db.collection("link_generator").document("serial_data").delete()
                st.session_state.serial_data = {}
                st.session_state.serial_final_txt = ""
                st.success("Data serial di database telah direset.")
                st.rerun()

# --- KONTEN UNTUK TAB 2: MODE KONTEN TUNGGAL ---
with tab2:
    st.header("Mode Bentuk Link Drakor")
    st.info("Gunakan mode ini untuk membuat daftar link seperti berbentuk link drakor.")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Masukan Data Disini")
        resolutions_single = st.text_input("Daftar Resolusi (pisahkan spasi)", value="360p 540p 720p 1080p", key="res_single")
        resolutions = [r.strip() for r in resolutions_single.strip().split() if r.strip()]
        
        server_name_single = st.text_input("Nama Server", placeholder="contoh: TeraBox", key="server_single")
        links_single = st.text_area(f"Link untuk '{server_name_single or '...'}'", placeholder=f"Tempel {len(resolutions)} link di sini...", height=150)

        if st.button("➕ Tambah Data", type="primary", key="add_single"):
            links = [l.strip() for l in links_single.strip().splitlines() if l.strip()]
            if not server_name_single:
                st.warning("Nama server tidak boleh kosong.")
            elif len(resolutions) != len(links):
                st.error(f"Jumlah link ({len(links)}) tidak cocok dengan jumlah resolusi ({len(resolutions)}).")
            else:
                for i, res in enumerate(resolutions):
                    if res not in st.session_state.single_data:
                        st.session_state.single_data[res] = {}
                    st.session_state.single_data[res][server_name_single] = links[i]
                if server_name_single not in st.session_state.single_server_order:
                    st.session_state.single_server_order.append(server_name_single)
                
                # Simpan ke Firestore
                payload = {"data": st.session_state.single_data, "order": st.session_state.single_server_order}
                db.collection("link_generator").document("single_data").set(payload)
                st.success(f"Server '{server_name_single}' ditambahkan dan disimpan ke database!")
                
        if st.button("🔄 Reset Data Konten Tunggal"):
            db.collection("link_generator").document("single_data").delete()
            st.session_state.single_data = {}
            st.session_state.single_server_order = []
            st.session_state.single_final_html = ""
            st.success("Data konten tunggal di database telah direset.")
            st.rerun()

    with col2:
        st.subheader("Hasil Generator Data")
        if not st.session_state.get('single_server_order'):
            st.write("Belum ada server yang ditambahkan.")
        else:
            st.write("**Urutan Server Ditambahkan (dari Database):**")
            st.write(" -> ".join(f"`{s}`" for s in st.session_state.single_server_order))
            st.divider()
            
            if st.button("🚀 Generate HTML", key="generate_single"):
                st.session_state.single_final_html = generate_single_output(
                    st.session_state.single_data,
                    resolutions,
                    st.session_state.single_server_order
                )
            
            if st.session_state.single_final_html:
                st.code(st.session_state.single_final_html, language="html")
            else:
                st.write("Klik 'Generate HTML' untuk melihat hasil.")
