"""
DramaStream Quickfill Generator - Streamlit Version
====================================================
Shadcn-inspired Dark Dashboard UI
"""

import streamlit as st
import streamlit.components.v1 as components
import re
import requests
import time
import json
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Set
import zipfile
import io

# =============================================================================
# LINK SHORTENING
# =============================================================================

DEFAULT_OUO_API_KEY = "8pHuHRq5"
DEFAULT_SAFELINKEARN_API_TOKEN = "b7e08e60216a7e4af740e7cd46e348a7e6fcea17"
DEFAULT_SAFELINKU_API_TOKEN = "3e3844f4c831f2bc46cfdd15e8d8c370b2c39c2b"

@st.cache_data(show_spinner=False, ttl=3600)
def shorten_url_cached(provider: str, api_key: str, url: str) -> str:
    """Shorten URL using selected provider (cached)."""
    if not api_key:
        return url

    provider = (provider or "").strip().lower()

    def normalize_shortened(value: str) -> str:
        """Normalize provider output; return empty string when not a URL."""
        if not value:
            return ""
        value = value.strip().replace("\\/", "/")
        if value.startswith('"') and value.endswith('"'):
            try:
                value = json.loads(value)
            except Exception:
                pass
            value = str(value).strip().replace("\\/", "/")
        if value.startswith("http://") or value.startswith("https://"):
            return value
        return ""

    try:
        if provider == "safelinku":
            response = requests.post(
                "https://safelinku.com/api/v1/links",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                },
                json={"url": url},
                timeout=10,
            )
            if response.status_code in (200, 201):
                time.sleep(1.05)  # 60 requests/minute rate limit
                try:
                    data = response.json()
                except Exception:
                    try:
                        data = json.loads(response.text or "{}")
                    except Exception:
                        data = {}
                for key in ("shortenedUrl", "shortened_url", "short_url", "url", "link"):
                    short = normalize_shortened(str(data.get(key, "")))
                    if short:
                        return short
            return url

        if provider == "safelinkearn":
            response = requests.get(
                "https://www.safelinkearn.com/api",
                params={"api": api_key, "url": url, "format": "text"},
                timeout=10,
            )
            if response.status_code == 200:
                time.sleep(0.3)  # Rate limiting
                body = response.text.strip()
                short = normalize_shortened(body)
                if short:
                    return short
                # Fallback if provider still returns JSON despite format=text
                if body.startswith("{") and body.endswith("}"):
                    try:
                        data = response.json()
                    except Exception:
                        try:
                            data = json.loads(body)
                        except Exception:
                            data = {}
                    short = normalize_shortened(str(data.get("shortenedUrl", "")))
                    if short:
                        return short
            return url

        # Default: ouo.io
        response = requests.get(
            f"https://ouo.io/api/{api_key}",
            params={"s": url},
            timeout=10,
        )
        if response.status_code == 200:
            time.sleep(0.3)  # Rate limiting
            short = normalize_shortened(response.text.strip())
            return short or url
        return url
    except:
        return url


def maybe_shorten_url(
    url: str,
    hosting: str,
    shorten_hosts: Set[str],
    api_key: str,
    shortener_provider: str,
    shorten_warnings: Optional[List[str]] = None,
    context_label: str = "",
) -> str:
    """Apply shortening only for selected hosts and collect warnings when it fails."""
    if hosting not in shorten_hosts or not api_key:
        return url

    short = shorten_url_cached(shortener_provider, api_key, url)
    if not short or not (short.startswith("http://") or short.startswith("https://")):
        if shorten_warnings is not None:
            shorten_warnings.append(f"{context_label} invalid shortlink response for {hosting}: {url}")
        return url
    if short == url and shorten_warnings is not None:
        shorten_warnings.append(f"{context_label} shortener returned original URL for {hosting}: {url}")
    return short

# =============================================================================
# CUSTOM CSS - SHADCN DARK THEME
# =============================================================================

def inject_custom_css():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Material+Symbols+Rounded:opsz,wght,FILL,GRAD@24,400,0,0&display=swap');
    
    /* Base */
    .stApp {
        background-color: #09090b;
    }
    
    *:not(.material-icons):not(.material-symbols-outlined):not(.material-symbols-rounded):not(.material-symbols-sharp):not([class*="material-symbols"]):not([data-testid="stIconMaterial"]) {
        font-family: 'Inter', 'Apple Color Emoji', 'Segoe UI Emoji', 'Segoe UI Symbol', 'Noto Color Emoji', -apple-system, BlinkMacSystemFont, sans-serif !important;
    }

    /* Keep icon ligatures rendered as icons (avoid showing raw text like "arrow_downward") */
    .material-icons,
    .material-symbols-outlined,
    .material-symbols-rounded,
    .material-symbols-sharp,
    [class*="material-symbols"],
    [data-testid="stIconMaterial"] {
        font-family: 'Material Symbols Rounded', 'Material Symbols Outlined', 'Material Icons' !important;
        font-weight: normal !important;
        font-style: normal !important;
        letter-spacing: normal !important;
        text-transform: none !important;
        white-space: nowrap !important;
        font-feature-settings: 'liga' !important;
        -webkit-font-feature-settings: 'liga' !important;
        font-variation-settings: 'FILL' 0, 'wght' 400, 'GRAD' 0, 'opsz' 24 !important;
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
    {'pattern': 'bysetayico.com', 'name': 'FileMoon'},
    {'pattern': 'byselapuix.com', 'name': 'FileMoon'},
    {'pattern': 'nuna.upns.pro', 'name': 'Upnshare'},
    {'pattern': 'short.icu', 'name': 'HydraX'},
    {'pattern': 'ok.ru', 'name': 'OKru'},
    {'pattern': 'turbovidhls.com', 'name': 'TurboVid'},
    {'pattern': 'emturbovid.com', 'name': 'TurboVid'},
    {'pattern': 'hqq.to', 'name': 'LuluTV'},
    {'pattern': 'nuna.p2pstream.vip', 'name': 'StreamP2P'},
    {'pattern': 'veev.to', 'name': 'Veev'},
]

DEFAULT_DOWNLOAD_HOST_MAP = {
    'terabox': 'Terabox',
    'mirrored': 'Mirrored',
    'mir.cr': 'Mirrored',
    'upfiles': 'Upfiles',
    'buzzheavier': 'BuzzHeavier',
    'gofile': 'Gofile',
    'filemoon': 'FileMoon',
    'vidhide': 'VidHide',
    'krakenfiles': 'Krakenfiles',
    'vikingfile': 'Vikingfile',
    'veev.to': 'Veev',
    'bysetayico': 'FileMoon',
    'byselapuix': 'FileMoon',
    'doodstream': 'Doodstream',
    'streamtape': 'StreamTape',
    'jiouploads': 'Jioupload',
    'filekeeper': 'Filekeeper',
    'minochinos': 'VidHide',
}

DEFAULT_EMBED_HOST_MAP = {
    'short.icu': 'HydraX',
    'ok.ru': 'OKru',
    'turbovidhls.com': 'TurboVid',
    'emturbovid.com': 'TurboVid',
    'waaw.to': 'Waaw',
    'p2pstream': 'StreamP2P',
    'upns.pro': 'Upnshare',
    'bysetayico': 'FileMoon',
    'byselapuix': 'FileMoon',
    'hqq.to': 'LuluTV',
    'veev.to': 'Veev',
}


def build_embed_host_config(custom_embed_rules: Optional[Dict[str, str]] = None) -> List[Dict[str, str]]:
    if not custom_embed_rules:
        return EMBED_HOST_CONFIG
    custom_items = [{'pattern': k.lower(), 'name': v} for k, v in custom_embed_rules.items() if k and v]
    return custom_items + EMBED_HOST_CONFIG


def get_embed_hostname(iframe: str, custom_embed_rules: Optional[Dict[str, str]] = None) -> str:
    src_match = re.search(r'src=["\']([^"\']+)["\']', iframe)
    if src_match:
        url = src_match.group(1).lower()
        for config in build_embed_host_config(custom_embed_rules):
            if config['pattern'] in url:
                return config['name']
    return 'Other'


def get_embed_priority(iframe: str, custom_embed_rules: Optional[Dict[str, str]] = None) -> int:
    src_match = re.search(r'src=["\']([^"\']+)["\']', iframe)
    if src_match:
        url = src_match.group(1).lower()
        for idx, config in enumerate(build_embed_host_config(custom_embed_rules)):
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
    
    # Format 2: [Tag] Series.SxxExx / Series SxxExx / Series_SxxExx
    pattern2 = r'\[.*?\]\s*(.+?)[.\s_-]S(\d+)E(\d+)'
    match = re.search(pattern2, filename, re.IGNORECASE)
    if match:
        series = match.group(1).strip().replace('.', ' ').replace('_', ' ')
        series = re.sub(r'\s*-\s*re$', '', series, flags=re.IGNORECASE).strip()
        return {'series_name': series, 'year': '', 'episode': match.group(3), 'season': match.group(2)}
    
    # Format 3: Just Exx anywhere - [Tag] Series.Name.Year.Exx
    pattern3 = r'\[.*?\]\s*(.+?)[.\s_-]E(\d+)'
    match = re.search(pattern3, filename, re.IGNORECASE)
    if match:
        series = match.group(1).strip().replace('.', ' ').replace('_', ' ')
        series = re.sub(r'\s+\d{4}\s*$', '', series).strip()
        series = re.sub(r'\s*-\s*re$', '', series, flags=re.IGNORECASE).strip()
        return {'series_name': series, 'year': '', 'episode': match.group(2), 'season': None}
    
    return None


def extract_resolution(text: str) -> str:
    match = re.search(r'(\d{3,4}p)', text, re.IGNORECASE)
    return match.group(1) if match else '720p'


