import tkinter as tk
from tkinter import filedialog, messagebox, Listbox, Scrollbar, MULTIPLE
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from classes.pointer_manager import PointerManager

class CSVPlotterApp:
    def __init__(self, master):
        self.master = master
        master.title("CSV Column Plotter")

        self.df = None
        self.fig = None
        self.canvas = None

        # --- Configure master grid to allow expansion ---
        master.grid_columnconfigure(0, weight=1)
        master.grid_rowconfigure(1, weight=1)

        # --- Control Frame (for buttons, dropdowns, listbox) ---
        self.control_frame = tk.Frame(master)
        self.control_frame.grid(row=0, column=0, pady=10, padx=10, sticky="ew")

        # Configure control_frame's grid
        self.control_frame.grid_columnconfigure(1, weight=1)
        self.control_frame.grid_rowconfigure(2, weight=1) # Row for Y-axis listbox

        # Select File Button
        self.select_file_button = tk.Button(self.control_frame, text="Select CSV File", command=self.select_csv_file)
        self.select_file_button.grid(row=0, column=0, columnspan=2, pady=5)

        # X-axis selection
        tk.Label(self.control_frame, text="X-axis Column:").grid(row=1, column=0, sticky="w", padx=5)
        self.x_axis_var = tk.StringVar(master)
        self.x_axis_dropdown = tk.OptionMenu(self.control_frame, self.x_axis_var, "No file loaded")
        self.x_axis_dropdown.config(width=20)
        self.x_axis_dropdown.grid(row=1, column=1, padx=5, sticky="ew")

        # Y-axis selection (Listbox)
        tk.Label(self.control_frame, text="Y-axis Columns:").grid(row=2, column=0, sticky="nw", padx=5)
        
        # Frame to contain the Listbox and Scrollbar (with border for visibility debug)
        self.y_axis_listbox_frame = tk.Frame(self.control_frame, relief=tk.RIDGE, borderwidth=2)
        self.y_axis_listbox_frame.grid(row=2, column=1, padx=5, sticky="nsew")

        # Configure the internal grid of y_axis_listbox_frame for Listbox expansion
        self.y_axis_listbox_frame.grid_rowconfigure(0, weight=1)
        self.y_axis_listbox_frame.grid_columnconfigure(0, weight=1)

        # The Listbox itself (with increased height/width for visibility debug)
        self.y_axis_listbox = Listbox(self.y_axis_listbox_frame, selectmode=MULTIPLE, height=10, width=40)
        self.y_axis_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=2, pady=2)

        # The Scrollbar
        self.y_axis_scrollbar = Scrollbar(self.y_axis_listbox_frame, orient="vertical")
        self.y_axis_scrollbar.config(command=self.y_axis_listbox.yview)
        self.y_axis_listbox.config(yscrollcommand=self.y_axis_scrollbar.set)
        self.y_axis_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Y-axis selection buttons
        self.select_all_btn = tk.Button(self.control_frame, text="Select All Y", command=self.select_all_y_columns)
        self.select_all_btn.grid(row=3, column=0, pady=2, padx=5, sticky="ew")
        self.deselect_all_btn = tk.Button(self.control_frame, text="Deselect All Y", command=self.deselect_all_y_columns)
        self.deselect_all_btn.grid(row=3, column=1, pady=2, padx=5, sticky="ew")

        # In your CSVPlotterApp's __init__ method, find the Generate Plot Button section.
        # We'll add the new elements just below it, or in a new section.

        # Generate Plot Button
        self.plot_button = tk.Button(self.control_frame, text="Generate Plot", command=self.plot_columns)
        self.plot_button.grid(row=4, column=0, columnspan=2, pady=10)

