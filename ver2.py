import streamlit as st
import json
import re
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime

# =============================================================================
# DATA CLASSES & MODELS
# =============================================================================

@dataclass
class LinkData:
    """Data class for storing link information"""
    url: str
    label: str
    server: str
    resolution: str
    
    def to_dict(self) -> Dict:
        return asdict(self)

@dataclass
class ProjectSettings:
    """Data class for project settings"""
    name: str
    description: str
    created_at: str
    last_modified: str

# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

class LinkGenerator:
    """Main class for generating different types of links"""
    
    @staticmethod
    def validate_url(url: str) -> bool:
        """Validate URL format"""
        url_pattern = re.compile(
            r'^https?://'  # http:// or https://
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
            r'localhost|'  # localhost...
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
            r'(?::\d+)?'  # optional port
            r'(?:/?|[/?]\S+)$', re.IGNORECASE)
        return url_pattern.match(url) is not None
    
    @staticmethod
    def generate_serial_links(episodes_data: Dict, grouping_style: str, resolutions: List[str]) -> str:
        """Generate HTML for serial/episode links"""
        if not episodes_data:
            return ""
            
        html_lines = []
        html_lines.append('<div class="episode-links">')
        
        for ep_num in sorted(episodes_data.keys()):
            links = []
            episode_data = episodes_data[ep_num]
            
            if "Server" in grouping_style:
                # Group by server first
                for server in sorted(episode_data.keys()):
                    server_links = []
                    for res in resolutions:
                        if res in episode_data[server]:
                            link = episode_data[server][res]
                            server_links.append(f'<a href="{link["url"]}" rel="nofollow" target="_blank" class="download-link {res.lower()}">{link["label"]}</a>')
                    if server_links:
                        links.extend(server_links)
            else:
                # Group by resolution first
                for res in resolutions:
                    res_links = []
                    for server in sorted(episode_data.keys()):
                        if res in episode_data[server]:
                            link = episode_data[server][res]
                            res_links.append(f'<a href="{link["url"]}" rel="nofollow" target="_blank" class="download-link {res.lower()}">{link["label"]}</a>')
                    if res_links:
                        links.extend(res_links)
            
            if links:
                html_lines.append(f'  <div class="episode-item">')
                html_lines.append(f'    <h3 class="episode-title">Episode {ep_num}</h3>')
                html_lines.append(f'    <div class="episode-links-container">')
                html_lines.append(f'      {" | ".join(links)}')
                html_lines.append(f'    </div>')
                html_lines.append(f'  </div>')
        
        html_lines.append('</div>')
        return "\n".join(html_lines)
    
    @staticmethod
    def generate_single_content_links(data: Dict, resolutions: List[str], servers: List[str]) -> str:
        """Generate HTML for single content links (Korean drama style)"""
        if not data:
            return ""
            
        html_lines = []
        html_lines.append('<div class="single-content-links">')
        
        for res in resolutions:
            if res not in data:
                continue
                
            server_links = []
            for server in servers:
                if server in data[res]:
                    url = data[res][server]
                    server_links.append(f'<a href="{url}" target="_blank" class="server-link">{server}</a>')
            
            if server_links:
                links_string = " | ".join(server_links)
                html_lines.append(f'  <div class="resolution-group">')
                html_lines.append(f'    <h4 class="resolution-title">{res} (Hardsub Indo)</h4>')
                html_lines.append(f'    <div class="server-links">{links_string}</div>')
                html_lines.append(f'  </div>')
        
        html_lines.append('</div>')
        return "\n".join(html_lines)
    
    @staticmethod
    def generate_css_styles() -> str:
        """Generate CSS styles for the HTML output"""
        return """
        <style>
        .episode-links, .single-content-links {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
        }
        
        .episode-item {
            background: #f8f9fa;
            border: 1px solid #dee2e6;
            border-radius: 8px;
            margin: 15px 0;
            padding: 15px;
            transition: box-shadow 0.3s ease;
        }
        
        .episode-item:hover {
            box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        }
        
        .episode-title {
            color: #2c3e50;
            margin: 0 0 10px 0;
            font-size: 1.2em;
            font-weight: 600;
        }
        
        .resolution-group {
            text-align: center;
            margin: 20px 0;
            padding: 15px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border-radius: 10px;
            color: white;
        }
        
        .resolution-title {
            margin: 0 0 10px 0;
            font-size: 1.1em;
            font-weight: 600;
        }
        
        .download-link, .server-link {
            display: inline-block;
            padding: 8px 16px;
            margin: 3px;
            background: #007bff;
            color: white !important;
            text-decoration: none;
            border-radius: 20px;
            font-size: 0.9em;
            font-weight: 500;
            transition: all 0.3s ease;
        }
        
        .download-link:hover, .server-link:hover {
            background: #0056b3;
            transform: translateY(-2px);
            box-shadow: 0 4px 8px rgba(0,0,0,0.2);
        }
        
        .download-link.720p, .download-link.1080p {
            background: #28a745;
        }
        
        .download-link.720p:hover, .download-link.1080p:hover {
            background: #1e7e34;
        }
        
        .server-links {
            margin-top: 10px;
        }
        </style>
        """

