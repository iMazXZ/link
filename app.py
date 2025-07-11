import streamlit as st

# --- Fungsi Inti dari Skrip #2 ---
# Fungsi ini paling cocok untuk format output akhir yang diinginkan
def generate_html_code(data, resolutions, servers):
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


# --- Inisialisasi State Aplikasi ---
# `st.session_state` adalah cara Streamlit "mengingat" data
if 'all_data' not in st.session_state:
    st.session_state.all_data = {}
if 'server_order' not in st.session_state:
    st.session_state.server_order = []
if 'final_html' not in st.session_state:
    st.session_state.final_html = ""


# ==================================
# Tampilan Antarmuka (UI)
# ==================================

st.set_page_config(layout="wide", page_title="HTML Link Generator")
st.title("⚙️ HTML Link Generator Pro")
st.markdown("Aplikasi untuk membuat daftar link unduhan dari berbagai server dengan mudah.")

# --- SIDEBAR UNTUK SEMUA INPUT ---
with st.sidebar:
    st.header("Langkah 1: Konfigurasi")
    resolutions_str = st.text_input(
        "Daftar Resolusi (pisahkan spasi)",
        value="360p 540p 720p 1080p",
        help="Tentukan urutan resolusi yang akan Anda gunakan."
    )
    resolutions = [r.strip() for r in resolutions_str.strip().split() if r.strip()]

    st.divider()

    st.header("Langkah 2: Tambah Server")
    server_name = st.text_input("Nama Server", placeholder="cth: TeraBox")
    links_str = st.text_area(
        f"Link untuk '{server_name or '...'}':",
        placeholder=f"Tempel {len(resolutions)} link di sini, satu per baris, sesuai urutan resolusi di atas.",
        height=150
    )

    # Tombol diletakkan dalam kolom agar sejajar
    col1, col2 = st.columns(2)
    with col1:
        if st.button("➕ Tambah Server", use_container_width=True, type="primary"):
            links = [l.strip() for l in links_str.strip().splitlines() if l.strip()]
            if not server_name:
                st.warning("Nama server tidak boleh kosong.")
            elif len(resolutions) != len(links):
                st.error(f"Jumlah link ({len(links)}) tidak cocok dengan jumlah resolusi ({len(resolutions)}).")
            else:
                for i, res in enumerate(resolutions):
                    if res not in st.session_state.all_data:
                        st.session_state.all_data[res] = {}
                    st.session_state.all_data[res][server_name] = links[i]
                
                if server_name not in st.session_state.server_order:
                    st.session_state.server_order.append(server_name)
                st.success(f"Server '{server_name}' ditambahkan!")
    
    with col2:
        if st.button("🔄 Reset", use_container_width=True):
            st.session_state.all_data = {}
            st.session_state.server_order = []
            st.session_state.final_html = ""
            st.info("Semua data direset.")


# --- AREA UTAMA UNTUK OUTPUT ---
st.subheader("📋 Ringkasan Server yang Ditambahkan")

if not st.session_state.server_order:
    st.info("Belum ada server yang ditambahkan. Silakan gunakan form di sidebar.")
else:
    # Menampilkan server yang sudah ada sebagai "pills"
    server_pills = " ".join([f"`{s}`" for s in st.session_state.server_order])
    st.markdown(f"**Urutan Server:** {server_pills}")

st.divider()

st.subheader("✔️ Hasil Akhir (HTML)")

if st.button("🚀 Generate HTML", disabled=not st.session_state.server_order):
    st.session_state.final_html = generate_html_code(
        st.session_state.all_data,
        resolutions,
        st.session_state.server_order
    )

if st.session_state.final_html:
    st.code(st.session_state.final_html, language="html")
else:
    st.write("Klik tombol 'Generate HTML' untuk melihat hasilnya di sini.")
