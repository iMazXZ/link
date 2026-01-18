"""
DramaStream Quickfill Generator - Streamlit Version
====================================================
Light Glassmorphism UI Design
"""

import streamlit as st
import re
from dataclasses import dataclass, field
from typing import List, Dict, Optional
import zipfile
import io

# =============================================================================
# CUSTOM CSS - GLASSMORPHISM THEME
# =============================================================================

def inject_custom_css():
    st.markdown("""
    <style>
    /* Import Google Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    /* Root Variables */
    :root {
        --glass-bg: rgba(255, 255, 255, 0.7);
        --glass-border: rgba(255, 255, 255, 0.3);
        --accent-color: #6366f1;
        --accent-hover: #4f46e5;
        --text-primary: #1e293b;
        --text-secondary: #64748b;
        --shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
    }
    
    /* Main Background */
    .stApp {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 50%, #f093fb 100%);
        font-family: 'Inter', sans-serif;
    }
    
    /* Hide Streamlit Branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Main Container */
    .main .block-container {
        padding: 2rem 3rem;
        max-width: 1400px;
    }
    
    /* Glass Card Effect */
    .glass-card {
        background: var(--glass-bg);
        backdrop-filter: blur(20px);
        -webkit-backdrop-filter: blur(20px);
        border-radius: 20px;
        border: 1px solid var(--glass-border);
        box-shadow: var(--shadow);
        padding: 2rem;
        margin-bottom: 1.5rem;
    }
    
    /* Title Styling */
    .main-title {
        font-size: 2.5rem;
        font-weight: 700;
        color: white;
        text-align: center;
        margin-bottom: 0.5rem;
        text-shadow: 0 2px 10px rgba(0,0,0,0.2);
    }
    
    .main-subtitle {
        font-size: 1rem;
        color: rgba(255,255,255,0.9);
        text-align: center;
        margin-bottom: 2rem;
    }
    
    /* Section Headers */
    .section-header {
        font-size: 1.25rem;
        font-weight: 600;
        color: var(--text-primary);
        margin-bottom: 1rem;
        padding-bottom: 0.5rem;
        border-bottom: 2px solid var(--accent-color);
    }
    
    /* Input Styling */
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea {
        background: rgba(255, 255, 255, 0.9) !important;
        border: 1px solid rgba(99, 102, 241, 0.3) !important;
        border-radius: 12px !important;
        padding: 0.75rem 1rem !important;
        font-family: 'Inter', sans-serif !important;
        font-size: 0.9rem !important;
        transition: all 0.3s ease !important;
    }
    
    .stTextInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus {
        border-color: var(--accent-color) !important;
        box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.2) !important;
    }
    
    /* Button Styling */
    .stButton > button {
        background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%) !important;
        color: white !important;
        border: none !important;
        border-radius: 12px !important;
        padding: 0.75rem 2rem !important;
        font-weight: 600 !important;
        font-family: 'Inter', sans-serif !important;
        transition: all 0.3s ease !important;
        box-shadow: 0 4px 15px rgba(99, 102, 241, 0.4) !important;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 20px rgba(99, 102, 241, 0.5) !important;
    }
    
    /* Download Button */
    .stDownloadButton > button {
        background: linear-gradient(135deg, #10b981 0%, #059669 100%) !important;
        box-shadow: 0 4px 15px rgba(16, 185, 129, 0.4) !important;
    }
    
    .stDownloadButton > button:hover {
        box-shadow: 0 6px 20px rgba(16, 185, 129, 0.5) !important;
    }
    
    /* Select Box */
    .stSelectbox > div > div {
        background: rgba(255, 255, 255, 0.9) !important;
        border-radius: 12px !important;
    }
    
    /* Code Block */
    .stCode {
        border-radius: 12px !important;
        border: 1px solid rgba(99, 102, 241, 0.2) !important;
    }
    
    /* Info/Success/Warning/Error boxes */
    .stAlert {
        border-radius: 12px !important;
        border: none !important;
    }
    
    /* Expander */
    .streamlit-expanderHeader {
        background: rgba(255, 255, 255, 0.5) !important;
        border-radius: 12px !important;
        font-weight: 500 !important;
    }
    
    /* Divider */
    hr {
        border: none;
        height: 1px;
        background: linear-gradient(90deg, transparent, rgba(99, 102, 241, 0.3), transparent);
        margin: 1.5rem 0;
    }
    
    /* Sidebar */
    [data-testid="stSidebar"] {
        background: rgba(255, 255, 255, 0.1) !important;
        backdrop-filter: blur(10px) !important;
    }
    
    [data-testid="stSidebar"] .block-container {
        padding: 2rem 1rem;
    }
    
    /* Spinner */
    .stSpinner > div {
        border-top-color: var(--accent-color) !important;
    }
    
    /* Caption */
    .stCaption {
        color: var(--text-secondary) !important;
    }
    
    /* Result Card */
    .result-info {
        background: linear-gradient(135deg, rgba(99, 102, 241, 0.1) 0%, rgba(139, 92, 246, 0.1) 100%);
        border-radius: 12px;
        padding: 1rem;
        margin-bottom: 1rem;
        border-left: 4px solid var(--accent-color);
    }
    
    .result-info strong {
        color: var(--accent-color);
    }
    </style>
    """, unsafe_allow_html=True)


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class DownloadLink:
    hosting: str
    url: str
    resolution: str