def parse_movie_filename(filename: str) -> Optional[Dict]:
    """Parse movie filename: [tag] Title.Year.Res.ext -> returns title, year, resolution"""
    # Guard: if filename clearly has episode token (E11 / S01E02), treat as series, not movie.
    if re.search(r'(^|[.\s_-])S\d{1,2}E\d{1,4}($|[.\s_-])', filename, re.IGNORECASE) or \
       re.search(r'(^|[.\s_-])E\d{1,4}($|[.\s_-])', filename, re.IGNORECASE):
        return None

    # Pattern 1: [tag] Title.Year.<source>.Resolution.ext (dots)
    pattern1 = r'\[.*?\]\s*(.+?)\.(\d{4})(?:\.[A-Za-z0-9-]+)*\.(\d{3,4})p'
    match = re.search(pattern1, filename, re.IGNORECASE)
    if match:
        title = match.group(1).strip().replace('.', ' ').replace('_', ' ')
        title = re.sub(r'^\[[^\]]+\]\s*', '', title).strip()
        return {'title': title, 'year': match.group(2), 'resolution': match.group(3) + 'p'}
    
    # Pattern 2: [tag] Title Year.<source>.Resolution.ext (spaces in title)
    pattern2 = r'\[.*?\]\s*(.+?)\s+(\d{4})(?:[.\s][A-Za-z0-9-]+)*[.\s](\d{3,4})p'
    match = re.search(pattern2, filename, re.IGNORECASE)
    if match:
        title = match.group(1).strip().replace('.', ' ').replace('_', ' ')
        title = re.sub(r'^\[[^\]]+\]\s*', '', title).strip()
        return {'title': title, 'year': match.group(2), 'resolution': match.group(3) + 'p'}
    
    # Pattern 3: [tag]_Title_Year_<source>_Resolution.ext (underscores)
    pattern3 = r'\[.*?\]_(.+?)_(\d{4})(?:_[A-Za-z0-9-]+)*_(\d{3,4})p'
    match = re.search(pattern3, filename, re.IGNORECASE)
    if match:
        title = match.group(1).strip().replace('.', ' ').replace('_', ' ')
        title = re.sub(r'^\[[^\]]+\]\s*', '', title).strip()
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
    title = re.sub(r'^\s*\[[^\]]+\]\s*', '', title).strip()
    title = title.replace('+', ' ')
    title = re.sub(r'\s+', ' ', title)
    return title.lower().replace('.', ' ').replace('-', ' ').replace('_', ' ').strip()


def format_movie_display_title(title: str, year: str) -> str:
    """Return movie title for UI/JS, including year when available."""
    clean_title = title.strip()
    clean_year = (year or "").strip()
    if clean_year and re.fullmatch(r'\d{4}', clean_year):
        return f"{clean_title} ({clean_year})"
    return clean_title


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


def detect_input_content_types(text: str) -> Dict[str, bool]:
    """Detect whether input contains movie items, series items, or both."""
    has_movie = False
    has_series = False
    for raw_line in text.strip().split('\n'):
        line = raw_line.strip()
        if not line or line.startswith('<iframe') or line.lower() == 'download link':
            continue
        candidate = None
        if line.startswith('[url='):
            bbcode = parse_bbcode(line)
            if bbcode:
                candidate = bbcode['filename']
        elif line.startswith('['):
            candidate = line
        if not candidate:
            continue
        if parse_movie_filename(candidate):
            has_movie = True
        if parse_filename(candidate):
            has_series = True
        if has_movie and has_series:
            break
    return {'has_movie': has_movie, 'has_series': has_series}


def build_parser_debug_report(
    text: str,
    custom_download_host_rules: Optional[Dict[str, str]] = None,
    custom_embed_host_rules: Optional[Dict[str, str]] = None,
) -> List[str]:
    """Create line-by-line parser diagnostics."""
    report: List[str] = []
    for idx, raw_line in enumerate(text.splitlines(), start=1):
        line = raw_line.strip()
        if not line:
            report.append(f"L{idx:03d}: skip (empty)")
            continue

        if line.lower() == "download link":
            report.append(f"L{idx:03d}: marker -> download section")
            continue

        if line.startswith("[url="):
            bb = parse_bbcode(line)
            if not bb:
                report.append(f"L{idx:03d}: skip (invalid BBCode)")
                continue
            host = detect_hosting(bb["url"], custom_download_host_rules)
            embed_host = detect_embed_host_from_url(bb["url"], custom_embed_host_rules)
            movie_info = parse_movie_filename(bb["filename"])
            series_info = parse_filename(bb["filename"])
            if movie_info:
                report.append(
                    f"L{idx:03d}: BBCode movie | host={host} | title={movie_info['title']} | res={movie_info['resolution']}"
                )
            elif series_info:
                report.append(
                    f"L{idx:03d}: BBCode episode | host={host} | series={series_info['series_name']} | ep={series_info['episode']}"
                )
            elif embed_host != "Other":
                report.append(f"L{idx:03d}: BBCode embed-only | embedHost={embed_host}")
            else:
                report.append(f"L{idx:03d}: skip (BBCode filename unsupported)")
            continue

        if line.startswith("<iframe"):
            src_match = re.search(r'src=["\']([^"\']+)["\']', line)
            if not src_match:
                report.append(f"L{idx:03d}: skip (iframe without src)")
                continue
            src = src_match.group(1)
            embed_host = detect_embed_host_from_url(src, custom_embed_host_rules)
            url_info = parse_url_path(src)
            if url_info:
                report.append(
                    f"L{idx:03d}: iframe embed+urlmeta | embedHost={embed_host} | series={url_info['series_name']} | ep={url_info['episode']} | res={url_info['resolution']}"
                )
            else:
                report.append(f"L{idx:03d}: iframe embed | embedHost={embed_host}")
            continue

        if line.startswith("http://") or line.startswith("https://"):
            host = detect_hosting(line, custom_download_host_rules)
            movie_info = parse_movie_from_url(line)
            url_info = parse_url_path(line)
            if movie_info:
                report.append(
                    f"L{idx:03d}: direct URL movie-download | host={host} | title={movie_info['title']} | res={movie_info['resolution']}"
                )
            elif url_info:
                report.append(
                    f"L{idx:03d}: direct URL episode-download | host={host} | series={url_info['series_name']} | ep={url_info['episode']} | res={url_info['resolution']}"
                )
            elif host != "Other":
                report.append(f"L{idx:03d}: direct URL generic-download | host={host}")
            else:
                report.append(f"L{idx:03d}: skip (unknown direct URL host)")
            continue

        if line.startswith("["):
            movie_info = parse_movie_filename(line)
            series_info = parse_filename(line)
            if movie_info:
                report.append(
                    f"L{idx:03d}: header movie | title={movie_info['title']} | year={movie_info['year']} | res={movie_info['resolution']}"
                )
            elif series_info:
                report.append(
                    f"L{idx:03d}: header episode | series={series_info['series_name']} | ep={series_info['episode']}"
                )
            else:
                report.append(f"L{idx:03d}: skip (header pattern unsupported)")
            continue

        if " - http" in line:
            report.append(f"L{idx:03d}: filename-url pair")
            continue

        report.append(f"L{idx:03d}: skip (unrecognized format)")

    return report


def parse_url_path(url: str) -> Optional[Dict]:
    """Parse episode info from URL path"""
    path_match = re.search(r'/([^/]+)(?:\.[^/]+)?$', url)
    if not path_match:
        return None
    
    path = path_match.group(1).lower()
    
    # Try SxxExx format first
    sxxexx_match = re.search(r'[-._]s(\d{1,2})e(\d{1,3})(?:[-._]|$)', path)
    if sxxexx_match:
        season = sxxexx_match.group(1).zfill(2)
        episode = sxxexx_match.group(2).zfill(2)
    else:
        # Try just Exx format
        ep_match = re.search(r'[-._]e(\d{1,3})(?:[-._]|$)', path)
        if not ep_match:
            return None
        season = None
        episode = ep_match.group(1).zfill(2)
    
    res_match = re.search(r'[-._](360|480|720|1080|2160)p?(?:[-._]|$)', path)
    resolution = res_match.group(1) + 'p' if res_match else '720p'
    series_match = re.search(r'^[^/]*?[-._](.+?)(?:[-._]\d{4})?(?:[-._]s\d+)?e\d+', path)
    series_name = series_match.group(1).replace('-', ' ').replace('.', ' ').replace('_', ' ').title() if series_match else 'Unknown'
    
    return {'episode': episode, 'resolution': resolution, 'series_name': series_name, 'season': season}


def parse_custom_host_rules(raw_text: str) -> Dict[str, str]:
    """
    Parse custom host rule lines:
      domain=HostName
      domain -> HostName
      domain,HostName
    """
    rules: Dict[str, str] = {}
    for raw_line in (raw_text or "").splitlines():
        line = raw_line.strip()
        if not line or line.startswith('#'):
            continue
        parts = None
        if '=' in line:
            parts = line.split('=', 1)
        elif '->' in line:
            parts = line.split('->', 1)
        elif ',' in line:
            parts = line.split(',', 1)
        if not parts:
            continue
        pattern = parts[0].strip().lower()
        host_name = parts[1].strip()
        if pattern and host_name:
            rules[pattern] = host_name
    return rules


def split_url_and_label(line: str) -> (str, str):
    """Split 'URL [optional label]' line into URL and trailing label text."""
    match = re.match(r'^(https?://\S+)(?:\s+(.+))?$', line.strip())
    if not match:
        return line.strip(), ""
    return match.group(1).strip(), (match.group(2) or "").strip()


def detect_hosting(url: str, custom_host_rules: Optional[Dict[str, str]] = None) -> str:
    url_lower = url.lower()
    hosts = dict(DEFAULT_DOWNLOAD_HOST_MAP)
    if custom_host_rules:
        hosts.update({k.lower(): v for k, v in custom_host_rules.items() if k and v})
    for key, name in hosts.items():
        if key in url_lower:
            return name
    return 'Other'


def detect_shorten_hosts_from_input(
    text: str,
    available_hosts: List[str],
    custom_host_rules: Optional[Dict[str, str]] = None,
) -> List[str]:
    """Auto-detect hosts present in current input for shortening defaults."""
    if not text.strip():
        return []

    available_set = set(available_hosts)
    detected: List[str] = []

    for raw_line in text.split('\n'):
        line = raw_line.strip()
        if not line:
            continue

        url = None
        if line.startswith('[url='):
            bbcode = parse_bbcode(line)
            if bbcode:
                url = bbcode['url']
        elif line.startswith('<iframe'):
            src_match = re.search(r'src=["\']([^"\']+)["\']', line)
            if src_match:
                url = src_match.group(1)
        elif line.startswith('http://') or line.startswith('https://'):
            url = line.split()[0]

        if not url:
            continue

        hosting = detect_hosting(url, custom_host_rules)
        if hosting in available_set and hosting not in detected:
            detected.append(hosting)

    return detected


