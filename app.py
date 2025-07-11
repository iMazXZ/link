import streamlit as st



# =============================================================================

# BAGIAN 1: FUNGSI-FUNGSI HELPER (DARI KEDUA SKRIP)

# =============================================================================



# Fungsi dari Skrip #1 (Mode Serial)

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

# BAGIAN 2: INISIALISASI SESSION STATE UNTUK KEDUA MODE

# =============================================================================



# State untuk Mode Serial

if 'serial_data' not in st.session_state:

    st.session_state.serial_data = {}

if 'serial_final_txt' not in st.session_state:

    st.session_state.serial_final_txt = ""



# State untuk Mode Konten Tunggal

if 'single_data' not in st.session_state:

    st.session_state.single_data = {}

if 'single_server_order' not in st.session_state:

    st.session_state.single_server_order = []

if 'single_final_html' not in st.session_state:

    st.session_state.single_final_html = ""





# =============================================================================

# BAGIAN 3: TAMPILAN UTAMA APLIKASI

# =============================================================================



st.set_page_config(layout="wide", page_title="Universal Link Generator")

st.title("Universal Link Generator")



# Membuat dua tab utama untuk memisahkan fungsionalitas

tab1, tab2 = st.tabs([" Bentuk Link Ringkas", "Bentuk Link Drakor"])





# --- KONTEN UNTUK TAB 1: MODE SERIAL ---

with tab1:

    st.header("Mode Bentuk Link Ringkas")

    st.info("Gunakan mode ini untuk membuat daftar link dari satu atau lebih server untuk banyak episode sekaligus.")

    

    col1, col2 = st.columns(2)



    with col1:

        st.subheader("Masukan Data Disini")

        with st.form("serial_form", clear_on_submit=True):

            resolutions_serial = st.text_input("Resolusi (pisahkan spasi)", value="480p 720p", key="res_serial")

            start_episode = st.number_input("Mulai dari Episode", min_value=1, step=1, value=1)

            server_name_serial = st.text_input("Nama Server", placeholder="cth: MR", key="server_serial").strip().upper()

            links_serial = st.text_area("Tempel Link (urut per episode & resolusi)", placeholder="Contoh: Ep1 480p Ep1 720p Ep2 480p Ep2 720p...", height=150)

            

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

                resolutions = [res.strip() for res in resolutions_serial.strip().split() if res.strip()]

                st.session_state.serial_final_txt = generate_serial_output(st.session_state.serial_data, grouping_style, resolutions)

            

            st.text_area("Hasil HTML:", value=st.session_state.serial_final_txt, height=200, key="output_serial")

            

            if st.button("🔄 Reset Data Serial"):

                st.session_state.serial_data = {}

                st.session_state.serial_final_txt = ""

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

        links_single = st.text_area(f"Link untuk '{server_name_single or '...'}'", placeholder=f"Tempel {len(resolutions)} link di sini, satu per baris, sesuai urutan resolusi.", height=150)



        if st.button("➕ Tambah Data", type="primary"):

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

                st.success(f"Server '{server_name_single}' ditambahkan!")

                

        if st.button("🔄 Reset Data Konten Tunggal"):

            st.session_state.single_data = {}

            st.session_state.single_server_order = []

            st.session_state.single_final_html = ""

            st.rerun()



    with col2:

        st.subheader("Hasil Generator Data")

        if not st.session_state.single_server_order:

            st.write("Belum ada server yang ditambahkan.")

        else:

            st.write("**Urutan Server Ditambahkan:**")

            st.write(" -> ".join(f"`{s}`" for s in st.session_state.single_server_order))

            st.divider()

            

            if st.button("🚀 Generate HTML"):

                st.session_state.single_final_html = generate_single_output(

                    st.session_state.single_data,

                    resolutions,

                    st.session_state.single_server_order

                )

            

            if st.session_state.single_final_html:

                st.code(st.session_state.single_final_html, language="html")

            else:

                st.write("Klik 'Generate HTML' untuk melihat hasil.")
