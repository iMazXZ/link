"""
DramaStream Quickfill Generator - Streamlit Version
====================================================
Deploy ke share.streamlit.io untuk akses web.

Jalankan lokal: streamlit run streamlit_quickfill.py
"""

import streamlit as st
import re
from dataclasses import dataclass, field
from typing import List, Dict, Optional
import zipfile
import io

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
    """Parse filename like [LayarAsia] I Live Alone (2025) E625.720p.mp4"""
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
    """Extract resolution from text"""
    match = re.search(r'(\d{3,4}p)', text, re.IGNORECASE)
    return match.group(1) if match else '720p'


def detect_hosting(url: str) -> str:
    """Detect hosting name from URL"""
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
    """Parse the full input text and return episodes dict"""
    episodes: Dict[str, Episode] = {}
    
    lines = text.strip().split('\n')
    
    # Find separator "Download Link"
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
    
    # ========== PARSE EMBED SECTION ==========
    embed_lines = lines[:download_section_start] if download_section_start > 0 else lines
    embed_server_count = {}
    
    # First pass: filename + iframe
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
                        episodes[ep_num] = Episode(
                            number=ep_num,
                            series_name=info['series_name'],
                            year=info['year']
                        )
                    if ep_num not in embed_server_count:
                        embed_server_count[ep_num] = 0
                    embed_server_count[ep_num] += 1
                    episodes[ep_num].embeds.append(EmbedData(
                        hostname=f"Server {embed_server_count[ep_num]}",
                        embed=next_line
                    ))
                    i += 2
                    continue
        i += 1
    
    # Second pass: filename|url
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
                    episodes[ep_num] = Episode(
                        number=ep_num,
                        series_name=info['series_name'],
                        year=info['year']
                    )
                if ep_num not in embed_server_count:
                    embed_server_count[ep_num] = 0
                embed_server_count[ep_num] += 1
                embed_code = f'<iframe src="{url}" width="100%" height="100%" frameborder="0" allowfullscreen></iframe>'
                episodes[ep_num].embeds.append(EmbedData(
                    hostname=f"Server {embed_server_count[ep_num]}",
                    embed=embed_code
                ))
    
    # ========== PARSE DOWNLOAD SECTION ==========
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
                    episodes[ep_num].downloads[res].append(
                        DownloadLink(hosting='Mirrored', url=url, resolution=res)
                    )
        
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
                        episodes[current_episode].downloads[res].append(
                            DownloadLink(hosting=hosting, url=url, resolution=res)
                        )
                        current_res_index += 1
    
    return episodes


def generate_quickfill_js(episode: Episode, subbed: str = "Sub") -> str:
    """Generate JavaScript quickfill code for an episode"""
    
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
    page_title="DramaStream Quickfill Generator",
    page_icon="🎬",
    layout="wide"
)

st.title("🎬 DramaStream Quickfill Generator")
st.caption("Generate script autofill untuk posting episode ke WordPress")

# Session state
if 'generated_scripts' not in st.session_state:
    st.session_state.generated_scripts = {}
if 'selected_episode' not in st.session_state:
    st.session_state.selected_episode = None

# Sidebar settings
st.sidebar.header("⚙️ Pengaturan")
series_name = st.sidebar.text_input("Nama Series", placeholder="Contoh: I Live Alone")
st.sidebar.caption("Kosongkan untuk auto-detect dari filename")

# Main layout
col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("📝 Input Data")
    
    input_text = st.text_area(
        "Paste data episode:",
        height=400,
        placeholder="""[LayarAsia] Series Name (2025) E001.720p.mp4
<iframe src="https://server1/xxx" ...></iframe>

[LayarAsia] Series Name (2025) E001.720p.mp4|https://short.icu/xxx

Download Link

https://www.mirrored.to/.../E001.360p.mp4_links
https://www.mirrored.to/.../E001.720p.mp4_links
https://1024terabox.com/s/xxx
https://1024terabox.com/s/xxx
..."""
    )
    
    if st.button("🚀 Generate Scripts", type="primary", use_container_width=True):
        if input_text.strip():
            with st.spinner("Parsing data..."):
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
                    st.success(f"✅ Generated {len(scripts)} episode scripts!")
                else:
                    st.error("❌ Tidak ada episode yang terdeteksi!")
        else:
            st.warning("⚠️ Paste data episode terlebih dahulu")

with col2:
    st.subheader("📋 Output Scripts")
    
    if st.session_state.generated_scripts:
        scripts = st.session_state.generated_scripts
        
        # Episode selector
        episode_options = [f"Episode {ep}" for ep in sorted(scripts.keys(), key=int)]
        selected_label = st.selectbox("Pilih Episode:", episode_options)
        selected_ep = selected_label.replace("Episode ", "") if selected_label else None
        
        if selected_ep and selected_ep in scripts:
            script_data = scripts[selected_ep]
            
            # Info
            st.info(f"**Series:** {script_data['series']} | **Embeds:** {script_data['embeds']} | **Resolutions:** {', '.join(script_data['resolutions'])}")
            
            # Code output
            st.code(script_data['js'], language='javascript')
            
            # Copy instruction
            st.caption("👆 Copy script di atas, lalu paste ke Console browser (F12) di halaman WordPress Add New Post")
        
        st.divider()
        
        # Download all as ZIP
        if st.button("📥 Download Semua (ZIP)", use_container_width=True):
            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
                for ep_num, data in scripts.items():
                    zf.writestr(f"quickfill_E{ep_num}.js", data['js'])
            
            st.download_button(
                label="💾 Simpan ZIP",
                data=zip_buffer.getvalue(),
                file_name="quickfill_scripts.zip",
                mime="application/zip",
                use_container_width=True
            )
    else:
        st.info("Generate script terlebih dahulu untuk melihat output")

# Help section
with st.expander("📖 Panduan Format Input"):
    st.markdown("""
### Format Embed
```
[LayarAsia] Series Name (2025) E001.720p.mp4
<iframe src="https://server1/xxx" width="100%" height="100%" frameborder="0" allowfullscreen></iframe>

[LayarAsia] Series Name (2025) E001.720p.mp4|https://short.icu/xxx
```

### Format Download (setelah "Download Link")
```
Download Link

https://www.mirrored.to/.../E001.360p.mp4_links  ← anchor (punya episode + resolusi)
https://www.mirrored.to/.../E001.720p.mp4_links
https://1024terabox.com/s/xxx                    ← ikut urutan resolusi
https://1024terabox.com/s/xxx
https://upfiles.com/xxx                          ← ikut urutan resolusi
https://upfiles.com/xxx
```

### Aturan Penting
- **Mirrored** harus ada episode (E001) dan resolusi (360p/720p/1080p) di URL
- Hosting lain mengikuti urutan resolusi dari Mirrored
- Setiap hosting harus punya link per resolusi yang sama
""")
