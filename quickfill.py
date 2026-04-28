"""
DramaStream Quickfill Generator - Streamlit Version
====================================================
Shadcn-inspired Dark Dashboard UI — Rewritten with bug fixes & UI improvements
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
# COMPILED REGEX PATTERNS (module-level, not re-compiled every call)
# =============================================================================

_RE_IFRAME_SRC       = re.compile(r'src=["\']([^"\']+)["\']', re.IGNORECASE)
_RE_RESOLUTION       = re.compile(r'(\d{3,4}p)', re.IGNORECASE)
_RE_BBCODE           = re.compile(r'\[url=([^\]]+)\](.+?)\[/url\]', re.IGNORECASE)
_RE_SXXEXX           = re.compile(r'[-._]s(\d{1,2})e(\d{1,3})(?:[-._]|$)', re.IGNORECASE)
_RE_EXX              = re.compile(r'[-._]e(\d{1,3})(?:[-._]|$)', re.IGNORECASE)
_RE_RESOLUTION_PATH  = re.compile(r'[-._](360|480|540|720|1080|2160)p?(?:[-._]|$)', re.IGNORECASE)
_RE_EP_FILENAME      = re.compile(r'S\d+E(\d+)|E(\d+)', re.IGNORECASE)
_RE_YEAR             = re.compile(r'\b(?:19|20)\d{2}\b')
_RE_URL_LABEL        = re.compile(r'^(https?://\S+)(?:\s+(.+))?$')

# Filename parse patterns
_RE_FN_PAT1 = re.compile(r'\[.*?\]\s*(.+?)\s*\((\d{4})\)\s*E(\d+)')
_RE_FN_PAT2 = re.compile(r'\[.*?\]\s*(.+?)[.\s_-]S(\d+)E(\d+)', re.IGNORECASE)
_RE_FN_PAT3 = re.compile(r'\[.*?\]\s*(.+?)[.\s_-]E(\d+)', re.IGNORECASE)

# Movie filename patterns
_RE_MV_EPISODE_GUARD = re.compile(r'(^|[.\s_-])S\d{1,2}E\d{1,4}($|[.\s_-])|(^|[.\s_-])E\d{1,4}($|[.\s_-])', re.IGNORECASE)
_RE_MV_PAT1 = re.compile(r'\[.*?\]\s*(.+?)\.(\d{4})(?:\.[A-Za-z0-9-]+)*\.(\d{3,4})p', re.IGNORECASE)
_RE_MV_PAT2 = re.compile(r'\[.*?\]\s*(.+?)\s+(\d{4})(?:[.\s][A-Za-z0-9-]+)*[.\s](\d{3,4})p', re.IGNORECASE)
_RE_MV_PAT3 = re.compile(r'\[.*?\]_(.+?)_(\d{4})(?:_[A-Za-z0-9-]+)*_(\d{3,4})p', re.IGNORECASE)

# URL path movie pattern
_RE_MV_URL_PATH = re.compile(r'^[^-]+-(.+?)-(\d{4})-(\d{3,4})p?$')

# Episode header detection for adapt_input_format
_RE_EP_HEADER = re.compile(r'(?:S\d{1,2}E\d{1,4}|(?:^|[.\s_-])E\d{1,4})$', re.IGNORECASE)
_RE_MOVIE_HEADER_YEAR = re.compile(r'(?:^|[.\s_-])(19|20)\d{2}(?:$|[.\s_-])')
_RE_RESOLUTION_ONLY  = re.compile(r'^(360|480|540|720|1080|2160)p$', re.IGNORECASE)
_RE_URL_FILE_ADAPT   = re.compile(r'^(https?://\S+)\s*-\s*(.+?\.mp4)\s*$', re.IGNORECASE)
_RE_FILE_IFRAME      = re.compile(r'^([^|\[]+?\.mp4)\s*\|\s*(<iframe.+)$', re.IGNORECASE)

# FileMoon derive
_RE_FILEMOON_E_PATH  = re.compile(r'(^https?://[^/]+)/e/', re.IGNORECASE)

# Series name normalization
_RE_NORM_CHARS       = re.compile(r'[\(\)\[\],:;\'"`!?]+')
_RE_MULTI_SPACE      = re.compile(r'\s+')
_RE_SEASON_TOKEN_P1  = re.compile(r'\bseason\s*0*{n}\b', re.IGNORECASE)
_RE_SEASON_IN_NAME   = re.compile(r'\bseason\s+(\d+)\b|\bs(\d+)\b', re.IGNORECASE)

# mirrored link parsing
_RE_MIRRORED_FN = re.compile(r'/([^/]+\.mp4)', re.IGNORECASE)
_RE_MIRRORED_EP = re.compile(r'\[.*?\]_(.+?)(?:[-._]S\d+)?[-._]E(\d+)', re.IGNORECASE)
_RE_MIRRORED_SERIES = re.compile(r'\[.*?\]_(.+?)(?:[-._]S\d+)?[-._]E\d+', re.IGNORECASE)

# =============================================================================
# LINK SHORTENING
# =============================================================================

DEFAULT_OUO_API_KEY = "8pHuHRq5"
DEFAULT_SAFELINKEARN_API_TOKEN = "b7e08e60216a7e4af740e7cd46e348a7e6fcea17"
DEFAULT_SAFELINKU_API_TOKEN = "3e3844f4c831f2bc46cfdd15e8d8c370b2c39c2b"


def _normalize_shortened(value: str) -> str:
    """Return shortened URL string, or empty string if not a valid URL."""
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


@st.cache_data(show_spinner=False, ttl=3600)
def _shorten_cached(provider: str, api_key: str, url: str) -> tuple[str, str]:
    """
    Returns (shortened_url, error_message).
    Caches only on success (error string non-empty = failure, caller should not cache).
    """
    if not api_key:
        return url, ""

    provider = (provider or "").strip().lower()
    try:
        if provider == "safelinku":
            resp = requests.post(
                "https://safelinku.com/api/v1/links",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                },
                json={"url": url},
                timeout=10,
            )
            if resp.status_code in (200, 201):
                time.sleep(1.05)
                try:
                    data = resp.json()
                except Exception:
                    try:
                        data = json.loads(resp.text or "{}")
                    except Exception:
                        data = {}
                for key in ("shortenedUrl", "shortened_url", "short_url", "url", "link"):
                    short = _normalize_shortened(str(data.get(key, "")))
                    if short:
                        return short, ""
            return url, f"safelinku HTTP {resp.status_code}"

        if provider == "safelinkearn":
            resp = requests.get(
                "https://www.safelinkearn.com/api",
                params={"api": api_key, "url": url, "format": "text"},
                timeout=10,
            )
            if resp.status_code == 200:
                time.sleep(0.3)
                body = resp.text.strip()
                short = _normalize_shortened(body)
                if short:
                    return short, ""
                if body.startswith("{") and body.endswith("}"):
                    try:
                        data = resp.json()
                    except Exception:
                        data = {}
                    short = _normalize_shortened(str(data.get("shortenedUrl", "")))
                    if short:
                        return short, ""
            return url, f"safelinkearn HTTP {resp.status_code}"

        # Default: ouo.io
        resp = requests.get(
            f"https://ouo.io/api/{api_key}",
            params={"s": url},
            timeout=10,
        )
        if resp.status_code == 200:
            time.sleep(0.3)
            short = _normalize_shortened(resp.text.strip())
            if short:
                return short, ""
        return url, f"ouo HTTP {resp.status_code}"

    except Exception as e:
        return url, f"{type(e).__name__}: {e}"


def shorten_url(provider: str, api_key: str, url: str) -> tuple[str, str]:
    """Public wrapper — returns (url, error_msg). Skips cache on error."""
    short, err = _shorten_cached(provider, api_key, url)
    return short, err


def maybe_shorten_url(
    url: str,
    hosting: str,
    shorten_hosts: Set[str],
    api_key: str,
    shortener_provider: str,
    shorten_warnings: Optional[List[str]] = None,
    context_label: str = "",
) -> str:
    if hosting not in shorten_hosts or not api_key:
        return url
    short, err = shorten_url(shortener_provider, api_key, url)
    if err:
        if shorten_warnings is not None:
            shorten_warnings.append(f"{context_label} [{hosting}] {err} — url: {url}")
        return url
    if short == url and shorten_warnings is not None:
        shorten_warnings.append(f"{context_label} [{hosting}] shortener returned original URL — url: {url}")
    return short


# =============================================================================
# CUSTOM CSS
# =============================================================================

def inject_custom_css():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Material+Symbols+Rounded:opsz,wght,FILL,GRAD@24,400,0,0&display=swap');

    .stApp { background-color: #09090b; }

    .stApp *:not(.material-icons):not(.material-symbols-outlined):not(.material-symbols-rounded):not(.material-symbols-sharp):not([class*="material-symbols"]):not([data-testid="stIconMaterial"]) {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
    }

    .material-icons, .material-symbols-outlined, .material-symbols-rounded,
    .material-symbols-sharp, [class*="material-symbols"], [data-testid="stIconMaterial"] {
        font-family: 'Material Symbols Rounded', 'Material Icons' !important;
        font-feature-settings: 'liga' !important;
        -webkit-font-feature-settings: 'liga' !important;
    }

    #MainMenu, footer, header { visibility: hidden; }

    .main .block-container { padding: 2rem 3rem; max-width: 1400px; }

    h1, h2, h3 { color: #fafafa !important; font-weight: 600 !important; }
    p, span, label { color: #a1a1aa !important; }

    /* Inputs */
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea {
        background-color: #18181b !important;
        border: 1px solid #27272a !important;
        border-radius: 6px !important;
        color: #fafafa !important;
        padding: 0.625rem 0.75rem !important;
        transition: border-color 0.15s ease !important;
    }
    .stTextInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus {
        border-color: #6366f1 !important;
        box-shadow: 0 0 0 2px rgba(99,102,241,0.2) !important;
    }
    .stTextInput > div > div > input::placeholder,
    .stTextArea > div > div > textarea::placeholder { color: #52525b !important; }

    /* Labels */
    .stTextInput > label, .stTextArea > label, .stSelectbox > label,
    .stMultiSelect > label, .stCheckbox > label {
        color: #fafafa !important;
        font-size: 0.875rem !important;
        font-weight: 500 !important;
    }

    /* Primary button */
    .stButton > button {
        background-color: #6366f1 !important;
        color: #ffffff !important;
        border: none !important;
        border-radius: 6px !important;
        font-weight: 500 !important;
        padding: 0.5rem 1rem !important;
        transition: all 0.15s ease !important;
        box-shadow: 0 1px 3px rgba(99,102,241,0.3) !important;
    }
    .stButton > button:hover { background-color: #4f46e5 !important; }
    .stButton > button:active { transform: scale(0.98) !important; }

    /* Download button */
    .stDownloadButton > button {
        background-color: transparent !important;
        color: #fafafa !important;
        border: 1px solid #27272a !important;
        border-radius: 6px !important;
        font-weight: 500 !important;
        transition: all 0.15s ease !important;
    }
    .stDownloadButton > button:hover { background-color: #27272a !important; }

    /* Selectbox */
    .stSelectbox > div > div, .stMultiSelect > div > div {
        background-color: #18181b !important;
        border: 1px solid #27272a !important;
        border-radius: 6px !important;
        color: #fafafa !important;
    }
    .stSelectbox > div > div > div, .stMultiSelect > div > div > div { color: #fafafa !important; }

    /* Code block */
    .stCode, pre, code {
        background-color: #18181b !important;
        border: 1px solid #27272a !important;
        border-radius: 6px !important;
    }
    .stCode { max-height: 320px !important; overflow-y: auto !important; }

    /* Alerts */
    .stSuccess { background-color: rgba(34,197,94,0.08) !important; border: 1px solid rgba(34,197,94,0.25) !important; border-radius: 6px !important; }
    .stError   { background-color: rgba(239,68,68,0.08)  !important; border: 1px solid rgba(239,68,68,0.25)  !important; border-radius: 6px !important; }
    .stWarning { background-color: rgba(234,179,8,0.08)  !important; border: 1px solid rgba(234,179,8,0.25)  !important; border-radius: 6px !important; }
    .stInfo    { background-color: rgba(99,102,241,0.08) !important; border: 1px solid rgba(99,102,241,0.25) !important; border-radius: 6px !important; }

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

    hr { border-color: #27272a !important; }
    .stCaption, small { color: #71717a !important; }
    .stSpinner > div > div { border-top-color: #6366f1 !important; }

    /* Checkbox */
    .stCheckbox > label { color: #a1a1aa !important; }

    /* Sidebar */
    [data-testid="stSidebar"] {
        background-color: #18181b !important;
        border-right: 1px solid #27272a !important;
    }

    /* Tag chips in multiselect */
    .stMultiSelect span[data-baseweb="tag"] {
        background-color: #3f3f46 !important;
        color: #fafafa !important;
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
    season: str = ""
    embeds: List[EmbedData] = field(default_factory=list)
    downloads: Dict[str, List[DownloadLink]] = field(default_factory=dict)


# =============================================================================
# HOST CONFIGURATION
# =============================================================================

EMBED_HOST_CONFIG = [
    {'pattern': 'bysetayico.com', 'name': 'FileMoon'},
    {'pattern': 'byselapuix.com', 'name': 'FileMoon'},
    {'pattern': 'nuna.upns.pro',  'name': 'Upnshare'},
    {'pattern': 'short.icu',      'name': 'HydraX'},
    {'pattern': 'ok.ru',          'name': 'OKru'},
    {'pattern': 'turbovidhls.com','name': 'TurboVid'},
    {'pattern': 'emturbovid.com', 'name': 'TurboVid'},
    {'pattern': 'hqq.to',         'name': 'LuluTV'},
    {'pattern': 'nuna.p2pstream.vip', 'name': 'StreamP2P'},
    {'pattern': 'veev.to',        'name': 'Veev'},
]

DEFAULT_DOWNLOAD_HOST_MAP = {
    'terabox':      'Terabox',
    'mirrored':     'Mirrored',
    'mir.cr':       'Mirrored',
    'upfiles':      'Upfiles',
    'buzzheavier':  'BuzzHeavier',
    'gofile':       'Gofile',
    'filemoon':     'FileMoon',
    'vidhide':      'VidHide',
    'krakenfiles':  'Krakenfiles',
    'vikingfile':   'Vikingfile',
    'veev.to':      'Veev',
    'bysetayico':   'FileMoon',
    'byselapuix':   'FileMoon',
    'doodstream':   'Doodstream',
    'streamtape':   'StreamTape',
    'jiouploads':   'Jioupload',
    'filekeeper':   'Filekeeper',
    'minochinos':   'VidHide',
}

DEFAULT_EMBED_HOST_MAP = {
    'short.icu':        'HydraX',
    'ok.ru':            'OKru',
    'turbovidhls.com':  'TurboVid',
    'emturbovid.com':   'TurboVid',
    'waaw.to':          'Waaw',
    'p2pstream':        'StreamP2P',
    'upns.pro':         'Upnshare',
    'bysetayico':       'FileMoon',
    'byselapuix':       'FileMoon',
    'hqq.to':           'LuluTV',
    'veev.to':          'Veev',
}


def build_embed_host_config(custom: Optional[Dict[str, str]] = None) -> List[Dict[str, str]]:
    if not custom:
        return EMBED_HOST_CONFIG
    return [{'pattern': k.lower(), 'name': v} for k, v in custom.items() if k and v] + EMBED_HOST_CONFIG


def get_embed_hostname(iframe: str, custom: Optional[Dict[str, str]] = None) -> str:
    m = _RE_IFRAME_SRC.search(iframe)
    if m:
        url_lower = m.group(1).lower()
        for cfg in build_embed_host_config(custom):
            if cfg['pattern'] in url_lower:
                return cfg['name']
    return 'Other'


def get_embed_priority(iframe: str, custom: Optional[Dict[str, str]] = None) -> int:
    m = _RE_IFRAME_SRC.search(iframe)
    if m:
        url_lower = m.group(1).lower()
        for idx, cfg in enumerate(build_embed_host_config(custom)):
            if cfg['pattern'] in url_lower:
                return idx
    return 999


# =============================================================================
# PARSERS
# =============================================================================

def parse_filename(filename: str) -> Optional[Dict]:
    m = _RE_FN_PAT1.search(filename)
    if m:
        return {'series_name': m.group(1).strip(), 'year': m.group(2), 'episode': m.group(3), 'season': None}
    m = _RE_FN_PAT2.search(filename)
    if m:
        series = m.group(1).strip().replace('.', ' ').replace('_', ' ')
        series = re.sub(r'\s*-\s*re$', '', series, flags=re.IGNORECASE).strip()
        return {'series_name': series, 'year': '', 'episode': m.group(3), 'season': m.group(2)}
    m = _RE_FN_PAT3.search(filename)
    if m:
        series = m.group(1).strip().replace('.', ' ').replace('_', ' ')
        series = re.sub(r'\s+\d{4}\s*$', '', series).strip()
        series = re.sub(r'\s*-\s*re$', '', series, flags=re.IGNORECASE).strip()
        return {'series_name': series, 'year': '', 'episode': m.group(2), 'season': None}
    return None


def extract_resolution(text: str) -> str:
    m = _RE_RESOLUTION.search(text)
    return m.group(1) if m else '720p'


def parse_movie_filename(filename: str) -> Optional[Dict]:
    if _RE_MV_EPISODE_GUARD.search(filename):
        return None
    for pat in (_RE_MV_PAT1, _RE_MV_PAT2, _RE_MV_PAT3):
        m = pat.search(filename)
        if m:
            title = m.group(1).strip().replace('.', ' ').replace('_', ' ')
            title = re.sub(r'^\[[^\]]+\]\s*', '', title).strip()
            title = re.sub(r'^\s*-\s*', '', title).strip()
            return {'title': title, 'year': m.group(2), 'resolution': m.group(3) + 'p'}
    return None


def parse_movie_from_url(url: str) -> Optional[Dict]:
    pm = re.search(r'/([^/]+)(?:\.[^/]+)?$', url)
    if not pm:
        return None
    path = pm.group(1).lower()
    if re.search(r'-[se]\d+', path):
        return None
    m = _RE_MV_URL_PATH.search(path)
    if m:
        title = m.group(1).replace('-', ' ').title()
        return {'title': title, 'year': m.group(2), 'resolution': m.group(3) + 'p'}
    return None


def normalize_movie_title(title: str) -> str:
    title = re.sub(r'^\s*\[[^\]]+\]\s*', '', title).strip()
    title = title.replace('+', ' ')
    title = _RE_MULTI_SPACE.sub(' ', title)
    return title.lower().replace('.', ' ').replace('-', ' ').replace('_', ' ').strip()


def format_movie_display_title(title: str, year: str) -> str:
    clean_title = title.strip()
    clean_year = (year or "").strip()
    if clean_year and re.fullmatch(r'\d{4}', clean_year):
        return f"{clean_title} ({clean_year})"
    return clean_title


def detect_input_content_types(text: str) -> Dict[str, bool]:
    has_movie = has_series = False
    for raw_line in text.strip().split('\n'):
        line = raw_line.strip()
        if not line or line.startswith('<iframe') or line.lower() == 'download link':
            continue
        candidate = None
        if line.startswith('[url='):
            bb = parse_bbcode(line)
            if bb:
                candidate = bb['filename']
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
    report: List[str] = []
    for idx, raw_line in enumerate(text.splitlines(), start=1):
        line = raw_line.strip()
        if not line:
            report.append(f"L{idx:03d}: skip (empty)")
            continue
        if line.lower() == "download link":
            report.append(f"L{idx:03d}: marker → download section")
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
                report.append(f"L{idx:03d}: BBCode movie | host={host} | title={movie_info['title']} | res={movie_info['resolution']}")
            elif series_info:
                report.append(f"L{idx:03d}: BBCode episode | host={host} | series={series_info['series_name']} | ep={series_info['episode']}")
            elif embed_host != "Other":
                report.append(f"L{idx:03d}: BBCode embed-only | embedHost={embed_host}")
            else:
                report.append(f"L{idx:03d}: skip (BBCode filename unsupported)")
            continue
        if line.startswith("<iframe"):
            sm = _RE_IFRAME_SRC.search(line)
            if not sm:
                report.append(f"L{idx:03d}: skip (iframe without src)")
                continue
            src = sm.group(1)
            embed_host = detect_embed_host_from_url(src, custom_embed_host_rules)
            url_info = parse_url_path(src)
            if url_info:
                report.append(f"L{idx:03d}: iframe embed+urlmeta | embedHost={embed_host} | series={url_info['series_name']} | ep={url_info['episode']} | res={url_info['resolution']}")
            else:
                report.append(f"L{idx:03d}: iframe embed | embedHost={embed_host}")
            continue
        if line.startswith("http://") or line.startswith("https://"):
            host = detect_hosting(line, custom_download_host_rules)
            movie_info = parse_movie_from_url(line)
            url_info = parse_url_path(line)
            if movie_info:
                report.append(f"L{idx:03d}: direct URL movie-download | host={host} | title={movie_info['title']} | res={movie_info['resolution']}")
            elif url_info:
                report.append(f"L{idx:03d}: direct URL episode-download | host={host} | series={url_info['series_name']} | ep={url_info['episode']} | res={url_info['resolution']}")
            elif host != "Other":
                report.append(f"L{idx:03d}: direct URL generic-download | host={host}")
            else:
                report.append(f"L{idx:03d}: skip (unknown direct URL host)")
            continue
        if line.startswith("["):
            movie_info = parse_movie_filename(line)
            series_info = parse_filename(line)
            if movie_info:
                report.append(f"L{idx:03d}: header movie | title={movie_info['title']} | year={movie_info['year']} | res={movie_info['resolution']}")
            elif series_info:
                report.append(f"L{idx:03d}: header episode | series={series_info['series_name']} | ep={series_info['episode']}")
            else:
                report.append(f"L{idx:03d}: skip (header pattern unsupported)")
            continue
        if " - http" in line:
            report.append(f"L{idx:03d}: filename-url pair")
            continue
        report.append(f"L{idx:03d}: skip (unrecognized format)")
    return report


def parse_url_path(url: str) -> Optional[Dict]:
    pm = re.search(r'/([^/]+)(?:\.[^/]+)?$', url)
    if not pm:
        return None
    path = pm.group(1).lower()
    m = _RE_SXXEXX.search(path)
    if m:
        season = m.group(1).zfill(2)
        episode = m.group(2).zfill(2)
    else:
        m2 = _RE_EXX.search(path)
        if not m2:
            return None
        season = None
        episode = m2.group(1).zfill(2)
    rm = _RE_RESOLUTION_PATH.search(path)
    resolution = rm.group(1) + 'p' if rm else '720p'
    sm = re.search(r'^[^/]*?[-._](.+?)(?:[-._]\d{4})?(?:[-._]s\d+)?e\d+', path)
    series_name = sm.group(1).replace('-', ' ').replace('.', ' ').replace('_', ' ').title() if sm else 'Unknown'
    return {'episode': episode, 'resolution': resolution, 'series_name': series_name, 'season': season}


def parse_custom_host_rules(raw_text: str) -> Dict[str, str]:
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


def split_url_and_label(line: str) -> tuple[str, str]:
    m = _RE_URL_LABEL.match(line.strip())
    if not m:
        return line.strip(), ""
    return m.group(1).strip(), (m.group(2) or "").strip()


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
            bb = parse_bbcode(line)
            if bb:
                url = bb['url']
        elif line.startswith('<iframe'):
            sm = _RE_IFRAME_SRC.search(line)
            if sm:
                url = sm.group(1)
        elif line.startswith('http://') or line.startswith('https://'):
            url = line.split()[0]
        if not url:
            continue
        hosting = detect_hosting(url, custom_host_rules)
        if hosting in available_set and hosting not in detected:
            detected.append(hosting)
    return detected


def parse_bbcode(line: str) -> Optional[Dict]:
    m = _RE_BBCODE.match(line)
    if m:
        return {'url': m.group(1), 'filename': m.group(2)}
    return None


def adapt_input_format(text: str) -> str:
    lines = text.splitlines()
    if not lines:
        return text

    def is_resolution_line(s: str) -> bool:
        return bool(_RE_RESOLUTION_ONLY.fullmatch(s.strip()))

    def is_episode_header_line(s: str) -> bool:
        t = s.strip()
        if not t or t.startswith('http') or t.startswith('[') or t.startswith('<iframe'):
            return False
        if is_resolution_line(t) or t.lower() == 'download link' or '.mp4' in t.lower():
            return False
        return bool(_RE_EP_HEADER.search(t))

    def is_movie_download_header_line(s: str) -> bool:
        t = s.strip()
        if not t or t.startswith('http') or t.startswith('[') or t.startswith('<iframe'):
            return False
        if is_resolution_line(t) or t.lower() == 'download link' or '.mp4' in t.lower():
            return False
        if re.search(r'(?:^|[.\s_-])(?:S\d{1,2}E\d{1,4}|E\d{1,4})(?:$|[.\s_-])', t, re.IGNORECASE):
            return False
        return bool(_RE_MOVIE_HEADER_YEAR.search(t))

    def to_tagged_filename(name: str) -> str:
        n = name.strip()
        if n.startswith('['):
            return n
        return f"[LayarAsia] {n}"

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
        m = _RE_URL_FILE_ADAPT.match(s)
        if m:
            url = m.group(1).strip()
            fname = to_tagged_filename(m.group(2).strip())
            adapted_embed.append(f"[url={url}]{fname}[/url]")
            continue
        m = _RE_FILE_IFRAME.match(s)
        if m:
            fname = to_tagged_filename(m.group(1).strip())
            iframe = m.group(2).strip()
            adapted_embed.append(f"{fname}|{iframe}")
            continue
        if re.match(r'^[^\[]+?\.mp4$', s, re.IGNORECASE):
            adapted_embed.append(to_tagged_filename(s))
            continue
        adapted_embed.append(raw)

    adapted_download: List[str] = []
    current_header = ""
    current_resolution = ""
    for raw in download_lines:
        s = raw.strip()
        if not s:
            current_header = ""
            current_resolution = ""
            adapted_download.append(raw)
            continue
        if s.startswith('[url='):
            adapted_download.append(raw)
            continue
        if s.lower() == 'download link':
            current_header = ""
            current_resolution = ""
            adapted_download.append(raw)
            continue
        if is_episode_header_line(s) or is_movie_download_header_line(s):
            current_header = s
            current_resolution = ""
            adapted_download.append(raw)
            continue
        if is_resolution_line(s):
            current_resolution = s.lower()
            adapted_download.append(raw)
            continue
        if (s.startswith('http://') or s.startswith('https://')) and current_header and current_resolution:
            filename = f"{current_header}.{current_resolution}.mp4"
            adapted_download.append(f"[url={s}][LayarAsia] {filename}[/url]")
            continue
        adapted_download.append(raw)

    if marker_idx == -1:
        return '\n'.join(adapted_embed)
    return '\n'.join(adapted_embed + [lines[marker_idx]] + adapted_download)


def detect_embed_host_from_url(url: str, custom_embed_rules: Optional[Dict[str, str]] = None) -> str:
    url_lower = url.lower()
    hosts = dict(DEFAULT_EMBED_HOST_MAP)
    if custom_embed_rules:
        hosts.update({k.lower(): v for k, v in custom_embed_rules.items() if k and v})
    for key, name in hosts.items():
        if key in url_lower:
            return name
    return 'Other'


def to_embed_src(url: str) -> str:
    url = url.strip()
    ok_m = re.search(r'ok\.ru/video/(\d+)', url, re.IGNORECASE)
    if ok_m:
        return f"https://ok.ru/videoembed/{ok_m.group(1)}?nochat=1"
    turbo_m = re.search(r'emturbovid\.com/d/([A-Za-z0-9]+)', url, re.IGNORECASE)
    if turbo_m:
        return f"https://turbovidhls.com/t/{turbo_m.group(1)}"
    return url


def derive_filemoon_download_url(iframe_or_url: str) -> Optional[str]:
    src = iframe_or_url.strip()
    if '<iframe' in src.lower():
        sm = _RE_IFRAME_SRC.search(src)
        if not sm:
            return None
        src = sm.group(1).strip()
    lower_src = src.lower()
    if not (('bysetayico.com' in lower_src) or ('byselapuix.com' in lower_src)):
        return None
    converted = _RE_FILEMOON_E_PATH.sub(r'\1/d/', src, count=1)
    if converted == src:
        return None
    return converted


def normalize_series_name(name: str) -> str:
    cleaned = name.lower().replace('.', ' ').replace('-', ' ').replace('_', ' ')
    cleaned = _RE_NORM_CHARS.sub(' ', cleaned)
    cleaned = _RE_MULTI_SPACE.sub(' ', cleaned).strip()
    return cleaned


def strip_year_tokens(name: str) -> str:
    cleaned = _RE_YEAR.sub(' ', name)
    return _RE_MULTI_SPACE.sub(' ', cleaned).strip()


def find_episode_key(episodes: Dict[str, Episode], series_name: str, ep_num: str) -> Optional[str]:
    exact_key = f"{series_name}_{ep_num}"
    if exact_key in episodes:
        return exact_key
    normalized_input = normalize_series_name(series_name)
    normalized_input_no_year = strip_year_tokens(normalized_input)
    ep_input = ep_num.lstrip('0') or ep_num
    for key, ep in episodes.items():
        ep_stored = ep.number.lstrip('0') or ep.number
        if ep_stored == ep_input:
            normalized_stored = normalize_series_name(ep.series_name)
            normalized_stored_no_year = strip_year_tokens(normalized_stored)
            if (
                normalized_input in normalized_stored or
                normalized_stored in normalized_input or
                normalized_input_no_year in normalized_stored_no_year or
                normalized_stored_no_year in normalized_input_no_year
            ):
                return key
    return None


# =============================================================================
# MOVIE PARSER
# =============================================================================

def parse_movie_input(
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
    if shorten_warnings is None:
        shorten_warnings = []

    movies: Dict[str, Episode] = {}
    lines = text.strip().split('\n')

    download_section_start = -1
    for i, line in enumerate(lines):
        if line.strip().lower() == 'download link':
            download_section_start = i
            break

    embed_lines = lines[:download_section_start] if download_section_start > 0 else lines

    movie_list = []
    seen_movie_keys: Set[str] = set()

    for line in embed_lines:
        line = line.strip()
        if not line or line.startswith('<iframe'):
            continue

        movie_info = None
        bbcode = None

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
            if key not in seen_movie_keys:
                seen_movie_keys.add(key)
                movie_list.append({'key': key, 'title': display_title})
            if bbcode:
                hostname = detect_embed_host_from_url(bbcode['url'], custom_embed_host_rules)
                embed_src = to_embed_src(bbcode["url"])
                iframe = f'<iframe src="{embed_src}" width="100%" height="100%" frameborder="0" allowfullscreen></iframe>'
                movies[key].embeds.append(EmbedData(hostname=hostname, embed=iframe))
                if hostname == 'FileMoon':
                    d_url = derive_filemoon_download_url(bbcode['url'])
                    if d_url:
                        res = movie_info.get('resolution', '720p')
                        if res not in movies[key].downloads:
                            movies[key].downloads[res] = []
                        if not any(dl.hosting == 'FileMoon' and dl.url == d_url for dl in movies[key].downloads[res]):
                            movies[key].downloads[res].append(DownloadLink(hosting='FileMoon', url=d_url, resolution=res))

    standalone_iframes = []
    byse_embeds = {}

    for line in embed_lines:
        line = line.strip()
        if '|<iframe' in line and '.mp4' in line.lower():
            left, right = line.split('|', 1)
            info = parse_movie_filename(f"[LayarAsia] {left.strip()}")
            iframe_part = right.strip()
            if info and iframe_part.startswith('<iframe'):
                key = normalize_movie_title(info['title'])
                if key not in movies:
                    display_title = format_movie_display_title(info['title'], info.get('year', ''))
                    movies[key] = Episode(number='HD', series_name=display_title, year=info.get('year', ''), season=None)
                hostname = get_embed_hostname(iframe_part, custom_embed_host_rules)
                movies[key].embeds.append(EmbedData(hostname=hostname, embed=iframe_part))
            continue
        if line.startswith('<iframe'):
            sm = _RE_IFRAME_SRC.search(line)
            if sm:
                url = sm.group(1)
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

    if movie_list and standalone_iframes:
        num_movies = len(movie_list)
        for idx, iframe in enumerate(standalone_iframes):
            movie_idx = idx % num_movies
            key = movie_list[movie_idx]['key']
            if key in movies:
                hostname = get_embed_hostname(iframe, custom_embed_host_rules)
                movies[key].embeds.append(EmbedData(hostname=hostname, embed=iframe))

    for key, res_dict in byse_embeds.items():
        if res_dict and key in movies:
            highest_res = max(res_dict.keys())
            iframe = res_dict[highest_res]
            hostname = get_embed_hostname(iframe, custom_embed_host_rules)
            movies[key].embeds.append(EmbedData(hostname=hostname, embed=iframe))

    for key in movies:
        movies[key].embeds.sort(key=lambda e: get_embed_priority(e.embed, custom_embed_host_rules))

    for key, movie in movies.items():
        for e in movie.embeds:
            d_url = derive_filemoon_download_url(e.embed)
            if not d_url:
                continue
            res = extract_resolution(d_url)
            if res not in movie.downloads:
                movie.downloads[res] = []
            if not any(dl.hosting == 'FileMoon' and dl.url == d_url for dl in movie.downloads[res]):
                movie.downloads[res].append(DownloadLink(hosting='FileMoon', url=d_url, resolution=res))

    if download_section_start > 0:
        download_lines = lines[download_section_start + 1:]
        unassigned_links_by_host: Dict[str, List[str]] = {}
        pending_embed_movie_info: Optional[Dict] = None

        def ensure_movie_from_info(movie_info: Dict) -> str:
            key = normalize_movie_title(movie_info['title'])
            display_title = format_movie_display_title(movie_info['title'], movie_info.get('year', ''))
            if key not in movies:
                movies[key] = Episode(number='HD', series_name=display_title, year=movie_info.get('year', ''), season=None)
            return key

        def add_embed_for_movie(movie_info: Dict, raw_url: str, embed_host: str):
            key = ensure_movie_from_info(movie_info)
            embed_src = to_embed_src(raw_url)
            iframe = f'<iframe src="{embed_src}" width="100%" height="100%" frameborder="0" allowfullscreen></iframe>'
            sm2 = _RE_IFRAME_SRC.search(iframe)
            target_src = sm2.group(1).lower() if sm2 else ""
            exists = any(
                (lambda sm3=_RE_IFRAME_SRC.search(e.embed): sm3 and sm3.group(1).lower() == target_src)()
                for e in movies[key].embeds
            )
            if not exists:
                movies[key].embeds.append(EmbedData(hostname=embed_host, embed=iframe))
            if embed_host == 'FileMoon':
                d_url = derive_filemoon_download_url(raw_url)
                if d_url:
                    res = movie_info.get('resolution', '720p')
                    if res not in movies[key].downloads:
                        movies[key].downloads[res] = []
                    if not any(dl.hosting == 'FileMoon' and dl.url == d_url for dl in movies[key].downloads[res]):
                        movies[key].downloads[res].append(DownloadLink(hosting='FileMoon', url=d_url, resolution=res))

        for line in download_lines:
            line = line.strip()
            if not line:
                pending_embed_movie_info = None
                continue
            if line.lower() == 'download link':
                pending_embed_movie_info = None
                continue
            if '|<iframe' in line and '.mp4' in line.lower():
                left, right = line.split('|', 1)
                info = parse_movie_filename(f"[LayarAsia] {left.strip()}")
                if info and right.strip().startswith('<iframe'):
                    sm3 = _RE_IFRAME_SRC.search(right)
                    if sm3:
                        hostname = get_embed_hostname(right.strip(), custom_embed_host_rules)
                        add_embed_for_movie(info, sm3.group(1), hostname)
                continue
            if (line.lower().endswith('.mp4') or line.lower().endswith('.mp4.mp4')) and not line.startswith('http') and not line.startswith('[url='):
                pending_embed_movie_info = parse_movie_filename(f"[LayarAsia] {line}")
                continue
            if line.startswith('<iframe'):
                if pending_embed_movie_info:
                    sm4 = _RE_IFRAME_SRC.search(line)
                    if sm4:
                        hostname = get_embed_hostname(line, custom_embed_host_rules)
                        add_embed_for_movie(pending_embed_movie_info, sm4.group(1), hostname)
                pending_embed_movie_info = None
                continue

            movie_info, url, hosting = None, None, None

            if 'mirrored' in line.lower() and line.startswith('http'):
                url, hosting = line, 'Mirrored'
                fn_match = _RE_MIRRORED_FN.search(line)
                if fn_match:
                    movie_info = parse_movie_filename(fn_match.group(1))
            elif line.startswith('[url='):
                bbcode_match = _RE_BBCODE.match(line)
                if bbcode_match:
                    url, filename = bbcode_match.group(1), bbcode_match.group(2)
                    movie_info = parse_movie_filename(filename)
                    hosting = detect_hosting(url, custom_download_host_rules)
                    embed_host = detect_embed_host_from_url(url, custom_embed_host_rules)
                    if movie_info and embed_host != 'Other' and hosting == 'Other':
                        add_embed_for_movie(movie_info, url, embed_host)
                        continue
            elif line.startswith('http'):
                raw_url, trailing_label = split_url_and_label(line)
                label_info = parse_movie_filename(f"[LayarAsia] {trailing_label}") if trailing_label else None
                embed_host = detect_embed_host_from_url(raw_url, custom_embed_host_rules)
                hosting = detect_hosting(raw_url, custom_download_host_rules)
                if label_info and embed_host != 'Other' and (
                    hosting == 'Other' or re.search(r'/(e|t|embed)/', raw_url, re.IGNORECASE)
                ):
                    add_embed_for_movie(label_info, raw_url, embed_host)
                    continue
                movie_info = parse_movie_from_url(raw_url) or label_info
                if movie_info:
                    url = raw_url
                else:
                    if embed_host != 'Other' and re.search(r'/(e|t|embed)/', raw_url, re.IGNORECASE):
                        continue
                    if hosting != 'Other':
                        unassigned_links_by_host.setdefault(hosting, []).append(raw_url)

            if movie_info and url and hosting:
                url = maybe_shorten_url(url, hosting, shorten_hosts, api_key, shortener_provider, shorten_warnings,
                                        f"[Movie {movie_info.get('title', '-')}]")
                key = normalize_movie_title(movie_info['title'])
                display_title = format_movie_display_title(movie_info['title'], movie_info.get('year', ''))
                res = movie_info['resolution']
                if key not in movies:
                    movies[key] = Episode(number='HD', series_name=display_title, year=movie_info['year'], season=None)
                if res not in movies[key].downloads:
                    movies[key].downloads[res] = []
                movies[key].downloads[res].append(DownloadLink(hosting=hosting, url=url, resolution=res))

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
                    url = maybe_shorten_url(url, host_name, shorten_hosts, api_key, shortener_provider, shorten_warnings,
                                            f"[Movie {movie_entry.get('title', '-')}]")
                    if res not in movies[key].downloads:
                        movies[key].downloads[res] = []
                    if not any(l.hosting == host_name and l.url == url for l in movies[key].downloads[res]):
                        movies[key].downloads[res].append(DownloadLink(hosting=host_name, url=url, resolution=res))
                if host_idx >= len(host_links):
                    break

    for key in movies:
        movies[key].embeds.sort(key=lambda e: get_embed_priority(e.embed, custom_embed_host_rules))

    return movies


# =============================================================================
# SERIES PARSER
# =============================================================================

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
    if shorten_warnings is None:
        shorten_warnings = []

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

    if not has_explicit_download_marker:
        non_empty = [ln.strip() for ln in lines if ln.strip()]
        has_iframe = any('<iframe' in ln.lower() for ln in non_empty)
        bbcode_lines = [ln for ln in non_empty if ln.startswith('[url=')]
        if not has_iframe and bbcode_lines:
            recognized_download = sum(
                1 for ln in bbcode_lines
                if (bb := parse_bbcode(ln)) and detect_hosting(bb['url'], custom_download_host_rules) != 'Other'
            )
            if recognized_download / max(len(bbcode_lines), 1) >= 0.6:
                force_download_only = True

    embed_lines = [] if force_download_only else (lines[:download_section_start] if download_section_start > 0 else lines)
    standalone_embeds = []
    veev_embeds: Dict[str, Dict[int, str]] = {}
    url_embeds: Dict[str, Dict[int, str]] = {}

    series_header_list = []

    for line in embed_lines:
        line = line.strip()
        if not line:
            continue
        if line.startswith('<iframe'):
            break

        if line.startswith('[url='):
            bbcode = parse_bbcode(line)
            if bbcode:
                info = parse_filename(bbcode['filename'])
                if info:
                    unique_key = f"{info['series_name']}_{info['episode']}"
                    info['unique_key'] = unique_key
                    info['bbcode_url'] = bbcode['url']
                    series_header_list.append(info)
                    if unique_key not in episodes:
                        episodes[unique_key] = Episode(
                            number=info['episode'], series_name=info['series_name'],
                            year=info.get('year', ''), season=info.get('season', '')
                        )
                    hostname = detect_embed_host_from_url(bbcode['url'], custom_embed_host_rules)
                    if hostname != 'Other':
                        embed_src = to_embed_src(bbcode["url"])
                        iframe = f'<iframe src="{embed_src}" width="100%" height="100%" frameborder="0" allowfullscreen></iframe>'
                        episodes[unique_key].embeds.append(EmbedData(hostname=hostname, embed=iframe))
                        if hostname == 'FileMoon':
                            d_url = derive_filemoon_download_url(bbcode['url'])
                            if d_url:
                                res = extract_resolution(bbcode['filename'])
                                if res not in episodes[unique_key].downloads:
                                    episodes[unique_key].downloads[res] = []
                                if not any(dl.hosting == 'FileMoon' and dl.url == d_url for dl in episodes[unique_key].downloads[res]):
                                    episodes[unique_key].downloads[res].append(DownloadLink(hosting='FileMoon', url=d_url, resolution=res))
            continue

        if line.startswith('[') and '|' not in line:
            info = parse_filename(line)
            if info:
                unique_key = f"{info['series_name']}_{info['episode']}"
                info['unique_key'] = unique_key
                series_header_list.append(info)
                if unique_key not in episodes:
                    episodes[unique_key] = Episode(
                        number=info['episode'], series_name=info['series_name'],
                        year=info.get('year', ''), season=info.get('season', '')
                    )

    series_header_episodes = {h['episode'] for h in series_header_list}

    i = 0
    while i < len(embed_lines):
        line = embed_lines[i].strip()
        if line.startswith('[url='):
            bbcode = parse_bbcode(line)
            if bbcode:
                info = parse_filename(bbcode['filename'])
                if info:
                    key = find_episode_key(episodes, info['series_name'], info['episode'])
                    if not key:
                        key = f"{info['series_name']}_{info['episode']}"
                        episodes[key] = Episode(
                            number=info['episode'], series_name=info['series_name'],
                            year=info.get('year', ''), season=info.get('season', ''),
                        )
                    hostname = detect_embed_host_from_url(bbcode['url'], custom_embed_host_rules)
                    if hostname != 'Other':
                        embed_src = to_embed_src(bbcode["url"])
                        embed_code = f'<iframe src="{embed_src}" width="100%" height="100%" frameborder="0" allowfullscreen></iframe>'
                        sm = _RE_IFRAME_SRC.search(embed_code)
                        target_src = sm.group(1).lower() if sm else ""
                        exists = any(
                            (lambda sm2=_RE_IFRAME_SRC.search(e.embed): sm2 and sm2.group(1).lower() == target_src)()
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
                                if not any(dl.hosting == 'FileMoon' and dl.url == d_url for dl in episodes[key].downloads[res]):
                                    episodes[key].downloads[res].append(DownloadLink(hosting='FileMoon', url=d_url, resolution=res))
            i += 1
            continue

        if line.startswith('[') and '|' not in line and ' - <iframe' not in line:
            info = parse_filename(line)
            if info and i + 1 < len(embed_lines):
                next_line = embed_lines[i + 1].strip()
                if next_line.startswith('<iframe') and info['episode'] not in series_header_episodes:
                    ep_num = info['episode']
                    key = find_episode_key(episodes, info['series_name'], ep_num)
                    if not key:
                        key = f"{info['series_name']}_{ep_num}"
                        episodes[key] = Episode(
                            number=ep_num, series_name=info['series_name'],
                            year=info.get('year', ''), season=info.get('season', ''),
                        )
                    hostname = get_embed_hostname(next_line, custom_embed_host_rules)
                    episodes[key].embeds.append(EmbedData(hostname=hostname, embed=next_line))
                    i += 2
                    continue

        elif line.startswith('<iframe'):
            sm = _RE_IFRAME_SRC.search(line)
            if sm:
                url = sm.group(1)
                url_info = parse_url_path(url)
                if url_info:
                    ep_num = url_info['episode']
                    res = url_info['resolution']
                    series_name = url_info['series_name']
                    res_num = int(re.search(r'\d+', res).group())
                    key = find_episode_key(episodes, series_name, ep_num)
                    if key:
                        if key not in url_embeds:
                            url_embeds[key] = {}
                        if res_num not in url_embeds[key] or res_num > max(url_embeds[key].keys(), default=0):
                            url_embeds[key][res_num] = line
                    else:
                        standalone_embeds.append(line)
                else:
                    standalone_embeds.append(line)
            else:
                standalone_embeds.append(line)

        elif '|' in line and '<iframe' in line:
            pass

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
                        number=ep_num, series_name=info['series_name'],
                        year=info.get('year', ''), season=info.get('season', ''),
                    )
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

    for key, res_dict in veev_embeds.items():
        if res_dict and key in episodes:
            highest_res = max(res_dict.keys())
            iframe_code = res_dict[highest_res]
            hostname = get_embed_hostname(iframe_code, custom_embed_host_rules)
            episodes[key].embeds.append(EmbedData(hostname=hostname, embed=iframe_code))

    for key, res_dict in url_embeds.items():
        if res_dict and key in episodes:
            highest_res = max(res_dict.keys())
            iframe_code = res_dict[highest_res]
            hostname = get_embed_hostname(iframe_code, custom_embed_host_rules)
            episodes[key].embeds.append(EmbedData(hostname=hostname, embed=iframe_code))

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
                        number=ep_num, series_name=info['series_name'],
                        year=info.get('year', ''), season=info.get('season', ''),
                    )
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
        current_resolution = None
        current_key = None
        resolution_links: Dict[str, Dict[str, List[tuple]]] = {}

        for line in download_lines:
            line = line.strip()
            if not line:
                continue

            if line.startswith('[url='):
                bbcode_match = _RE_BBCODE.match(line)
                if bbcode_match:
                    url, filename = bbcode_match.group(1), bbcode_match.group(2)
                    ep_match = _RE_EP_FILENAME.search(filename)
                    res = extract_resolution(filename)
                    if ep_match:
                        ep_num = ep_match.group(1) or ep_match.group(2)
                        hosting = detect_hosting(url, custom_download_host_rules)
                        url = maybe_shorten_url(url, hosting, shorten_hosts, api_key, shortener_provider, shorten_warnings,
                                                f"[Episode {ep_num}]")
                        info = parse_filename(filename)
                        if info:
                            key = find_episode_key(episodes, info['series_name'], ep_num)
                            if not key:
                                key = f"{info['series_name']}_{ep_num}"
                                episodes[key] = Episode(number=ep_num, series_name=info['series_name'],
                                                        year='', season=info.get('season', ''))
                        else:
                            key = ep_num
                            if key not in episodes:
                                episodes[key] = Episode(number=ep_num, series_name='Unknown', year='', season='')
                        current_key = key
                        current_resolution = res
                        if key not in resolution_links:
                            resolution_links[key] = {}
                        if res not in resolution_links[key]:
                            resolution_links[key][res] = []
                        resolution_links[key][res].append((hosting, url))

            elif line.startswith('http'):
                raw_url, trailing_label = split_url_and_label(line)
                url_info = parse_url_path(raw_url)
                hosting = detect_hosting(raw_url, custom_download_host_rules)
                url = maybe_shorten_url(raw_url, hosting, shorten_hosts, api_key, shortener_provider, shorten_warnings,
                                        f"[URL {raw_url[:40]}]")
                label_info = parse_filename(trailing_label) if trailing_label else None
                label_res = extract_resolution(trailing_label) if trailing_label else None

                if url_info:
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
                    ep_num = label_info['episode']
                    res = label_res or '720p'
                    series_name = label_info['series_name']
                    key = find_episode_key(episodes, series_name, ep_num)
                    if not key:
                        key = f"{series_name}_{ep_num}"
                        episodes[key] = Episode(number=ep_num, series_name=series_name,
                                                year=label_info.get('year', ''), season=label_info.get('season', ''))
                    current_key = key
                    current_resolution = res
                    if key not in resolution_links:
                        resolution_links[key] = {}
                    if res not in resolution_links[key]:
                        resolution_links[key][res] = []
                    resolution_links[key][res].append((hosting, url))
                elif hosting == 'Mirrored':
                    download_urls.append(raw_url)
                elif current_key and current_resolution:
                    if current_key not in resolution_links:
                        resolution_links[current_key] = {}
                    if current_resolution not in resolution_links[current_key]:
                        resolution_links[current_key][current_resolution] = []
                    resolution_links[current_key][current_resolution].append((hosting, url))
                else:
                    download_urls.append(raw_url)

            elif ' - http' in line:
                parts = line.split(' - http', 1)
                filename, url = parts[0].strip(), 'http' + parts[1].strip()
                ep_match = _RE_EP_FILENAME.search(filename)
                res = extract_resolution(filename)
                if ep_match:
                    ep_num = ep_match.group(1) or ep_match.group(2)
                    hosting = detect_hosting(url, custom_download_host_rules)
                    url = maybe_shorten_url(url, hosting, shorten_hosts, api_key, shortener_provider, shorten_warnings,
                                            f"[Episode {ep_num}]")
                    if ep_num not in episodes:
                        info = parse_filename(filename)
                        episodes[ep_num] = Episode(number=ep_num,
                                                   series_name=info['series_name'] if info else 'Unknown',
                                                   year='', season=info.get('season', '') if info else '')
                    if res not in episodes[ep_num].downloads:
                        episodes[ep_num].downloads[res] = []
                    episodes[ep_num].downloads[res].append(DownloadLink(hosting=hosting, url=url, resolution=res))

        for key, res_dict in resolution_links.items():
            if key in episodes:
                for res, links in res_dict.items():
                    if res not in episodes[key].downloads:
                        episodes[key].downloads[res] = []
                    for hosting, url in links:
                        episodes[key].downloads[res].append(DownloadLink(hosting=hosting, url=url, resolution=res))

        for url in download_urls:
            if 'mirrored' in url.lower():
                parsed_info = None
                fn_match = _RE_MIRRORED_FN.search(url)
                if fn_match:
                    parsed_info = parse_filename(fn_match.group(1))
                if parsed_info:
                    series_from_url = parsed_info['series_name']
                    ep_num = parsed_info['episode']
                    season = parsed_info.get('season', '')
                else:
                    series_match = _RE_MIRRORED_EP.search(url)
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
                final_url = maybe_shorten_url(url, 'Mirrored', shorten_hosts, api_key, shortener_provider, shorten_warnings,
                                              f"[Episode {ep_num}]")
                episodes[key].downloads[res].append(DownloadLink(hosting='Mirrored', url=final_url, resolution=res))

        for url in download_urls:
            if 'mirrored' in url.lower():
                detected_series = None
                fn_match = _RE_MIRRORED_FN.search(url)
                if fn_match:
                    parsed_info = parse_filename(fn_match.group(1))
                    if parsed_info:
                        detected_series = parsed_info['series_name']
                if not detected_series:
                    sm = _RE_MIRRORED_SERIES.search(url)
                    if sm:
                        detected_series = sm.group(1).replace('_', ' ')
                if detected_series:
                    for ep in episodes.values():
                        if ep.series_name == "Unknown":
                            ep.series_name = detected_series
                    break

        if standalone_embeds and len(episodes) == 1:
            ep_key = list(episodes.keys())[0]
            for embed in standalone_embeds:
                hostname = get_embed_hostname(embed, custom_embed_host_rules)
                episodes[ep_key].embeds.append(EmbedData(hostname=hostname, embed=embed))

    for ep in episodes.values():
        ep.embeds.sort(key=lambda x: get_embed_priority(x.embed, custom_embed_host_rules))

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
                if not _RE_RESOLUTION.search(d_url):
                    continue
                res = extract_resolution(d_url)
            if res not in ep.downloads:
                ep.downloads[res] = []
            if not any(dl.hosting == 'FileMoon' and dl.url == d_url for dl in ep.downloads[res]):
                ep.downloads[res].append(DownloadLink(hosting='FileMoon', url=d_url, resolution=res))

    return episodes


# =============================================================================
# JS GENERATOR
# =============================================================================

def generate_quickfill_js(episode: Episode, subbed: str = "Sub", fill_mode: str = "replace") -> str:
    embeds_js = ',\n'.join([
        f"""        {{ hostname: "{e.hostname}", embed: '{e.embed.replace("'", "\\'")}' }}"""
        for e in episode.embeds
    ])

    hosting_priority = {
        "Terabox": 0, "BuzzHeavier": 1, "Gofile": 2,
        "FileMoon": 3, "VidHide": 4, "Mirrored": 5,
    }

    resolutions_js = []
    for res in sorted(episode.downloads.keys(), key=lambda x: int(re.search(r'\d+', x).group())):
        sorted_links = sorted(
            episode.downloads[res],
            key=lambda l: (hosting_priority.get(l.hosting, 999), l.hosting.lower(), l.url.lower())
        )
        links_js = ',\n'.join([
            f'                    {{ hosting: "{l.hosting}", url: "{l.url}" }}'
            for l in sorted_links
        ])
        resolutions_js.append(
            f'            {{ pixel: "{res}", links: [\n{links_js}\n                ] }}'
        )
    resolutions_str = ',\n'.join(resolutions_js)

    def series_has_season(name: str, season: str) -> bool:
        if not season:
            return False
        season_norm = season.lstrip('0') or season
        p1 = re.compile(rf'\bseason\s*0*{re.escape(season_norm)}\b', re.IGNORECASE)
        p2 = re.compile(rf'\bs0*{re.escape(season_norm)}\b', re.IGNORECASE)
        return bool(p1.search(name) or p2.search(name))

    season_display = episode.season.lstrip('0') or episode.season if episode.season else ""
    ep_display = episode.number.lstrip('0') or episode.number
    season_str = f" Season {season_display}" if season_display and not series_has_season(episode.series_name, episode.season) else ""

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
                if (clone) continue;
                const targetIdx = clones.length;
                while (clones.length <= targetIdx) {{ await addClone(container); clones = getClones(container); }}
                clone = clones[targetIdx];
            }} else {{
                while (clones.length <= i) {{ await addClone(container); clones = getClones(container); }}
                clone = clones[i];
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
                    while (resClones.length <= resClones.length) {{ await addClone(resContainer); resClones = getClones(resContainer); }}
                    resClone = resClones[resClones.length - 1];
                }}
            }} else {{
                while (resClones.length <= r) {{ await addClone(resContainer); resClones = getClones(resContainer); }}
                resClone = resClones[r];
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
                            urlField.value = linkData.url; trigger(urlField);
                        }}
                        continue;
                    }}
                    while (linkClones.length <= linkClones.length) {{ await addClone(linkContainer); linkClones = getClones(linkContainer); }}
                    linkClone = linkClones[linkClones.length - 1];
                }} else {{
                    while (linkClones.length <= l) {{ await addClone(linkContainer); linkClones = getClones(linkContainer); }}
                    linkClone = linkClones[l];
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
    const seriesHasSeason = seasonNum ? (
        seriesNorm.includes(`season ${{seasonNum}}`) || seriesNorm.includes(`s${{seasonNum}}`)
    ) : false;
    const epNum = d.episodeNumber.replace(/^0+/, '') || d.episodeNumber;
    const seasonPart = (seasonNum && !seriesHasSeason) ? ` Season ${{seasonNum}}` : '';
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
# STREAMLIT APP
# =============================================================================

st.set_page_config(
    page_title="DramaStream Quickfill",
    page_icon="▶",
    layout="wide",
    initial_sidebar_state="collapsed",
)
inject_custom_css()

# Session state init
for key, default in [
    ('generated_scripts', {}),
    ('parser_debug_report', []),
    ('shorten_warnings', []),
    ('generate_version', 0),
]:
    if key not in st.session_state:
        st.session_state[key] = default

# ── Header ──────────────────────────────────────────────────────────────────
st.markdown("# DramaStream Quickfill")
st.caption("Generate autofill scripts untuk posting episode ke WordPress")
st.markdown("---")

col1, col2 = st.columns(2, gap="large")

# ── INPUT COLUMN ─────────────────────────────────────────────────────────────
with col1:
    st.markdown("### Input")

    series_name = st.text_input(
        "Series Name (optional)",
        placeholder="Auto-detect dari filename/URL",
    )

    input_text = st.text_area(
        "Episode Data",
        height=260,
        placeholder="<iframe src=...></iframe>\nid | <iframe ...></iframe>\n[url=URL][filename][/url]\n\nDownload Link\n\nhttps://mirrored.to/...",
    )

    fill_mode_label = st.selectbox(
        "Fill Mode",
        options=["Append (keep existing data)", "Replace (overwrite from top)"],
        index=0,
    )
    fill_mode = "append" if fill_mode_label.startswith("Append") else "replace"

    parser_debug_enabled = st.checkbox(
        "Parser Debug Mode",
        value=False,
        help="Tampilkan diagnostik parsing per-baris setelah Generate.",
    )

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

    with st.expander("Link Shortening", expanded=False):
        shortener_enabled = st.checkbox("Enable Link Shortening", value=False, key="shortener_enabled")
        if shortener_enabled:
            provider_label = st.selectbox(
                "Provider",
                options=["ouo.io", "safelinkearn.com", "safelinku.com"],
                index=2,
                key="shortener_provider_select",
            )
            if provider_label.startswith("safelinkearn"):
                shortener_provider = "safelinkearn"
            elif provider_label.startswith("safelinku"):
                shortener_provider = "safelinku"
            else:
                shortener_provider = "ouo"

            if shortener_provider == "ouo":
                shortener_api_key = st.text_input("API Key", value=DEFAULT_OUO_API_KEY, type="password", key="ouo_key")
            elif shortener_provider == "safelinkearn":
                shortener_api_key = st.text_input("API Token", value=DEFAULT_SAFELINKEARN_API_TOKEN, type="password", key="sle_key")
            else:
                shortener_api_key = st.text_input("API Token", value=DEFAULT_SAFELINKU_API_TOKEN, type="password", key="slu_key")

            base_hosts = ['BuzzHeavier', 'Gofile', 'Upfiles', 'Terabox', 'FileMoon', 'Mirrored', 'Jioupload', 'Filekeeper', 'VidHide']
            excluded_auto_hosts = {'Mirrored', 'Terabox', 'FileMoon', 'VidHide'}
            custom_hosts = sorted({v for v in custom_download_host_rules.values() if v})
            available_hosts = sorted(set(base_hosts + custom_hosts))
            detected_hosts = detect_shorten_hosts_from_input(input_text, available_hosts, custom_download_host_rules)
            auto_hosts = [h for h in detected_hosts if h not in excluded_auto_hosts] or ['BuzzHeavier', 'Gofile']

            input_sig = input_text.strip()
            prev_sig = st.session_state.get("_shorten_hosts_input_sig")
            prev_auto = st.session_state.get("_shorten_hosts_auto", [])
            current_sel = st.session_state.get("shorten_hosts")

            if "shorten_hosts" not in st.session_state:
                st.session_state["shorten_hosts"] = auto_hosts
            elif prev_sig != input_sig and (not current_sel or current_sel == prev_auto):
                st.session_state["shorten_hosts"] = auto_hosts

            st.session_state["_shorten_hosts_input_sig"] = input_sig
            st.session_state["_shorten_hosts_auto"] = auto_hosts

            shorten_hosts = st.multiselect("Servers to shorten", options=available_hosts, key="shorten_hosts")
            if detected_hosts:
                st.caption(f"Terdeteksi di input: {', '.join(detected_hosts)} — auto-exclude: Mirrored, Terabox, FileMoon, VidHide")
            else:
                st.caption("Belum ada host terdeteksi (fallback: BuzzHeavier, Gofile)")
            st.caption("Link yang diperpendek di-cache 1 jam.")
        else:
            shortener_provider = "ouo"
            shortener_api_key = ""
            shorten_hosts = []

    # ── GENERATE BUTTON ──────────────────────────────────────────────────────
    if st.button("⚡ Generate", type="primary", use_container_width=True):
        if not input_text.strip():
            st.warning("Masukkan episode data terlebih dahulu.")
        else:
            adapted = adapt_input_format(input_text)
            shorten_set = set(shorten_hosts) if shortener_enabled else set()
            active_key = shortener_api_key if shortener_enabled else ""
            sw: List[str] = []

            parser_report = (
                build_parser_debug_report(adapted, custom_download_host_rules, custom_embed_host_rules)
                if parser_debug_enabled else []
            )

            content_types = detect_input_content_types(adapted)
            has_movie = content_types['has_movie']
            has_series = content_types['has_series']

            with st.spinner("Parsing & generating..."):
                movie_items: Dict[str, Episode] = {}
                series_items: Dict[str, Episode] = {}

                if has_movie:
                    movie_items = parse_movie_input(
                        adapted, shorten_set, active_key, shortener_provider,
                        custom_download_host_rules, custom_embed_host_rules, sw,
                    )
                if has_series or (not has_movie and not has_series):
                    series_items = parse_input(
                        adapted, shorten_set, active_key, shortener_provider,
                        custom_download_host_rules, custom_embed_host_rules, sw,
                    )

            if series_name:
                for ep in movie_items.values():
                    ep.series_name = series_name
                for ep in series_items.values():
                    ep.series_name = series_name

            scripts = {}

            for key, ep in sorted(movie_items.items()):
                scripts[f"movie::{key}"] = {
                    'js': generate_quickfill_js(ep, fill_mode=fill_mode),
                    'embeds': len(ep.embeds),
                    'resolutions': list(ep.downloads.keys()),
                    'series': ep.series_name,
                    'episode': ep.number,
                    'season': ep.season or '',
                    'is_movie': True,
                }

            for key, ep in sorted(series_items.items(), key=lambda item: (item[1].series_name, int(item[1].number) if item[1].number.isdigit() else 0)):
                scripts[f"series::{key}"] = {
                    'js': generate_quickfill_js(ep, fill_mode=fill_mode),
                    'embeds': len(ep.embeds),
                    'resolutions': list(ep.downloads.keys()),
                    'series': ep.series_name,
                    'episode': ep.number,
                    'season': ep.season or '',
                    'is_movie': False,
                }

            st.session_state.generated_scripts = scripts
            st.session_state.parser_debug_report = parser_report
            st.session_state.shorten_warnings = sorted(set(sw))
            st.session_state.generate_version += 1

            if scripts:
                mc = sum(1 for d in scripts.values() if d['is_movie'])
                sc = len(scripts) - mc
                if mc and sc:
                    st.success(f"✓ {len(scripts)} scripts generated — {mc} movie, {sc} episode")
                elif mc:
                    st.success(f"✓ {mc} movie script{'s' if mc > 1 else ''} generated")
                else:
                    st.success(f"✓ {sc} episode script{'s' if sc > 1 else ''} generated")
            else:
                st.error(
                    "Tidak ada episode/movie terdeteksi. Pastikan format input benar.\n\n"
                    "Format yang didukung: `[Tag] Series (Year) EXXX`, `[url=URL][filename][/url]`, "
                    "`<iframe>`, atau aktifkan **Parser Debug Mode** untuk melihat detail."
                )


# ── OUTPUT COLUMN ─────────────────────────────────────────────────────────────
with col2:
    st.markdown("### Output")

    scripts = st.session_state.generated_scripts
    if scripts:
        key_list = list(scripts.keys())
        has_any_movie  = any(scripts[k]['is_movie'] for k in key_list)
        has_any_series = any(not scripts[k]['is_movie'] for k in key_list)

        def make_label(k: str) -> str:
            d = scripts[k]
            prefix = "[Movie] " if d['is_movie'] else f"E{d['episode']} · "
            return f"{prefix}{d['series']}"

        if has_any_movie and has_any_series:
            options = [make_label(k) for k in key_list]
            selected_idx = st.selectbox("Item", range(len(options)), format_func=lambda i: options[i])
        elif has_any_movie:
            options = [scripts[k]['series'] for k in key_list]
            selected_idx = st.selectbox("Movie", range(len(options)), format_func=lambda i: options[i])
        else:
            options = [f"{scripts[k]['series']} · E{scripts[k]['episode']}" for k in key_list]
            selected_idx = st.selectbox("Episode", range(len(options)), format_func=lambda i: options[i])

        sel_key = key_list[selected_idx] if selected_idx is not None else None

        if sel_key and sel_key in scripts:
            d = scripts[sel_key]
            title = d['series']
            res_tags = " · ".join(d['resolutions']) if d['resolutions'] else "no downloads"
            embed_count = d['embeds']

            # Meta bar with clickable title copy + copy-JS button
            components.html(f"""
            <style>
            * {{ box-sizing: border-box; margin: 0; padding: 0; }}
            .meta {{ display: flex; align-items: center; justify-content: space-between; gap: 8px; }}
            .left {{ display: flex; align-items: center; gap: 8px; flex: 1; min-width: 0; }}
            .title-btn {{
                cursor: pointer; background: none; border: none; padding: 0;
                color: #fafafa; font-weight: 600; font-size: 14px;
                font-family: system-ui, sans-serif; text-align: left;
                white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
                max-width: 340px;
            }}
            .title-btn:hover {{ color: #6366f1; text-decoration: underline; }}
            .chip {{
                font-size: 11px; color: #71717a;
                font-family: system-ui, sans-serif;
                white-space: nowrap;
            }}
            .copy-js {{
                flex-shrink: 0; cursor: pointer;
                background: #27272a; border: 1px solid #3f3f46;
                border-radius: 5px; padding: 4px 10px;
                color: #fafafa; font-size: 12px; font-weight: 500;
                font-family: system-ui, sans-serif;
                transition: background 0.15s;
            }}
            .copy-js:hover {{ background: #3f3f46; }}
            </style>
            <div class="meta">
              <div class="left">
                <button class="title-btn"
                  title="Klik untuk copy judul"
                  onclick="
                    navigator.clipboard.writeText({json.dumps(title)});
                    this.style.color='#22c55e';
                    setTimeout(()=>this.style.color='#fafafa', 1500);
                  ">{title}</button>
                <span class="chip">{embed_count} embed · {res_tags}</span>
              </div>
              <button class="copy-js" id="copybtn" onclick="copyJS()">Copy JS</button>
            </div>
            <script>
            const JS_CODE = {json.dumps(d['js'])};
            function copyJS() {{
              navigator.clipboard.writeText(JS_CODE).then(() => {{
                const btn = document.getElementById('copybtn');
                btn.textContent = '✓ Copied!';
                btn.style.background = '#052e16';
                btn.style.borderColor = '#166534';
                btn.style.color = '#22c55e';
                setTimeout(() => {{
                  btn.textContent = 'Copy JS';
                  btn.style.background = '#27272a';
                  btn.style.borderColor = '#3f3f46';
                  btn.style.color = '#fafafa';
                }}, 2000);
              }});
            }}
            </script>
            """, height=40)

            st.code(d['js'], language='javascript')

            # ZIP download with collision-safe filenames
            zip_buf = io.BytesIO()
            with zipfile.ZipFile(zip_buf, 'w', zipfile.ZIP_DEFLATED) as zf:
                seen_names: Dict[str, int] = {}
                for n, data in scripts.items():
                    if data.get('is_movie'):
                        safe = re.sub(r'[^\w\s-]', '', data['series']).strip().replace(' ', '_')
                        base_name = f"quickfill_{safe}"
                    else:
                        words = data['series'].split()
                        abbrev = ''.join(w[0].upper() for w in words if w)[:10] if len(words) > 1 else data['series'][:10].replace(' ', '')
                        season_part = f"S{data['season'].zfill(2)}" if data.get('season') else ""
                        ep_part = f"E{data['episode'].zfill(2)}"
                        base_name = f"quickfill_{abbrev}_{season_part}{ep_part}" if season_part else f"quickfill_{abbrev}_{ep_part}"

                    # Deduplicate filenames
                    filename = base_name + ".js"
                    if filename in seen_names:
                        seen_names[filename] += 1
                        filename = f"{base_name}_{seen_names[filename]}.js"
                    else:
                        seen_names[filename] = 0

                    zf.writestr(filename, data['js'])

            st.download_button(
                "⬇ Download All (ZIP)",
                zip_buf.getvalue(),
                "quickfill.zip",
                "application/zip",
                use_container_width=True,
            )
    else:
        st.info("Generate scripts untuk melihat output di sini.")

# ── WARNINGS & DEBUG ──────────────────────────────────────────────────────────
if st.session_state.shorten_warnings:
    with st.expander(f"⚠ Shortener Warnings ({len(st.session_state.shorten_warnings)})", expanded=False):
        for msg in st.session_state.shorten_warnings:
            st.caption(f"• {msg}")

if st.session_state.parser_debug_report:
    with st.expander(f"🔍 Parser Debug ({len(st.session_state.parser_debug_report)} lines)", expanded=False):
        st.code('\n'.join(st.session_state.parser_debug_report), language='text')

# ── HELP ─────────────────────────────────────────────────────────────────────
with st.expander("Panduan Format Input"):
    st.markdown("""
**Format embed yang didukung:**
- `<iframe src="..."></iframe>` — embed standalone
- `[Tag] Series (Year) EXXX.mp4` diikuti baris `<iframe ...>`  
- `id | <iframe ...>` — embed dengan label episode
- `[url=URL][Tag] filename.mp4[/url]` — BBCode embed/download

**Format download (setelah baris `Download Link`):**
- URL Mirrored: `https://mirrored.to/files/...`
- BBCode: `[url=https://...][Tag] Series.E01.1080p.mp4[/url]`
- URL langsung dengan resolusi di path

**Tips:**
- Aktifkan **Parser Debug Mode** untuk melihat baris mana yang berhasil di-parse
- **Fill Mode Append** aman untuk update parsial tanpa menghapus data existing
- Nama series di field atas akan *override* nama yang terdeteksi otomatis
""")
