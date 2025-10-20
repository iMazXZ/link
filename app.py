# app.py — Universal Link Generator (Gradio)
# Cocok untuk Hugging Face Spaces (SDK: Gradio, CPU Basic).
# Fitur: input batch/single, kelola server, ouo.io shortener (cached),
# export/import sesi, generate 3 format HTML + preview.
# Catatan: Untuk menyetel OUO API Key default dari Secrets Spaces, pakai variable: OUO_API_KEY

import gradio as gr
import requests, time, json, base64, os
from datetime import datetime
from functools import lru_cache

# =========================
# Helper: pemendek ouo.io
# =========================
def shorten_with_ouo_raw(url: str, api_key: str) -> str:
    if not api_key:
        return url
    try:
        api_url = f"https://ouo.io/api/{api_key}?s={url}"
        r = requests.get(api_url, timeout=10)
        if r.status_code == 200:
            time.sleep(0.5)  # throttle ringan
            return r.text.strip()
        return url
    except requests.exceptions.RequestException:
        return url

@lru_cache(maxsize=4096)
def ouo_cached(api_key: str, url: str) -> str:
    return shorten_with_ouo_raw(url, api_key)

# =========================
# Generator HTML
# =========================
def generate_output_resolusi_per_baris(data, episode_range, resolutions, servers,
                                       use_uppercase=True, shorten_servers=None, api_key=""):
    shorten_servers = shorten_servers or []
    all_html_lines = []
    for ep_num in episode_range:
        if ep_num not in data:
            continue
        download_links = data[ep_num].get('download_links', {})
        if not any(res in download_links for res in resolutions):
            continue
        if len(episode_range) > 1:
            all_html_lines.append(f"<li><strong>EPISODE {ep_num}</strong></li>")
        for res in resolutions:
            if res not in download_links:
                continue
            line_parts = [f"<strong>{res}</strong>"]
            for server in servers:
                if server in download_links.get(res, {}):
                    url = download_links[res][server]
                    if server in shorten_servers:
                        url = ouo_cached(api_key, url)
                    display_server = server.upper() if use_uppercase else server
                    link_html = f'<a href="{url}" rel="nofollow" data-wpel-link="external">{display_server}</a>'
                    line_parts.append(link_html)
            if len(line_parts) > 1:
                all_html_lines.append("<li>" + " ".join(line_parts) + "</li>")
    return "<ul>\n" + "\n".join(all_html_lines) + "\n</ul>"

def generate_output_ringkas(data, episode_range, resolutions, servers, grouping_style,
                            use_uppercase=True, include_streaming=False,
                            shorten_servers=None, api_key=""):
    shorten_servers = shorten_servers or []
    txt_lines = []
    for ep_num in episode_range:
        if ep_num not in data:
            continue
        link_parts = []
        if include_streaming and data[ep_num].get('stream_link'):
            stream_url = data[ep_num]['stream_link']
            if "Streaming" in shorten_servers:
                stream_url = ouo_cached(api_key, stream_url)
            link_parts.append(f'<a href="{stream_url}">Streaming</a>')
        download_links = data[ep_num].get('download_links', {})
        if "Server" in grouping_style:
            for server in servers:
                for res in resolutions:
                    if res in download_links and server in download_links[res]:
                        url = download_links[res][server]
                        if server in shorten_servers:
                            url = ouo_cached(api_key, url)
                        display_server = server.upper() if use_uppercase else server
                        link_parts.append(f'<a href="{url}" rel="nofollow" data-wpel-link="external">{display_server} {res}</a>')
        else:
            for res in resolutions:
                for server in servers:
                    if res in download_links and server in download_links[res]:
                        url = download_links[res][server]
                        if server in shorten_servers:
                            url = ouo_cached(api_key, url)
                        display_server = server.upper() if use_uppercase else server
                        link_parts.append(f'<a href="{url}" rel="nofollow" data-wpel-link="external">{display_server} {res}</a>')
        if link_parts:
            txt_lines.append(f'<li><strong>EPISODE {ep_num}</strong> {" ".join(link_parts)}</li>')
    return "\n".join(txt_lines)