@dataclass
class EmbedData:
    hostname: str
    embed: str


@dataclass
class Episode:
    number: str
    series_name: str
    year: str
    embeds: List[EmbedData] = field(default_factory=list)
    downloads: Dict[str, List[DownloadLink]] = field(default_factory=dict)


# =============================================================================
# PARSING FUNCTIONS
# =============================================================================

def parse_filename(filename: str) -> Optional[Dict]:
    pattern = r'\[.*?\]\s*(.+?)\s*\((\d{4})\)\s*E(\d+)'
    match = re.search(pattern, filename)
    if match:
        return {
            'series_name': match.group(1).strip(),
            'year': match.group(2),
            'episode': match.group(3)
        }
    return None


def extract_resolution(text: str) -> str:
    match = re.search(r'(\d{3,4}p)', text, re.IGNORECASE)
    return match.group(1) if match else '720p'


def detect_hosting(url: str) -> str:
    url_lower = url.lower()
    if 'terabox' in url_lower:
        return 'Terabox'
    elif 'mirrored' in url_lower or 'mir.cr' in url_lower:
        return 'Mirrored'
    elif 'upfiles' in url_lower:
        return 'Upfiles'
    elif 'buzzheavier' in url_lower:
        return 'BuzzHeavier'
    elif 'gofile' in url_lower:
        return 'Gofile'
    elif 'filemoon' in url_lower:
        return 'FileMoon'
    elif 'vidhide' in url_lower:
        return 'VidHide'
    elif 'krakenfiles' in url_lower:
        return 'Krakenfiles'
    elif 'ouo.io' in url_lower or 'short.icu' in url_lower:
        return 'Shortlink'
    else:
        return 'Other'


