import streamlit as st

# Fungsi generate_txt tidak perlu diubah, logikanya tetap sama.
def generate_txt(episodes_data, grouping_style, resolutions):
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

# ==============================================================================
# APLIKASI STREAMLIT
# ==============================================================================

st.set_page_config(layout="centered", page_title="Link Organizer")

# 1. Inisialisasi Session State
# Ini adalah cara Streamlit untuk "mengingat" data antar interaksi.
if 'episode_data' not in st.session_state:
    st.session_state.episode_data = {}
if 'final_txt' not in st.session_state:
    st.session_state.final_txt = ""

# --- Tampilan UI ---
st.title("📁 Custom TXT Link Organizer")

st.info("Isi form di bawah untuk menambahkan data episode, lalu generate hasilnya di bagian bawah.")

# --- Form Input untuk Menambah Data ---
with st.form("add_server_form", clear_on_submit=True):
    st.subheader("➕ Tambah Data Server")
    
    # Input diganti dengan komponen Streamlit
    resolutions_str = st.text_input("Resolusi (pisahkan dengan spasi)", value="480p 720p")
    start_episode = st.number_input("Mulai dari Episode", min_value=1, step=1, value=1)
    server_name = st.text_input("Nama Server", placeholder="contoh: AB atau BH atau MR").strip().upper()
    links_str = st.text_area("Tempel Link (satu link per baris atau pisahkan spasi)", placeholder="480p 720p 480p 720p...")
    
    submitted = st.form_submit_button("Tambahkan")
    
    if submitted:
        links = [x.strip() for x in links_str.split() if x.strip()]
        resolutions = [res.strip() for res in resolutions_str.strip().split() if res.strip()]
        
        # Validasi Input
        if not server_name:
            st.warning("⚠️ Silakan isi nama server terlebih dahulu.")
        elif not resolutions:
            st.warning("⚠️ Silakan isi kolom Resolusi.")
        elif len(links) % len(resolutions) != 0:
            num_res = len(resolutions)
            st.warning(f"⚠️ Jumlah link harus kelipatan dari jumlah resolusi ({num_res}). Cek kembali input link Anda.")
        else:
            count = len(links) // len(resolutions)
            for i in range(count):
                ep = start_episode + i
                if ep not in st.session_state.episode_data:
                    st.session_state.episode_data[ep] = {}
                
                st.session_state.episode_data[ep][server_name] = {}
                
                for j, res in enumerate(resolutions):
                    link_index = i * len(resolutions) + j
                    st.session_state.episode_data[ep][server_name][res] = {
                        "url": links[link_index],
                        "label": f"{server_name} {res}",
                    }
            st.success(f"✅ Server **{server_name}** ditambahkan untuk Episode **{start_episode}** hingga **{start_episode + count - 1}**")

# --- Menampilkan Ringkasan Data yang Sudah Masuk ---
if st.session_state.episode_data:
    st.divider()
    st.subheader("📋 Ringkasan Data Saat Ini")
    
    # Menampilkan ringkasan dengan lebih rapi
    sorted_eps = sorted(st.session_state.episode_data.keys())
    for ep in sorted_eps:
        servers = ", ".join(sorted(st.session_state.episode_data[ep].keys()))
        st.markdown(f"- **Episode {ep}**: `{servers}`")

st.divider()

# --- Bagian untuk Generate Hasil Akhir ---
st.subheader("🔨 Generate Hasil Akhir")

if not st.session_state.episode_data:
    st.warning("Belum ada data yang ditambahkan. Silakan isi form di atas.")
else:
    grouping_style = st.radio(
        "Pilih Gaya Urutan Output:",
        ['Berdasarkan Server', 'Berdasarkan Resolusi'],
        horizontal=True
    )

    if st.button("Generate Txt"):
        resolutions = [res.strip() for res in resolutions_str.strip().split() if res.strip()]
        # Memanggil fungsi generate dengan data dari session_state
        final_txt = generate_txt(st.session_state.episode_data, grouping_style, resolutions)
        # Menyimpan hasil ke session_state agar tidak hilang
        st.session_state.final_txt = final_txt
        st.success("✅ Konten berhasil digenerate!")

# Menampilkan hasil akhir di text_area
st.text_area(
    "Hasil Jadi (HTML):", 
    value=st.session_state.final_txt, 
    height=300,
    help="Anda bisa salin teks ini dengan menekan tombol copy di pojok kanan atas."
)

# Tombol untuk mereset semua data
if st.button("🔄 Reset Semua Data"):
    st.session_state.episode_data = {}
    st.session_state.final_txt = ""
    st.rerun()
