import flet as ft
import sys
import os
import threading
import time
import json
from datetime import datetime

# srcをパスに追加
sys.path.append(os.path.join(os.path.dirname(__file__), "../../.."))

from src.logger.application.controller import ActivityLoggerController

class ActivityLoggerGUI:
    def __init__(self, page: ft.Page):
        # #region agent log
        with open("/Users/takumi/Documents/src/private_src/mac_logs/mac_activity_logger/.cursor/debug.log", "a") as f:
            f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"A","location":"gui.py:14","message":"__init__ entry","data":{"thread":threading.current_thread().name},"timestamp":int(time.time()*1000)}) + "\n")
        # #endregion
        self.page = page
        self.page.title = "macOS Activity Logger"
        self.page.theme_mode = "dark"
        self.page.bgcolor = "#121212" # Explicit background
        self.page.window_width = 1000
        self.page.window_height = 800
        self.page.padding = 0
        self.page.spacing = 0
        
        # UI State initialization
        self.is_ready = False
        self.history_list = ft.ListView(expand=True, spacing=10, padding=10)
        
        # Loading screen
        self.loading_screen = ft.Container(
            content=ft.Column([
                ft.ProgressRing(),
                ft.Text("Initializing AI models...", size=16),
            ], alignment="center", horizontal_alignment="center"),
            alignment=ft.Alignment(0, 0),
            visible=True,
            expand=True
        )
        # #region agent log
        with open("/Users/takumi/Documents/src/private_src/mac_logs/mac_activity_logger/.cursor/debug.log", "a") as f:
            f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"D","location":"gui.py:37","message":"loading_screen created","data":{"visible":self.loading_screen.visible},"timestamp":int(time.time()*1000)}) + "\n")
        # #endregion
        
        # Main layout (initially hidden)
        self.main_layout = ft.Container(visible=False, expand=True)
        
        self.page.add(self.loading_screen, self.main_layout)
        # #region agent log
        with open("/Users/takumi/Documents/src/private_src/mac_logs/mac_activity_logger/.cursor/debug.log", "a") as f:
            f.write(json.dumps({"sessionId":"debug-session","runId":"post-fix","hypothesisId":"C","location":"gui.py:51","message":"page.add called","data":{"control_count":len(self.page.controls)},"timestamp":int(time.time()*1000)}) + "\n")
        # #endregion

        # Instantiate Controller (Empty)
        self.controller = ActivityLoggerController(lazy_init=True)
        
        # Wire callbacks
        self.controller.on_log_entry = self._handle_log_entry
        self.controller.on_status_change = self._handle_status_change
        self.controller.on_error = self._handle_error
        self.controller.on_summary = self._handle_summary

        self.init_ui()
        
        # TEMPORARY: Show main UI directly without background initialization
        # This is to debug UI display issues first
        # #region agent log
        with open("/Users/takumi/Documents/src/private_src/mac_logs/mac_activity_logger/.cursor/debug.log", "a") as f:
            f.write(json.dumps({"sessionId":"debug-session","runId":"ui-only","hypothesisId":"UI","location":"gui.py:67","message":"showing main UI directly without background init","data":{"has_rail":hasattr(self,"rail"),"has_content_container":hasattr(self,"content_container")},"timestamp":int(time.time()*1000)}) + "\n")
        # #endregion
        
        # Clear loading screen and show main layout directly
        self.page.controls.clear()
        # #region agent log
        with open("/Users/takumi/Documents/src/private_src/mac_logs/mac_activity_logger/.cursor/debug.log", "a") as f:
            f.write(json.dumps({"sessionId":"debug-session","runId":"ui-only","hypothesisId":"UI","location":"gui.py:76","message":"cleared page controls, creating full layout","data":{"control_count":len(self.page.controls)},"timestamp":int(time.time()*1000)}) + "\n")
        # #endregion
        
        # Create main layout - Custom sidebar on left, content on right
        # Workaround: NavigationRail has rendering issues on macOS desktop in this app.
        sidebar_container = self.nav_sidebar
        
        self.main_layout_row = ft.Row(
            controls=[
                sidebar_container,
                ft.VerticalDivider(width=1, color="grey"),
                self.content_container,
            ],
            expand=True,
            spacing=0
        )
        
        # Ensure container fills entire page and has proper background
        main_container = ft.Container(
            content=self.main_layout_row,
            expand=True,
            bgcolor="#121212",
            padding=0,
            margin=0
        )
        self.page.add(main_container)
        self.is_ready = True
        
        # Force page update to ensure rendering
        # #region agent log
        with open("/Users/takumi/Documents/src/private_src/mac_logs/mac_activity_logger/.cursor/debug.log", "a") as f:
            f.write(json.dumps({"sessionId":"debug-session","runId":"ui-only","hypothesisId":"UI","location":"gui.py:107","message":"main_container added, checking page state","data":{"page_bgcolor":self.page.bgcolor,"page_theme_mode":self.page.theme_mode,"container_bgcolor":main_container.bgcolor},"timestamp":int(time.time()*1000)}) + "\n")
        # #endregion
        
        # #region agent log
        with open("/Users/takumi/Documents/src/private_src/mac_logs/mac_activity_logger/.cursor/debug.log", "a") as f:
            rail_destinations = len(self.rail.destinations) if hasattr(self.rail, 'destinations') else 0
            rail_visible = self.rail.visible if hasattr(self.rail, 'visible') else None
            f.write(json.dumps({"sessionId":"debug-session","runId":"ui-only","hypothesisId":"UI","location":"gui.py:115","message":"full layout added to page","data":{"control_count":len(self.page.controls),"rail_min_width":self.rail.min_width if hasattr(self.rail, 'min_width') else None,"rail_destinations":rail_destinations,"rail_bgcolor":self.rail.bgcolor if hasattr(self.rail, 'bgcolor') else None,"rail_visible":rail_visible,"row_controls_count":len(self.main_layout_row.controls)},"timestamp":int(time.time()*1000)}) + "\n")
        # #endregion
        self.page.update()
        # #region agent log
        with open("/Users/takumi/Documents/src/private_src/mac_logs/mac_activity_logger/.cursor/debug.log", "a") as f:
            f.write(json.dumps({"sessionId":"debug-session","runId":"ui-only","hypothesisId":"UI","location":"gui.py:123","message":"page.update completed","data":{"thread":threading.current_thread().name},"timestamp":int(time.time()*1000)}) + "\n")
        # #endregion
        # #region agent log
        with open("/Users/takumi/Documents/src/private_src/mac_logs/mac_activity_logger/.cursor/debug.log", "a") as f:
            f.write(json.dumps({"sessionId":"debug-session","runId":"ui-only","hypothesisId":"UI","location":"gui.py:95","message":"page.update called in __init__","data":{"thread":threading.current_thread().name},"timestamp":int(time.time()*1000)}) + "\n")
        # #endregion
        
        # DISABLED: Background initialization - will re-enable after UI is confirmed working
        # print("Starting initialization thread...")
        # threading.Thread(target=self._initialize_background_services, daemon=True).start()

    def _initialize_background_services(self):
        # #region agent log
        with open("/Users/takumi/Documents/src/private_src/mac_logs/mac_activity_logger/.cursor/debug.log", "a") as f:
            f.write(json.dumps({"sessionId":"debug-session","runId":"post-fix","hypothesisId":"B","location":"gui.py:87","message":"background thread entry","data":{"thread":threading.current_thread().name},"timestamp":int(time.time()*1000)}) + "\n")
        # #endregion
        print("--- Background Initialization Started ---")
        try:
            print("Step 1: Setting up OS Services...")
            # Run OS setup in thread -> If this crashes due to thread restrictions, we'll know.
            # But blocking main thread is worse (no window).
            self.controller.setup_os_services()
            print("Step 1 Done: OS Services Ready.")
            
            print("Step 2: Setting up AI Services (Heavy)...")
            self.controller.setup_ai_services()
            print("Step 2 Done: AI Services Ready.")
            
            # Switch view - Use page.run_task to update UI from main thread
            print("Step 3: Final UI Update...")
            # #region agent log
            with open("/Users/takumi/Documents/src/private_src/mac_logs/mac_activity_logger/.cursor/debug.log", "a") as f:
                f.write(json.dumps({"sessionId":"debug-session","runId":"post-fix","hypothesisId":"B","location":"gui.py:108","message":"before page.run_task for UI update","data":{"control_count":len(self.page.controls),"thread":threading.current_thread().name},"timestamp":int(time.time()*1000)}) + "\n")
            # #endregion
            
            async def show_final_ui():
                import asyncio
                # #region agent log
                with open("/Users/takumi/Documents/src/private_src/mac_logs/mac_activity_logger/.cursor/debug.log", "a") as f:
                    f.write(json.dumps({"sessionId":"debug-session","runId":"post-fix","hypothesisId":"B","location":"gui.py:112","message":"show_final_ui entry in main thread","data":{"thread":threading.current_thread().name},"timestamp":int(time.time()*1000)}) + "\n")
                # #endregion
                # Show ready message
                self.page.controls.clear()
                self.page.add(ft.Text("SYSTEM READY - STARTING UI...", color="green", size=20))
                self.page.update()
                # #region agent log
                with open("/Users/takumi/Documents/src/private_src/mac_logs/mac_activity_logger/.cursor/debug.log", "a") as f:
                    f.write(json.dumps({"sessionId":"debug-session","runId":"post-fix","hypothesisId":"B","location":"gui.py:118","message":"ready message shown","data":{"control_count":len(self.page.controls),"thread":threading.current_thread().name},"timestamp":int(time.time()*1000)}) + "\n")
                # #endregion
                # Wait 0.5 seconds
                await asyncio.sleep(0.5)
                # Show main layout
                # #region agent log
                with open("/Users/takumi/Documents/src/private_src/mac_logs/mac_activity_logger/.cursor/debug.log", "a") as f:
                    f.write(json.dumps({"sessionId":"debug-session","runId":"post-fix","hypothesisId":"B","location":"gui.py:123","message":"before showing main layout","data":{"thread":threading.current_thread().name},"timestamp":int(time.time()*1000)}) + "\n")
                # #endregion
                self.page.controls.clear()
                # #region agent log
                with open("/Users/takumi/Documents/src/private_src/mac_logs/mac_activity_logger/.cursor/debug.log", "a") as f:
                    f.write(json.dumps({"sessionId":"debug-session","runId":"post-fix","hypothesisId":"B","location":"gui.py:130","message":"before creating main_layout_row","data":{"has_rail":hasattr(self,"rail"),"has_content_container":hasattr(self,"content_container")},"timestamp":int(time.time()*1000)}) + "\n")
                # #endregion
                # Main layout - According to Flet docs, NavigationRail should be used directly
                # NavigationRail automatically expands to fill available height in Row
                # Don't set width explicitly, let it use min_width
                # Remove any width setting to let NavigationRail use its natural size
                if hasattr(self.rail, 'width'):
                    self.rail.width = None
                # #region agent log
                with open("/Users/takumi/Documents/src/private_src/mac_logs/mac_activity_logger/.cursor/debug.log", "a") as f:
                    rail_visible = self.rail.visible if hasattr(self.rail, 'visible') else None
                    rail_destinations_count = len(self.rail.destinations) if hasattr(self.rail, 'destinations') else 0
                    rail_min_width = self.rail.min_width if hasattr(self.rail, 'min_width') else None
                    f.write(json.dumps({"sessionId":"debug-session","runId":"post-fix","hypothesisId":"B","location":"gui.py:137","message":"rail configured for direct use in Row","data":{"rail_min_width":rail_min_width,"rail_bgcolor":self.rail.bgcolor if hasattr(self.rail, 'bgcolor') else None,"rail_visible":rail_visible,"rail_destinations_count":rail_destinations_count},"timestamp":int(time.time()*1000)}) + "\n")
                # #endregion
                self.main_layout_row = ft.Row(
                    [
                        self.rail,
                        ft.VerticalDivider(width=1, color="grey"),
                        self.content_container,
                    ],
                    expand=True,
                    spacing=0
                )
                # #region agent log
                with open("/Users/takumi/Documents/src/private_src/mac_logs/mac_activity_logger/.cursor/debug.log", "a") as f:
                    f.write(json.dumps({"sessionId":"debug-session","runId":"post-fix","hypothesisId":"B","location":"gui.py:149","message":"main_layout_row created with rail width","data":{"controls_count":len(self.main_layout_row.controls),"rail_width":self.rail.width},"timestamp":int(time.time()*1000)}) + "\n")
                # #endregion
                # #region agent log
                with open("/Users/takumi/Documents/src/private_src/mac_logs/mac_activity_logger/.cursor/debug.log", "a") as f:
                    rail_type = type(self.rail).__name__ if hasattr(self, "rail") else "None"
                    container_type = type(self.content_container).__name__ if hasattr(self, "content_container") else "None"
                    dashboard_type = type(self.dashboard_view).__name__ if hasattr(self, "dashboard_view") else "None"
                    f.write(json.dumps({"sessionId":"debug-session","runId":"post-fix","hypothesisId":"B","location":"gui.py:142","message":"main_layout_row created","data":{"controls_count":len(self.main_layout_row.controls),"rail_type":rail_type,"container_type":container_type,"dashboard_type":dashboard_type},"timestamp":int(time.time()*1000)}) + "\n")
                # #endregion
                # Wrap in Container to ensure proper sizing and background
                main_container = ft.Container(
                    content=self.main_layout_row,
                    expand=True,
                    bgcolor="#121212"
                )
                # #region agent log
                with open("/Users/takumi/Documents/src/private_src/mac_logs/mac_activity_logger/.cursor/debug.log", "a") as f:
                    f.write(json.dumps({"sessionId":"debug-session","runId":"post-fix","hypothesisId":"B","location":"gui.py:155","message":"main_container created and adding to page","data":{"container_bgcolor":main_container.bgcolor},"timestamp":int(time.time()*1000)}) + "\n")
                # #endregion
                self.page.add(main_container)
                self.is_ready = True
                print(f"Diagnostic: Page control count = {len(self.page.controls)}")
                # #region agent log
                with open("/Users/takumi/Documents/src/private_src/mac_logs/mac_activity_logger/.cursor/debug.log", "a") as f:
                    f.write(json.dumps({"sessionId":"debug-session","runId":"post-fix","hypothesisId":"B","location":"gui.py:150","message":"before final page.update in main thread","data":{"control_count":len(self.page.controls),"thread":threading.current_thread().name},"timestamp":int(time.time()*1000)}) + "\n")
                # #endregion
                self.page.update()
                # #region agent log
                with open("/Users/takumi/Documents/src/private_src/mac_logs/mac_activity_logger/.cursor/debug.log", "a") as f:
                    f.write(json.dumps({"sessionId":"debug-session","runId":"post-fix","hypothesisId":"B","location":"gui.py:143","message":"after final page.update in main thread","data":{"thread":threading.current_thread().name},"timestamp":int(time.time()*1000)}) + "\n")
                # #endregion
            
            self.page.run_task(show_final_ui)
            print("--- GUI Initialization Completed Successfully ---")
            
        except Exception as e:
            print(f"!!! Initialization Error: {e}")
            import traceback
            traceback.print_exc()
            # #region agent log
            with open("/Users/takumi/Documents/src/private_src/mac_logs/mac_activity_logger/.cursor/debug.log", "a") as f:
                f.write(json.dumps({"sessionId":"debug-session","runId":"post-fix","hypothesisId":"B","location":"gui.py:150","message":"exception in background thread","data":{"error":str(e),"thread":threading.current_thread().name},"timestamp":int(time.time()*1000)}) + "\n")
            # #endregion
            
            async def show_error():
                self.page.controls.clear()
                self.page.add(ft.Text(f"Critical Error: {e}", color="red"))
                self.page.update()
            
            self.page.run_task(show_error)

    def init_ui(self):
        # Navigation - Create NavigationRail with proper settings
        # Ensure it has visible=True and proper sizing
        # Navigation - Create NavigationRail with proper settings
        # According to Flet docs, NavigationRail should work in Row
        # Set extended=True to show labels alongside icons
        self.rail = ft.NavigationRail(
            selected_index=0,
            label_type="all",
            extended=True,  # Show labels alongside icons
            min_width=72,  # Default min_width according to docs
            min_extended_width=400,
            group_alignment=-0.9,
            bgcolor="#1e1e1e", # Explicit background for sidebar
            visible=True,  # Explicitly set visible
            destinations=[
                ft.NavigationRailDestination(
                    icon="dashboard",
                    selected_icon="dashboard_rounded",
                    label="Home",
                ),
                ft.NavigationRailDestination(
                    icon="history",
                    selected_icon="history_rounded",
                    label="History",
                ),
                ft.NavigationRailDestination(
                    icon="settings",
                    selected_icon="settings_rounded",
                    label="Settings",
                ),
            ],
            on_change=self._on_nav_change,
        )
        # #region agent log
        with open("/Users/takumi/Documents/src/private_src/mac_logs/mac_activity_logger/.cursor/debug.log", "a") as f:
            f.write(json.dumps({"sessionId":"debug-session","runId":"ui-only","hypothesisId":"UI","location":"gui.py:237","message":"NavigationRail created in init_ui","data":{"rail_visible":self.rail.visible if hasattr(self.rail, 'visible') else None,"rail_destinations":len(self.rail.destinations) if hasattr(self.rail, 'destinations') else 0,"rail_bgcolor":self.rail.bgcolor if hasattr(self.rail, 'bgcolor') else None},"timestamp":int(time.time()*1000)}) + "\n")
        # #endregion

        # Dashboard View
        self.dashboard_view = self._create_dashboard_view()
        self.history_view = self._create_history_view()
        self.settings_view = self._create_settings_view()
        
        self.content_container = ft.Container(
            content=self.dashboard_view,
            expand=True,
            padding=20,
            bgcolor="#121212" # Ensure main area has color
        )

        # Custom sidebar (workaround for NavigationRail rendering issue)
        self._nav_key = "home"
        self._nav_items = {}

        def _make_nav_item(key: str, label: str, icon_name: str):
            is_selected = key == self._nav_key
            # Simple approach: Container with Row containing Icon and Text
            # Ensure all colors are explicitly set and visible
            icon = ft.Icon(
                icon_name, 
                color="white" if is_selected else "#cfcfcf", 
                size=20,
                opacity=1.0,
                visible=True
            )
            text = ft.Text(
                label, 
                color="white" if is_selected else "#cfcfcf", 
                size=14, 
                weight="w500" if is_selected else "normal",
                opacity=1.0,
                visible=True
            )
            row = ft.Row(
                controls=[icon, text], 
                spacing=10, 
                vertical_alignment="center",
                tight=True,
                visible=True
            )
            # Wrap in GestureDetector to ensure click handling works
            container = ft.GestureDetector(
                content=ft.Container(
                    content=row,
                    padding=ft.padding.only(left=12, top=8, right=12, bottom=8),
                    border_radius=8,
                    height=44,
                    width=None,  # Let it expand naturally
                    bgcolor="#2a2a2a" if is_selected else "#1e1e1e",
                    ink=False,
                    visible=True,
                ),
                on_tap=lambda e, k=key: self._set_view(k),
            )
            # Store both container and row for updates
            self._nav_items[key] = {"container": container, "row": row, "icon": icon, "text": text}
            return container

        sidebar_content = ft.Container(
            bgcolor="#1e1e1e",
            expand=True,
            content=ft.Column(
                controls=[
                    ft.Container(
                        bgcolor="#1e1e1e",
                        content=ft.Text("MENU", color="#cfcfcf", size=12),
                        padding=ft.padding.only(left=12, top=16, right=12, bottom=8),
                    ),
                    _make_nav_item("home", "Home", "dashboard"),
                    _make_nav_item("history", "History", "history"),
                    _make_nav_item("settings", "Settings", "settings"),
                ],
                spacing=4,
                expand=True,
            ),
        )

        self.nav_sidebar = ft.Container(
            content=sidebar_content,
            width=220,
            bgcolor="#1e1e1e",
            padding=0,
            margin=0,
            expand=False,
        )
        # #region agent log
        with open("/Users/takumi/Documents/src/private_src/mac_logs/mac_activity_logger/.cursor/debug.log", "a") as f:
            f.write(json.dumps({"sessionId":"debug-session","runId":"ui-only","hypothesisId":"UI","location":"gui.py:344","message":"custom sidebar created","data":{"sidebar_width":self.nav_sidebar.width,"sidebar_bgcolor":self.nav_sidebar.bgcolor,"nav_keys":list(self._nav_items.keys())},"timestamp":int(time.time()*1000)}) + "\n")
        # #endregion

        # Ensure initial view matches nav state
        self._set_view("home", initial=True)

    def _set_view(self, key: str, initial: bool = False):
        # #region agent log
        with open("/Users/takumi/Documents/src/private_src/mac_logs/mac_activity_logger/.cursor/debug.log", "a") as f:
            f.write(json.dumps({"sessionId":"debug-session","runId":"ui-only","hypothesisId":"UI","location":"gui.py:360","message":"_set_view called","data":{"key":key,"initial":initial},"timestamp":int(time.time()*1000)}) + "\n")
        # #endregion

        self._nav_key = key

        if key == "home":
            self.content_container.content = self.dashboard_view
        elif key == "history":
            self.content_container.content = self.history_view
            self._refresh_history()
        elif key == "settings":
            self.content_container.content = self.settings_view
        else:
            self.content_container.content = ft.Text(f"Unknown view: {key}", color="red")

        # Update sidebar highlight - update container, icon, and text styles
        for k, item_data in getattr(self, "_nav_items", {}).items():
            is_selected = k == self._nav_key
            gesture_detector = item_data["container"]  # This is now a GestureDetector
            icon = item_data["icon"]
            text = item_data["text"]
            
            # Update the actual Container inside GestureDetector
            if hasattr(gesture_detector, 'content') and isinstance(gesture_detector.content, ft.Container):
                actual_container = gesture_detector.content
                actual_container.bgcolor = "#2a2a2a" if is_selected else "#1e1e1e"
            
            icon.color = "white" if is_selected else "#cfcfcf"
            text.color = "white" if is_selected else "#cfcfcf"
            text.weight = "w500" if is_selected else "normal"

        if hasattr(self, "page") and self.page is not None:
            self.page.update()


    def _create_dashboard_view(self):
        self.status_text = ft.Text("Status: Stopped", size=20, weight="bold")
        self.start_stop_btn = ft.FilledButton(
            "Start Monitoring",
            icon="play_arrow",
            color="white", # Text/icon color
            bgcolor="green",
            on_click=self._toggle_monitoring
        )
        
        self.latest_log_text = ft.Text("No activity yet", size=14)
        self.latest_log_card = ft.Card(
            content=ft.Container(
                content=ft.Column([
                    ft.Text("Latest Activity", size=16, weight="bold"),
                    self.latest_log_text,
                ]),
                padding=10
            )
        )
        
        self.summary_text = ft.Text("Summarization not active", italic=True)
        self.summary_card = ft.Card(
            content=ft.Container(
                content=ft.Column([
                    ft.Text("AI Summary (Live)", size=16, weight="bold"),
                    self.summary_text,
                ]),
                padding=10
            )
        )

        return ft.Column([
            ft.Row([self.status_text, self.start_stop_btn], alignment="spaceBetween"),
            ft.Divider(),
            ft.Text("Live Monitor", size=18, weight="w500"),
            self.latest_log_card,
            ft.Text("Recent Highlights", size=18, weight="w500"),
            self.summary_card,
        ], expand=True, spacing=20)

    def _create_history_view(self):
        self.history_list = ft.ListView(expand=True, spacing=10, padding=10)
        return ft.Column([
            ft.Row([
                ft.Text("Activity History", size=20, weight="bold"),
                ft.IconButton("refresh", on_click=self._refresh_history)
            ], alignment="center"), # Row alignment
            self.history_list
        ], expand=True)

    def _create_settings_view(self):
        return ft.Column([
            ft.Text("Settings", size=20, weight="bold"),
            ft.Switch(label="Audio Recording (Whisper)", value=not self.controller.no_audio, on_change=self._toggle_audio),
            ft.Switch(label="Summarization (Gemma)", value=not self.controller.no_summarize, on_change=self._toggle_summarize),
            ft.Text("Screen Change Threshold"),
            ft.Slider(min=0, max=100, divisions=100, value=self.controller.threshold, label="{value}%", on_change=self._on_threshold_change),
            ft.Text("Capture Interval (seconds)"),
            ft.Slider(min=0.5, max=10, divisions=19, value=self.controller.interval, label="{value}s", on_change=self._on_interval_change),
        ], expand=True, spacing=20)

    # Callbacks from Controller
    def _handle_log_entry(self, entry):
        ts = entry.timestamp.strftime("%H:%M:%S")
        app = entry.screen.app_name
        title = entry.screen.window_title
        transcript = entry.audio_transcript
        
        msg = f"[{ts}] {app} - {title}"
        if transcript:
            msg += f"\n🎙️: {transcript}"
            
        self.latest_log_text.value = msg
        
        # Add to history list (UI side)
        self.history_list.controls.insert(0, ft.ListTile(
            leading=ft.Icon("screenshot" if entry.metadata.get("is_screen_change") else "stay_current_landscape"),
            title=ft.Text(f"{app} - {ts}"),
            subtitle=ft.Text(title + (f"\nAudio: {transcript}" if transcript else "")),
        ))
        
        self.page.update()

    def _handle_status_change(self, status):
        self.status_text.value = f"Status: {status}"
        if status == "Running":
            self.start_stop_btn.text = "Stop Monitoring"
            self.start_stop_btn.icon = "stop"
            self.start_stop_btn.color = "red"
        else:
            self.start_stop_btn.text = "Start Monitoring"
            self.start_stop_btn.icon = "play_arrow"
            self.start_stop_btn.color = "green"
        self.page.update()

    def _handle_error(self, error):
        self.page.show_snack_bar(ft.SnackBar(ft.Text(f"Error: {error}"), open=True))

    def _handle_summary(self, summary_type, summary_text):
        prefix = "🎨 Visual Summary: " if summary_type == "visual" else "🎙️ Audio Summary: "
        self.summary_text.value = prefix + summary_text
        self.page.update()

    # UI Event Handlers
    def _on_nav_change(self, e):
        idx = e.control.selected_index
        if idx == 0:
            self.content_container.content = self.dashboard_view
        elif idx == 1:
            self.content_container.content = self.history_view
            self._refresh_history()
        elif idx == 2:
            self.content_container.content = self.settings_view
        self.page.update()

    def _toggle_monitoring(self, e):
        if self.controller.is_running:
            self.controller.stop()
        else:
            self.controller.start()

    def _refresh_history(self, e=None):
        self.history_list.controls.clear()
        
        today = datetime.now().strftime("%Y-%m-%d")
        log_file = os.path.join(self.controller.logs_dir, today, "activity.jsonl")
        
        if not os.path.exists(log_file):
            self.history_list.controls.append(ft.Text("No logs for today."))
            self.page.update()
            return

        try:
            import json
            with open(log_file, "r") as f:
                lines = f.readlines()
                # 最新のログを上に表示するため逆順にする
                for line in reversed(lines):
                    data = json.loads(line)
                    ts = data.get("timestamp", "").split("T")[-1][:8]
                    screen = data.get("screen", {})
                    app = screen.get("app_name", "Unknown")
                    title = screen.get("window_title", "")
                    audio = data.get("audio", {}).get("transcript", "")
                    
                    is_change = data.get("metadata", {}).get("is_screen_change", False)
                    
                    self.history_list.controls.append(ft.ListTile(
                        leading=ft.Icon("screenshot" if is_change else "stay_current_landscape"),
                        title=ft.Text(f"{app} - {ts}"),
                        subtitle=ft.Text(title + (f"\nAudio: {audio}" if audio else "")),
                    ))
        except Exception as e:
            self._handle_error(f"Failed to load history: {e}")
            
        self.page.update()

    def _toggle_audio(self, e):
        self.controller.no_audio = not e.control.value
        self.controller._init_services() # Re-init services with new config

    def _toggle_summarize(self, e):
        self.controller.no_summarize = not e.control.value
        self.controller._init_services()

    def _on_threshold_change(self, e):
        self.controller.threshold = e.control.value
        self.controller.similarity_service.threshold_percent = e.control.value

    def _on_interval_change(self, e):
        self.controller.interval = e.control.value

def main(page: ft.Page):
    # #region agent log
    with open("/Users/takumi/Documents/src/private_src/mac_logs/mac_activity_logger/.cursor/debug.log", "a") as f:
        f.write(json.dumps({"sessionId":"debug-session","runId":"post-fix","hypothesisId":"E","location":"gui.py:381","message":"main() entry","data":{"thread":threading.current_thread().name},"timestamp":int(time.time()*1000)}) + "\n")
    # #endregion
    ActivityLoggerGUI(page)
    # #region agent log
    with open("/Users/takumi/Documents/src/private_src/mac_logs/mac_activity_logger/.cursor/debug.log", "a") as f:
        f.write(json.dumps({"sessionId":"debug-session","runId":"post-fix","hypothesisId":"E","location":"gui.py:384","message":"main() exit, ActivityLoggerGUI created","data":{"thread":threading.current_thread().name},"timestamp":int(time.time()*1000)}) + "\n")
    # #endregion

if __name__ == "__main__":
    ft.app(main)