def generate_output_drakor(data, episode_range, resolutions, servers, use_uppercase=True,
                           is_centered=False, shorten_servers=None, api_key=""):
    shorten_servers = shorten_servers or []
    html_lines = []
    style_attr = ' style="text-align: center;"' if is_centered else ''
    for ep_num in episode_range:
        if ep_num not in data:
            continue
        if len(episode_range) > 1:
            html_lines.append(f'<p{style_attr}><strong>EPISODE {ep_num}</strong></p>')
        download_links = data[ep_num].get('download_links', {})
        for res in resolutions:
            if res not in download_links:
                continue
            link_parts = []
            for server in servers:
                if server in download_links[res]:
                    url = download_links[res][server]
                    if server in shorten_servers:
                        url = ouo_cached(api_key, url)
                    display_server = server.upper() if use_uppercase else server
                    link_parts.append(f'<a href="{url}">{display_server}</a>')
            if link_parts:
                html_lines.append(f'<p{style_attr}><strong>{res} (Hardsub Indo):</strong> {" | ".join(link_parts)}</p>')
    return "\n".join(html_lines)

# =========================
# State & operasi
# =========================
DEFAULT_RES = ["360p","480p","540p","720p","1080p"]
SERVER_OPTIONS = ["TeraBox","VidGuard","BuzzHeav","UpFiles","Mirrored","GoFileIo","AkiraBox","SendNow","KrakenFl","StreamHG"]

def init_state():
    return {
        "main_data": {},         # {ep: {"stream_link": "...", "download_links": {res: {server: url}}}}
        "server_order": [],      # ["TeraBox", ...]
        "resolutions": ["480p","720p"],
        "start_ep": 1,
        "end_ep": 1,
        "final_html": ""
    }

state = init_state()

def add_data(mode, start_ep, end_ep, server_name, links_text, stream_links_text, active_res):
    global state
    st = state.copy()
    links = [x.strip() for x in (links_text or "").splitlines() if x.strip()]
    stream_links = [x.strip() for x in (stream_links_text or "").splitlines() if x.strip()]

    if mode == "Batch Episode":
        ep_range = range(int(start_ep), int(end_ep) + 1)
        needed = len(active_res) * len(list(ep_range))
        if links and len(links) != needed:
            return f"⚠️ Jumlah link download tidak sesuai. Diperlukan: {needed}, Disediakan: {len(links)}."
        if stream_links and len(stream_links) not in (0, len(list(ep_range))):
            return f"⚠️ Jumlah link streaming ({len(stream_links)}) ≠ jumlah episode ({len(list(ep_range))})."
    else:
        ep_range = [1]
        needed = len(active_res)
        if links and len(links) != needed:
            return f"⚠️ Single Link: butuh {needed} link download, dapat {len(links)}."

    link_idx, stream_idx = 0, 0
    for ep in ep_range:
        if ep not in st["main_data"]:
            st["main_data"][ep] = {}
        if stream_links:
            st["main_data"][ep]["stream_link"] = stream_links[stream_idx] if stream_idx < len(stream_links) else st["main_data"][ep].get("stream_link")
            stream_idx += 1
        if links and server_name:
            st["main_data"][ep].setdefault("download_links", {})
            for res in active_res:
                st["main_data"][ep]["download_links"].setdefault(res, {})
                st["main_data"][ep]["download_links"][res][server_name] = links[link_idx]
                link_idx += 1
            if server_name not in st["server_order"]:
                st["server_order"].append(server_name)

    st["resolutions"] = active_res
    st["start_ep"] = int(start_ep)
    st["end_ep"] = int(end_ep)
    state = st
    return "✅ OK"