def parse_bbcode(line: str) -> Optional[Dict]:
    """Parse BBCode format [url=URL]filename[/url]"""
    match = re.match(r'\[url=([^\]]+)\](.+?)\[/url\]', line, re.IGNORECASE)
    if match:
        return {'url': match.group(1), 'filename': match.group(2)}
    return None


def adapt_input_format(text: str) -> str:
    """
    Adapt new/plain input variants into legacy-compatible format without
    changing existing supported formats.
    """
    lines = text.splitlines()
    if not lines:
        return text

    def is_resolution_line(s: str) -> bool:
        return bool(re.fullmatch(r'(360|480|540|720|1080|2160)p', s.strip(), re.IGNORECASE))

    def is_episode_header_line(s: str) -> bool:
        t = s.strip()
        if not t or t.startswith('http') or t.startswith('[') or t.startswith('<iframe'):
            return False
        if is_resolution_line(t) or t.lower() == 'download link' or '.mp4' in t.lower():
            return False
        # Accept both "...E12" and "...S02E12" headers used in block-style download lists.
        return bool(
            re.search(
                r'(?:S\d{1,2}E\d{1,4}|(?:^|[.\s_-])E\d{1,4})$',
                t,
                re.IGNORECASE,
            )
        )

    def to_tagged_filename(name: str) -> str:
        n = name.strip()
        if n.startswith('['):
            return n
        return f"[LayarAsia] {n}"

    # Split embed/download section
    marker_idx = -1
    for i, raw in enumerate(lines):
        if raw.strip().lower() == 'download link':
            marker_idx = i
            break
    embed_lines = lines if marker_idx == -1 else lines[:marker_idx]
    download_lines = [] if marker_idx == -1 else lines[marker_idx + 1:]

    adapted_embed: List[str] = []
    for raw in embed_lines:
        s = raw.strip()
        if not s:
            adapted_embed.append(raw)
            continue

        # Convert: URL - filename.mp4  --> [url=URL][LayarAsia] filename.mp4[/url]
        m_url_file = re.match(r'^(https?://\S+)\s*-\s*(.+?\.mp4)\s*$', s, re.IGNORECASE)
        if m_url_file:
            url = m_url_file.group(1).strip()
            fname = to_tagged_filename(m_url_file.group(2).strip())
            adapted_embed.append(f"[url={url}]{fname}[/url]")
            continue

        # Convert: filename.mp4|<iframe...> --> [LayarAsia] filename.mp4|<iframe...>
        m_file_iframe = re.match(r'^([^|\[]+?\.mp4)\s*\|\s*(<iframe.+)$', s, re.IGNORECASE)
        if m_file_iframe:
            fname = to_tagged_filename(m_file_iframe.group(1).strip())
            iframe = m_file_iframe.group(2).strip()
            adapted_embed.append(f"{fname}|{iframe}")
            continue

        # Convert bare filename header to tagged format
        if re.match(r'^[^\[]+?\.mp4$', s, re.IGNORECASE):
            adapted_embed.append(to_tagged_filename(s))
            continue

        adapted_embed.append(raw)

    adapted_download: List[str] = []
    current_episode = ""
    current_resolution = ""
    for raw in download_lines:
        s = raw.strip()
        if not s:
            adapted_download.append(raw)
            continue

        # Keep already-supported formats untouched
        if s.startswith('[url='):
            adapted_download.append(raw)
            continue

        # Detect block-style episode header:
        # Yumi's.Cell.2021.E01
        if is_episode_header_line(s):
            current_episode = s
            current_resolution = ""
            adapted_download.append(raw)
            continue

        # Detect block-style resolution line:
        # 1080p
        if is_resolution_line(s):
            current_resolution = s.lower()
            adapted_download.append(raw)
            continue

        # Convert block-style URL line into BBCode filename line for parser stability
        if s.startswith('http://') or s.startswith('https://'):
            if current_episode and current_resolution:
                filename = f"{current_episode}.{current_resolution}.mp4"
                adapted_download.append(f"[url={s}][LayarAsia] {filename}[/url]")
            else:
                adapted_download.append(raw)
            continue

        adapted_download.append(raw)

    if marker_idx == -1:
        return '\n'.join(adapted_embed)
    return '\n'.join(adapted_embed + [lines[marker_idx]] + adapted_download)


def detect_embed_host_from_url(url: str, custom_embed_rules: Optional[Dict[str, str]] = None) -> str:
    """Detect embed hostname dari URL"""
    url_lower = url.lower()
    hosts = dict(DEFAULT_EMBED_HOST_MAP)
    if custom_embed_rules:
        hosts.update({k.lower(): v for k, v in custom_embed_rules.items() if k and v})
    for key, name in hosts.items():
        if key in url_lower:
            return name
    return 'Other'


def to_embed_src(url: str) -> str:
    """Normalize URL to embeddable src for known providers."""
    url = url.strip()
    # OK.ru watch URL -> videoembed URL
    ok_match = re.search(r'ok\.ru/video/(\d+)', url, re.IGNORECASE)
    if ok_match:
        return f"https://ok.ru/videoembed/{ok_match.group(1)}?nochat=1"
    # emturbovid /d/<id> -> turbovidhls /t/<id>
    turbo_match = re.search(r'emturbovid\.com/d/([A-Za-z0-9]+)', url, re.IGNORECASE)
    if turbo_match:
        return f"https://turbovidhls.com/t/{turbo_match.group(1)}"
    return url


def derive_filemoon_download_url(iframe_or_url: str) -> Optional[str]:
    """
    Convert known FileMoon-style embed URL (.../e/...) to download URL (.../d/...).
    Only for supported domains to avoid collisions with other formats.
    """
    src = iframe_or_url.strip()
    if '<iframe' in src.lower():
        src_match = re.search(r'src=["\']([^"\']+)["\']', src, re.IGNORECASE)
        if not src_match:
            return None
        src = src_match.group(1).strip()

    lower_src = src.lower()
    if not (('bysetayico.com' in lower_src) or ('byselapuix.com' in lower_src)):
        return None

    # Transform first '/e/' segment into '/d/' only when clearly present.
    converted = re.sub(r'(^https?://[^/]+)/e/', r'\1/d/', src, count=1, flags=re.IGNORECASE)
    if converted == src:
        return None
    return converted