def parse_input(text: str) -> Dict[str, Episode]:
    episodes: Dict[str, Episode] = {}
    lines = text.strip().split('\n')
    
    download_section_start = -1
    for i, line in enumerate(lines):
        if line.strip().lower() == 'download link':
            download_section_start = i
            break
    
    if download_section_start == -1:
        for i, line in enumerate(lines):
            if line.startswith('http') and ('mirrored' in line.lower() or 'terabox' in line.lower()):
                download_section_start = i
                break
    
    embed_lines = lines[:download_section_start] if download_section_start > 0 else lines
    embed_server_count = {}
    standalone_embeds = []
    
    i = 0
    while i < len(embed_lines):
        line = embed_lines[i].strip()
        if line.startswith('[') and '|' not in line:
            info = parse_filename(line)
            if info and i + 1 < len(embed_lines):
                next_line = embed_lines[i + 1].strip()
                if next_line.startswith('<iframe'):
                    ep_num = info['episode']
                    if ep_num not in episodes:
                        episodes[ep_num] = Episode(number=ep_num, series_name=info['series_name'], year=info['year'])
                    if ep_num not in embed_server_count:
                        embed_server_count[ep_num] = 0
                    embed_server_count[ep_num] += 1
                    episodes[ep_num].embeds.append(EmbedData(hostname=f"Server {embed_server_count[ep_num]}", embed=next_line))
                    i += 2
                    continue
        elif line.startswith('<iframe'):
            standalone_embeds.append(line)
        elif '|' in line and '<iframe' in line:
            parts = line.split('|', 1)
            iframe_part = parts[1].strip()
            if iframe_part.startswith('<iframe'):
                standalone_embeds.append(iframe_part)
        i += 1
    
    for line in embed_lines:
        line = line.strip()
        if line.startswith('[') and '|' in line:
            parts = line.split('|', 1)
            filename = parts[0].strip()
            url = parts[1].strip()
            info = parse_filename(filename)
            if info:
                ep_num = info['episode']
                if ep_num not in episodes:
                    episodes[ep_num] = Episode(number=ep_num, series_name=info['series_name'], year=info['year'])
                if ep_num not in embed_server_count:
                    embed_server_count[ep_num] = 0
                embed_server_count[ep_num] += 1
                embed_code = f'<iframe src="{url}" width="100%" height="100%" frameborder="0" allowfullscreen></iframe>'
                episodes[ep_num].embeds.append(EmbedData(hostname=f"Server {embed_server_count[ep_num]}", embed=embed_code))
    
    if download_section_start > 0:
        download_lines = lines[download_section_start + 1:]
        download_urls = [line.strip() for line in download_lines if line.strip() and line.strip().startswith('http')]
        
        episode_resolutions = {}
        
        for url in download_urls:
            if 'mirrored' in url.lower():
                ep_match = re.search(r'E(\d+)', url)
                res = extract_resolution(url)
                if ep_match:
                    ep_num = ep_match.group(1)
                    if ep_num not in episodes:
                        episodes[ep_num] = Episode(number=ep_num, series_name="Unknown", year="2025")
                    if ep_num not in episode_resolutions:
                        episode_resolutions[ep_num] = []
                    if res not in episode_resolutions[ep_num]:
                        episode_resolutions[ep_num].append(res)
                    if res not in episodes[ep_num].downloads:
                        episodes[ep_num].downloads[res] = []
                    episodes[ep_num].downloads[res].append(DownloadLink(hosting='Mirrored', url=url, resolution=res))
        
        current_episode = None
        current_res_index = 0
        current_hosting = None
        
        for url in download_urls:
            if 'mirrored' in url.lower():
                ep_match = re.search(r'E(\d+)', url)
                if ep_match:
                    new_ep = ep_match.group(1)
                    if new_ep != current_episode:
                        current_episode = new_ep
                        current_res_index = 0
                        current_hosting = 'Mirrored'
                    else:
                        current_res_index += 1
            else:
                if current_episode and current_episode in episode_resolutions:
                    resolutions = episode_resolutions[current_episode]
                    hosting = detect_hosting(url)
                    if hosting != current_hosting:
                        current_hosting = hosting
                        current_res_index = 0
                    if current_res_index < len(resolutions):
                        res = resolutions[current_res_index]
                        episodes[current_episode].downloads[res].append(DownloadLink(hosting=hosting, url=url, resolution=res))
                        current_res_index += 1
        
        for url in download_urls:
            if 'mirrored' in url.lower():
                series_match = re.search(r'\[.*?\]_(.+?)_E\d+', url)
                if series_match:
                    detected_series = series_match.group(1).replace('_', ' ')
                    for ep in episodes.values():
                        if ep.series_name == "Unknown":
                            ep.series_name = detected_series
                    break
        
        if standalone_embeds and len(episodes) == 1:
            ep_num = list(episodes.keys())[0]
            for embed in standalone_embeds:
                if ep_num not in embed_server_count:
                    embed_server_count[ep_num] = 0
                embed_server_count[ep_num] += 1
                episodes[ep_num].embeds.append(EmbedData(hostname=f"Server {embed_server_count[ep_num]}", embed=embed))
    
    return episodes


