"""
Simple CSV Editor GUI for tool data management.

This module provides a basic Tkinter interface for editing the tool-data.csv file.
Automatically creates a backup when opened.
"""

import os
import sys
import tkinter as tk
from tkinter import ttk, messagebox
from typing import Tuple, Dict, Any, List
from datetime import datetime

# Add parent directory to Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Project imports
from Utils.file_utils import FileUtils
from Utils.logging_utils import setup_logger
from Backups.backup_manager import BackupManager


class CSVTableView:
    """Handles the table display and editing functionality."""
    
    def __init__(self, parent):
        """Initialize the table view."""
        self.parent = parent
        self.headers = []
        self.original_date_values = {}  # Store original date values by item ID
        self.create_table()
        
    def create_table(self):
        """Create the treeview widget with scrollbars."""
        # Frame for table and scrollbars
        table_frame = ttk.Frame(self.parent)
        table_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Scrollbars
        vsb = ttk.Scrollbar(table_frame, orient="vertical")
        hsb = ttk.Scrollbar(table_frame, orient="horizontal")
        
        # Treeview
        self.tree = ttk.Treeview(table_frame, 
                                yscrollcommand=vsb.set,
                                xscrollcommand=hsb.set)
        
        # Configure scrollbars
        vsb.config(command=self.tree.yview)
        hsb.config(command=self.tree.xview)
        
        # Grid layout
        self.tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        vsb.grid(row=0, column=1, sticky=(tk.N, tk.S))
        hsb.grid(row=1, column=0, sticky=(tk.W, tk.E))
        
        # Configure weights
        table_frame.columnconfigure(0, weight=1)
        table_frame.rowconfigure(0, weight=1)
        
        # Bind double-click
        self.tree.bind("<Double-1>", self._on_double_click)
        
    def load_data(self, headers: List[str], data: List[List[str]]):
        """Load data into the table."""
        # Clear existing
        self.clear()
        
        # Store headers
        self.headers = headers
        
        if not headers:
            return
            
        # Configure columns
        self.tree["columns"] = headers
        self.tree["show"] = "headings"  # Hide the tree column (row numbers)
        
        # Set column widths based on header and content type
        numeric_columns = ['tool_number', 'tool_direction', 'diameter', 'tool_length', 
                          'max_working_length', 'tool_holder_z_offset', 'in_spindle']
        narrow_columns = ['tool_type', 'rotation_direction']
        wide_columns = ['notes', 'description', 'last_change_time']
        
        for header in headers:
            self.tree.heading(header, text=header)
            
            # Determine column width
            if header in numeric_columns:
                width = 80  # Narrow for numbers
            elif header in narrow_columns:
                width = 100  # Medium for short text
            elif header in wide_columns:
                width = 200  # Wide for long text
            else:
                width = 150  # Default
                
            self.tree.column(header, width=width)
            
        # Insert data rows with date formatting
        for i, row in enumerate(data):
            # Format last_change_time for display if it exists
            display_row = row.copy()
            if 'last_change_time' in headers:
                time_idx = headers.index('last_change_time')
                if time_idx < len(row) and row[time_idx]:
                    try:
                        # Convert Excel date number to readable format
                        excel_date = float(row[time_idx])
                        # Excel dates start from 1900-01-01
                        date_obj = datetime(1900, 1, 1) + pd.Timedelta(days=excel_date - 2)
                        display_row[time_idx] = date_obj.strftime('%Y-%m-%d %H:%M')
                    except:
                        # Keep original if conversion fails
                        pass
            
            item = self.tree.insert("", "end", values=display_row)
            
            # Store original date value
            if 'last_change_time' in headers:
                time_idx = headers.index('last_change_time')
                if time_idx < len(row):
                    self.original_date_values[item] = row[time_idx]
            
    def get_all_data(self) -> List[List[str]]:
        """Get all data from the table including headers."""
        if not self.headers:
            return []
            
        # Start with headers
        all_data = [self.headers]
        
        # Add all rows
        for child in self.tree.get_children():
            values = self.tree.item(child)['values']
            all_data.append(list(values))
            
        return all_data
        
    def add_row(self):
        """Add an empty row to the table."""
        if not self.headers:
            return
            
        # Create empty row
        new_row = [''] * len(self.headers)
        self.tree.insert("", "end", values=new_row)
        
    def delete_selected_row(self):
        """Delete the currently selected row."""
        selection = self.tree.selection()
        if not selection:
            return False
            
        # Delete selected items
        for item in selection:
            self.tree.delete(item)
            
        # Renumber remaining rows
        self._renumber_rows()
        return True
        
    def clear(self):
        """Clear all data from the table."""
        for item in self.tree.get_children():
            self.tree.delete(item)
            
    def _renumber_rows(self):
        """Renumber all rows sequentially."""
        # No longer needed since we don't show row numbers
        pass
            
    def _on_double_click(self, event):
        """Handle double-click for editing."""
        selection = self.tree.selection()
        if not selection:
            return
            
        item = selection[0]
        column = self.tree.identify_column(event.x)
        
        # Get column index (columns are numbered from #1)
        try:
            col_idx = int(column.replace('#', '')) - 1
        except ValueError:
            return
        
        # Get current value
        values = list(self.tree.item(item)['values'])
        current_value = values[col_idx] if col_idx < len(values) else ''
        
        # Open edit dialog
        self._edit_cell(item, col_idx, current_value)
        
    def _edit_cell(self, item, col_idx: int, current_value: str):
        """Open a dialog to edit a cell value."""
        dialog = tk.Toplevel(self.tree)
        dialog.title("Edit Cell")
        dialog.geometry("300x100")
        dialog.transient(self.tree.master)
        dialog.grab_set()
        
        # Entry widget
        entry = ttk.Entry(dialog, width=40)
        entry.insert(0, str(current_value))
        entry.pack(pady=20)
        entry.select_range(0, tk.END)
        entry.focus()
        
        # Save function
        def save():
            new_value = entry.get()
            values = list(self.tree.item(item)['values'])
            values[col_idx] = new_value
            self.tree.item(item, values=values)
            dialog.destroy()
            
        # Buttons
        button_frame = ttk.Frame(dialog)
        button_frame.pack()
        
        ttk.Button(button_frame, text="OK", command=save).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Cancel", command=dialog.destroy).pack(side=tk.LEFT)
        
        # Enter key saves
        entry.bind('<Return>', lambda e: save())