def parse_movie_input(
    text: str,
    shorten_hosts: Set[str] = None,
    api_key: str = "",
    shortener_provider: str = "ouo",
    custom_download_host_rules: Optional[Dict[str, str]] = None,
    custom_embed_host_rules: Optional[Dict[str, str]] = None,
    shorten_warnings: Optional[List[str]] = None,
) -> Dict[str, Episode]:
    """Parse movie input format and return movies as episodes (keyed by normalized title)"""
    if shorten_hosts is None:
        shorten_hosts = set()
    movies: Dict[str, Episode] = {}
    lines = text.strip().split('\n')
    
    download_section_start = -1
    for i, line in enumerate(lines):
        if line.strip().lower() == 'download link':
            download_section_start = i
            break
    
    embed_lines = lines[:download_section_start] if download_section_start > 0 else lines
    
    # Phase 1: Collect movie headers (supports plain filename and BBCode embeds)
    movie_list = []
    seen_movie_keys = set()
    for line in embed_lines:
        line = line.strip()
        if not line:
            continue
        if line.startswith('<iframe'):
            # Keep scanning: some inputs interleave "filename" then iframe per line block.
            continue
        
        movie_info = None
        bbcode = None
        
        # New format: [url=LINK][LayarAsia] Title.Year.Res.mp4[/url]
        if line.startswith('[url='):
            bbcode = parse_bbcode(line)
            if bbcode:
                movie_info = parse_movie_filename(bbcode['filename'])
        elif line.startswith('['):
            movie_info = parse_movie_filename(line)
        
        if movie_info:
            key = normalize_movie_title(movie_info['title'])
            display_title = format_movie_display_title(movie_info['title'], movie_info.get('year', ''))
            if key not in movies:
                movies[key] = Episode(number='HD', series_name=display_title, year=movie_info['year'], season=None)
            
            # Keep stable movie ordering without duplicates
            if key not in seen_movie_keys:
                seen_movie_keys.add(key)
                movie_list.append({'key': key, 'title': display_title})
            
            # If this is BBCode embed, convert URL to iframe immediately
            if bbcode:
                hostname = detect_embed_host_from_url(bbcode['url'], custom_embed_host_rules)
                embed_src = to_embed_src(bbcode["url"])
                iframe = f'<iframe src="{embed_src}" width="100%" height="100%" frameborder="0" allowfullscreen></iframe>'
                movies[key].embeds.append(EmbedData(hostname=hostname, embed=iframe))
                # If FileMoon embed URL is provided, also derive /d/ link with resolution from filename context.
                if hostname == 'FileMoon':
                    d_url = derive_filemoon_download_url(bbcode['url'])
                    if d_url:
                        res = movie_info.get('resolution', '720p')
                        if res not in movies[key].downloads:
                            movies[key].downloads[res] = []
                        exists = any(dl.hosting == 'FileMoon' and dl.url == d_url for dl in movies[key].downloads[res])
                        if not exists:
                            movies[key].downloads[res].append(
                                DownloadLink(hosting='FileMoon', url=d_url, resolution=res)
                            )
    
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
        for idx, iframe in enumerate(standalone_iframes):
            movie_idx = idx % num_movies
            key = movie_list[movie_idx]['key']
            if key in movies:
                hostname = get_embed_hostname(iframe, custom_embed_host_rules)
                movies[key].embeds.append(EmbedData(hostname=hostname, embed=iframe))
    
    # Phase 4: Add highest resolution bysetayico embeds
    for key, res_dict in byse_embeds.items():
        if res_dict and key in movies:
            highest_res = max(res_dict.keys())
            iframe = res_dict[highest_res]
            hostname = get_embed_hostname(iframe, custom_embed_host_rules)
            movies[key].embeds.append(EmbedData(hostname=hostname, embed=iframe))
    
    # Sort embeds by priority
    for key in movies:
        movies[key].embeds.sort(key=lambda e: get_embed_priority(e.embed, custom_embed_host_rules))

    # Derive FileMoon download links from embed links when explicit /d/ links are absent.
    for key, movie in movies.items():
        for e in movie.embeds:
            d_url = derive_filemoon_download_url(e.embed)
            if not d_url:
                continue
            res = extract_resolution(d_url)
            if res not in movie.downloads:
                movie.downloads[res] = []
            exists = any(
                dl.hosting == 'FileMoon' and dl.url == d_url
                for dl in movie.downloads[res]
            )
            if not exists:
                movie.downloads[res].append(DownloadLink(hosting='FileMoon', url=d_url, resolution=res))
    
    # Phase 5: Parse downloads
    if download_section_start > 0:
        download_lines = lines[download_section_start + 1:]
        # Plain URLs without filename metadata (e.g. Terabox/Upfiles) to map positionally later.
        unassigned_links_by_host: Dict[str, List[str]] = {}
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
                    hosting = detect_hosting(url, custom_download_host_rules)
            elif line.startswith('http'):
                movie_info = parse_movie_from_url(line)
                if movie_info:
                    url, hosting = line, detect_hosting(line, custom_download_host_rules)
                else:
                    # Fallback: plain URL tanpa metadata movie ikut mapping positional
                    # per-host selama host bisa dideteksi (bukan "Other").
                    hosting = detect_hosting(line, custom_download_host_rules)
                    if hosting != 'Other':
                        unassigned_links_by_host.setdefault(hosting, []).append(line)
            
            if movie_info and url and hosting:
                url = maybe_shorten_url(
                    url,
                    hosting,
                    shorten_hosts,
                    api_key,
                    shortener_provider,
                    shorten_warnings,
                    f"[Movie {movie_info.get('title', '-')}]",
                )
                key = normalize_movie_title(movie_info['title'])
                display_title = format_movie_display_title(movie_info['title'], movie_info.get('year', ''))
                res = movie_info['resolution']
                if key not in movies:
                    movies[key] = Episode(number='HD', series_name=display_title, year=movie_info['year'], season=None)
                if res not in movies[key].downloads:
                    movies[key].downloads[res] = []
                movies[key].downloads[res].append(DownloadLink(hosting=hosting, url=url, resolution=res))
        
        # Map plain host URLs positionally (Terabox/Upfiles):
        # each movie consumes links in its known resolution order (480p, 720p, 1080p, ...).
        for host_name, host_links in unassigned_links_by_host.items():
            host_idx = 0
            if not movie_list:
                continue
            for movie_entry in movie_list:
                key = movie_entry['key']
                if key not in movies:
                    continue
                known_resolutions = sorted(
                    movies[key].downloads.keys(),
                    key=lambda x: int(re.search(r'\d+', x).group()) if re.search(r'\d+', x) else 9999
                )
                if not known_resolutions:
                    known_resolutions = ['480p', '720p', '1080p']
                for res in known_resolutions:
                    if host_idx >= len(host_links):
                        break
                    url = host_links[host_idx]
                    host_idx += 1
                    url = maybe_shorten_url(
                        url,
                        host_name,
                        shorten_hosts,
                        api_key,
                        shortener_provider,
                        shorten_warnings,
                        f"[Movie {movie_entry.get('title', '-')}]",
                    )
                    if res not in movies[key].downloads:
                        movies[key].downloads[res] = []
                    # Avoid accidental duplicate insertion.
                    exists = any(l.hosting == host_name and l.url == url for l in movies[key].downloads[res])
                    if not exists:
                        movies[key].downloads[res].append(
                            DownloadLink(hosting=host_name, url=url, resolution=res)
                        )
                if host_idx >= len(host_links):
                    break
    
    return movies


def normalize_series_name(name: str) -> str:
    """Normalize series name for comparison"""
    cleaned = name.lower().replace('.', ' ').replace('-', ' ').replace('_', ' ')
    cleaned = re.sub(r'[\(\)\[\],:;\'"`!?]+', ' ', cleaned)
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    return cleaned


def strip_year_tokens(name: str) -> str:
    """Remove standalone year tokens to improve fuzzy matching."""
    cleaned = re.sub(r'\b(?:19|20)\d{2}\b', ' ', name)
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    return cleaned


def find_episode_key(episodes: Dict[str, Episode], series_name: str, ep_num: str) -> Optional[str]:
    """Find episode key in dict by series name (fuzzy) and episode number"""
    # First try exact match
    exact_key = f"{series_name}_{ep_num}"
    if exact_key in episodes:
        return exact_key
    
    # Try normalized match
    normalized_input = normalize_series_name(series_name)
    normalized_input_no_year = strip_year_tokens(normalized_input)
    ep_input = ep_num.lstrip('0') or ep_num
    for key, ep in episodes.items():
        ep_stored = ep.number.lstrip('0') or ep.number
        if ep_stored == ep_input:
            normalized_stored = normalize_series_name(ep.series_name)
            normalized_stored_no_year = strip_year_tokens(normalized_stored)
            # Check if one contains the other (partial match)
            if (
                normalized_input in normalized_stored or
                normalized_stored in normalized_input or
                normalized_input_no_year in normalized_stored_no_year or
                normalized_stored_no_year in normalized_input_no_year
            ):
                return key
    
    return None


