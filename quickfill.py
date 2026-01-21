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
        background-color: #6366f1 !important;
        color: #ffffff !important;
        border: none !important;
        border-radius: 6px !important;
        font-weight: 500 !important;
        padding: 0.5rem 1rem !important;
        transition: all 0.15s ease !important;
    }
    
    .stButton > button:hover {
        background-color: #4f46e5 !important;
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
    
    /* Code block - fixed height with scroll */
    .stCode, pre, code {
        background-color: #18181b !important;
        border: 1px solid #27272a !important;
        border-radius: 6px !important;
    }
    
    .stCode {
        max-height: 350px !important;
        overflow-y: auto !important;
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
    season: str = ""
    embeds: List[EmbedData] = field(default_factory=list)
    downloads: Dict[str, List[DownloadLink]] = field(default_factory=dict)


# Embed hostname configuration - priority order (first = highest priority)
EMBED_HOST_CONFIG = [
    {'pattern': 'nuna.upns.pro', 'name': 'Upnshare'},
    {'pattern': 'short.icu', 'name': 'HydraX'},
    {'pattern': 'hqq.to', 'name': 'LuluTV'},
    {'pattern': 'nuna.p2pstream.vip', 'name': 'StreamP2P'},
    {'pattern': 'veev.to', 'name': 'Veev'},
    {'pattern': 'bysetayico.com', 'name': 'FileMoon'},
]


def get_embed_hostname(iframe: str) -> str:
    src_match = re.search(r'src=["\']([^"\']+)["\']', iframe)
    if src_match:
        url = src_match.group(1).lower()
        for config in EMBED_HOST_CONFIG:
            if config['pattern'] in url:
                return config['name']
    return 'Other'


def get_embed_priority(iframe: str) -> int:
    src_match = re.search(r'src=["\']([^"\']+)["\']', iframe)
    if src_match:
        url = src_match.group(1).lower()
        for idx, config in enumerate(EMBED_HOST_CONFIG):
            if config['pattern'] in url:
                return idx
    return 999


def parse_filename(filename: str) -> Optional[Dict]:
    """Parse filename - supports multiple formats"""
    # Format 1: [Tag] Series Name (Year) EXXX
    pattern1 = r'\[.*?\]\s*(.+?)\s*\((\d{4})\)\s*E(\d+)'
    match = re.search(pattern1, filename)
    if match:
        return {'series_name': match.group(1).strip(), 'year': match.group(2), 'episode': match.group(3), 'season': None}
    
    # Format 2: [Tag] Series.SxxExx or [Tag] Series SxxExx (no year)
    pattern2 = r'\[.*?\]\s*(.+?)[.\s]S(\d+)E(\d+)'
    match = re.search(pattern2, filename, re.IGNORECASE)
    if match:
        series = match.group(1).strip().replace('.', ' ').replace('_', ' ')
        return {'series_name': series, 'year': '', 'episode': match.group(3), 'season': match.group(2)}
    
    # Format 3: Just Exx anywhere - [Tag] Series.Name.Year.Exx
    pattern3 = r'\[.*?\]\s*(.+?)[.\s]E(\d+)'
    match = re.search(pattern3, filename)
    if match:
        series = match.group(1).strip().replace('.', ' ').replace('_', ' ')
        series = re.sub(r'\s+\d{4}\s*$', '', series).strip()
        return {'series_name': series, 'year': '', 'episode': match.group(2), 'season': None}
    
    return None


def extract_resolution(text: str) -> str:
    match = re.search(r'(\d{3,4}p)', text, re.IGNORECASE)
    return match.group(1) if match else '720p'


def parse_movie_filename(filename: str) -> Optional[Dict]:
    """Parse movie filename: [tag] Title.Year.Res.ext -> returns title, year, resolution"""
    # Pattern 1: [tag] Title.Year.Resolution.ext (dots)
    pattern1 = r'\[.*?\]\s*(.+?)\.(\d{4})\.(\d{3,4})p'
    match = re.search(pattern1, filename, re.IGNORECASE)
    if match:
        title = match.group(1).strip().replace('.', ' ').replace('_', ' ')
        return {'title': title, 'year': match.group(2), 'resolution': match.group(3) + 'p'}
    
    # Pattern 2: [tag] Title Year.Resolution.ext (spaces in title)
    pattern2 = r'\[.*?\]\s*(.+?)\s+(\d{4})\.(\d{3,4})p'
    match = re.search(pattern2, filename, re.IGNORECASE)
    if match:
        title = match.group(1).strip().replace('.', ' ').replace('_', ' ')
        return {'title': title, 'year': match.group(2), 'resolution': match.group(3) + 'p'}
    
    # Pattern 3: [tag]_Title_Year.Resolution.ext (underscores)
    pattern3 = r'\[.*?\]_(.+?)_(\d{4})\.(\d{3,4})p'
    match = re.search(pattern3, filename, re.IGNORECASE)
    if match:
        title = match.group(1).strip().replace('.', ' ').replace('_', ' ')
        return {'title': title, 'year': match.group(2), 'resolution': match.group(3) + 'p'}
    
    return None


def parse_movie_from_url(url: str) -> Optional[Dict]:
    """Parse movie info from URL path like 'nunadrama-roofman-2025-1080p'"""
    path_match = re.search(r'/([^/]+)(?:\.[^/]+)?$', url)
    if not path_match:
        return None
    path = path_match.group(1).lower()
    if re.search(r'-[se]\d+', path):
        return None
    movie_match = re.search(r'^[^-]+-(.+?)-(\d{4})-(\d{3,4})p?$', path)
    if movie_match:
        title = movie_match.group(1).replace('-', ' ').title()
        return {'title': title, 'year': movie_match.group(2), 'resolution': movie_match.group(3) + 'p'}
    return None


def normalize_movie_title(title: str) -> str:
    return title.lower().replace('.', ' ').replace('-', ' ').replace('_', ' ').strip()


def is_movie_format(text: str) -> bool:
    """Check if input is movie format (no Exx pattern in header lines)"""
    lines = text.strip().split('\n')
    header_lines = []
    for line in lines:
        line = line.strip()
        if not line:
            continue
        if line.startswith('<iframe'):
            break
        if line.startswith('['):
            header_lines.append(line)
        if len(header_lines) >= 3:
            break
    for line in header_lines:
        if re.search(r'[.\s_]E\d+|S\d+E\d+', line, re.IGNORECASE):
            return False
    return len(header_lines) > 0

def parse_url_path(url: str) -> Optional[Dict]:
    """Parse episode info from URL path"""
    path_match = re.search(r'/([^/]+)(?:\.[^/]+)?$', url)
    if not path_match:
        return None
    
    path = path_match.group(1).lower()
    
    # Try SxxExx format first
    sxxexx_match = re.search(r'-s(\d{1,2})e(\d{1,3})(?:-|$)', path)
    if sxxexx_match:
        season = sxxexx_match.group(1).zfill(2)
        episode = sxxexx_match.group(2).zfill(2)
    else:
        # Try just Exx format
        ep_match = re.search(r'-e(\d{1,3})(?:-|$)', path)
        if not ep_match:
            return None
        season = None
        episode = ep_match.group(1).zfill(2)
    
    res_match = re.search(r'-(360|480|720|1080|2160)p?(?:-|$)', path)
    resolution = res_match.group(1) + 'p' if res_match else '720p'
    series_match = re.search(r'^[^/]*?-(.+?)(?:-\d{4})?-(?:s\d+)?e\d+', path)
    series_name = series_match.group(1).replace('-', ' ').title() if series_match else 'Unknown'
    
    return {'episode': episode, 'resolution': resolution, 'series_name': series_name, 'season': season}


def detect_hosting(url: str) -> str:
    url_lower = url.lower()
    hosts = {'terabox': 'Terabox', 'mirrored': 'Mirrored', 'mir.cr': 'Mirrored', 'upfiles': 'Upfiles',
             'buzzheavier': 'BuzzHeavier', 'gofile': 'Gofile', 'filemoon': 'FileMoon', 
             'vidhide': 'VidHide', 'krakenfiles': 'Krakenfiles', 'vikingfile': 'Vikingfile', 'veev.to': 'Veev',
             'bysetayico': 'FileMoon', 'doodstream': 'Doodstream', 'streamtape': 'StreamTape'}
    for key, name in hosts.items():
        if key in url_lower:
            return name
    return 'Other'


def parse_movie_input(text: str) -> Dict[str, Episode]:
    """Parse movie input format and return movies as episodes (keyed by normalized title)"""
    movies: Dict[str, Episode] = {}
    lines = text.strip().split('\n')
    
    download_section_start = -1
    for i, line in enumerate(lines):
        if line.strip().lower() == 'download link':
            download_section_start = i
            break
    
    embed_lines = lines[:download_section_start] if download_section_start > 0 else lines
    
    # Phase 1: Collect movie headers
    movie_list = []
    for line in embed_lines:
        line = line.strip()
        if not line:
            continue
        if line.startswith('<iframe'):
            break
        if line.startswith('['):
            movie_info = parse_movie_filename(line)
            if movie_info:
                movie_list.append(movie_info)
                key = normalize_movie_title(movie_info['title'])
                if key not in movies:
                    movies[key] = Episode(number='HD', series_name=movie_info['title'], year=movie_info['year'], season=None)
    
    # Phase 2: Collect standalone iframes and bysetayico embeds
    standalone_iframes = []
    byse_embeds = {}
    
    for line in embed_lines:
        line = line.strip()
        if line.startswith('<iframe'):
            src_match = re.search(r'src=["\']([^"\']+)["\']', line)
            if src_match:
                url = src_match.group(1)
                if 'bysetayico' in url:
                    movie_info = parse_movie_from_url(url)
                    if movie_info:
                        key = normalize_movie_title(movie_info['title'])
                        res_num = int(re.search(r'\d+', movie_info['resolution']).group())
                        if key not in byse_embeds:
                            byse_embeds[key] = {}
                        if res_num not in byse_embeds[key] or res_num > max(byse_embeds[key].keys(), default=0):
                            byse_embeds[key][res_num] = line
                        continue
            standalone_iframes.append(line)
    
    # Phase 3: Assign standalone iframes positionally
    if movie_list and standalone_iframes:
        num_movies = len(movie_list)
        server_count = {normalize_movie_title(m['title']): 0 for m in movie_list}
        for idx, iframe in enumerate(standalone_iframes):
            movie_idx = idx % num_movies
            movie_info = movie_list[movie_idx]
            key = normalize_movie_title(movie_info['title'])
            if key in movies:
                hostname = get_embed_hostname(iframe)
                movies[key].embeds.append(EmbedData(hostname=hostname, embed=iframe))
    
    # Phase 4: Add highest resolution bysetayico embeds
    for key, res_dict in byse_embeds.items():
        if res_dict and key in movies:
            highest_res = max(res_dict.keys())
            iframe = res_dict[highest_res]
            hostname = get_embed_hostname(iframe)
            movies[key].embeds.append(EmbedData(hostname=hostname, embed=iframe))
    
    # Sort embeds by priority
    for key in movies:
        movies[key].embeds.sort(key=lambda e: get_embed_priority(e.embed))
    
    # Phase 5: Parse downloads
    if download_section_start > 0:
        download_lines = lines[download_section_start + 1:]
        for line in download_lines:
            line = line.strip()
            if not line:
                continue
            movie_info, url, hosting = None, None, None
            
            if 'mirrored' in line.lower() and line.startswith('http'):
                url, hosting = line, 'Mirrored'
                fn_match = re.search(r'/([^/]+\.mp4)', line)
                if fn_match:
                    movie_info = parse_movie_filename(fn_match.group(1))
            elif line.startswith('[url='):
                bbcode_match = re.match(r'\[url=([^\]]+)\](.+?)\[/url\]', line, re.IGNORECASE)
                if bbcode_match:
                    url, filename = bbcode_match.group(1), bbcode_match.group(2)
                    movie_info = parse_movie_filename(filename)
                    hosting = detect_hosting(url)
            elif line.startswith('http'):
                movie_info = parse_movie_from_url(line)
                if movie_info:
                    url, hosting = line, detect_hosting(line)
            
            if movie_info and url and hosting:
                key = normalize_movie_title(movie_info['title'])
                res = movie_info['resolution']
                if key not in movies:
                    movies[key] = Episode(number='HD', series_name=movie_info['title'], year=movie_info['year'], season=None)
                if res not in movies[key].downloads:
                    movies[key].downloads[res] = []
                movies[key].downloads[res].append(DownloadLink(hosting=hosting, url=url, resolution=res))
        
        # Parse Terabox links positionally (no filename info in URL)
        terabox_links = [line.strip() for line in download_lines if 'terabox' in line.lower() and line.strip().startswith('http')]
        if terabox_links and movie_list:
            resolutions = ['720p', '1080p']
            num_movies = len(movie_list)
            for idx, url in enumerate(terabox_links):
                movie_idx = idx // 2
                res_idx = idx % 2
                if movie_idx < num_movies:
                    movie_info = movie_list[movie_idx]
                    key = normalize_movie_title(movie_info['title'])
                    res = resolutions[res_idx]
                    if key in movies:
                        if res not in movies[key].downloads:
                            movies[key].downloads[res] = []
                        movies[key].downloads[res].append(DownloadLink(hosting='Terabox', url=url, resolution=res))
    
    return movies


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
    veev_embeds = {}  # ep_num -> {resolution_num: iframe_code}
    url_embeds = {}   # ep_num -> {resolution_num: iframe_code} for URL-parsed embeds
    
    # Collect series headers (consecutive filenames at start, before iframes) for positional mapping
    series_header_list = []
    for line in embed_lines:
        line = line.strip()
        if not line:
            continue
        if line.startswith('<iframe'):
            break
        if line.startswith('[') and '|' not in line:
            info = parse_filename(line)
            if info:
                series_header_list.append(info)
                ep_num = info['episode']
                if ep_num not in episodes:
                    episodes[ep_num] = Episode(number=ep_num, series_name=info['series_name'], year=info.get('year', ''), season=info.get('season', ''))
    
    i = 0
    while i < len(embed_lines):
        line = embed_lines[i].strip()
        if line.startswith('[') and '|' not in line and ' - <iframe' not in line:
            info = parse_filename(line)
            if info and i + 1 < len(embed_lines):
                next_line = embed_lines[i + 1].strip()
                if next_line.startswith('<iframe'):
                    ep_num = info['episode']
                    if ep_num not in episodes:
                        episodes[ep_num] = Episode(number=ep_num, series_name=info['series_name'], year=info.get('year', ''), season=info.get('season', ''))
                    hostname = get_embed_hostname(next_line)
                    episodes[ep_num].embeds.append(EmbedData(hostname=hostname, embed=next_line))
                    i += 2
                    continue
        elif line.startswith('<iframe'):
            # Try to parse episode info from URL
            src_match = re.search(r'src=["\']([^"\']+)["\']', line)
            if src_match:
                url = src_match.group(1)
                url_info = parse_url_path(url)
                if url_info:
                    ep_num = url_info['episode']
                    res = url_info['resolution']
                    res_num = int(re.search(r'\d+', res).group())
                    if ep_num not in url_embeds:
                        url_embeds[ep_num] = {}
                    if res_num not in url_embeds[ep_num] or res_num > max(url_embeds[ep_num].keys(), default=0):
                        url_embeds[ep_num][res_num] = line
                else:
                    standalone_embeds.append(line)
            else:
                standalone_embeds.append(line)
        elif '|' in line and '<iframe' in line:
            parts = line.split('|', 1)
            iframe_part = parts[1].strip()
            if iframe_part.startswith('<iframe'):
                standalone_embeds.append(iframe_part)
        # Handle "filename - <iframe..." format
        elif ' - <iframe' in line:
            parts = line.split(' - <iframe', 1)
            filename = parts[0].strip()
            iframe_code = '<iframe' + parts[1]
            info = parse_filename(filename)
            if info:
                ep_num = info['episode']
                if ep_num not in episodes:
                    episodes[ep_num] = Episode(number=ep_num, series_name=info['series_name'], year=info.get('year', ''), season=info.get('season', ''))
                # For veev embeds, track by resolution and only keep highest
                if 'veev.to' in iframe_code:
                    res = extract_resolution(filename)
                    res_num = int(re.search(r'\d+', res).group())
                    if ep_num not in veev_embeds:
                        veev_embeds[ep_num] = {}
                    if res_num not in veev_embeds[ep_num] or res_num > max(veev_embeds[ep_num].keys(), default=0):
                        veev_embeds[ep_num][res_num] = iframe_code
                else:
                    hostname = get_embed_hostname(iframe_code)
                    episodes[ep_num].embeds.append(EmbedData(hostname=hostname, embed=iframe_code))
        i += 1
    
    # Add highest resolution veev embeds
    for ep_num, res_dict in veev_embeds.items():
        if res_dict and ep_num in episodes:
            highest_res = max(res_dict.keys())
            iframe_code = res_dict[highest_res]
            hostname = get_embed_hostname(iframe_code)
            episodes[ep_num].embeds.append(EmbedData(hostname=hostname, embed=iframe_code))
    
    # Add highest resolution URL-parsed embeds
    for ep_num, res_dict in url_embeds.items():
        if res_dict:
            highest_res = max(res_dict.keys())
            iframe_code = res_dict[highest_res]
            if ep_num not in episodes:
                src_match = re.search(r'src=["\']([^"\']+)["\']', iframe_code)
                url_info = parse_url_path(src_match.group(1)) if src_match else None
                episodes[ep_num] = Episode(number=ep_num, series_name=url_info['series_name'] if url_info else 'Unknown', year='', season='')
            hostname = get_embed_hostname(iframe_code)
            episodes[ep_num].embeds.append(EmbedData(hostname=hostname, embed=iframe_code))
    
    # Assign standalone iframes positionally if we have series headers
    if series_header_list and standalone_embeds:
        num_episodes = len(series_header_list)
        for idx, iframe in enumerate(standalone_embeds):
            ep_idx = idx % num_episodes
            ep_num = series_header_list[ep_idx]['episode']
            if ep_num in episodes:
                hostname = get_embed_hostname(iframe)
                episodes[ep_num].embeds.append(EmbedData(hostname=hostname, embed=iframe))
        standalone_embeds = []

    for line in embed_lines:
        line = line.strip()
        if line.startswith('[') and '|' in line:
            parts = line.split('|', 1)
            info = parse_filename(parts[0].strip())
            url_or_iframe = parts[1].strip()
            if info:
                ep_num = info['episode']
                if ep_num not in episodes:
                    episodes[ep_num] = Episode(number=ep_num, series_name=info['series_name'], year=info.get('year', ''), season=info.get('season', ''))
                hostname = get_embed_hostname(iframe_code)
                # Check if it's already an iframe or just a URL
                if url_or_iframe.startswith('<iframe'):
                    embed_code = url_or_iframe
                else:
                    embed_code = f'<iframe src="{url_or_iframe}" width="100%" height="100%" frameborder="0" allowfullscreen></iframe>'
                hostname = get_embed_hostname(embed_code)
                episodes[ep_num].embeds.append(EmbedData(hostname=hostname, embed=embed_code))
    
    if download_section_start > 0:
        download_lines = lines[download_section_start + 1:]
        download_urls = []
        episode_resolutions = {}
        
        for line in download_lines:
            line = line.strip()
            if not line:
                continue
            
            # Direct URL - try to parse episode info from path
            if line.startswith('http'):
                url_info = parse_url_path(line)
                if url_info:
                    ep_num = url_info['episode']
                    res = url_info['resolution']
                    hosting = detect_hosting(line)
                    if ep_num not in episodes:
                        episodes[ep_num] = Episode(number=ep_num, series_name=url_info['series_name'], year='', season='')
                    if res not in episodes[ep_num].downloads:
                        episodes[ep_num].downloads[res] = []
                    episodes[ep_num].downloads[res].append(DownloadLink(hosting=hosting, url=line, resolution=res))
                else:
                    download_urls.append(line)
            
            # BBCode [url=URL]filename[/url]
            elif line.startswith('[url='):
                bbcode_match = re.match(r'\[url=([^\]]+)\](.+?)\[/url\]', line, re.IGNORECASE)
                if bbcode_match:
                    url, filename = bbcode_match.group(1), bbcode_match.group(2)
                    ep_match = re.search(r'S\d+E(\d+)|E(\d+)', filename, re.IGNORECASE)
                    res = extract_resolution(filename)
                    if ep_match:
                        ep_num = ep_match.group(1) or ep_match.group(2)
                        hosting = detect_hosting(url)
                        if ep_num not in episodes:
                            info = parse_filename(filename)
                            episodes[ep_num] = Episode(number=ep_num, series_name=info['series_name'] if info else 'Unknown', year='', season=info.get('season', '') if info else '')
                        if res not in episodes[ep_num].downloads:
                            episodes[ep_num].downloads[res] = []
                        episodes[ep_num].downloads[res].append(DownloadLink(hosting=hosting, url=url, resolution=res))
            
            # filename - URL
            elif ' - http' in line:
                parts = line.split(' - http', 1)
                filename, url = parts[0].strip(), 'http' + parts[1].strip()
                ep_match = re.search(r'S\d+E(\d+)|E(\d+)', filename, re.IGNORECASE)
                res = extract_resolution(filename)
                if ep_match:
                    ep_num = ep_match.group(1) or ep_match.group(2)
                    hosting = detect_hosting(url)
                    if ep_num not in episodes:
                        info = parse_filename(filename)
                        episodes[ep_num] = Episode(number=ep_num, series_name=info['series_name'] if info else 'Unknown', year='', season=info.get('season', '') if info else '')
                    if res not in episodes[ep_num].downloads:
                        episodes[ep_num].downloads[res] = []
                    episodes[ep_num].downloads[res].append(DownloadLink(hosting=hosting, url=url, resolution=res))
        
        # Parse Mirrored links for episode/resolution structure
        for url in download_urls:
            if 'mirrored' in url.lower():
                # Require delimiter before E to avoid matching URL hashes
                ep_match = re.search(r'[._\s]S(\d+)E(\d+)|[._\s]E(\d+)', url, re.IGNORECASE)
                res = extract_resolution(url)
                if ep_match:
                    ep_num = ep_match.group(2) or ep_match.group(3)
                    if ep_num not in episodes:
                        episodes[ep_num] = Episode(number=ep_num, series_name="Unknown", year="", season="")
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
                hostname = get_embed_hostname(embed)
                episodes[ep_num].embeds.append(EmbedData(hostname=hostname, embed=embed))
    
    # Sort embeds by priority
    for ep in episodes.values():
        ep.embeds.sort(key=lambda x: get_embed_priority(x.embed))
    
    return episodes


def generate_quickfill_js(episode: Episode, subbed: str = "Sub") -> str:
    embeds_js = ',\n'.join([f"""        {{ hostname: "{e.hostname}", embed: '{e.embed.replace("'", "\\'")}' }}""" for e in episode.embeds])
    
    resolutions_js = []
    for res in sorted(episode.downloads.keys(), key=lambda x: int(re.search(r'\d+', x).group())):
        links_js = ',\n'.join([f'                    {{ hosting: "{l.hosting}", url: "{l.url}" }}' for l in episode.downloads[res]])
        resolutions_js.append(f'            {{ pixel: "{res}", links: [\n{links_js}\n                ] }}')
    resolutions_str = ',\n'.join(resolutions_js)
    
    # Build title with season if available (strip leading zeros for display)
    season_display = episode.season.lstrip('0') or episode.season if episode.season else ""
    ep_display = episode.number.lstrip('0') or episode.number
    season_str = f" Season {season_display}" if season_display else ""
    
    # For movies (HD), omit Episode part from title
    if episode.number == 'HD':
        ep_title = f"{episode.series_name}{season_str}"
        download_title = "HD"
    else:
        ep_title = f"{episode.series_name}{season_str} Episode {ep_display}"
        download_title = f"Episode {episode.number}"
    
    return f'''/**
 * DramaStream Quick-Fill - {ep_title}
 */
const EPISODE_DATA = {{
    seriesName: "{episode.series_name}",
    seasonNumber: "{episode.season}",
    episodeNumber: "{episode.number}",
    subbed: "{subbed}",
    embeds: [
{embeds_js}
    ],
    downloads: {{
        episodeTitle: "{download_title}",
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
    const seasonNum = (d.seasonNumber && d.seasonNumber !== 'None') ? d.seasonNumber.replace(/^0+/, '') || d.seasonNumber : '';
    const epNum = d.episodeNumber.replace(/^0+/, '') || d.episodeNumber;
    const seasonPart = seasonNum ? ` Season ${{seasonNum}}` : '';
    // For movies (HD), don't add Episode part
    const episodePart = (epNum === 'HD') ? '' : ` Episode ${{epNum}}`;
    setField('title', `${{d.seriesName}}${{seasonPart}}${{episodePart}} Subtitle Indonesia`);
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
            # Detect if movie or series format
            is_movie = is_movie_format(input_text)
            if is_movie:
                episodes = parse_movie_input(input_text)
            else:
                episodes = parse_input(input_text)
            
            if series_name:
                for ep in episodes.values():
                    ep.series_name = series_name
            if episodes:
                # Sort keys appropriately
                if is_movie:
                    sorted_items = sorted(episodes.items())
                    scripts = {key: {'js': generate_quickfill_js(ep), 'embeds': len(ep.embeds), 'resolutions': list(ep.downloads.keys()), 'series': ep.series_name, 'is_movie': True} for key, ep in sorted_items}
                else:
                    sorted_items = sorted(episodes.items(), key=lambda x: int(x[0]) if x[0].isdigit() else 0)
                    scripts = {ep_num: {'js': generate_quickfill_js(ep), 'embeds': len(ep.embeds), 'resolutions': list(ep.downloads.keys()), 'series': ep.series_name, 'is_movie': False} for ep_num, ep in sorted_items}
                st.session_state.generated_scripts = scripts
                item_type = "movie" if is_movie else "episode"
                st.success(f"Generated {len(scripts)} {item_type} scripts")
            else:
                st.error("No episodes/movies detected")
        else:
            st.warning("Enter episode data first")

with col2:
    st.markdown("### Output")
    if st.session_state.generated_scripts:
        scripts = st.session_state.generated_scripts
        # Check if it's movie format
        first_script = next(iter(scripts.values()), {})
        is_movie = first_script.get('is_movie', False)
        
        # Create display options based on type
        if is_movie:
            episode_options = list(scripts.keys())  # Just movie titles
            selected = st.selectbox("Movie", episode_options)
            key = selected
        else:
            episode_options = [f"{scripts[ep]['series']} E{ep}" for ep in scripts.keys()]
            selected = st.selectbox("Episode", episode_options)
            key = selected.split(" E")[-1] if selected else None
        
        if key and key in scripts:
            d = scripts[key]
            st.caption(f"**{d['series']}** · {d['embeds']} embeds · {', '.join(d['resolutions'])}")
            
            # Use container with height limit via CSS
            st.markdown("""<style>.code-container div[data-testid="stCode"] { max-height: 300px; overflow-y: auto; }</style>""", unsafe_allow_html=True)
            with st.container():
                st.markdown('<div class="code-container">', unsafe_allow_html=True)
                st.code(d['js'], language='javascript')
                st.markdown('</div>', unsafe_allow_html=True)
            
            zip_buf = io.BytesIO()
            with zipfile.ZipFile(zip_buf, 'w', zipfile.ZIP_DEFLATED) as zf:
                for n, data in scripts.items():
                    if is_movie:
                        safe_title = re.sub(r'[^\w\s-]', '', n).strip().replace(' ', '_')
                        zf.writestr(f"quickfill_{safe_title}.js", data['js'])
                    else:
                        zf.writestr(f"quickfill_E{n}.js", data['js'])
            st.download_button("Download All (ZIP)", zip_buf.getvalue(), "quickfill.zip", "application/zip", use_container_width=True)
    else:
        st.info("Generate scripts to see output")

with st.expander("Help"):
    st.markdown("""
**Embed formats:** `&lt;iframe&gt;`, `id | &lt;iframe&gt;`, `[Tag] Series (Year) EXXX.mp4` + iframe

**Download:** After "Download Link", Mirrored URLs define episodes/resolutions. Other hosts follow order.
""", unsafe_allow_html=True)
