class PointerManager:
    """Manages interactive, movable pointers on a Matplotlib axis."""

    def __init__(self, ax, canvas, start_pointer_line, end_pointer_line, x_data_range_mpl, start_var, end_var, app_instance):
        self.ax = ax
        self.canvas = canvas
        self.start_pointer_line = start_pointer_line
        self.end_pointer_line = end_pointer_line
        self.x_data_range_mpl = x_data_range_mpl
        self.start_var = start_var
        self.end_var = end_var
        self.app = app_instance # --- NEW: Store reference to the main app instance ---

        self.selected_pointer = None
        self.epsilon = 0.01 * (x_data_range_mpl[1] - x_data_range_mpl[0]) 
        if self.epsilon == 0: 
            self.epsilon = 1e-6 

        self.cid_press = self.canvas.mpl_connect('button_press_event', self.on_press)
        self.cid_motion = self.canvas.mpl_connect('motion_notify_event', self.on_motion)
        self.cid_release = self.canvas.mpl_connect('button_release_event', self.on_release)

        self._update_pointer_display() # Initial update of the GUI displays and internal datetimes

    def _get_clamped_x_value(self, event):
        """Converts mouse x-coordinate to data x-value, clamped to the plot's data range."""
        if event.inaxes != self.ax: # Check if click is within the axes
            return None
        
        x = event.xdata
        if x is None: # Clicked outside valid data area on axes
            return None

        # Clamp x to the actual plot's data range
        min_x, max_x = self.x_data_range_mpl
        return max(min_x, min(max_x, x))

    def on_press(self, event):
        """Handles mouse button press event."""
        if event.inaxes != self.ax: return # Clicked outside the plot area
        if event.button != 1: return # Only respond to left-click

        clicked_x = event.xdata
        if clicked_x is None: return # Clicked but not on data

        # Get current x-positions of the pointers (Matplotlib internal float values)
        start_x_pos = self.start_pointer_line.get_xdata()[0]
        end_x_pos = self.end_pointer_line.get_xdata()[0]

        # Check if the click is close to the start pointer
        if abs(clicked_x - start_x_pos) < self.epsilon:
            self.selected_pointer = self.start_pointer_line
            self.start_pointer_line.set_color('blue') # Highlight selected pointer
            self.canvas.draw_idle() # Request redraw for immediate visual feedback
            return

        # Check if the click is close to the end pointer
        if abs(clicked_x - end_x_pos) < self.epsilon:
            self.selected_pointer = self.end_pointer_line
            self.end_pointer_line.set_color('blue') # Highlight selected pointer
            self.canvas.draw_idle()
            return

    def on_motion(self, event):
        """Handles mouse motion event (dragging)."""
        if self.selected_pointer is None: return # No pointer is currently selected for dragging
        
        new_x = self._get_clamped_x_value(event)
        if new_x is None: return # Mouse is outside axes or no valid data x-coord

        # Ensure start pointer doesn't go past end pointer, and vice versa
        if self.selected_pointer == self.start_pointer_line:
            end_x_pos = self.end_pointer_line.get_xdata()[0]
            if new_x > end_x_pos:
                new_x = end_x_pos # Clamp start pointer to end pointer's position
        elif self.selected_pointer == self.end_pointer_line:
            start_x_pos = self.start_pointer_line.get_xdata()[0]
            if new_x < start_x_pos:
                new_x = start_x_pos # Clamp end pointer to start pointer's position

        self.selected_pointer.set_xdata([new_x, new_x]) # Update the line's x-position
        self._update_pointer_display() # Update Tkinter StringVars with new positions
        self.canvas.draw_idle() # Request redraw

    def on_release(self, event):
        """Handles mouse button release event."""
        if self.selected_pointer:
            # Revert pointer color to original
            if self.selected_pointer == self.start_pointer_line:
                self.start_pointer_line.set_color('red')
            else:
                self.end_pointer_line.set_color('green')
            self.selected_pointer = None # Deselect the pointer
            self._update_pointer_display() # Final update after release
            self.canvas.draw_idle()

    def _update_pointer_display(self):
        """Updates the Tkinter StringVars with the current pointer positions
           AND stores the actual datetime objects in the main app."""
        start_x_val_mpl = self.start_pointer_line.get_xdata()[0]
        end_x_val_mpl = self.end_pointer_line.get_xdata()[0]


        self.start_var.set(f"{start_x_val_mpl}")
        self.end_var.set(f"{end_x_val_mpl}")
        # --- NEW: Store numeric values for non-datetime x-axis (important for consistency) ---
        self.app._selected_start_dt = start_x_val_mpl # Store the raw numeric value
        self.app._selected_end_dt = end_x_val_mpl
        print(self.app._selected_end_dt)
        # --- END NEW ---

    def disconnect(self):
        """Disconnects all Matplotlib event handlers for cleanup."""
        self.canvas.mpl_disconnect(self.cid_press)
        self.canvas.mpl_disconnect(self.cid_motion)
        self.canvas.mpl_disconnect(self.cid_release)
        # --- NEW: Clear stored datetime objects on disconnect ---
        self.app._selected_start_dt = None
        self.app._selected_end_dt = None
        # --- END NEW ---