# =============================================================================
# SESSION STATE MANAGEMENT
# =============================================================================

class SessionManager:
    """Manage Streamlit session state"""
    
    @staticmethod
    def initialize_session():
        """Initialize session state variables"""
        defaults = {
            'serial_data': {},
            'serial_final_html': "",
            'single_data': {},
            'single_server_order': [],
            'single_final_html': "",
            'project_settings': ProjectSettings(
                name="Untitled Project",
                description="",
                created_at=datetime.now().isoformat(),
                last_modified=datetime.now().isoformat()
            ),
            'show_advanced_options': False,
            'custom_css': "",
            'history': []
        }
        
        for key, value in defaults.items():
            if key not in st.session_state:
                st.session_state[key] = value
    
    @staticmethod
    def export_project() -> Dict:
        """Export current project data"""
        return {
            'serial_data': st.session_state.serial_data,
            'single_data': st.session_state.single_data,
            'single_server_order': st.session_state.single_server_order,
            'project_settings': asdict(st.session_state.project_settings),
            'custom_css': st.session_state.custom_css
        }
    
    @staticmethod
    def import_project(data: Dict):
        """Import project data"""
        st.session_state.serial_data = data.get('serial_data', {})
        st.session_state.single_data = data.get('single_data', {})
        st.session_state.single_server_order = data.get('single_server_order', [])
        st.session_state.custom_css = data.get('custom_css', "")
        
        settings_data = data.get('project_settings', {})
        st.session_state.project_settings = ProjectSettings(**settings_data)

# =============================================================================
# UI COMPONENTS
# =============================================================================