# Inside your CSVPlotterApp's __init__ method:

        # --- Subsequence Extraction Controls (Modified for Pointers) ---
        # Add a visual separator
        tk.Frame(self.control_frame, height=2, bd=1, relief=tk.SUNKEN).grid(row=5, column=0, columnspan=2, sticky="ew", pady=5)

        tk.Label(self.control_frame, text="Extract Subsequence (Use Pointers):").grid(row=6, column=0, columnspan=2, sticky="w", padx=5)

        # Start Timestamp Display (read-only Entry)
        tk.Label(self.control_frame, text="Start Timestamp:").grid(row=7, column=0, sticky="w", padx=5)
        self.start_timestamp_var = tk.StringVar(master)
        self.start_timestamp_display = tk.Entry(self.control_frame, textvariable=self.start_timestamp_var, width=30, state='readonly')
        self.start_timestamp_display.grid(row=7, column=1, padx=5, sticky="ew")

        # End Timestamp Display (read-only Entry)
        tk.Label(self.control_frame, text="End Timestamp:").grid(row=8, column=0, sticky="w", padx=5)
        self.end_timestamp_var = tk.StringVar(master)
        self.end_timestamp_display = tk.Entry(self.control_frame, textvariable=self.end_timestamp_var, width=30, state='readonly')
        self.end_timestamp_display.grid(row=8, column=1, padx=5, sticky="ew")

        # Export Subsequence Button
        self.export_subsequence_button = tk.Button(self.control_frame, text="Export Subsequence", command=self.export_subsequence)
        self.export_subsequence_button.grid(row=9, column=0, columnspan=2, pady=10)

        # Variables to hold Matplotlib Line2D objects and the PointerManager instance
        self.start_pointer_line = None
        self.end_pointer_line = None
        self.pointer_manager = None

        # --- NEW: Attributes to store the actual datetime objects from pointer positions ---
        self._selected_start_dt = None
        self._selected_end_dt = None
        # --- END NEW ---

        # Ensure enough rows in control_frame can hold the new elements
        # (Assuming you already have grid_rowconfigure(2, weight=1) for listbox/checkboxes)
        # No additional weights are typically needed for rows with fixed-height widgets like labels/entries/buttons.

        # --- End Subsequence Extraction Controls ---

        # Important: Update master grid_rowconfigure to accommodate new rows
        # The plot_frame is in row 1, so ensure rows after 1 are handled.
        # This is flexible, just make sure there's enough room for new rows
        self.master.grid_rowconfigure(1, weight=1) # Plot frame row remains expansive
        # No specific weight for control_frame rows beyond row 2 (Listbox/Checkbuttons)
        # as the entries/buttons don't need to expand vertically much.

        # --- Plot Frame ---
        self.plot_frame = tk.Frame(master, bg="lightgray")
        self.plot_frame.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")

        # Initial state of controls
        self.disable_plotting_controls()

    def disable_plotting_controls(self):
        self.x_axis_dropdown.config(state=tk.DISABLED)
        self.y_axis_listbox.config(state=tk.DISABLED)
        # If using Checkbuttons: self.y_axis_canvas.config(state=tk.DISABLED)
        
        self.plot_button.config(state=tk.DISABLED)
        self.select_all_btn.config(state=tk.DISABLED)
        self.deselect_all_btn.config(state=tk.DISABLED)

        # Disable pointer-related GUI elements
        self.start_timestamp_display.config(state=tk.DISABLED) # Make display non-interactive
        self.end_timestamp_display.config(state=tk.DISABLED)   # Make display non-interactive
        self.export_subsequence_button.config(state=tk.DISABLED)

        # Disconnect pointers if they exist (important for cleanup)
        if self.pointer_manager:
            self.pointer_manager.disconnect()
            self.pointer_manager = None
            # Also remove lines from plot if they exist and are not managed by manager cleanup
            if self.start_pointer_line and self.start_pointer_line.axes:
                self.start_pointer_line.remove()
                self.start_pointer_line = None
            if self.end_pointer_line and self.end_pointer_line.axes:
                self.end_pointer_line.remove()
                self.end_pointer_line = None
            if self.canvas and self.canvas.figure: # Request a redraw after removing lines
                self.canvas.draw_idle()

    def enable_plotting_controls(self):
        self.x_axis_dropdown.config(state=tk.NORMAL)
        self.y_axis_listbox.config(state=tk.NORMAL)
        # If using Checkbuttons: self.y_axis_canvas.config(state=tk.NORMAL)
        
        self.plot_button.config(state=tk.NORMAL)
        self.select_all_btn.config(state=tk.NORMAL)
        self.deselect_all_btn.config(state=tk.NORMAL)

        # Enable pointer-related GUI elements
        self.start_timestamp_display.config(state=tk.NORMAL) # Set to NORMAL to allow value updates
        self.end_timestamp_display.config(state=tk.NORMAL)   # Set to NORMAL to allow value updates
        self.export_subsequence_button.config(state=tk.NORMAL)

    def update_column_options(self):
        print("DEBUG: update_column_options called.")
        if self.df is not None:
            columns = self.df.columns.tolist()
            print(f"DEBUG: Columns retrieved for update (before Listbox insert): {columns}")
            print(f"DEBUG: Type of self.y_axis_listbox: {type(self.y_axis_listbox)}")
            print(f"DEBUG: ID of self.y_axis_listbox: {id(self.y_axis_listbox)}")


            # Update X-axis dropdown
            self.x_axis_dropdown['menu'].delete(0, 'end')
            for col in columns:
                self.x_axis_dropdown['menu'].add_command(label=col, command=tk._setit(self.x_axis_var, col))
            if columns:
                self.x_axis_var.set(columns[0])
            else:
                self.x_axis_var.set("No columns")

            self.y_axis_listbox.config(state=tk.NORMAL)

            # Update Y-axis listbox
            self.y_axis_listbox.delete(0, tk.END) # Clear existing items
            for col in (columns):
                self.y_axis_listbox.insert(tk.END, col) # THIS IS WHERE IT SHOULD INSERT
                print(f"DEBUG: Inserted '{col}'. Current size: {self.y_axis_listbox.size()}") # Print size after each insert


            print(f"DEBUG: Y-axis listbox populated with {self.y_axis_listbox.size()} items (after insert loop).")
            print(f"DEBUG: Y-axis listbox state AFTER population: {self.y_axis_listbox.cget('state')}")

            self.enable_plotting_controls()
            print(f"DEBUG: Y-axis listbox state AFTER enable_plotting_controls: {self.y_axis_listbox.cget('state')}")
        else:
            print("DEBUG: DataFrame is None, disabling controls.")
            self.x_axis_var.set("No file loaded")
            self.x_axis_dropdown['menu'].delete(0, 'end')
            self.y_axis_listbox.delete(0, tk.END)
            self.disable_plotting_controls()

    def select_csv_file(self):
        file_path = filedialog.askopenfilename(
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        if file_path:
            try:
                self.df = pd.read_csv(file_path)
                
                # --- Crucial: Convert 'timestamp' column to datetime here ---
                # if 'timestamp' in self.df.columns:
                    # self.df['timestamp'] = pd.to_datetime(self.df['timestamp'], unit='ns', errors='coerce')
                    # Optionally, drop rows where timestamp conversion failed.
                    # This might remove valid data if only a few timestamps are bad.
                    # self.df.dropna(subset=['timestamp'], inplace=True)
                    # messagebox.showinfo("Timestamp Conversion", "Attempted to convert 'timestamp' column to datetime format.")
                # else:
                    # messagebox.showwarning("No Timestamp Column", "CSV does not have a 'timestamp' column. Subsequence extraction by pointers might not work as expected.")
                # --- End Crucial Addition ---

                # Your existing debug prints (optional to keep)
                # print(f"DEBUG: CSV file loaded. DataFrame head:\n{self.df.head()}")
                # print(f"DEBUG: Columns found: {self.df.columns.tolist()}")
                # print(f"DEBUG: Before update_column_options call. ID of Listbox: {id(self.y_axis_listbox)}")
                
                # messagebox.showinfo("File Loaded", f"Successfully loaded: {file_path}")
                self.update_column_options() # This will now enable listbox/checkboxes AND the pointer display fields
                
                # print(f"DEBUG: After update_column_options call. ID of Listbox: {id(self.y_axis_listbox)}")
                self.clear_plot() # Clear previous plot if any
            except Exception as e:
                messagebox.showerror("Error", f"Failed to read CSV: {e}")
                # print(f"DEBUG: Error loading CSV: {e}") # Optional debug
                self.df = None
                # print(f"DEBUG: Error path: Before update_column_options call. ID of Listbox: {id(self.y_axis_listbox)}") # Optional debug
                self.update_column_options() # This will disable controls if df is None
                # print(f"DEBUG: Error path: After update_column_options call. ID of Listbox: {id(self.y_axis_listbox)}") # Optional debug
                self.clear_plot()

    def select_all_y_columns(self):
        if self.df is not None:
            for i in range(self.y_axis_listbox.size()):
                self.y_axis_listbox.select_set(i)

    def deselect_all_y_columns(self):
        self.y_axis_listbox.selection_clear(0, tk.END)

    def clear_plot(self):
        if self.canvas:
            self.canvas.get_tk_widget().destroy()
            plt.close(self.fig)
            self.canvas = None
            self.fig = None

    def plot_columns(self):
        if self.df is None:
            messagebox.showwarning("No Data", "Please load a CSV file first.")
            return

        x_col = self.x_axis_var.get()
        selected_y_indices = self.y_axis_listbox.curselection() # Use .curselection() for Listbox
        y_cols = [self.y_axis_listbox.get(i) for i in selected_y_indices]
        # If using Checkbuttons:
        # y_cols = [col_name for col_name, var in self.y_axis_checkboxes.items() if var.get()]

        if not x_col or x_col == "No file loaded" or x_col not in self.df.columns:
            messagebox.showwarning("Invalid Selection", "Please select a valid X-axis column.")
            return

        if not y_cols:
            messagebox.showwarning("No Selection", "Please select at least one Y-axis column.")
            return
        
        # Ensure X-axis data is suitable for plotting and pointer interaction
        x_data_for_plot = self.df[x_col]
        is_datetime_x = pd.api.types.is_datetime64_any_dtype(x_data_for_plot)

        if not is_datetime_x: # If X-axis is not datetime, convert to numeric for plotting
            x_data_for_plot = pd.to_numeric(x_data_for_plot, errors='coerce')
            if x_data_for_plot.isnull().all():
                messagebox.showwarning("Invalid X-axis Data", f"X-axis column '{x_col}' contains no valid numeric or datetime data for plotting.")
                return
            
        # Ensure Y-axis data is numeric
        for y_col in y_cols:
            if not pd.api.types.is_numeric_dtype(self.df[y_col]):
                messagebox.showwarning("Invalid Y-axis Data", f"Y-axis column '{y_col}' is not numeric and cannot be plotted.")
                y_cols.remove(y_col) # Remove non-numeric columns from list to plot
        if not y_cols: # If all y_cols were removed due to non-numeric data
            messagebox.showwarning("No Plottable Y-axis Data", "All selected Y-axis columns contain no valid numeric data for plotting.")
            return

        self.clear_plot() # Clear previous plot

        self.fig, ax = plt.subplots(figsize=(10, 7))

        plotted_any = False
        for y_col in y_cols:
            # We already converted Y-axis to numeric or removed non-numeric above
            ax.plot(x_data_for_plot, self.df[y_col], label=y_col)
            plotted_any = True

        if not plotted_any:
            messagebox.showwarning("No Plottable Data", "No valid numeric Y-axis columns found to plot against the selected X-axis.")
            self.clear_plot()
            return

        ax.set_title(f"Plot of {', '.join(y_cols)} vs {x_col}")
        ax.set_xlabel(x_col)
        ax.set_ylabel("Value")
        ax.legend()
        ax.grid(True)
        self.fig.tight_layout()

        self.canvas = FigureCanvasTkAgg(self.fig, master=self.plot_frame)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        # --- Initialize Pointers ---
        # Get the X-axis limits of the plot for initial pointer positions and clamping
        min_x_plot, max_x_plot = ax.get_xlim()

        
        # Calculate initial pointer positions (e.g., 20% and 80% of the x-range)
        range_span = max_x_plot - min_x_plot
        initial_start_pos_mpl = min_x_plot + 0.2 * range_span
        initial_end_pos_mpl = min_x_plot + 0.8 * range_span

        # Draw the initial vertical lines (pointers) on the plot
        self.start_pointer_line = ax.axvline(x=initial_start_pos_mpl, color='red', linestyle='--', linewidth=2, label='Start Marker')
        self.end_pointer_line = ax.axvline(x=initial_end_pos_mpl, color='green', linestyle='--', linewidth=2, label='End Marker')
        
        # Initialize the PointerManager
        self.pointer_manager = PointerManager(
            ax=ax,
            canvas=self.canvas,
            start_pointer_line=self.start_pointer_line,
            end_pointer_line=self.end_pointer_line,
            x_data_range_mpl=(min_x_plot, max_x_plot),
            start_var=self.start_timestamp_var,
            end_var=self.end_timestamp_var,
            app_instance=self # --- MODIFICATION: Pass 'self' here ---
        )
        
        # Explicitly set the readonly state of the display entries after initial plot, 
        # as the enable_plotting_controls might have set them to NORMAL for a brief moment.
        self.start_timestamp_display.config(state='readonly')
        self.end_timestamp_display.config(state='readonly')

        self.canvas.draw_idle() # Request final redraw to show pointers

    def export_subsequence(self):
        if self.df is None:
            messagebox.showwarning("No Data", "Please load a CSV file first.")
            return

        start_ts_str = self.start_timestamp_var.get().strip()
        end_ts_str = self.end_timestamp_var.get().strip()

        if not start_ts_str or not end_ts_str:
            messagebox.showwarning("Input Error", "Please move the pointers to define the start and end timestamps.")
            return
        
        if 'timestamp' not in self.df.columns:
            messagebox.showerror("Error", "The 'timestamp' column is not available or not in datetime format. Please load a CSV with valid timestamps.")
            return

        try:
            # --- MODIFICATION: Add the 'format' argument to pd.to_datetime ---
            # '%f' here correctly handles microseconds (up to 6 digits)

            start_dt = int(float(start_ts_str))
            end_dt = int(float(end_ts_str))
            # --- END MODIFICATION ---
        except Exception as e:
            messagebox.showerror("Timestamp Parse Error", f"Could not parse timestamps from pointer positions. Error: {e}\nEnsure CSV 'timestamp' format is compatible.")
            return

        # Filter the DataFrame based on the datetime range
        sub_df = self.df[(self.df['timestamp'] >= start_dt) & (self.df['timestamp'] <= end_dt)].copy()

        if sub_df.empty:
            messagebox.showwarning("No Data Found", "No data points found within the specified timestamp range.")
            return

        # Prompt user for save location
        output_file_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            title="Save Subsequence As"
        )

        if output_file_path:
            try:
                sub_df.to_csv(output_file_path, index=False)
                messagebox.showinfo("Export Successful", f"Subsequence exported to:\n{output_file_path}")
            except Exception as e:
                messagebox.showerror("Export Error", f"Failed to export subsequence: {e}")
        else:
            messagebox.showinfo("Export Cancelled", "Subsequence export was cancelled.")