def reorder_server(name, direction):
    global state
    st = state.copy()
    if name not in st["server_order"]:
        return
    idx = st["server_order"].index(name)
    if direction == "up" and idx > 0:
        st["server_order"].insert(idx-1, st["server_order"].pop(idx))
    elif direction == "down" and idx < len(st["server_order"]) - 1:
        st["server_order"].insert(idx+1, st["server_order"].pop(idx))
    state = st

def delete_server(name):
    global state
    st = state.copy()
    if name in st["server_order"]:
        st["server_order"].remove(name)
    for ep_data in st["main_data"].values():
        if "download_links" in ep_data:
            for res_map in ep_data["download_links"].values():
                if name in res_map:
                    del res_map[name]
    state = st

def save_session():
    payload = {
        "main_data": state["main_data"],
        "server_order": state["server_order"],
        "resolutions": state["resolutions"],
        "start_ep": state["start_ep"],
        "end_ep": state["end_ep"],
    }
    js = json.dumps(payload, indent=2)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"link_generator_session_{ts}.json"
    path = f"/tmp/{filename}"
    with open(path, "w") as f:
        f.write(js)
    return path

def load_session(json_text):
    global state
    data = json.loads(json_text)
    state["main_data"] = {int(k): v for k, v in data["main_data"].items()}
    state["server_order"] = data["server_order"]
    state["resolutions"] = data["resolutions"]
    state["start_ep"] = int(data["start_ep"])
    state["end_ep"] = int(data["end_ep"])
    state["final_html"] = ""

def generate_html(fmt, api_key, include_streaming, grouping_style,
                  use_uppercase, is_centered, shorten_for):
    global state
    stt = state.copy()
    active_res = stt["resolutions"]
    episode_range = [1] if (stt["start_ep"] == 1 and stt["end_ep"] == 1) else range(stt["start_ep"], stt["end_ep"] + 1)

    if fmt == "Format Ringkas":
        html = generate_output_ringkas(
            stt["main_data"], episode_range, active_res,
            stt["server_order"], grouping_style, use_uppercase,
            include_streaming, shorten_for, api_key
        )
    elif fmt == "Format Drakor":
        html = generate_output_drakor(
            stt["main_data"], episode_range, active_res,
            stt["server_order"], use_uppercase, is_centered,
            shorten_for, api_key
        )
    else:
        html = generate_output_resolusi_per_baris(
            stt["main_data"], episode_range, active_res,
            stt["server_order"], use_uppercase, shorten_for, api_key
        )
    stt["final_html"] = html
    state = stt
    return html

# =========================
# Gradio UI
# =========================
DEFAULT_OUO = os.getenv("OUO_API_KEY", "")

