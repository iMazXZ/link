"""
DramaStream Quickfill Generator - Streamlit Version
====================================================
Shadcn-inspired Dark Dashboard UI
"""

import streamlit as st
import re
from dataclasses import dataclass, field
from typing import List, Dict, Optional
import zipfile
import io

# =============================================================================
# CUSTOM CSS - SHADCN DARK THEME
# =============================================================================

def inject_custom_css():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    
    /* Base */
    .stApp {
        background-color: #09090b;
    }
    
    * {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
    }
    
    /* Hide defaults */
    #MainMenu, footer, header {visibility: hidden;}
    
    .main .block-container {
        padding: 2rem 3rem;
        max-width: 1400px;
    }
    
    /* Headings */
    h1, h2, h3 {
        color: #fafafa !important;
        font-weight: 600 !important;
    }
    
    p, span, label {
        color: #a1a1aa !important;
    }
    
    /* Input fields */
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea {
        background-color: #18181b !important;
        border: 1px solid #27272a !important;
        border-radius: 6px !important;
        color: #fafafa !important;
        padding: 0.625rem 0.75rem !important;
    }
    
    .stTextInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus {
        border-color: #3f3f46 !important;
        box-shadow: 0 0 0 2px rgba(63, 63, 70, 0.3) !important;
    }
    
    .stTextInput > div > div > input::placeholder,
    .stTextArea > div > div > textarea::placeholder {
        color: #52525b !important;
    }
    
    /* Labels */
    .stTextInput > label,
    .stTextArea > label,
    .stSelectbox > label {
        color: #fafafa !important;
        font-size: 0.875rem !important;
        font-weight: 500 !important;
    }
    
    /* Primary button */
    .stButton > button[kind="primary"],
    .stButton > button {
        background-color: #fafafa !important;
        color: #18181b !important;
        border: none !important;
        border-radius: 6px !important;
        font-weight: 500 !important;
        padding: 0.5rem 1rem !important;
        transition: all 0.15s ease !important;
    }
    
    .stButton > button:hover {
        background-color: #e4e4e7 !important;
    }
    
    /* Download button */
    .stDownloadButton > button {
        background-color: transparent !important;
        color: #fafafa !important;
        border: 1px solid #27272a !important;
        border-radius: 6px !important;
    }
    
    .stDownloadButton > button:hover {
        background-color: #27272a !important;
    }
    
    /* Select box */
    .stSelectbox > div > div {
        background-color: #18181b !important;
        border: 1px solid #27272a !important;
        border-radius: 6px !important;
        color: #fafafa !important;
    }
    
    .stSelectbox > div > div > div {
        color: #fafafa !important;
    }
    
    /* Code block */
    .stCode, pre, code {
        background-color: #18181b !important;
        border: 1px solid #27272a !important;
        border-radius: 6px !important;
    }
    
    /* Alerts */
    .stSuccess {
        background-color: rgba(34, 197, 94, 0.1) !important;
        border: 1px solid rgba(34, 197, 94, 0.3) !important;
        color: #22c55e !important;
    }
    
    .stError {
        background-color: rgba(239, 68, 68, 0.1) !important;
        border: 1px solid rgba(239, 68, 68, 0.3) !important;
        color: #ef4444 !important;
    }
    
    .stWarning {
        background-color: rgba(234, 179, 8, 0.1) !important;
        border: 1px solid rgba(234, 179, 8, 0.3) !important;
        color: #eab308 !important;
    }
    
    .stInfo {
        background-color: rgba(59, 130, 246, 0.1) !important;
        border: 1px solid rgba(59, 130, 246, 0.3) !important;
        color: #3b82f6 !important;
    }
    
    /* Expander */
    .streamlit-expanderHeader {
        background-color: #18181b !important;
        border: 1px solid #27272a !important;
        border-radius: 6px !important;
        color: #fafafa !important;
    }
    
    .streamlit-expanderContent {
        background-color: #18181b !important;
        border: 1px solid #27272a !important;
        border-top: none !important;
    }
    
    /* Divider */
    hr {
        border-color: #27272a !important;
    }
    
    /* Caption */
    .stCaption, small {
        color: #71717a !important;
    }
    
    /* Spinner */
    .stSpinner > div > div {
        border-top-color: #fafafa !important;
    }
    
    /* Card style container */
    div[data-testid="column"] > div {
        background-color: #18181b;
        border: 1px solid #27272a;
        border-radius: 8px;
        padding: 1.5rem;
    }
    
    /* Sidebar */
    [data-testid="stSidebar"] {
        background-color: #18181b !important;
        border-right: 1px solid #27272a !important;
    }
    </style>
    """, unsafe_allow_html=True)


# =============================================================================
# DATA CLASSES & PARSING (same as before)
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


def parse_filename(filename: str) -> Optional[Dict]:
    pattern = r'\[.*?\]\s*(.+?)\s*\((\d{4})\)\s*E(\d+)'
    match = re.search(pattern, filename)
    if match:
        return {'series_name': match.group(1).strip(), 'year': match.group(2), 'episode': match.group(3)}
    return None


def extract_resolution(text: str) -> str:
    match = re.search(r'(\d{3,4}p)', text, re.IGNORECASE)
    return match.group(1) if match else '720p'


def detect_hosting(url: str) -> str:
    url_lower = url.lower()
    hosts = {'terabox': 'Terabox', 'mirrored': 'Mirrored', 'mir.cr': 'Mirrored', 'upfiles': 'Upfiles',
             'buzzheavier': 'BuzzHeavier', 'gofile': 'Gofile', 'filemoon': 'FileMoon', 
             'vidhide': 'VidHide', 'krakenfiles': 'Krakenfiles'}
    for key, name in hosts.items():
        if key in url_lower:
            return name
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
                    embed_server_count[ep_num] = embed_server_count.get(ep_num, 0) + 1
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
            info = parse_filename(parts[0].strip())
            if info:
                ep_num = info['episode']
                if ep_num not in episodes:
                    episodes[ep_num] = Episode(number=ep_num, series_name=info['series_name'], year=info['year'])
                embed_server_count[ep_num] = embed_server_count.get(ep_num, 0) + 1
                embed_code = f'<iframe src="{parts[1].strip()}" width="100%" height="100%" frameborder="0" allowfullscreen></iframe>'
                episodes[ep_num].embeds.append(EmbedData(hostname=f"Server {embed_server_count[ep_num]}", embed=embed_code))
    
    if download_section_start > 0:
        download_urls = [l.strip() for l in lines[download_section_start + 1:] if l.strip().startswith('http')]
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
        
        current_episode, current_res_index, current_hosting = None, 0, None
        
        for url in download_urls:
            if 'mirrored' in url.lower():
                ep_match = re.search(r'E(\d+)', url)
                if ep_match:
                    new_ep = ep_match.group(1)
                    if new_ep != current_episode:
                        current_episode, current_res_index, current_hosting = new_ep, 0, 'Mirrored'
                    else:
                        current_res_index += 1
            elif current_episode and current_episode in episode_resolutions:
                resolutions = episode_resolutions[current_episode]
                hosting = detect_hosting(url)
                if hosting != current_hosting:
                    current_hosting, current_res_index = hosting, 0
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
                embed_server_count[ep_num] = embed_server_count.get(ep_num, 0) + 1
                episodes[ep_num].embeds.append(EmbedData(hostname=f"Server {embed_server_count[ep_num]}", embed=embed))
    
    return episodes


def generate_quickfill_js(episode: Episode, subbed: str = "Sub") -> str:
    embeds_js = ',\n'.join([f"""        {{ hostname: "{e.hostname}", embed: '{e.embed.replace("'", "\\'")}' }}""" for e in episode.embeds])
    
    resolutions_js = []
    for res in sorted(episode.downloads.keys(), key=lambda x: int(re.search(r'\d+', x).group())):
        links_js = ',\n'.join([f'                    {{ hosting: "{l.hosting}", url: "{l.url}" }}' for l in episode.downloads[res]])
        resolutions_js.append(f'            {{ pixel: "{res}", links: [\n{links_js}\n                ] }}')
    resolutions_str = ',\n'.join(resolutions_js)
    
    return f'''/**
 * DramaStream Quick-Fill - {episode.series_name} Episode {episode.number}
 */
const EPISODE_DATA = {{
    seriesName: "{episode.series_name}",
    episodeNumber: "{episode.number}",
    subbed: "{subbed}",
    embeds: [
{embeds_js}
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
    const sleep = ms => new Promise(r => setTimeout(r, ms));
    const trigger = el => {{ el.dispatchEvent(new Event('change', {{bubbles:true}})); el.dispatchEvent(new Event('input', {{bubbles:true}})); }};
    
    const setField = (id, val) => {{ const el = document.getElementById(id); if(el) {{ el.value = val; trigger(el); }} }};
    
    const setSeries = async name => {{
        const el = document.getElementById('ero_seri');
        if (!el) return;
        for (const opt of el.options) {{
            if (opt.text.trim().toLowerCase() === name.toLowerCase()) {{
                el.value = opt.value;
                if (window.jQuery) jQuery(el).val(opt.value).trigger('change');
                return;
            }}
        }}
    }};
    
    const setCategory = name => {{
        document.querySelectorAll('#categorychecklist input[type="checkbox"]').forEach(cb => {{
            const label = cb.closest('label');
            if (label && label.textContent.trim().toLowerCase() === name.toLowerCase()) {{
                cb.checked = true; trigger(cb);
            }}
        }});
    }};
    
    const addClone = async container => {{
        const btn = container.querySelector(':scope > .add-clone');
        if (btn) {{ btn.click(); await sleep(DELAY); }}
    }};
    
    const setEmbeds = async embeds => {{
        const container = document.querySelector('#embed-video .rwmb-tab-panel-input-version .rwmb-input');
        if (!container) return;
        for (let i = 0; i < embeds.length; i++) {{
            let clones = container.querySelectorAll(':scope > .rwmb-clone:not(.rwmb-clone-template)');
            while (clones.length <= i) {{ await addClone(container); clones = container.querySelectorAll(':scope > .rwmb-clone:not(.rwmb-clone-template)'); }}
            const clone = clones[i];
            const h = clone.querySelector('input[name*="ab_hostname"]');
            const e = clone.querySelector('textarea[name*="ab_embed"]');
            if (h) {{ h.value = embeds[i].hostname; trigger(h); }}
            if (e) {{ e.value = embeds[i].embed; trigger(e); }}
        }}
    }};
    
    const setDownloads = async downloads => {{
        const epContainer = document.querySelector('#episode-download .rwmb-meta-box > .rwmb-field > .rwmb-input');
        if (!epContainer) return;
        const epClone = epContainer.querySelector(':scope > .rwmb-clone:not(.rwmb-clone-template)');
        if (!epClone) return;
        const epTitle = epClone.querySelector('input[name*="ab_eptitle_ep"]');
        if (epTitle) {{ epTitle.value = downloads.episodeTitle; trigger(epTitle); }}
        const resContainer = epClone.querySelector('.rwmb-group-collapsible > .rwmb-input');
        if (!resContainer) return;
        for (let r = 0; r < downloads.resolutions.length; r++) {{
            const resData = downloads.resolutions[r];
            let resClones = resContainer.querySelectorAll(':scope > .rwmb-clone:not(.rwmb-clone-template)');
            while (resClones.length <= r) {{ await addClone(resContainer); resClones = resContainer.querySelectorAll(':scope > .rwmb-clone:not(.rwmb-clone-template)'); }}
            const resClone = resClones[r];
            const pixel = resClone.querySelector('select[name*="ab_pixel_ep"]');
            if (pixel) {{ pixel.value = resData.pixel; trigger(pixel); }}
            const linkContainer = resClone.querySelector('.rwmb-group-wrapper:not(.rwmb-group-collapsible) > .rwmb-input');
            if (!linkContainer) continue;
            for (let l = 0; l < resData.links.length; l++) {{
                const linkData = resData.links[l];
                let linkClones = linkContainer.querySelectorAll(':scope > .rwmb-clone:not(.rwmb-clone-template)');
                while (linkClones.length <= l) {{ await addClone(linkContainer); linkClones = linkContainer.querySelectorAll(':scope > .rwmb-clone:not(.rwmb-clone-template)'); }}
                const linkClone = linkClones[l];
                const hosting = linkClone.querySelector('select[name*="ab_hostingname_ep"]');
                if (hosting) {{ hosting.value = linkData.hosting; trigger(hosting); }}
                const url = linkClone.querySelector('input[name*="ab_linkurl_ep"]');
                if (url) {{ url.value = linkData.url; trigger(url); }}
            }}
        }}
    }};
    
    console.log('Starting auto-fill...');
    const d = EPISODE_DATA;
    setField('title', `${{d.seriesName}} Episode ${{d.episodeNumber}} Subtitle Indonesia`);
    await sleep(DELAY);
    await setSeries(d.seriesName);
    await sleep(DELAY);
    setCategory(d.seriesName);
    await sleep(DELAY);
    setField('ero_episodebaru', d.episodeNumber);
    await sleep(DELAY);
    setField('ero_subepisode', d.subbed);
    await sleep(DELAY);
    if (d.embeds?.length) await setEmbeds(d.embeds);
    await sleep(DELAY);
    if (d.downloads) await setDownloads(d.downloads);
    console.log('Done! Review and publish.');
}})();
'''


# =============================================================================
# STREAMLIT UI
# =============================================================================

st.set_page_config(page_title="DramaStream Quickfill", page_icon="▶", layout="wide", initial_sidebar_state="collapsed")
inject_custom_css()

if 'generated_scripts' not in st.session_state:
    st.session_state.generated_scripts = {}

# Header
st.markdown("# DramaStream Quickfill")
st.caption("Generate autofill scripts untuk posting episode ke WordPress")
st.markdown("---")

# Layout
col1, col2 = st.columns(2, gap="large")

with col1:
    st.markdown("### Input")
    series_name = st.text_input("Series Name (optional)", placeholder="Auto-detect from URL")
    input_text = st.text_area("Episode Data", height=300, placeholder="<iframe src=...></iframe>\nid | <iframe ...></iframe>\n\nDownload Link\n\nhttps://mirrored.to/...")
    
    if st.button("Generate", type="primary", use_container_width=True):
        if input_text.strip():
            episodes = parse_input(input_text)
            if series_name:
                for ep in episodes.values():
                    ep.series_name = series_name
            if episodes:
                scripts = {ep_num: {'js': generate_quickfill_js(ep), 'embeds': len(ep.embeds), 'resolutions': list(ep.downloads.keys()), 'series': ep.series_name} for ep_num, ep in sorted(episodes.items(), key=lambda x: int(x[0]))}
                st.session_state.generated_scripts = scripts
                st.success(f"Generated {len(scripts)} scripts")
            else:
                st.error("No episodes detected")
        else:
            st.warning("Enter episode data first")

with col2:
    st.markdown("### Output")
    if st.session_state.generated_scripts:
        scripts = st.session_state.generated_scripts
        selected = st.selectbox("Episode", [f"E{ep}" for ep in scripts.keys()])
        ep_num = selected.replace("E", "") if selected else None
        
        if ep_num and ep_num in scripts:
            d = scripts[ep_num]
            st.caption(f"**{d['series']}** · {d['embeds']} embeds · {', '.join(d['resolutions'])}")
            st.code(d['js'], language='javascript')
            
            zip_buf = io.BytesIO()
            with zipfile.ZipFile(zip_buf, 'w', zipfile.ZIP_DEFLATED) as zf:
                for n, data in scripts.items():
                    zf.writestr(f"quickfill_E{n}.js", data['js'])
            st.download_button("Download All (ZIP)", zip_buf.getvalue(), "quickfill.zip", "application/zip", use_container_width=True)
    else:
        st.info("Generate scripts to see output")

with st.expander("Help"):
    st.markdown("""
**Embed formats:** `<iframe>`, `id | <iframe>`, `[Tag] Series (Year) EXXX.mp4` + iframe

**Download:** After "Download Link", Mirrored URLs define episodes/resolutions. Other hosts follow order.
""")