def generate_quickfill_js(episode: Episode, subbed: str = "Sub") -> str:
    embeds_js = []
    for emb in episode.embeds:
        embed_escaped = emb.embed.replace('\\', '\\\\').replace("'", "\\'").replace('\n', '\\n')
        embeds_js.append(f"""        {{
            hostname: "{emb.hostname}",
            embed: '{embed_escaped}'
        }}""")
    embeds_str = ',\n'.join(embeds_js) if embeds_js else ''
    
    resolutions_js = []
    for res in sorted(episode.downloads.keys(), key=lambda x: int(re.search(r'\d+', x).group())):
        links_js = []
        for link in episode.downloads[res]:
            links_js.append(f"""                    {{ hosting: "{link.hosting}", url: "{link.url}" }}""")
        links_str = ',\n'.join(links_js)
        resolutions_js.append(f"""            {{
                pixel: "{res}",
                links: [
{links_str}
                ]
            }}""")
    resolutions_str = ',\n'.join(resolutions_js) if resolutions_js else ''
    
    js_code = f'''/**
 * DramaStream Quick-Fill - {episode.series_name} Episode {episode.number}
 * Paste ke browser console di halaman "Add New Post"
 */

const EPISODE_DATA = {{
    seriesName: "{episode.series_name}",
    episodeNumber: "{episode.number}",
    subbed: "{subbed}",
    embeds: [
{embeds_str}
    ],
    downloads: {{
        episodeTitle: "Episode {episode.number}",
        resolutions: [
{resolutions_str}
        ]
    }}
}};

(async function() {{
    'use strict';
    const DELAY = 150;
    function sleep(ms) {{ return new Promise(resolve => setTimeout(resolve, ms)); }}
    function triggerChange(el) {{
        el.dispatchEvent(new Event('change', {{ bubbles: true }}));
        el.dispatchEvent(new Event('input', {{ bubbles: true }}));
    }}
    function setTitle(title) {{
        const el = document.getElementById('title');
        if (el) {{ el.value = title; triggerChange(el); console.log('✓ Title:', title); }}
    }}
    function setEpisodeNumber(num) {{
        const el = document.getElementById('ero_episodebaru');
        if (el) {{ el.value = num; triggerChange(el); console.log('✓ Episode Number:', num); }}
    }}
    function setSubbed(val) {{
        const el = document.getElementById('ero_subepisode');
        if (el) {{ el.value = val; triggerChange(el); console.log('✓ Subbed:', val); }}
    }}
    async function setSeries(name) {{
        const el = document.getElementById('ero_seri');
        if (!el) return;
        for (const opt of el.options) {{
            if (opt.text.trim().toLowerCase() === name.toLowerCase()) {{
                el.value = opt.value;
                if (window.jQuery) jQuery(el).val(opt.value).trigger('change');
                console.log('✓ Series:', name);
                return;
            }}
        }}
        console.warn('⚠ Series tidak ditemukan:', name);
    }}
    function setCategory(name) {{
        const checkboxes = document.querySelectorAll('#categorychecklist input[type="checkbox"]');
        for (const cb of checkboxes) {{
            const label = cb.closest('label');
            if (label && label.textContent.trim().toLowerCase() === name.toLowerCase()) {{
                cb.checked = true; triggerChange(cb);
                console.log('✓ Category:', name);
                return;
            }}
        }}
    }}
    async function addClone(container) {{
        const btn = container.querySelector(':scope > .add-clone');
        if (btn) {{ btn.click(); await sleep(DELAY); }}
    }}
    async function setEmbeds(embeds) {{
        const container = document.querySelector('#embed-video .rwmb-tab-panel-input-version .rwmb-input');
        if (!container) return;
        for (let i = 0; i < embeds.length; i++) {{
            let clones = container.querySelectorAll(':scope > .rwmb-clone:not(.rwmb-clone-template)');
            while (clones.length <= i) {{ await addClone(container); clones = container.querySelectorAll(':scope > .rwmb-clone:not(.rwmb-clone-template)'); }}
            const clone = clones[i];
            const hostnameInput = clone.querySelector('input[name*="ab_hostname"]');
            const embedArea = clone.querySelector('textarea[name*="ab_embed"]');
            if (hostnameInput) {{ hostnameInput.value = embeds[i].hostname; triggerChange(hostnameInput); }}
            if (embedArea) {{ embedArea.value = embeds[i].embed; triggerChange(embedArea); }}
        }}
        console.log('✓ Embeds:', embeds.length, 'servers');
    }}
    async function setDownloads(downloads) {{
        const epContainer = document.querySelector('#episode-download .rwmb-meta-box > .rwmb-field > .rwmb-input');
        if (!epContainer) return;
        const epClone = epContainer.querySelector(':scope > .rwmb-clone:not(.rwmb-clone-template)');
        if (!epClone) return;
        const epTitleInput = epClone.querySelector('input[name*="ab_eptitle_ep"]');
        if (epTitleInput) {{ epTitleInput.value = downloads.episodeTitle; triggerChange(epTitleInput); }}
        const resContainer = epClone.querySelector('.rwmb-group-collapsible > .rwmb-input');
        if (!resContainer) return;
        for (let r = 0; r < downloads.resolutions.length; r++) {{
            const resData = downloads.resolutions[r];
            let resClones = resContainer.querySelectorAll(':scope > .rwmb-clone:not(.rwmb-clone-template)');
            while (resClones.length <= r) {{ await addClone(resContainer); resClones = resContainer.querySelectorAll(':scope > .rwmb-clone:not(.rwmb-clone-template)'); }}
            const resClone = resClones[r];
            const pixelSelect = resClone.querySelector('select[name*="ab_pixel_ep"]');
            if (pixelSelect) {{ pixelSelect.value = resData.pixel; triggerChange(pixelSelect); }}
            const linkContainer = resClone.querySelector('.rwmb-group-wrapper:not(.rwmb-group-collapsible) > .rwmb-input');
            if (!linkContainer) continue;
            for (let l = 0; l < resData.links.length; l++) {{
                const linkData = resData.links[l];
                let linkClones = linkContainer.querySelectorAll(':scope > .rwmb-clone:not(.rwmb-clone-template)');
                while (linkClones.length <= l) {{ await addClone(linkContainer); linkClones = linkContainer.querySelectorAll(':scope > .rwmb-clone:not(.rwmb-clone-template)'); }}
                const linkClone = linkClones[l];
                const hostingSelect = linkClone.querySelector('select[name*="ab_hostingname_ep"]');
                if (hostingSelect) {{ hostingSelect.value = linkData.hosting; triggerChange(hostingSelect); }}
                const urlInput = linkClone.querySelector('input[name*="ab_linkurl_ep"]');
                if (urlInput) {{ urlInput.value = linkData.url; triggerChange(urlInput); }}
            }}
        }}
        console.log('✓ Downloads:', downloads.resolutions.length, 'resolutions');
    }}
    console.log('🎬 Auto-filling: {episode.series_name} E{episode.number}...');
    const data = EPISODE_DATA;
    setTitle(`${{data.seriesName}} Episode ${{data.episodeNumber}} Subtitle Indonesia`);
    await sleep(DELAY);
    await setSeries(data.seriesName);
    await sleep(DELAY);
    setCategory(data.seriesName);
    await sleep(DELAY);
    setEpisodeNumber(data.episodeNumber);
    await sleep(DELAY);
    setSubbed(data.subbed);
    await sleep(DELAY);
    if (data.embeds && data.embeds.length > 0) await setEmbeds(data.embeds);
    await sleep(DELAY);
    if (data.downloads) await setDownloads(data.downloads);
    console.log('✅ Done! Review dan klik Publish.');
}})();
'''
    return js_code