def parse_input(
    text: str,
    shorten_hosts: Set[str] = None,
    api_key: str = "",
    shortener_provider: str = "ouo",
    custom_download_host_rules: Optional[Dict[str, str]] = None,
    custom_embed_host_rules: Optional[Dict[str, str]] = None,
    shorten_warnings: Optional[List[str]] = None,
) -> Dict[str, Episode]:
    if shorten_hosts is None:
        shorten_hosts = set()
    episodes: Dict[str, Episode] = {}
    lines = text.strip().split('\n')
    
    download_section_start = -1
    has_explicit_download_marker = False
    force_download_only = False
    for i, line in enumerate(lines):
        if line.strip().lower() == 'download link':
            download_section_start = i
            has_explicit_download_marker = True
            break
    
    if download_section_start == -1:
        for i, line in enumerate(lines):
            if line.startswith('http') and ('mirrored' in line.lower() or 'terabox' in line.lower()):
                download_section_start = i
                break
    
    # Heuristic: if there is no iframe and most BBCode URLs look like download hosts,
    # treat the whole input as download section even without "Download Link" marker.
    if not has_explicit_download_marker:
        non_empty = [ln.strip() for ln in lines if ln.strip()]
        has_iframe = any('<iframe' in ln.lower() for ln in non_empty)
        bbcode_lines = [ln for ln in non_empty if ln.startswith('[url=')]
        if not has_iframe and bbcode_lines:
            recognized_download = 0
            for ln in bbcode_lines:
                bb = parse_bbcode(ln)
                if bb:
                    host = detect_hosting(bb['url'], custom_download_host_rules)
                    if host != 'Other':
                        recognized_download += 1
            if recognized_download / max(len(bbcode_lines), 1) >= 0.6:
                force_download_only = True

    embed_lines = [] if force_download_only else (lines[:download_section_start] if download_section_start > 0 else lines)
    embed_server_count = {}
    standalone_embeds = []
    veev_embeds = {}  # episode_key -> {resolution_num: iframe_code}
    url_embeds = {}   # ep_num -> {resolution_num: iframe_code} for URL-parsed embeds
    
    # Collect series headers (consecutive filenames at start, before iframes) for positional mapping
    # Also handle BBCode embed format: [url=URL][filename][/url]
    series_header_list = []  # List of {episode, series_name, season, year, unique_key} in order
    bbcode_embeds = []  # Store BBCode embeds to process later
    
    for line in embed_lines:
        line = line.strip()
        if not line:
            continue
        if line.startswith('<iframe'):
            break
        
        # Check for BBCode embed format: [url=URL][filename][/url]
        if line.startswith('[url='):
            bbcode = parse_bbcode(line)
            if bbcode:
                info = parse_filename(bbcode['filename'])
                if info:
                    unique_key = f"{info['series_name']}_{info['episode']}"
                    info['unique_key'] = unique_key
                    info['bbcode_url'] = bbcode['url']  # Store the URL
                    series_header_list.append(info)
                    
                    if unique_key not in episodes:
                        episodes[unique_key] = Episode(
                            number=info['episode'],
                            series_name=info['series_name'],
                            year=info.get('year', ''),
                            season=info.get('season', '')
                        )
                    
                    hostname = detect_embed_host_from_url(bbcode['url'], custom_embed_host_rules)
                    # Only treat BBCode as embed if host is an embed provider.
                    if hostname != 'Other':
                        embed_src = to_embed_src(bbcode["url"])
                        iframe = f'<iframe src="{embed_src}" width="100%" height="100%" frameborder="0" allowfullscreen></iframe>'
                        episodes[unique_key].embeds.append(EmbedData(hostname=hostname, embed=iframe))
                        # If FileMoon embed URL is provided, also derive /d/ link with resolution from filename context.
                        if hostname == 'FileMoon':
                            d_url = derive_filemoon_download_url(bbcode['url'])
                            if d_url:
                                res = extract_resolution(bbcode['filename'])
                                if res not in episodes[unique_key].downloads:
                                    episodes[unique_key].downloads[res] = []
                                exists = any(
                                    dl.hosting == 'FileMoon' and dl.url == d_url
                                    for dl in episodes[unique_key].downloads[res]
                                )
                                if not exists:
                                    episodes[unique_key].downloads[res].append(
                                        DownloadLink(hosting='FileMoon', url=d_url, resolution=res)
                                    )
                continue
        
        # Regular filename header (no URL)
        if line.startswith('[') and '|' not in line:
            info = parse_filename(line)
            if info:
                # Create unique key: series_name + episode number
                unique_key = f"{info['series_name']}_{info['episode']}"
                info['unique_key'] = unique_key
                series_header_list.append(info)
                if unique_key not in episodes:
                    episodes[unique_key] = Episode(
                        number=info['episode'],
                        series_name=info['series_name'],
                        year=info.get('year', ''),
                        season=info.get('season', '')
                    )
    
    # Skip filename+iframe pattern for episodes in series_header_list (positional assignment)
    series_header_episodes = {h['episode'] for h in series_header_list}
    
    i = 0
    while i < len(embed_lines):
        line = embed_lines[i].strip()
        if line.startswith('[url='):
            # Handle BBCode embeds even when they appear after iframe blocks.
            bbcode = parse_bbcode(line)
            if bbcode:
                info = parse_filename(bbcode['filename'])
                if info:
                    key = find_episode_key(episodes, info['series_name'], info['episode'])
                    if not key:
                        key = f"{info['series_name']}_{info['episode']}"
                        episodes[key] = Episode(
                            number=info['episode'],
                            series_name=info['series_name'],
                            year=info.get('year', ''),
                            season=info.get('season', ''),
                        )
                    hostname = detect_embed_host_from_url(bbcode['url'], custom_embed_host_rules)
                    if hostname != 'Other':
                        embed_src = to_embed_src(bbcode["url"])
                        embed_code = f'<iframe src="{embed_src}" width="100%" height="100%" frameborder="0" allowfullscreen></iframe>'
                        src_match = re.search(r'src=["\']([^"\']+)["\']', embed_code, re.IGNORECASE)
                        target_src = src_match.group(1).lower() if src_match else ""
                        exists = any(
                            re.search(r'src=["\']([^"\']+)["\']', e.embed, re.IGNORECASE) and
                            re.search(r'src=["\']([^"\']+)["\']', e.embed, re.IGNORECASE).group(1).lower() == target_src
                            for e in episodes[key].embeds
                        )
                        if not exists:
                            episodes[key].embeds.append(EmbedData(hostname=hostname, embed=embed_code))
                        if hostname == 'FileMoon':
                            d_url = derive_filemoon_download_url(bbcode['url'])
                            if d_url:
                                res = extract_resolution(bbcode['filename'])
                                if res not in episodes[key].downloads:
                                    episodes[key].downloads[res] = []
                                d_exists = any(
                                    dl.hosting == 'FileMoon' and dl.url == d_url
                                    for dl in episodes[key].downloads[res]
                                )
                                if not d_exists:
                                    episodes[key].downloads[res].append(
                                        DownloadLink(hosting='FileMoon', url=d_url, resolution=res)
                                    )
            i += 1
            continue
        if line.startswith('[') and '|' not in line and ' - <iframe' not in line:
            info = parse_filename(line)
            if info and i + 1 < len(embed_lines):
                next_line = embed_lines[i + 1].strip()
                # Skip if episode is in series_header_list (will be assigned positionally)
                if next_line.startswith('<iframe') and info['episode'] not in series_header_episodes:
                    ep_num = info['episode']
                    key = find_episode_key(episodes, info['series_name'], ep_num)
                    if not key:
                        key = f"{info['series_name']}_{ep_num}"
                        episodes[key] = Episode(
                            number=ep_num,
                            series_name=info['series_name'],
                            year=info.get('year', ''),
                            season=info.get('season', ''),
                        )
                    hostname = get_embed_hostname(next_line, custom_embed_host_rules)
                    episodes[key].embeds.append(EmbedData(hostname=hostname, embed=next_line))
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
                    series_name = url_info['series_name']
                    res_num = int(re.search(r'\d+', res).group())
                    
                    # Find matching episode using unique key
                    key = find_episode_key(episodes, series_name, ep_num)
                    if key:
                        # Track by unique key and resolution, keep highest
                        if key not in url_embeds:
                            url_embeds[key] = {}
                        if res_num not in url_embeds[key] or res_num > max(url_embeds[key].keys(), default=0):
                            url_embeds[key][res_num] = line
                    else:
                        # No matching episode found, use standalone assignment
                        standalone_embeds.append(line)
                else:
                    standalone_embeds.append(line)
            else:
                standalone_embeds.append(line)
        elif '|' in line and '<iframe' in line:
            # Episode-scoped "filename|<iframe...>" lines are handled in the
            # dedicated pass below to avoid positional mis-assignment.
            pass
        # Handle "filename - <iframe..." format
        elif ' - <iframe' in line:
            parts = line.split(' - <iframe', 1)
            filename = parts[0].strip()
            iframe_code = '<iframe' + parts[1]
            info = parse_filename(filename)
            if info:
                ep_num = info['episode']
                key = find_episode_key(episodes, info['series_name'], ep_num)
                if not key:
                    key = f"{info['series_name']}_{ep_num}"
                    episodes[key] = Episode(
                        number=ep_num,
                        series_name=info['series_name'],
                        year=info.get('year', ''),
                        season=info.get('season', ''),
                    )
                # For veev embeds, track by resolution and only keep highest
                if 'veev.to' in iframe_code:
                    res = extract_resolution(filename)
                    res_num = int(re.search(r'\d+', res).group())
                    if key not in veev_embeds:
                        veev_embeds[key] = {}
                    if res_num not in veev_embeds[key] or res_num > max(veev_embeds[key].keys(), default=0):
                        veev_embeds[key][res_num] = iframe_code
                else:
                    hostname = get_embed_hostname(iframe_code, custom_embed_host_rules)
                    episodes[key].embeds.append(EmbedData(hostname=hostname, embed=iframe_code))
        i += 1
    
    # Add highest resolution veev embeds
    for key, res_dict in veev_embeds.items():
        if res_dict and key in episodes:
            highest_res = max(res_dict.keys())
            iframe_code = res_dict[highest_res]
            hostname = get_embed_hostname(iframe_code, custom_embed_host_rules)
            episodes[key].embeds.append(EmbedData(hostname=hostname, embed=iframe_code))
    
    # Add highest resolution URL-parsed embeds
    for key, res_dict in url_embeds.items():
        if res_dict and key in episodes:
            highest_res = max(res_dict.keys())
            iframe_code = res_dict[highest_res]
            hostname = get_embed_hostname(iframe_code, custom_embed_host_rules)
            episodes[key].embeds.append(EmbedData(hostname=hostname, embed=iframe_code))
    
    # Assign standalone iframes positionally if we have series headers
    if series_header_list and standalone_embeds:
        num_episodes = len(series_header_list)
        for idx, iframe in enumerate(standalone_embeds):
            ep_idx = idx % num_episodes
            unique_key = series_header_list[ep_idx]['unique_key']
            if unique_key in episodes:
                hostname = get_embed_hostname(iframe, custom_embed_host_rules)
                episodes[unique_key].embeds.append(EmbedData(hostname=hostname, embed=iframe))
        standalone_embeds = []

    for line in embed_lines:
        line = line.strip()
        if line.startswith('[') and '|' in line:
            parts = line.split('|', 1)
            info = parse_filename(parts[0].strip())
            url_or_iframe = parts[1].strip()
            if info:
                ep_num = info['episode']
                key = find_episode_key(episodes, info['series_name'], ep_num)
                if not key:
                    key = f"{info['series_name']}_{ep_num}"
                    episodes[key] = Episode(
                        number=ep_num,
                        series_name=info['series_name'],
                        year=info.get('year', ''),
                        season=info.get('season', ''),
                    )
                # Check if it's already an iframe or just a URL
                if url_or_iframe.startswith('<iframe'):
                    embed_code = url_or_iframe
                else:
                    embed_src = to_embed_src(url_or_iframe)
                    embed_code = f'<iframe src="{embed_src}" width="100%" height="100%" frameborder="0" allowfullscreen></iframe>'
                hostname = get_embed_hostname(embed_code, custom_embed_host_rules)
                if hostname != 'Other':
                    episodes[key].embeds.append(EmbedData(hostname=hostname, embed=embed_code))
    
    if force_download_only or download_section_start > 0:
        download_lines = lines if force_download_only else lines[download_section_start + 1:]
        download_urls = []
        episode_resolutions = {}
        
        # Positional grouping for plain URLs
        current_resolution = None
        current_key = None
        resolution_links = {}  # key -> {res -> [(hosting, url)]}
        
        for line in download_lines:
            line = line.strip()
            if not line:
                continue
            
            # BBCode [url=URL]filename[/url] - has resolution info
            if line.startswith('[url='):
                bbcode_match = re.match(r'\[url=([^\]]+)\](.+?)\[/url\]', line, re.IGNORECASE)
                if bbcode_match:
                    url, filename = bbcode_match.group(1), bbcode_match.group(2)
                    ep_match = re.search(r'S\d+E(\d+)|E(\d+)', filename, re.IGNORECASE)
                    res = extract_resolution(filename)
                    
                    if ep_match:
                        ep_num = ep_match.group(1) or ep_match.group(2)
                        hosting = detect_hosting(url, custom_download_host_rules)
                        
                        # Apply shortening if enabled
                        url = maybe_shorten_url(
                            url,
                            hosting,
                            shorten_hosts,
                            api_key,
                            shortener_provider,
                            shorten_warnings,
                            f"[Episode {ep_num}]",
                        )
                        
                        # Find or create episode with unique key
                        info = parse_filename(filename)
                        if info:
                            key = find_episode_key(episodes, info['series_name'], ep_num)
                            if not key:
                                key = f"{info['series_name']}_{ep_num}"
                                episodes[key] = Episode(number=ep_num, series_name=info['series_name'], year='', season=info.get('season', ''))
                        else:
                            key = ep_num
                            if key not in episodes:
                                episodes[key] = Episode(number=ep_num, series_name='Unknown', year='', season='')
                        
                        # Update current context for positional grouping
                        current_key = key
                        current_resolution = res
                        
                        if key not in resolution_links:
                            resolution_links[key] = {}
                        if res not in resolution_links[key]:
                            resolution_links[key][res] = []
                        resolution_links[key][res].append((hosting, url))
            
            # Direct URL - inherit current resolution if no resolution in URL
            elif line.startswith('http'):
                raw_url, trailing_label = split_url_and_label(line)
                url_info = parse_url_path(raw_url)
                hosting = detect_hosting(raw_url, custom_download_host_rules)
                
                # Apply shortening if enabled
                url = raw_url
                url = maybe_shorten_url(
                    raw_url,
                    hosting,
                    shorten_hosts,
                    api_key,
                    shortener_provider,
                    shorten_warnings,
                    f"[URL line {raw_url[:42]}]",
                )

                label_info = parse_filename(trailing_label) if trailing_label else None
                label_res = extract_resolution(trailing_label) if trailing_label else None
                
                if url_info:
                    # URL has explicit resolution info
                    ep_num = url_info['episode']
                    res = url_info['resolution']
                    series_name = url_info['series_name']
                    
                    key = find_episode_key(episodes, series_name, ep_num)
                    if not key:
                        key = f"{series_name}_{ep_num}"
                        episodes[key] = Episode(number=ep_num, series_name=series_name, year='', season='')
                    
                    current_key = key
                    current_resolution = res
                    
                    if key not in resolution_links:
                        resolution_links[key] = {}
                    if res not in resolution_links[key]:
                        resolution_links[key][res] = []
                    resolution_links[key][res].append((hosting, url))
                elif label_info:
                    # URL does not encode episode metadata, fallback to trailing label.
                    ep_num = label_info['episode']
                    res = label_res or '720p'
                    series_name = label_info['series_name']

                    key = find_episode_key(episodes, series_name, ep_num)
                    if not key:
                        key = f"{series_name}_{ep_num}"
                        episodes[key] = Episode(
                            number=ep_num,
                            series_name=series_name,
                            year=label_info.get('year', ''),
                            season=label_info.get('season', ''),
                        )

                    current_key = key
                    current_resolution = res

                    if key not in resolution_links:
                        resolution_links[key] = {}
                    if res not in resolution_links[key]:
                        resolution_links[key][res] = []
                    resolution_links[key][res].append((hosting, url))
                elif hosting == 'Mirrored':
                    # Mirrored URLs carry episode metadata in filename; parse in legacy block below.
                    download_urls.append(raw_url)
                elif current_key and current_resolution:
                    # Use current context from previous BBCode line
                    if current_key not in resolution_links:
                        resolution_links[current_key] = {}
                    if current_resolution not in resolution_links[current_key]:
                        resolution_links[current_key][current_resolution] = []
                    resolution_links[current_key][current_resolution].append((hosting, url))
                else:
                    download_urls.append(raw_url)
            
            # filename - URL
            elif ' - http' in line:
                parts = line.split(' - http', 1)
                filename, url = parts[0].strip(), 'http' + parts[1].strip()
                ep_match = re.search(r'S\d+E(\d+)|E(\d+)', filename, re.IGNORECASE)
                res = extract_resolution(filename)
                if ep_match:
                    ep_num = ep_match.group(1) or ep_match.group(2)
                    hosting = detect_hosting(url, custom_download_host_rules)
                    url = maybe_shorten_url(
                        url,
                        hosting,
                        shorten_hosts,
                        api_key,
                        shortener_provider,
                        shorten_warnings,
                        f"[Episode {ep_num}]",
                    )
                    if ep_num not in episodes:
                        info = parse_filename(filename)
                        episodes[ep_num] = Episode(number=ep_num, series_name=info['series_name'] if info else 'Unknown', year='', season=info.get('season', '') if info else '')
                    if res not in episodes[ep_num].downloads:
                        episodes[ep_num].downloads[res] = []
                    episodes[ep_num].downloads[res].append(DownloadLink(hosting=hosting, url=url, resolution=res))
        
        # Assign resolution_links to episodes
        for key, res_dict in resolution_links.items():
            if key in episodes:
                for res, links in res_dict.items():
                    if res not in episodes[key].downloads:
                        episodes[key].downloads[res] = []
                    for hosting, url in links:
                        episodes[key].downloads[res].append(DownloadLink(hosting=hosting, url=url, resolution=res))
        
        # Parse Mirrored links for episode/resolution structure (legacy support)
        for url in download_urls:
            if 'mirrored' in url.lower():
                parsed_info = None
                fn_match = re.search(r'/([^/]+\.mp4)', url, re.IGNORECASE)
                if fn_match:
                    parsed_info = parse_filename(fn_match.group(1))

                if parsed_info:
                    series_from_url = parsed_info['series_name']
                    ep_num = parsed_info['episode']
                    season = parsed_info.get('season', '')
                else:
                    # Fallback for uncommon mirrored naming.
                    series_match = re.search(r'\[.*?\]_(.+?)(?:[-._]S\d+)?[-._]E(\d+)', url, re.IGNORECASE)
                    if not series_match:
                        continue
                    series_from_url = series_match.group(1).replace('.', ' ').replace('_', ' ')
                    ep_num = series_match.group(2)
                    season = ''

                res = extract_resolution(url)
                key = find_episode_key(episodes, series_from_url, ep_num)
                if not key:
                    key = f"{series_from_url}_{ep_num}"
                    episodes[key] = Episode(number=ep_num, series_name=series_from_url, year='', season=season)

                if key not in episode_resolutions:
                    episode_resolutions[key] = []
                if res not in episode_resolutions[key]:
                    episode_resolutions[key].append(res)
                if res not in episodes[key].downloads:
                    episodes[key].downloads[res] = []
                final_url = maybe_shorten_url(
                    url,
                    'Mirrored',
                    shorten_hosts,
                    api_key,
                    shortener_provider,
                    shorten_warnings,
                    f"[Episode {ep_num}]",
                )
                episodes[key].downloads[res].append(DownloadLink(hosting='Mirrored', url=final_url, resolution=res))
        
        for url in download_urls:
            if 'mirrored' in url.lower():
                detected_series = None
                fn_match = re.search(r'/([^/]+\.mp4)', url, re.IGNORECASE)
                if fn_match:
                    parsed_info = parse_filename(fn_match.group(1))
                    if parsed_info:
                        detected_series = parsed_info['series_name']
                if not detected_series:
                    series_match = re.search(r'\[.*?\]_(.+?)(?:[-._]S\d+)?[-._]E\d+', url, re.IGNORECASE)
                    if series_match:
                        detected_series = series_match.group(1).replace('_', ' ')
                if detected_series:
                    for ep in episodes.values():
                        if ep.series_name == "Unknown":
                            ep.series_name = detected_series
                    break
        
        if standalone_embeds and len(episodes) == 1:
            ep_num = list(episodes.keys())[0]
            for embed in standalone_embeds:
                hostname = get_embed_hostname(embed, custom_embed_host_rules)
                episodes[ep_num].embeds.append(EmbedData(hostname=hostname, embed=embed))
    
    # Sort embeds by priority
    for ep in episodes.values():
        ep.embeds.sort(key=lambda x: get_embed_priority(x.embed, custom_embed_host_rules))

    # Derive FileMoon download links from embed links when explicit /d/ links are absent.
    for key, ep in episodes.items():
        for e in ep.embeds:
            d_url = derive_filemoon_download_url(e.embed)
            if not d_url:
                continue

            info = parse_url_path(d_url)
            if info:
                ep_num_info = info['episode'].lstrip('0') or info['episode']
                ep_num = ep.number.lstrip('0') or ep.number
                if ep_num_info != ep_num:
                    continue
                res = info['resolution']
            else:
                # If /d/ URL doesn't carry resolution token, skip auto-derive to avoid wrong default (e.g. forced 720p).
                if not re.search(r'(\d{3,4}p)', d_url, re.IGNORECASE):
                    continue
                res = extract_resolution(d_url)

            if res not in ep.downloads:
                ep.downloads[res] = []
            exists = any(
                dl.hosting == 'FileMoon' and dl.url == d_url
                for dl in ep.downloads[res]
            )
            if not exists:
                ep.downloads[res].append(DownloadLink(hosting='FileMoon', url=d_url, resolution=res))
    
    return episodes


