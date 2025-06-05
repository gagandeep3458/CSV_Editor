import tkinter as tk
from classes.csv_plotter import CSVPlotterApp

# Main part of the application
if __name__ == "__main__":
    root = tk.Tk()
    app = CSVPlotterApp(root)
    root.mainloop()