# =============================================================================
# STREAMLIT UI
# =============================================================================

st.set_page_config(
    page_title="DramaStream Quickfill",
    page_icon="▶",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Inject custom CSS
inject_custom_css()

# Session state
if 'generated_scripts' not in st.session_state:
    st.session_state.generated_scripts = {}
if 'selected_episode' not in st.session_state:
    st.session_state.selected_episode = None

# Header
st.markdown('<h1 class="main-title">DramaStream Quickfill</h1>', unsafe_allow_html=True)
st.markdown('<p class="main-subtitle">Generate autofill scripts untuk posting episode ke WordPress</p>', unsafe_allow_html=True)

# Main layout
col1, col2 = st.columns([1, 1], gap="large")

with col1:
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-header">Input Data</div>', unsafe_allow_html=True)
    
    series_name = st.text_input("Nama Series (opsional)", placeholder="Kosongkan untuk auto-detect")
    
    input_text = st.text_area(
        "Paste data episode",
        height=280,
        placeholder="""<iframe src="https://server1/xxx" ...></iframe>
id | <iframe src="https://short.icu/xxx" ...></iframe>

Download Link

https://www.mirrored.to/.../E001.360p.mp4_links
https://www.mirrored.to/.../E001.720p.mp4_links
https://upfiles.com/xxx
..."""
    )
    
    if st.button("Generate Scripts", type="primary", use_container_width=True):
        if input_text.strip():
            with st.spinner("Processing..."):
                episodes = parse_input(input_text)
                
                if series_name:
                    for ep in episodes.values():
                        ep.series_name = series_name
                
                if episodes:
                    scripts = {}
                    for ep_num in sorted(episodes.keys(), key=int):
                        ep = episodes[ep_num]
                        scripts[ep_num] = {
                            'js': generate_quickfill_js(ep),
                            'embeds': len(ep.embeds),
                            'resolutions': list(ep.downloads.keys()),
                            'series': ep.series_name
                        }
                    st.session_state.generated_scripts = scripts
                    st.session_state.selected_episode = list(scripts.keys())[0] if scripts else None
                    st.success(f"Generated {len(scripts)} episode scripts!")
                else:
                    st.error("Tidak ada episode yang terdeteksi!")
        else:
            st.warning("Paste data episode terlebih dahulu")
    
    st.markdown('</div>', unsafe_allow_html=True)

with col2:
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-header">Output Scripts</div>', unsafe_allow_html=True)
    
    if st.session_state.generated_scripts:
        scripts = st.session_state.generated_scripts
        
        episode_options = [f"Episode {ep}" for ep in sorted(scripts.keys(), key=int)]
        selected_label = st.selectbox("Pilih Episode", episode_options)
        selected_ep = selected_label.replace("Episode ", "") if selected_label else None
        
        if selected_ep and selected_ep in scripts:
            script_data = scripts[selected_ep]
            
            st.markdown(f"""
            <div class="result-info">
                <strong>Series:</strong> {script_data['series']} &nbsp;|&nbsp;
                <strong>Embeds:</strong> {script_data['embeds']} &nbsp;|&nbsp;
                <strong>Resolutions:</strong> {', '.join(script_data['resolutions'])}
            </div>
            """, unsafe_allow_html=True)
            
            st.code(script_data['js'], language='javascript')
            
            st.caption("Copy script di atas → Paste ke Console browser (F12) di WordPress")
        
        st.divider()
        
        if st.button("Download Semua (ZIP)", use_container_width=True):
            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
                for ep_num, data in scripts.items():
                    zf.writestr(f"quickfill_E{ep_num}.js", data['js'])
            
            st.download_button(
                label="Simpan ZIP",
                data=zip_buffer.getvalue(),
                file_name="quickfill_scripts.zip",
                mime="application/zip",
                use_container_width=True
            )
    else:
        st.info("Generate script terlebih dahulu untuk melihat output")
    
    st.markdown('</div>', unsafe_allow_html=True)

# Help section
with st.expander("Panduan Format Input"):
    st.markdown("""
**Format Embed:**
- `<iframe src="..." ...></iframe>` - Standalone iframe
- `id | <iframe ...></iframe>` - ID dengan iframe
- `[Tag] Series (Year) EXXX.720p.mp4` + iframe di baris berikut

**Format Download (setelah "Download Link"):**
- Mirrored links harus ada episode (E001) dan resolusi (360p/720p/1080p)
- Hosting lain mengikuti urutan resolusi dari Mirrored
""")