def generate_quickfill_js(episode: Episode, subbed: str = "Sub", fill_mode: str = "replace") -> str:
    embeds_js = ',\n'.join([f"""        {{ hostname: "{e.hostname}", embed: '{e.embed.replace("'", "\\'")}' }}""" for e in episode.embeds])
    
    hosting_priority = {
        "Terabox": 0,
        "BuzzHeavier": 1,
        "Gofile": 2,
        "FileMoon": 3,
        "VidHide": 4,
        "Mirrored": 5,
    }

    resolutions_js = []
    for res in sorted(episode.downloads.keys(), key=lambda x: int(re.search(r'\d+', x).group())):
        sorted_links = sorted(
            episode.downloads[res],
            key=lambda l: (hosting_priority.get(l.hosting, 999), l.hosting.lower(), l.url.lower())
        )
        links_js = ',\n'.join([f'                    {{ hosting: "{l.hosting}", url: "{l.url}" }}' for l in sorted_links])
        resolutions_js.append(f'            {{ pixel: "{res}", links: [\n{links_js}\n                ] }}')
    resolutions_str = ',\n'.join(resolutions_js)
    
    def series_has_season(name: str, season: str) -> bool:
        if not season:
            return False
        season_norm = season.lstrip('0') or season
        pattern1 = rf'\bseason\s*0*{re.escape(season_norm)}\b'
        pattern2 = rf'\bs0*{re.escape(season_norm)}\b'
        return bool(re.search(pattern1, name, re.IGNORECASE) or re.search(pattern2, name, re.IGNORECASE))

    # Build title with season if available (strip leading zeros for display)
    season_display = episode.season.lstrip('0') or episode.season if episode.season else ""
    ep_display = episode.number.lstrip('0') or episode.number
    season_str = f" Season {season_display}" if season_display and not series_has_season(episode.series_name, episode.season) else ""
    
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
    fillMode: "{fill_mode}",
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
    const CLONE_SELECTOR = ':scope > .rwmb-clone:not(.rwmb-clone-template)';
    const sleep = ms => new Promise(r => setTimeout(r, ms));
    const trigger = el => {{ el.dispatchEvent(new Event('change', {{bubbles:true}})); el.dispatchEvent(new Event('input', {{bubbles:true}})); }};
    const getClones = container => Array.from(container.querySelectorAll(CLONE_SELECTOR));
    
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
    
    const normalize = v => (v || '').toString().trim();
    const normalizeLower = v => normalize(v).toLowerCase();
    const extractSrc = html => {{
        const m = normalize(html).match(/src=["']([^"']+)["']/i);
        return m ? normalizeLower(m[1]) : '';
    }};
    const getSelectValue = select => {{
        if (!select) return '';
        const opt = select.options && select.selectedIndex >= 0 ? select.options[select.selectedIndex] : null;
        return normalize(select.value || (opt ? opt.text : ''));
    }};
    
    const setEmbeds = async embeds => {{
        const container = document.querySelector('#embed-video .rwmb-tab-panel-input-version .rwmb-input');
        if (!container) return;
        let clones = getClones(container);

        const findExistingEmbedClone = target => {{
            const targetSrc = extractSrc(target.embed);
            const targetHost = normalizeLower(target.hostname);
            return clones.find(clone => {{
                const h = clone.querySelector('input[name*="ab_hostname"]');
                const e = clone.querySelector('textarea[name*="ab_embed"]');
                const existingHost = normalizeLower(h?.value);
                const existingEmbed = normalize(e?.value);
                if (!existingHost && !existingEmbed) return false;
                const existingSrc = extractSrc(existingEmbed);
                if (targetSrc && existingSrc && targetSrc === existingSrc) return true;
                return existingHost === targetHost && existingEmbed === normalize(target.embed);
            }});
        }};

        for (let i = 0; i < embeds.length; i++) {{
            const target = embeds[i];
            let clone = null;

            if (isAppendMode) {{
                clone = findExistingEmbedClone(target);
                if (clone) continue; // smart merge: skip exact duplicate
                const targetIdx = clones.length;
                while (clones.length <= targetIdx) {{ await addClone(container); clones = getClones(container); }}
                clone = clones[targetIdx];
            }} else {{
                const targetIdx = i;
                while (clones.length <= targetIdx) {{ await addClone(container); clones = getClones(container); }}
                clone = clones[targetIdx];
            }}

            const h = clone.querySelector('input[name*="ab_hostname"]');
            const e = clone.querySelector('textarea[name*="ab_embed"]');
            if (h) {{ h.value = target.hostname; trigger(h); }}
            if (e) {{ e.value = target.embed; trigger(e); }}
        }}
    }};
    
    const setDownloads = async downloads => {{
        const epContainer = document.querySelector('#episode-download .rwmb-meta-box > .rwmb-field > .rwmb-input');
        if (!epContainer) return;
        const epClone = epContainer.querySelector(':scope > .rwmb-clone:not(.rwmb-clone-template)');
        if (!epClone) return;
        const epTitle = epClone.querySelector('input[name*="ab_eptitle_ep"]');
        if (epTitle && (!isAppendMode || !epTitle.value.trim())) {{ epTitle.value = downloads.episodeTitle; trigger(epTitle); }}

        const resContainer = epClone.querySelector('.rwmb-group-collapsible > .rwmb-input');
        if (!resContainer) return;
        let resClones = getClones(resContainer);

        const findResolutionClone = pixelName => resClones.find(clone => {{
            const pixel = clone.querySelector('select[name*="ab_pixel_ep"]');
            return normalizeLower(getSelectValue(pixel)) === normalizeLower(pixelName);
        }});

        for (let r = 0; r < downloads.resolutions.length; r++) {{
            const resData = downloads.resolutions[r];
            let resClone = null;

            if (isAppendMode) {{
                resClone = findResolutionClone(resData.pixel);
                if (!resClone) {{
                    const targetResIdx = resClones.length;
                    while (resClones.length <= targetResIdx) {{ await addClone(resContainer); resClones = getClones(resContainer); }}
                    resClone = resClones[targetResIdx];
                }}
            }} else {{
                const targetResIdx = r;
                while (resClones.length <= targetResIdx) {{ await addClone(resContainer); resClones = getClones(resContainer); }}
                resClone = resClones[targetResIdx];
            }}

            const pixel = resClone.querySelector('select[name*="ab_pixel_ep"]');
            if (pixel) {{ pixel.value = resData.pixel; trigger(pixel); }}

            const linkContainer = resClone.querySelector('.rwmb-group-wrapper:not(.rwmb-group-collapsible) > .rwmb-input');
            if (!linkContainer) continue;
            let linkClones = getClones(linkContainer);

            const findLinkCloneByHosting = hostingName => linkClones.find(clone => {{
                const h = clone.querySelector('select[name*="ab_hostingname_ep"]');
                return normalizeLower(getSelectValue(h)) === normalizeLower(hostingName);
            }});

            for (let l = 0; l < resData.links.length; l++) {{
                const linkData = resData.links[l];
                let linkClone = null;

                if (isAppendMode) {{
                    linkClone = findLinkCloneByHosting(linkData.hosting);
                    if (linkClone) {{
                        const urlField = linkClone.querySelector('input[name*="ab_linkurl_ep"]');
                        if (urlField && normalize(urlField.value) !== normalize(linkData.url)) {{
                            urlField.value = linkData.url; // smart merge: update same resolution+hosting
                            trigger(urlField);
                        }}
                        continue;
                    }}
                    const targetLinkIdx = linkClones.length;
                    while (linkClones.length <= targetLinkIdx) {{ await addClone(linkContainer); linkClones = getClones(linkContainer); }}
                    linkClone = linkClones[targetLinkIdx];
                }} else {{
                    const targetLinkIdx = l;
                    while (linkClones.length <= targetLinkIdx) {{ await addClone(linkContainer); linkClones = getClones(linkContainer); }}
                    linkClone = linkClones[targetLinkIdx];
                }}

                const hosting = linkClone.querySelector('select[name*="ab_hostingname_ep"]');
                if (hosting) {{ hosting.value = linkData.hosting; trigger(hosting); }}
                const url = linkClone.querySelector('input[name*="ab_linkurl_ep"]');
                if (url) {{ url.value = linkData.url; trigger(url); }}
            }}
        }}
    }};
    
    console.log('Starting auto-fill...');
    const d = EPISODE_DATA;
    const isAppendMode = (d.fillMode || 'replace').toLowerCase() === 'append';
    const seasonNum = (d.seasonNumber && d.seasonNumber !== 'None') ? d.seasonNumber.replace(/^0+/, '') || d.seasonNumber : '';
    const seriesNorm = (d.seriesName || '').toLowerCase();
    const seasonToken = seasonNum;
    const seriesHasSeason = seasonToken ? (
        seriesNorm.includes(`season ${{seasonToken}}`) ||
        seriesNorm.includes(`season 0${{seasonToken}}`) ||
        seriesNorm.includes(`season 00${{seasonToken}}`) ||
        seriesNorm.includes(`s${{seasonToken}}`) ||
        seriesNorm.includes(`s0${{seasonToken}}`) ||
        seriesNorm.includes(`s00${{seasonToken}}`)
    ) : false;
    const epNum = d.episodeNumber.replace(/^0+/, '') || d.episodeNumber;
    const seasonPart = (seasonToken && !seriesHasSeason) ? ` Season ${{seasonToken}}` : '';
    // For movies (HD), don't add Episode part
    const episodePart = (epNum === 'HD') ? '' : ` Episode ${{epNum}}`;
    setField('title', `${{d.seriesName}}${{seasonPart}}${{episodePart}} Subtitle Indonesia`);
    await sleep(DELAY);
    await setSeries(d.seriesName);
    await sleep(DELAY);
    setCategory(d.seriesName);
    await sleep(DELAY);
    setField('ero_episodebaru', epNum);
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
if 'parser_debug_report' not in st.session_state:
    st.session_state.parser_debug_report = []