with gr.Blocks(title="Universal Link Generator") as demo:
    gr.Markdown("## Universal Link Generator")

    with gr.Row():
        with gr.Column():
            ouo_api = gr.Textbox(label="API Key ouo.io", type="password", value=DEFAULT_OUO)

            input_mode = gr.Radio(["Batch Episode", "Single Link"], value="Batch Episode", label="Mode Input")
            with gr.Row():
                start_ep = gr.Number(label="Mulai Episode", value=1, precision=0)
                end_ep   = gr.Number(label="Sampai Episode", value=1, precision=0)

            res_checks = gr.CheckboxGroup(choices=DEFAULT_RES, value=["480p","720p"], label="Resolutions")

            server_name = gr.Dropdown(choices=["(Ketik Manual)"] + SERVER_OPTIONS, value="TeraBox", label="Nama Server Download")
            server_manual = gr.Textbox(label="Nama Server Manual (jika pilih '(Ketik Manual)')", value="")
            links_text = gr.Textbox(label="Tempel Link Download (1 per baris)", lines=8)
            stream_links_text = gr.Textbox(label="Link Streaming (1 per baris, opsional)", lines=4)

            add_btn = gr.Button("➕ Tambah Data", variant="primary")
            add_msg = gr.Markdown("")

            def handle_add(mode, start_ep, end_ep, server_name, server_manual, links_text, stream_links_text, res):
                name = server_manual.strip() if server_name == "(Ketik Manual)" else server_name
                return add_data(mode, int(start_ep), int(end_ep), name, links_text, stream_links_text, res)

            add_btn.click(
                handle_add,
                inputs=[input_mode, start_ep, end_ep, server_name, server_manual, links_text, stream_links_text, res_checks],
                outputs=add_msg
            )

            reset_btn = gr.Button("🔄 Reset Semua Data")
            reset_msg = gr.Markdown("")
            def reset_all():
                global state
                state = init_state()
                return "✅ Reset selesai."
            reset_btn.click(reset_all, outputs=reset_msg)

            save_btn = gr.Button("💾 Simpan Sesi (download JSON)")
            dl_json = gr.File(label="File sesi", interactive=False)
            save_btn.click(save_session, outputs=dl_json)

            load_area = gr.Textbox(label="Tempel JSON sesi di sini lalu klik 'Muat'", lines=8)
            load_btn = gr.Button("📥 Muat dari Teks")
            load_msg = gr.Markdown("")
            def do_load(txt):
                try:
                    load_session(txt); return "✅ Sesi dimuat."
                except Exception as e:
                    return f"⚠️ Gagal memuat: {e}"
            load_btn.click(do_load, inputs=load_area, outputs=load_msg)

        with gr.Column():
            gr.Markdown("### Urutan & Pengaturan Server")
            server_list = gr.Dropdown(choices=[], label="Pilih Server", interactive=True)
            refresh_btn = gr.Button("🔁 Refresh Daftar Server")
            def refresh_servers():
                return gr.Dropdown.update(choices=state["server_order"])
            refresh_btn.click(refresh_servers, outputs=server_list)

            up_btn = gr.Button("⬆️ Naikkan")
            down_btn = gr.Button("⬇️ Turunkan")
            del_btn = gr.Button("🗑️ Hapus")

            def do_up(name):
                reorder_server(name, "up")
                return gr.Dropdown.update(choices=state["server_order"], value=name)
            def do_down(name):
                reorder_server(name, "down")
                return gr.Dropdown.update(choices=state["server_order"], value=name)
            def do_del(name):
                delete_server(name)
                return gr.Dropdown.update(choices=state["server_order"], value=None)

            up_btn.click(do_up, inputs=server_list, outputs=server_list)
            down_btn.click(do_down, inputs=server_list, outputs=server_list)
            del_btn.click(do_del, inputs=server_list, outputs=server_list)

            gr.Markdown("---")
            output_fmt = gr.Radio(["Format Drakor","Format Ringkas","Format Resolusi per Baris"], value="Format Drakor", label="Format HTML")
            grouping_style = gr.Radio(["Server","Resolusi"], value="Server", label="(Ringkas) Urut berdasarkan")
            include_streaming = gr.Checkbox(label="(Ringkas) Sertakan Streaming", value=False)
            use_uppercase = gr.Checkbox(label="Server Uppercase", value=True)
            is_centered = gr.Checkbox(label="(Drakor) Rata Tengah", value=False)
            shorten_for = gr.CheckboxGroup(choices=["Streaming"] + SERVER_OPTIONS, label="Perpendek dengan ouo.io untuk server ini")

            gen_btn = gr.Button("🚀 Generate HTML", variant="primary")
            html_out = gr.Code(label="Hasil HTML", language="html")
            html_preview = gr.HTML()

            def do_generate(fmt, api_key, include_streaming, grouping_style, use_uppercase, is_centered, shorten_for):
                html = generate_html(fmt, api_key, include_streaming, grouping_style, use_uppercase, is_centered, tuple(shorten_for or []))
                return html, html

            gen_btn.click(
                do_generate,
                inputs=[output_fmt, ouo_api, include_streaming, grouping_style, use_uppercase, is_centered, shorten_for],
                outputs=[html_out, html_preview]
            )

if __name__ == "__main__":
    # Di Hugging Face Spaces, cukup panggil launch() default.
    demo.launch()
