import tkinter as tk
from tkinter import ttk, messagebox
import serial
import serial.tools.list_ports
import threading
import time
import math
import queue
from datetime import datetime

# Define Palette (Modern Sleek Dark Mode)
BG_MAIN = "#121214"       # Deep black/grey background
BG_CARD = "#1a1a24"       # Darker slate card background
BG_INNER = "#252538"      # Input fields and panels
TEXT_MAIN = "#ffffff"     # White text
TEXT_MUTED = "#8e8e9f"    # Secondary text
COLOR_ACCENT = "#38bdf8"   # Cyber blue for highlights
COLOR_GREEN = "#10b981"    # Safe/normal water level
COLOR_YELLOW = "#f59e0b"   # Warning water level
COLOR_RED = "#ef4444"      # Danger level

class IoTWaterLevelDashboard:
    def __init__(self, root):
        self.root = root
        self.root.title("AquaSync: Smart Water Level IoT Dashboard")
        self.root.geometry("1100x700")
        self.root.configure(bg=BG_MAIN)
        
        # State Variables
        self.sensor_value = 0
        self.percentage = 0.0
        self.current_state = "Offline / Inactive"
        self.is_connected = False
        self.simulation_mode = tk.BooleanVar(value=True) # Default to simulation mode for quick demo
        
        # Serial connection variables
        self.serial_port = None
        self.serial_thread = None
        self.running = True
        self.data_queue = queue.Queue()
        
        # Setup modern ttk styles
        self.setup_styles()
        
        # Build UI layout
        self.create_header()
        self.create_main_layout()
        
        # Start GUI polling loop
        self.root.after(100, self.process_queue)
        
        # Animated wave parameters
        self.wave_phase = 0.0
        self.animate_wave()
        
        # Initial logs
        self.log_event("Dashboard started in Simulation Mode. Use the slider to test the GUI.")
        self.log_event("To use physical Arduino, uncheck 'Simulation Mode', select COM Port, and click 'Connect'.")

    def setup_styles(self):
        self.style = ttk.Style()
        self.style.theme_use("clam")
        
        # Configure frames and widgets
        self.style.configure("TFrame", background=BG_MAIN)
        self.style.configure("Card.TFrame", background=BG_CARD, relief="flat")
        
        self.style.configure("TLabel", background=BG_CARD, foreground=TEXT_MAIN, font=("Segoe UI", 11))
        self.style.configure("Header.TLabel", background=BG_MAIN, foreground=TEXT_MAIN, font=("Segoe UI", 20, "bold"))
        self.style.configure("Sub.TLabel", background=BG_MAIN, foreground=TEXT_MUTED, font=("Segoe UI", 10))
        self.style.configure("Value.TLabel", background=BG_CARD, foreground=COLOR_ACCENT, font=("Segoe UI", 24, "bold"))
        
        self.style.configure("TButton", background=COLOR_ACCENT, foreground=BG_MAIN, font=("Segoe UI", 10, "bold"), borderwidth=0)
        self.style.map("TButton",
            background=[('pressed', '#0284c7'), ('active', '#0ea5e9')],
            foreground=[('pressed', '#ffffff'), ('active', BG_MAIN)]
        )
        
        self.style.configure("TCheckbutton", background=BG_CARD, foreground=TEXT_MAIN, font=("Segoe UI", 10))
        self.style.configure("TCombobox", fieldbackground=BG_INNER, background=BG_INNER, foreground=TEXT_MAIN, arrowcolor=TEXT_MAIN)

    def create_header(self):
        header_frame = ttk.Frame(self.root, style="TFrame")
        header_frame.pack(fill="x", padx=30, pady=(20, 10))
        
        title_label = ttk.Label(header_frame, text="💧 AQUASYNC: SMART WATER MONITORING SYSTEM", style="Header.TLabel")
        title_label.pack(side="left")
        
        sub_label = ttk.Label(header_frame, text="IoT & Embedded Systems Lab Project | Developer Edition", style="Sub.TLabel")
        sub_label.pack(side="right", pady=8)
        
        # Subtle horizontal divider line
        divider = tk.Frame(self.root, height=1, bg="#2d2d3a")
        divider.pack(fill="x", padx=30, pady=5)

    def create_main_layout(self):
        # Container frame
        main_container = ttk.Frame(self.root, style="TFrame")
        main_container.pack(fill="both", expand=True, padx=30, pady=15)
        
        # Column 1: Controls, Configurations, and LED Mockups
        left_col = ttk.Frame(main_container, style="TFrame")
        left_col.pack(side="left", fill="both", expand=True, padx=(0, 15))
        
        # Column 2: Water Tank Visual and Event Logs
        right_col = ttk.Frame(main_container, style="TFrame")
        right_col.pack(side="right", fill="both", expand=True, padx=(15, 0))
        
        # =========================================================
        # LEFT COLUMN COMPONENTS
        # =========================================================
        
        # 1. Connection Panel (Card)
        conn_card = ttk.Frame(left_col, style="Card.TFrame")
        conn_card.pack(fill="x", pady=(0, 15), ipady=10)
        self.draw_card_border(conn_card, "🔌 SYSTEM INTEGRATION & CONNECTIONS")
        
        # Simulation Switch
        sim_check = ttk.Checkbutton(
            conn_card, text="Run Simulation Mode (Hardware Mockup)", 
            variable=self.simulation_mode, command=self.toggle_simulation
        )
        sim_check.pack(anchor="w", padx=20, pady=10)
        
        # COM Port Selector
        port_frame = ttk.Frame(conn_card, style="Card.TFrame")
        port_frame.pack(fill="x", padx=20, pady=5)
        
        ttk.Label(port_frame, text="Arduino Serial Port:").pack(side="left")
        
        self.port_combobox = ttk.Combobox(port_frame, width=15, state="readonly")
        self.port_combobox.pack(side="left", padx=10)
        
        refresh_btn = ttk.Button(port_frame, text="🔄 Refresh", width=10, command=self.refresh_ports)
        refresh_btn.pack(side="left", padx=5)
        
        # Connect Button
        self.connect_btn = ttk.Button(conn_card, text="🔌 CONNECT ARDUINO", command=self.toggle_connection)
        self.connect_btn.pack(fill="x", padx=20, pady=(15, 5))
        
        # 2. Simulation Panel (Active only in Simulation Mode)
        self.sim_card = ttk.Frame(left_col, style="Card.TFrame")
        self.sim_card.pack(fill="x", pady=10, ipady=10)
        self.draw_card_border(self.sim_card, "🎛️ HARDWARE SENSOR SIMULATOR")
        
        ttk.Label(self.sim_card, text="Simulated Sensor Value (0 - 1023):", font=("Segoe UI", 10, "italic"), foreground=TEXT_MUTED).pack(anchor="w", padx=20, pady=(10, 5))
        
        self.sim_slider = ttk.Scale(
            self.sim_card, from_=0, to=1000, orient="horizontal", 
            command=self.on_slider_move
        )
        self.sim_slider.set(250) # default mid level
        self.sim_slider.pack(fill="x", padx=20, pady=10)
        
        # 3. Hardware Status & LED Output Panel
        status_card = ttk.Frame(left_col, style="Card.TFrame")
        status_card.pack(fill="both", expand=True, pady=(10, 0), ipady=10)
        self.draw_card_border(status_card, "🚨 ARDUINO DIGITAL PIN OUTPUTS (LEDs)")
        
        # Mini schematic label
        ttk.Label(status_card, text="Visualizing state of physical Arduino pins 2, 3, 4, and 5:", font=("Segoe UI", 9, "italic"), foreground=TEXT_MUTED).pack(anchor="w", padx=20, pady=(10, 15))
        
        # Grid of Virtual LEDs
        led_grid = ttk.Frame(status_card, style="Card.TFrame")
        led_grid.pack(fill="x", padx=20)
        
        # Pin 2 LED (Low-Mid)
        self.led2_canvas = tk.Canvas(led_grid, width=30, height=30, bg=BG_CARD, highlightthickness=0)
        self.led2_canvas.grid(row=0, column=0, padx=(10, 20), pady=10)
        self.led2_indicator = self.led2_canvas.create_oval(3, 3, 27, 27, fill="#27272a", outline="#4b5563", width=2)
        ttk.Label(led_grid, text="PIN 2: LOW-MID LEVEL (100 - 600)\nStatus LED: Green", font=("Segoe UI", 10, "bold")).grid(row=0, column=1, sticky="w")
        
        # Pin 3 LED (High)
        self.led3_canvas = tk.Canvas(led_grid, width=30, height=30, bg=BG_CARD, highlightthickness=0)
        self.led3_canvas.grid(row=1, column=0, padx=(10, 20), pady=10)
        self.led3_indicator = self.led3_canvas.create_oval(3, 3, 27, 27, fill="#27272a", outline="#4b5563", width=2)
        ttk.Label(led_grid, text="PIN 3: HIGH LEVEL (601 - 625)\nStatus LED: Yellow / Amber", font=("Segoe UI", 10, "bold")).grid(row=1, column=1, sticky="w")
        
        # Pin 4 & 5 LEDs (Full / Danger)
        self.led4_canvas = tk.Canvas(led_grid, width=30, height=30, bg=BG_CARD, highlightthickness=0)
        self.led4_canvas.grid(row=2, column=0, padx=(10, 20), pady=10)
        self.led4_indicator = self.led4_canvas.create_oval(3, 3, 27, 27, fill="#27272a", outline="#4b5563", width=2)
        
        self.led5_canvas = tk.Canvas(led_grid, width=30, height=30, bg=BG_CARD, highlightthickness=0)
        self.led5_canvas.grid(row=3, column=0, padx=(10, 20), pady=10)
        self.led5_indicator = self.led5_canvas.create_oval(3, 3, 27, 27, fill="#27272a", outline="#4b5563", width=2)
        
        ttk.Label(led_grid, text="PINS 4 & 5: DANGER OVERFLOW (626 - 700)\nSystem alarm: Dual RED LEDs + BUZZER", font=("Segoe UI", 10, "bold")).grid(row=2, column=1, rowspan=2, sticky="w")
        
        # =========================================================
        # RIGHT COLUMN COMPONENTS
        # =========================================================
        
        # 1. Real-time Telemetry (Values) and Tank Visualization
        tel_frame = ttk.Frame(right_col, style="TFrame")
        tel_frame.pack(fill="x", pady=(0, 15))
        
        # Values Card
        val_card = ttk.Frame(tel_frame, style="Card.TFrame", width=240)
        val_card.pack(side="left", fill="both", expand=True, padx=(0, 10))
        self.draw_card_border(val_card, "📊 LIVE VALUES")
        
        ttk.Label(val_card, text="SENSOR RAW DATA", foreground=TEXT_MUTED, font=("Segoe UI", 9, "bold")).pack(anchor="w", padx=20, pady=(15, 5))
        self.lbl_sensor = ttk.Label(val_card, text="0", style="Value.TLabel")
        self.lbl_sensor.pack(anchor="w", padx=20)
        
        ttk.Label(val_card, text="WATER FILL PERCENTAGE", foreground=TEXT_MUTED, font=("Segoe UI", 9, "bold")).pack(anchor="w", padx=20, pady=(15, 5))
        self.lbl_percent = ttk.Label(val_card, text="0.0 %", style="Value.TLabel")
        self.lbl_percent.pack(anchor="w", padx=20)
        
        ttk.Label(val_card, text="CURRENT ZONE STATE", foreground=TEXT_MUTED, font=("Segoe UI", 9, "bold")).pack(anchor="w", padx=20, pady=(15, 5))
        self.lbl_state = ttk.Label(val_card, text="EMPTY / OFFLINE", font=("Segoe UI", 12, "bold"), foreground=TEXT_MUTED)
        self.lbl_state.pack(anchor="w", padx=20, pady=(0, 15))
        
        # Animated Tank Visual Card
        tank_card = ttk.Frame(tel_frame, style="Card.TFrame")
        tank_card.pack(side="right", fill="both", expand=True, padx=(10, 0))
        self.draw_card_border(tank_card, "🌊 TANK LEVEL ANIMATION")
        
        # Canvas for animated tank
        self.tank_canvas = tk.Canvas(tank_card, width=220, height=230, bg=BG_CARD, highlightthickness=0)
        self.tank_canvas.pack(pady=15)
        
        # 2. Scrolling Event Log Panel
        log_card = ttk.Frame(right_col, style="Card.TFrame")
        log_card.pack(fill="both", expand=True, pady=(10, 0), ipady=10)
        self.draw_card_border(log_card, "📜 HISTORICAL SYSTEM EVENTS & LOGS")
        
        # Listbox and Scrollbar for Logs
        log_frame = ttk.Frame(log_card, style="Card.TFrame")
        log_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        self.log_listbox = tk.Listbox(
            log_frame, bg=BG_INNER, fg=TEXT_MAIN, font=("Consolas", 10),
            selectbackground=COLOR_ACCENT, selectforeground=BG_MAIN,
            borderwidth=0, highlightthickness=0
        )
        self.log_listbox.pack(side="left", fill="both", expand=True)
        
        scrollbar = ttk.Scrollbar(log_frame, orient="vertical", command=self.log_listbox.yview)
        scrollbar.pack(side="right", fill="y")
        self.log_listbox.config(yscrollcommand=scrollbar.set)
        
        # Populate COM ports and trigger initial scan logs now that widgets are created
        self.refresh_ports()

    def draw_card_border(self, parent, title):
        title_lbl = ttk.Label(parent, text=title, font=("Segoe UI", 11, "bold"), foreground=COLOR_ACCENT)
        title_lbl.pack(anchor="w", padx=20, pady=(15, 5))
        
        line = tk.Frame(parent, height=1, bg="#2e2e3e")
        line.pack(fill="x", padx=20, pady=(0, 10))

    def refresh_ports(self):
        ports = [p.device for p in serial.tools.list_ports.comports()]
        self.port_combobox['values'] = ports
        if ports:
            self.port_combobox.set(ports[0])
            self.log_event(f"Scanned ports. Found: {', '.join(ports)}")
        else:
            self.port_combobox.set("None Found")
            self.log_event("Scanned ports. No active COM ports found.")

    def toggle_simulation(self):
        if self.simulation_mode.get():
            self.log_event("Switched to Simulation Mode.")
            self.sim_slider.state(['!disabled'])
            if self.is_connected:
                self.disconnect_serial()
        else:
            self.log_event("Switched to Hardware Mode. Select COM port to connect.")
            self.sim_slider.state(['disabled'])

    def toggle_connection(self):
        if self.is_connected:
            self.disconnect_serial()
        else:
            self.connect_serial()

    def connect_serial(self):
        port = self.port_combobox.get()
        if port == "None Found" or not port:
            messagebox.showerror("Port Error", "Please select a valid COM Port.")
            return
        
        try:
            self.serial_port = serial.Serial(port, 9600, timeout=1.0)
            self.is_connected = True
            self.running = True
            self.simulation_mode.set(False)
            self.sim_slider.state(['disabled'])
            
            # Start serial receiver thread
            self.serial_thread = threading.Thread(target=self.read_serial_data, daemon=True)
            self.serial_thread.start()
            
            self.connect_btn.configure(text="❌ DISCONNECT", background=COLOR_RED, foreground=TEXT_MAIN)
            self.log_event(f"SUCCESS: Connected to Arduino on port {port} at 9600 baud rate.")
            
        except Exception as e:
            messagebox.showerror("Connection Failed", f"Could not open port {port}:\n{str(e)}")
            self.log_event(f"ERROR: Failed to connect to {port}. {str(e)}")

    def disconnect_serial(self):
        self.running = False
        self.is_connected = False
        
        if self.serial_port and self.serial_port.is_open:
            self.serial_port.close()
            
        self.connect_btn.configure(text="🔌 CONNECT ARDUINO", background=COLOR_ACCENT, foreground=BG_MAIN)
        self.log_event("SYSTEM: Serial Connection closed.")
        self.refresh_ports()
        
        # Reset displays
        self.update_telemetry(0)

    def read_serial_data(self):
        buffer = ""
        while self.running and self.is_connected:
            try:
                if self.serial_port.in_waiting > 0:
                    data = self.serial_port.read(self.serial_port.in_waiting).decode('utf-8', errors='ignore')
                    buffer += data
                    while "\n" in buffer:
                        line, buffer = buffer.split("\n", 1)
                        line = line.strip()
                        if line:
                            self.data_queue.put(line)
                time.sleep(0.01)
            except Exception as e:
                self.data_queue.put(f"ERROR: {str(e)}")
                break

    def process_queue(self):
        while not self.data_queue.empty():
            line = self.data_queue.get()
            if line.startswith("ERROR:"):
                self.log_event(line)
                self.disconnect_serial()
                break
            
            # Parse "sensor = 450"
            if "sensor =" in line:
                try:
                    parts = line.split("=")
                    val_str = parts[1].strip()
                    val = int(val_str)
                    self.update_telemetry(val)
                except Exception as e:
                    self.log_event(f"Parse Warning: Couldn't process line '{line}'. {str(e)}")
        
        # If in simulation mode, take value directly from slider
        if self.simulation_mode.get():
            self.update_telemetry(int(self.sim_slider.get()))
            
        self.root.after(50, self.process_queue)

    def update_telemetry(self, raw_value):
        # Safety shield: prevent callback triggers before GUI layout setup is fully completed
        if not hasattr(self, 'lbl_state') or not hasattr(self, 'led2_canvas') or not hasattr(self, 'log_listbox'):
            self.sensor_value = raw_value
            self.percentage = min(100.0, max(0.0, (raw_value / 700.0) * 100.0))
            return
            
        # Update raw values
        self.sensor_value = raw_value
        
        # Map sensor reading to percentage
        # The sensor typically goes up to 700 based on Arduino code thresholds. Let's map 0-700 as 0-100%
        # Above 700, clamp to 100% or show overflow
        self.percentage = min(100.0, max(0.0, (raw_value / 700.0) * 100.0))
        
        # Determine current zone status based on Arduino conditional thresholds
        old_state = self.current_state
        
        # Map to Arduino code exact conditionals:
        # State 1: 100 to 600
        # State 2: 601 to 625
        # State 3: 626 to 700
        # Else: Below 100 or Above 700
        
        led2_state = False
        led3_state = False
        led4_state = False
        led5_state = False
        
        if 100 <= raw_value <= 600:
            self.current_state = "LOW-MEDIUM LEVEL"
            self.lbl_state.configure(foreground=COLOR_GREEN)
            led2_state = True
            # In original code, once pins turn on, they stay on unless else is hit.
            # However, on our dashboard we will display the clean, target logic of active indicators.
        elif 601 <= raw_value <= 625:
            self.current_state = "HIGH LEVEL WARNING"
            self.lbl_state.configure(foreground=COLOR_YELLOW)
            led3_state = True
        elif 626 <= raw_value <= 700:
            self.current_state = "CRITICAL TANK FULL!"
            self.lbl_state.configure(foreground=COLOR_RED)
            led4_state = True
            led5_state = True
        else:
            if raw_value < 100:
                self.current_state = "TANK EMPTY / INACTIVE"
                self.lbl_state.configure(foreground=TEXT_MUTED)
            else:
                self.current_state = "OUT-OF-BOUNDS / SAFETY OFF"
                self.lbl_state.configure(foreground=COLOR_RED)
        
        # Update labels
        self.lbl_sensor.configure(text=f"{raw_value}")
        self.lbl_percent.configure(text=f"{self.percentage:.1f} %")
        self.lbl_state.configure(text=self.current_state)
        
        # Update Virtual LEDs (canvas colored circles)
        self.update_virtual_led(self.led2_canvas, self.led2_indicator, COLOR_GREEN if led2_state else "#27272a")
        self.update_virtual_led(self.led3_canvas, self.led3_indicator, COLOR_YELLOW if led3_state else "#27272a")
        self.update_virtual_led(self.led4_canvas, self.led4_indicator, COLOR_RED if led4_state else "#27272a")
        self.update_virtual_led(self.led5_canvas, self.led5_indicator, COLOR_RED if led5_state else "#27272a")
        
        # Log event if state changed
        if self.current_state != old_state:
            self.log_event(f"STATE CHANGE: System entered '{self.current_state}' (Sensor: {raw_value})")

    def update_virtual_led(self, canvas, item, color):
        canvas.itemconfig(item, fill=color, outline="#ffffff" if color != "#27272a" else "#4b5563")

    def log_event(self, message):
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}"
        self.log_listbox.insert(tk.END, log_entry)
        self.log_listbox.yview(tk.END) # Auto scroll to bottom
        
        # Keep logs capped at 100 entries
        if self.log_listbox.size() > 100:
            self.log_listbox.delete(0)

    def on_slider_move(self, val):
        # Triggered when slider moves in simulation mode
        if self.simulation_mode.get():
            self.update_telemetry(int(float(val)))

    def draw_tank(self):
        self.tank_canvas.delete("all")
        
        # Dimensions
        x1, y1 = 40, 20
        x2, y2 = 180, 210
        tank_width = x2 - x1
        tank_height = y2 - y1
        
        # Fill ratio based on percentage
        fill_height = tank_height * (self.percentage / 100.0)
        water_y = y2 - fill_height
        
        # Choose water color based on current danger state
        if "CRITICAL" in self.current_state or "OUT-OF-BOUNDS" in self.current_state:
            water_color = COLOR_RED
            glow_color = "#fca5a5"
        elif "WARNING" in self.current_state:
            water_color = COLOR_YELLOW
            glow_color = "#fde047"
        else:
            water_color = "#0284c7" # Vibrant cyber blue water
            glow_color = "#38bdf8"
            
        # Draw Water body (if above 0%)
        if fill_height > 0:
            # We will draw waves at the top boundary of water
            points = [x1, y2]
            
            # Create animated sine wave points
            steps = 40
            for i in range(steps + 1):
                px = x1 + (i / steps) * tank_width
                # Sine wave math: dynamic offset based on phase and index
                py = water_y + 6 * math.sin((i / 8) + self.wave_phase)
                
                # Clamp so wave doesn't overflow tank boundaries
                py = max(y1, min(y2, py))
                points.append(px)
                points.append(py)
                
            points.extend([x2, y2])
            
            # Draw liquid fill
            self.tank_canvas.create_polygon(points, fill=water_color, outline="", tags="water")
            
            # Glow line at the top wave surface
            wave_line = points[2:-2] # Extract top surface points
            self.tank_canvas.create_line(wave_line, fill=glow_color, width=3, tags="water_top")
            
        # Draw elegant glassmorphic Tank Structure
        # Outer thick border (representing structural steel support or thick glass)
        self.tank_canvas.create_rectangle(x1, y1, x2, y2, outline="#4b5563", width=3)
        
        # Draw level measurement grids (Ticks) on the right side
        for val in range(0, 101, 20):
            ty = y2 - (val / 100.0) * tank_height
            # Draw ticks
            self.tank_canvas.create_line(x2 - 15, ty, x2, ty, fill="#4b5563", width=1.5)
            self.tank_canvas.create_text(x2 - 28, ty, text=f"{val}%", fill=TEXT_MUTED, font=("Segoe UI", 8))
            
        # Draw central big Percentage inside tank
        text_bg_color = BG_CARD
        self.tank_canvas.create_text(
            110, 115, text=f"{self.percentage:.0f}%", 
            fill="#ffffff", font=("Segoe UI", 24, "bold"), tags="text"
        )
        
    def animate_wave(self):
        # Increment wave phase for ripple effect
        self.wave_phase += 0.12
        self.draw_tank()
        
        # Repeat every 50ms for smooth 20 FPS animation
        if self.running:
            self.root.after(50, self.animate_wave)

    def close_app(self):
        self.running = False
        self.is_connected = False
        if self.serial_port and self.serial_port.is_open:
            self.serial_port.close()
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = IoTWaterLevelDashboard(root)
    root.protocol("WM_DELETE_WINDOW", app.close_app)
    root.mainloop()