if 'shorten_warnings' not in st.session_state:
    st.session_state.shorten_warnings = []

# Header
st.markdown("# DramaStream Quickfill")
st.caption("Generate autofill scripts untuk posting episode ke WordPress")
st.markdown("---")

# Layout
col1, col2 = st.columns(2, gap="large")

with col1:
    st.markdown("### Input")
    series_name = st.text_input("Series Name (optional)", placeholder="Auto-detect from URL")
    input_text = st.text_area("Episode Data", height=250, placeholder="<iframe src=...></iframe>\nid | <iframe ...></iframe>\n[url=URL][filename][/url]\n\nDownload Link\n\nhttps://mirrored.to/...")
    fill_mode_label = st.selectbox(
        "Fill Mode",
        options=["Append (keep existing data)", "Replace (overwrite from top)"],
        index=0,
    )
    fill_mode = "append" if fill_mode_label.startswith("Append") else "replace"
    parser_debug_enabled = st.checkbox("Parser Debug Mode", value=False, help="Show line-by-line parsing diagnostics after Generate.")

    with st.expander("Custom Host Rules", expanded=False):
        custom_download_rules_text = st.text_area(
            "Download Host Rules (domain=HostingName)",
            key="custom_download_rules_text",
            height=90,
            placeholder="example.com=ExampleHost\ncdn.example.net=ExampleHost",
        )
        custom_embed_rules_text = st.text_area(
            "Embed Host Rules (domain=EmbedName)",
            key="custom_embed_rules_text",
            height=90,
            placeholder="embed.example.com=ExampleEmbed",
        )

    custom_download_host_rules = parse_custom_host_rules(custom_download_rules_text)
    custom_embed_host_rules = parse_custom_host_rules(custom_embed_rules_text)
    
    # Shortening settings (provider selectable)
    with st.expander("Link Shortening", expanded=False):
        shortener_enabled = st.checkbox("Enable Link Shortening", value=False, key="shortener_enabled")
        if shortener_enabled:
            provider_label = st.selectbox(
                "Provider",
                options=["ouo.io", "safelinkearn.com", "safelinku.com"],
                index=2,
                key="shortener_provider",
            )
            if provider_label.startswith("safelinkearn"):
                shortener_provider = "safelinkearn"
            elif provider_label.startswith("safelinku"):
                shortener_provider = "safelinku"
            else:
                shortener_provider = "ouo"
            if shortener_provider == "ouo":
                shortener_api_key = st.text_input(
                    "API Key",
                    value=DEFAULT_OUO_API_KEY,
                    type="password",
                    key="ouo_api_key",
                )
            elif shortener_provider == "safelinkearn":
                shortener_api_key = st.text_input(
                    "API Token",
                    value=DEFAULT_SAFELINKEARN_API_TOKEN,
                    type="password",
                    key="safelinkearn_api_token",
                )
            elif shortener_provider == "safelinku":
                shortener_api_key = st.text_input(
                    "API Token",
                    value=DEFAULT_SAFELINKU_API_TOKEN,
                    type="password",
                    key="safelinku_api_token",
                )
            base_hosts = ['BuzzHeavier', 'Gofile', 'Upfiles', 'Terabox', 'FileMoon', 'Mirrored', 'Jioupload', 'Filekeeper', 'VidHide']
            excluded_auto_hosts = {'Mirrored', 'Terabox', 'FileMoon', 'VidHide'}
            custom_hosts = sorted({v for v in custom_download_host_rules.values() if v})
            available_hosts = sorted(set(base_hosts + custom_hosts))
            detected_hosts = detect_shorten_hosts_from_input(input_text, available_hosts, custom_download_host_rules)
            auto_hosts = [h for h in detected_hosts if h not in excluded_auto_hosts]
            if not auto_hosts:
                auto_hosts = ['BuzzHeavier', 'Gofile']
            input_sig = input_text.strip()
            prev_sig = st.session_state.get("_shorten_hosts_input_sig")
            prev_auto = st.session_state.get("_shorten_hosts_auto", [])
            current_selection = st.session_state.get("shorten_hosts")

            # Auto-update default selection only when user has not customized it.
            if "shorten_hosts" not in st.session_state:
                st.session_state["shorten_hosts"] = auto_hosts
            elif prev_sig != input_sig and (not current_selection or current_selection == prev_auto):
                st.session_state["shorten_hosts"] = auto_hosts

            st.session_state["_shorten_hosts_input_sig"] = input_sig
            st.session_state["_shorten_hosts_auto"] = auto_hosts

            shorten_hosts = st.multiselect(
                "Servers to shorten",
                options=available_hosts,
                key="shorten_hosts"
            )
            if detected_hosts:
                st.caption(f"Auto-detected hosts in input: {', '.join(detected_hosts)}")
                st.caption("Auto-select excludes: Mirrored, Terabox, FileMoon, VidHide (still selectable manually).")
            else:
                st.caption("No host detected from input yet (fallback default: BuzzHeavier, Gofile).")
            st.caption("Shortened links are cached for 1 hour")
        else:
            shortener_provider = "ouo"
            shortener_api_key = ""
            shorten_hosts = []
    
    if st.button("Generate", type="primary", use_container_width=True):
        if input_text.strip():
            adapted_input_text = adapt_input_format(input_text)
            # Prepare shortening settings
            shorten_set = set(shorten_hosts) if shortener_enabled else set()
            active_shortener_key = shortener_api_key if shortener_enabled else ""
            shorten_warnings: List[str] = []
            parser_report = build_parser_debug_report(
                adapted_input_text,
                custom_download_host_rules=custom_download_host_rules,
                custom_embed_host_rules=custom_embed_host_rules,
            ) if parser_debug_enabled else []
            st.session_state.parser_debug_report = parser_report
            
            content_types = detect_input_content_types(adapted_input_text)
            has_movie = content_types['has_movie']
            has_series = content_types['has_series']
            movie_items: Dict[str, Episode] = {}
            series_items: Dict[str, Episode] = {}

            if has_movie:
                movie_items = parse_movie_input(
                    adapted_input_text,
                    shorten_set,
                    active_shortener_key,
                    shortener_provider,
                    custom_download_host_rules,
                    custom_embed_host_rules,
                    shorten_warnings,
                )
            if has_series or (not has_movie and not has_series):
                series_items = parse_input(
                    adapted_input_text,
                    shorten_set,
                    active_shortener_key,
                    shortener_provider,
                    custom_download_host_rules,
                    custom_embed_host_rules,
                    shorten_warnings,
                )

            st.session_state.shorten_warnings = sorted(set(shorten_warnings))

            if series_name:
                for ep in movie_items.values():
                    ep.series_name = series_name
                for ep in series_items.values():
                    ep.series_name = series_name

            scripts = {}

            if movie_items:
                sorted_movies = sorted(movie_items.items())
                for key, ep in sorted_movies:
                    script_key = f"movie::{key}"
                    scripts[script_key] = {
                        'js': generate_quickfill_js(ep, fill_mode=fill_mode),
                        'embeds': len(ep.embeds),
                        'resolutions': list(ep.downloads.keys()),
                        'series': ep.series_name,
                        'episode': ep.number,
                        'is_movie': True
                    }

            if series_items:
                # Sort by series name first, then by episode number
                def sort_key(item):
                    ep = item[1]
                    ep_num = int(ep.number) if ep.number.isdigit() else 0
                    return (ep.series_name, ep_num)

                sorted_series = sorted(series_items.items(), key=sort_key)
                for key, ep in sorted_series:
                    script_key = f"series::{key}"
                    scripts[script_key] = {
                        'js': generate_quickfill_js(ep, fill_mode=fill_mode),
                        'embeds': len(ep.embeds),
                        'resolutions': list(ep.downloads.keys()),
                        'series': ep.series_name,
                        'episode': ep.number,
                        'is_movie': False
                    }

            if scripts:
                st.session_state.generated_scripts = scripts
                movie_count = sum(1 for data in scripts.values() if data['is_movie'])
                series_count = len(scripts) - movie_count
                if movie_count and series_count:
                    st.success(f"Generated {len(scripts)} scripts ({movie_count} movie, {series_count} episode)")
                elif movie_count:
                    st.success(f"Generated {movie_count} movie scripts")
                else:
                    st.success(f"Generated {series_count} episode scripts")
            else:
                st.error("No episodes/movies detected")
        else:
            st.session_state.parser_debug_report = []
            st.session_state.shorten_warnings = []
            st.warning("Enter episode data first")