def render_header():
    """Render the main header"""
    st.set_page_config(
        page_title="Universal Link Generator Pro",
        page_icon="🔗",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    st.title("🔗 Universal Link Generator Pro")
    st.markdown("*Professional link management tool for content creators*")
    
    # Project info
    with st.expander("📋 Project Information", expanded=False):
        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input("Project Name", value=st.session_state.project_settings.name)
            if name != st.session_state.project_settings.name:
                st.session_state.project_settings.name = name
                st.session_state.project_settings.last_modified = datetime.now().isoformat()
        
        with col2:
            description = st.text_area("Description", value=st.session_state.project_settings.description, height=100)
            if description != st.session_state.project_settings.description:
                st.session_state.project_settings.description = description
                st.session_state.project_settings.last_modified = datetime.now().isoformat()

def render_sidebar():
    """Render the sidebar with tools and options"""
    with st.sidebar:
        st.header("🛠️ Tools & Options")
        
        # Export/Import
        st.subheader("📤 Export/Import")
        if st.button("📥 Export Project"):
            project_data = SessionManager.export_project()
            st.download_button(
                label="💾 Download Project File",
                data=json.dumps(project_data, indent=2),
                file_name=f"{st.session_state.project_settings.name.replace(' ', '_')}_project.json",
                mime="application/json"
            )
        
        uploaded_file = st.file_uploader("📁 Import Project", type=['json'])
        if uploaded_file is not None:
            try:
                project_data = json.load(uploaded_file)
                SessionManager.import_project(project_data)
                st.success("Project imported successfully!")
                st.rerun()
            except Exception as e:
                st.error(f"Error importing project: {str(e)}")
        
        st.divider()
        
        # Advanced Options
        st.subheader("⚙️ Advanced Options")
        st.session_state.show_advanced_options = st.checkbox("Show Advanced Options", value=st.session_state.show_advanced_options)
        
        if st.session_state.show_advanced_options:
            st.session_state.custom_css = st.text_area(
                "Custom CSS",
                value=st.session_state.custom_css,
                height=200,
                help="Add custom CSS styles to your generated HTML"
            )
        
        st.divider()
        
        # Statistics
        st.subheader("📊 Statistics")
        serial_count = len(st.session_state.serial_data)
        single_servers = len(st.session_state.single_server_order)
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Episodes", serial_count)
        with col2:
            st.metric("Servers", single_servers)

def render_serial_tab():
    """Render the serial/episode links tab"""
    st.header("📺 Serial/Episode Links")
    st.info("Create organized episode links with multiple servers and resolutions")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("📝 Input Data")
        
        # Resolution selection with presets
        preset_col1, preset_col2 = st.columns(2)
        with preset_col1:
            if st.button("🎬 HD Preset", help="480p, 720p, 1080p"):
                st.session_state.serial_resolutions = ["480p", "720p", "1080p"]
        with preset_col2:
            if st.button("📱 Mobile Preset", help="360p, 480p, 720p"):
                st.session_state.serial_resolutions = ["360p", "480p", "720p"]
        
        default_resolutions = ["360p", "480p", "540p", "720p", "1080p", "1440p", "2160p"]
        selected_resolutions = st.multiselect(
            "Select Resolutions",
            options=default_resolutions,
            default=st.session_state.get('serial_resolutions', ["480p", "720p"]),
            key="serial_resolutions"
        )
        
        # Episode range
        col_start, col_end = st.columns(2)
        with col_start:
            start_episode = st.number_input("Start Episode", min_value=1, step=1, value=1)
        with col_end:
            end_episode = st.number_input("End Episode", min_value=start_episode, step=1, value=start_episode)
        
        # Server information
        server_name = st.text_input(
            "Server Name",
            placeholder="e.g., MegaUp, TeraBox, GoogleDrive",
            help="Use descriptive server names"
        ).strip()
        
        # Link input with validation
        links_input = st.text_area(
            "Paste Links",
            placeholder="Paste your links here (one per line or space-separated)",
            height=150,
            help="Links should be in order: Episode 1 (all resolutions), Episode 2 (all resolutions), etc."
        )
        
        # Input validation
        if links_input:
            links = [link.strip() for link in re.split(r'[\s\n]+', links_input.strip()) if link.strip()]
            expected_count = (end_episode - start_episode + 1) * len(selected_resolutions)
            
            if len(links) != expected_count:
                st.warning(f"Expected {expected_count} links, got {len(links)}")
            else:
                st.success(f"✅ {len(links)} links ready to process")
        
        # Add data button
        if st.button("➕ Add Server Data", type="primary", disabled=not (server_name and selected_resolutions and links_input)):
            links = [link.strip() for link in re.split(r'[\s\n]+', links_input.strip()) if link.strip()]
            expected_count = (end_episode - start_episode + 1) * len(selected_resolutions)
            
            if len(links) == expected_count:
                # Validate URLs
                invalid_urls = [url for url in links if not LinkGenerator.validate_url(url)]
                if invalid_urls:
                    st.error(f"Invalid URLs found: {len(invalid_urls)} invalid URLs")
                    with st.expander("Show invalid URLs"):
                        for url in invalid_urls[:5]:  # Show first 5
                            st.write(f"❌ {url}")
                else:
                    # Process the data
                    link_index = 0
                    for ep in range(start_episode, end_episode + 1):
                        if ep not in st.session_state.serial_data:
                            st.session_state.serial_data[ep] = {}
                        
                        st.session_state.serial_data[ep][server_name] = {}
                        for res in selected_resolutions:
                            st.session_state.serial_data[ep][server_name][res] = {
                                "url": links[link_index],
                                "label": f"{server_name} {res}"
                            }
                            link_index += 1
                    
                    st.success(f"✅ Added {server_name} for Episodes {start_episode}-{end_episode}")
                    st.rerun()
    
    with col2:
        st.subheader("🎯 Generated Output")
        
        if not st.session_state.serial_data:
            st.info("No data added yet. Add server data to see the output.")
        else:
            # Show current data summary
            total_episodes = len(st.session_state.serial_data)
            total_servers = len(set(server for ep_data in st.session_state.serial_data.values() for server in ep_data.keys()))
            
            st.metric("Total Episodes", total_episodes)
            st.metric("Total Servers", total_servers)
            
            # Grouping options
            grouping_style = st.radio(
                "Grouping Style",
                ["By Server", "By Resolution"],
                horizontal=True,
                help="Choose how to organize the links"
            )
            
            # Generation options
            if st.button("🚀 Generate HTML", type="primary"):
                css_styles = LinkGenerator.generate_css_styles()
                if st.session_state.custom_css:
                    css_styles += f"\n<style>\n{st.session_state.custom_css}\n</style>"
                
                html_content = LinkGenerator.generate_serial_links(
                    st.session_state.serial_data,
                    grouping_style,
                    selected_resolutions
                )
                
                st.session_state.serial_final_html = css_styles + "\n" + html_content
            
            # Output display
            if st.session_state.serial_final_html:
                st.text_area(
                    "Generated HTML",
                    value=st.session_state.serial_final_html,
                    height=300,
                    help="Copy this HTML code to use in your website"
                )
                
                # Download button
                st.download_button(
                    label="💾 Download HTML",
                    data=st.session_state.serial_final_html,
                    file_name=f"{st.session_state.project_settings.name}_serial_links.html",
                    mime="text/html"
                )
            
            # Reset button
            if st.button("🔄 Reset Serial Data", type="secondary"):
                st.session_state.serial_data = {}
                st.session_state.serial_final_html = ""
                st.rerun()

def render_single_content_tab():
    """Render the single content (Korean drama style) tab"""
    st.header("🎭 Single Content Links")
    st.info("Create resolution-based links for movies, dramas, or single episodes")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("📝 Input Data")
        
        # Resolution selection
        default_resolutions = ["360p", "480p", "540p", "720p", "1080p", "1440p", "2160p"]
        selected_resolutions = st.multiselect(
            "Select Resolutions",
            options=default_resolutions,
            default=["360p", "480p", "540p", "720p"],
            key="single_resolutions"
        )
        
        # Server input
        server_name = st.text_input(
            "Server Name",
            placeholder="e.g., TeraBox, MegaUp, GoogleDrive",
            key="single_server_input"
        )
        
        # Links input
        links_input = st.text_area(
            "Links (one per line, matching resolution order)",
            height=150,
            placeholder="Paste links here in the same order as selected resolutions",
            key="single_links_input"
        )
        
        # Input validation
        if links_input and selected_resolutions:
            links = [link.strip() for link in links_input.strip().splitlines() if link.strip()]
            if len(links) != len(selected_resolutions):
                st.warning(f"Expected {len(selected_resolutions)} links, got {len(links)}")
            else:
                st.success(f"✅ {len(links)} links ready")
        
        # Add button
        if st.button("➕ Add Server", type="primary", disabled=not (server_name and selected_resolutions and links_input)):
            links = [link.strip() for link in links_input.strip().splitlines() if link.strip()]
            
            if len(links) == len(selected_resolutions):
                # Validate URLs
                invalid_urls = [url for url in links if not LinkGenerator.validate_url(url)]
                if invalid_urls:
                    st.error(f"Found {len(invalid_urls)} invalid URLs")
                else:
                    # Add data
                    for i, res in enumerate(selected_resolutions):
                        if res not in st.session_state.single_data:
                            st.session_state.single_data[res] = {}
                        st.session_state.single_data[res][server_name] = links[i]
                    
                    if server_name not in st.session_state.single_server_order:
                        st.session_state.single_server_order.append(server_name)
                    
                    st.success(f"✅ Added {server_name}")
                    
                    # Clear inputs
                    st.session_state.single_server_input = ""
                    st.session_state.single_links_input = ""
                    st.rerun()
    
    with col2:
        st.subheader("🎯 Generated Output")
        
        if not st.session_state.single_data:
            st.info("No servers added yet.")
        else:
            # Show server order
            st.write("**Server Order:**")
            for i, server in enumerate(st.session_state.single_server_order, 1):
                st.write(f"{i}. {server}")
            
            # Generate button
            if st.button("🚀 Generate HTML", type="primary", key="single_generate"):
                css_styles = LinkGenerator.generate_css_styles()
                if st.session_state.custom_css:
                    css_styles += f"\n<style>\n{st.session_state.custom_css}\n</style>"
                
                html_content = LinkGenerator.generate_single_content_links(
                    st.session_state.single_data,
                    list(st.session_state.single_data.keys()),
                    st.session_state.single_server_order
                )
                
                st.session_state.single_final_html = css_styles + "\n" + html_content
            
            # Output display
            if st.session_state.single_final_html:
                st.text_area(
                    "Generated HTML",
                    value=st.session_state.single_final_html,
                    height=200,
                    key="single_output"
                )
                
                # Download button
                st.download_button(
                    label="💾 Download HTML",
                    data=st.session_state.single_final_html,
                    file_name=f"{st.session_state.project_settings.name}_single_links.html",
                    mime="text/html"
                )
                
                # Preview
                with st.expander("👀 Live Preview"):
                    st.components.v1.html(st.session_state.single_final_html, height=400, scrolling=True)
            
            # Reset button
            if st.button("🔄 Reset Single Data", type="secondary", key="single_reset"):
                st.session_state.single_data = {}
                st.session_state.single_server_order = []
                st.session_state.single_final_html = ""
                st.rerun()

# =============================================================================
# MAIN APPLICATION
# =============================================================================

def main():
    """Main application function"""
    # Initialize session
    SessionManager.initialize_session()
    
    # Render UI
    render_header()
    render_sidebar()
    
    # Main tabs
    tab1, tab2, tab3 = st.tabs(["📺 Serial Links", "🎭 Single Content", "📊 Analytics"])
    
    with tab1:
        render_serial_tab()
    
    with tab2:
        render_single_content_tab()
    
    with tab3:
        st.header("📊 Project Analytics")
        st.info("Analytics and insights about your link generation project")
        
        # Project overview
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Episodes", len(st.session_state.serial_data))
        with col2:
            st.metric("Single Content Servers", len(st.session_state.single_server_order))
        with col3:
            total_links = sum(len(servers) * len(resolutions) for servers in st.session_state.serial_data.values() for resolutions in servers.values())
            total_links += sum(len(servers) for servers in st.session_state.single_data.values())
            st.metric("Total Links", total_links)
        
        # Project timeline
        st.subheader("📅 Project Timeline")
        settings = st.session_state.project_settings
        st.write(f"**Created:** {settings.created_at}")
        st.write(f"**Last Modified:** {settings.last_modified}")
        
        # Data visualization
        if st.session_state.serial_data:
            st.subheader("📈 Episode Distribution")
            episode_counts = {}
            for ep_num, servers in st.session_state.serial_data.items():
                episode_counts[f"Episode {ep_num}"] = len(servers)
            
            st.bar_chart(episode_counts)

if __name__ == "__main__":
    main()