class CSVEditor:
    """Main CSV editor application."""
    
    # Single source of truth for file path
    CSV_FILENAME = "tool-data.csv"
    
    def __init__(self):
        """Initialize the CSV editor."""
        # Logging
        self.logger = setup_logger(__name__)
        self.logger.info("Starting CSV Editor")
        
        # Components
        self.backup_manager = BackupManager()
        
        # Build path to CSV file
        self.csv_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
            "Data",
            self.CSV_FILENAME
        )
        
        # Create GUI
        self._create_gui()
        
        # Initialize
        self._create_startup_backup()
        self._load_csv_tool_data()
        
    def _create_gui(self):
        """Create the main window and components."""
        # Main window
        self.root = tk.Tk()
        self.root.title("CSV Tool Data Editor")
        self.root.geometry("1200x800")
        self.root.minsize(1200, 600)
        
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(1, weight=1)
        
        # Controls
        self._create_controls(main_frame)
        
        # Table
        self.table = CSVTableView(main_frame)
        
    def _create_controls(self, parent):
        """Create control buttons and status."""
        control_frame = ttk.Frame(parent)
        control_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Buttons - KISS principle
        ttk.Button(control_frame, text="Save", command=self._save_tool_data_to_csv).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="Reload", command=self._reload_tool_data_from_disk).pack(side=tk.LEFT, padx=5)
        
        # Status
        self.status_label = ttk.Label(control_frame, text="Ready")
        self.status_label.pack(side=tk.RIGHT, padx=5)
        
    def _create_startup_backup(self):
        """Create automatic backup of tool data when editor opens."""
        try:
            success, message, details = self.backup_manager.create_backup(
                self.csv_path
            )
            if success:
                backup_name = os.path.basename(details.get('backup_file', ''))
                self._set_status(f"Backup: {backup_name}")
                self.logger.info(f"Backup created: {backup_name}")
            else:
                self._show_error(f"Backup failed: {message}")
        except Exception as e:
            self._show_error(f"Backup error: {str(e)}")
            
    def _load_csv_tool_data(self):
        """Load CSV tool data file into table widget."""
        try:
            # Use existing util function
            success, rows, details = FileUtils.read_csv(self.csv_path)
            
            if not success:
                self._show_error(f"Load failed: {rows}")  # rows contains error message on failure
                return
                
            # Extract data from CSV (rows is list of dicts)
            tool_rows = details.get('rows', [])
            
            # Get headers from first row's keys
            headers = list(tool_rows[0].keys()) if tool_rows else []
            
            # Convert rows from dicts to lists for table display
            data = []
            for row_dict in tool_rows:
                row_list = [str(row_dict.get(h, '')) for h in headers]
                data.append(row_list)
            
            # Load into table
            self.table.load_data(headers, data)
            self._set_status(f"Loaded {len(data)} rows")
            
        except Exception as e:
            self._show_error(f"Load error: {str(e)}")
            
    def _save_tool_data_to_csv(self):
        """Save table widget data to CSV tool data file."""
        try:
            # Get data from table
            all_data = self.table.get_all_data()
            
            if not all_data:
                self._show_error("No data to save")
                return
                
            # Convert table data (list of lists) to list of dicts for FileUtils
            headers = all_data[0] if all_data else []
            rows_as_dicts = []
            
            for row_list in all_data[1:]:  # Skip header row
                row_dict = {}
                for i, header in enumerate(headers):
                    row_dict[header] = row_list[i] if i < len(row_list) else ''
                rows_as_dicts.append(row_dict)
            
            # Use existing util function
            success, message, _ = FileUtils.write_csv(self.csv_path, rows_as_dicts)
            
            if success:
                self._set_status("Saved")
                messagebox.showinfo("Success", "File saved")
            else:
                self._show_error(f"Save failed: {message}")
                
        except Exception as e:
            self._show_error(f"Save error: {str(e)}")
            
    def _reload_tool_data_from_disk(self):
        """Reload tool data from CSV file on disk."""
        self._load_csv_tool_data()
        messagebox.showinfo("Success", "File reloaded")
        
                
    def _set_status(self, text: str):
        """Update status label."""
        self.status_label.config(text=text)
        
    def _show_error(self, message: str):
        """Show error to user and log it."""
        self.logger.error(message)
        messagebox.showerror("Error", message)
        self._set_status("Error")
        
    def run(self):
        """Start the application."""
        self.root.mainloop()


def main():
    """Entry point."""
    try:
        csv_tool_editor = CSVEditor()
        csv_tool_editor.run()
    except Exception as e:
        logger = setup_logger(__name__)
        logger.exception("Startup failed")
        messagebox.showerror("Error", f"Failed to start:\n{str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()