with col2:
    st.markdown("### Output")
    if st.session_state.generated_scripts:
        scripts = st.session_state.generated_scripts
        key_list = list(scripts.keys())
        has_movie = any(scripts[k]['is_movie'] for k in key_list)
        has_series = any(not scripts[k]['is_movie'] for k in key_list)

        if has_movie and has_series:
            options = [
                f"[Movie] {scripts[k]['series']}" if scripts[k]['is_movie'] else f"[Episode] {scripts[k]['series']} E{scripts[k]['episode']}"
                for k in key_list
            ]
            selected_idx = st.selectbox("Item", range(len(options)), format_func=lambda i: options[i])
            key = key_list[selected_idx] if selected_idx is not None else None
        elif has_movie:
            options = [scripts[k]['series'] for k in key_list]
            selected_idx = st.selectbox("Movie", range(len(options)), format_func=lambda i: options[i])
            key = key_list[selected_idx] if selected_idx is not None else None
        else:
            options = [f"{scripts[k]['series']} E{scripts[k]['episode']}" for k in key_list]
            selected_idx = st.selectbox("Episode", range(len(options)), format_func=lambda i: options[i])
            key = key_list[selected_idx] if selected_idx is not None else None
        
        if key and key in scripts:
            d = scripts[key]
            title = d['series']
            # Clickable title that copies to clipboard using components.html
            components.html(f'''
            <style>
            .copy-title {{ cursor: pointer; color: #fafafa; font-weight: 600; font-family: system-ui, sans-serif; }}
            .copy-title:hover {{ text-decoration: underline; color: #3b82f6; }}
            p {{ color: #a1a1aa; font-size: 14px; margin: 0; font-family: system-ui, sans-serif; }}
            </style>
            <p>
                <span class="copy-title" onclick="navigator.clipboard.writeText('{title}').then(() => {{ this.style.color='#22c55e'; setTimeout(() => this.style.color='#fafafa', 1500); }});" title="Click to copy">{title}</span>
                · {d['embeds']} embeds · {', '.join(d['resolutions'])}
            </p>
            ''', height=30)
            
            # Use container with height limit via CSS
            st.markdown("""<style>.code-container div[data-testid="stCode"] { max-height: 300px; overflow-y: auto; }</style>""", unsafe_allow_html=True)
            with st.container():
                st.markdown('<div class="code-container">', unsafe_allow_html=True)
                st.code(d['js'], language='javascript')
                st.markdown('</div>', unsafe_allow_html=True)
            
            zip_buf = io.BytesIO()
            with zipfile.ZipFile(zip_buf, 'w', zipfile.ZIP_DEFLATED) as zf:
                for n, data in scripts.items():
                    if data.get('is_movie'):
                        safe_title = re.sub(r'[^\w\s-]', '', data['series']).strip().replace(' ', '_')
                        zf.writestr(f"quickfill_{safe_title}.js", data['js'])
                    else:
                        # Create abbreviated series name (first letters of each word, max 10 chars)
                        words = data['series'].split()
                        if len(words) > 1:
                            abbrev = ''.join(w[0].upper() for w in words if w)[:10]
                        else:
                            abbrev = data['series'][:10].replace(' ', '')
                        zf.writestr(f"quickfill_{abbrev}_E{data['episode']}.js", data['js'])
            st.download_button("Download All (ZIP)", zip_buf.getvalue(), "quickfill.zip", "application/zip", use_container_width=True)
    else:
        st.info("Generate scripts to see output")

if st.session_state.shorten_warnings:
    with st.expander(f"Shortener Warnings ({len(st.session_state.shorten_warnings)})", expanded=False):
        for msg in st.session_state.shorten_warnings:
            st.caption(f"- {msg}")

if st.session_state.parser_debug_report:
    with st.expander(f"Parser Debug ({len(st.session_state.parser_debug_report)} lines)", expanded=False):
        st.code('\n'.join(st.session_state.parser_debug_report), language='text')

with st.expander("Help"):
    st.markdown("""
**Embed formats:** `&lt;iframe&gt;`, `id | &lt;iframe&gt;`, `[Tag] Series (Year) EXXX.mp4` + iframe

**Download:** After "Download Link", Mirrored URLs define episodes/resolutions. Other hosts follow order.
""", unsafe_allow_html=True)
