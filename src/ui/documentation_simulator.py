"""
Standalone UI application for testing AI Documentation System functionality.
No external dependencies required beyond tkinter.
"""
import tkinter as tk
from tkinter import ttk, scrolledtext
import json
from pathlib import Path
from typing import Dict, Any
import asyncio
from datetime import datetime

# Hardcoded path to local documentation
LOCAL_DOCS_PATH = Path(r"C:\Users\bjcor\Desktop\Sage Local\Documentation")

class MockAgent:
    """Mock agent for testing."""
    async def process_request(self, **kwargs) -> Dict[str, Any]:
        return {
            "timestamp": datetime.now().isoformat(),
            "request": kwargs,
            "response": "Mock response for testing"
        }

class StandaloneSimulator:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("AI Documentation System Simulator")
        self.root.geometry("1200x800")
        
        # Initialize mock agents
        self.query_agent = MockAgent()
        self.draft_agent = MockAgent()
        self.review_agent = MockAgent()
        
        self.setup_ui()
        self.load_local_docs()
        
    def setup_ui(self):
        """Setup the UI components."""
        # Main container
        main_container = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        main_container.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Left panel - Document Browser
        left_panel = ttk.Frame(main_container)
        main_container.add(left_panel)
        
        # Document tree
        self.doc_tree = ttk.Treeview(left_panel)
        self.doc_tree.pack(fill=tk.BOTH, expand=True)
        self.doc_tree.heading('#0', text='Local Documentation')
        
        # Right panel
        right_panel = ttk.Frame(main_container)
        main_container.add(right_panel)
        
        # Operation buttons
        btn_frame = ttk.Frame(right_panel)
        btn_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(
            btn_frame,
            text="Generate Draft",
            command=lambda: self.run_async(self.generate_draft())
        ).pack(side=tk.LEFT, padx=2)
        
        ttk.Button(
            btn_frame,
            text="Review Content",
            command=lambda: self.run_async(self.review_content())
        ).pack(side=tk.LEFT, padx=2)
        
        ttk.Button(
            btn_frame,
            text="Query Docs",
            command=lambda: self.run_async(self.query_docs())
        ).pack(side=tk.LEFT, padx=2)
        
        # Input area
        input_frame = ttk.LabelFrame(right_panel, text="Input")
        input_frame.pack(fill=tk.BOTH, expand=True)
        
        self.input_text = scrolledtext.ScrolledText(
            input_frame,
            height=10
        )
        self.input_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Output area
        output_frame = ttk.LabelFrame(right_panel, text="Output")
        output_frame.pack(fill=tk.BOTH, expand=True)
        
        self.output_text = scrolledtext.ScrolledText(
            output_frame,
            height=20
        )
        self.output_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Status bar
        self.status_var = tk.StringVar()
        status_bar = ttk.Label(
            self.root,
            textvariable=self.status_var,
            relief=tk.SUNKEN,
            anchor=tk.W
        )
        status_bar.pack(fill=tk.X, side=tk.BOTTOM, padx=5)
        
    def run_async(self, coro):
        """Run coroutine in asyncio event loop."""
        asyncio.run(coro)
        
    def load_local_docs(self):
        """Load documentation from local path."""
        if not LOCAL_DOCS_PATH.exists():
            self.status_var.set(f"Error: Documentation path not found: {LOCAL_DOCS_PATH}")
            return
            
        try:
            self.populate_tree("", LOCAL_DOCS_PATH)
            self.status_var.set(f"Loaded documentation from: {LOCAL_DOCS_PATH}")
        except Exception as e:
            self.status_var.set(f"Error loading documentation: {str(e)}")
            
    def populate_tree(self, parent: str, path: Path):
        """Recursively populate document tree."""
        try:
            for item in path.iterdir():
                if item.name.startswith('.'):
                    continue
                    
                item_id = self.doc_tree.insert(
                    parent,
                    'end',
                    text=item.name,
                    values=[str(item)]
                )
                
                if item.is_dir():
                    self.populate_tree(item_id, item)
                    
        except Exception as e:
            self.status_var.set(f"Error populating tree: {str(e)}")
            
    async def generate_draft(self):
        """Handle draft generation request."""
        try:
            selected_item = self.doc_tree.selection()[0]
            template_path = self.doc_tree.item(selected_item)['values'][0]
            
            result = await self.draft_agent.process_request(
                template=template_path,
                content=self.input_text.get("1.0", tk.END).strip()
            )
            
            self.output_text.delete("1.0", tk.END)
            self.output_text.insert("1.0", json.dumps(result, indent=2))
            self.status_var.set("Draft generated successfully")
            
        except IndexError:
            self.status_var.set("Please select a template document first")
        except Exception as e:
            self.status_var.set(f"Error generating draft: {str(e)}")
            
    async def review_content(self):
        """Handle content review request."""
        try:
            result = await self.review_agent.process_request(
                content=self.input_text.get("1.0", tk.END).strip()
            )
            
            self.output_text.delete("1.0", tk.END)
            self.output_text.insert("1.0", json.dumps(result, indent=2))
            self.status_var.set("Content reviewed successfully")
            
        except Exception as e:
            self.status_var.set(f"Error reviewing content: {str(e)}")
            
    async def query_docs(self):
        """Handle documentation query request."""
        try:
            result = await self.query_agent.process_request(
                query=self.input_text.get("1.0", tk.END).strip()
            )
            
            self.output_text.delete("1.0", tk.END)
            self.output_text.insert("1.0", json.dumps(result, indent=2))
            self.status_var.set("Query processed successfully")
            
        except Exception as e:
            self.status_var.set(f"Error processing query: {str(e)}")
            
    def run(self):
        """Start the simulator."""
        self.root.mainloop()

def main():
    """Main entry point with error handling."""
    try:
        simulator = StandaloneSimulator()
        simulator.run()
    except Exception as e:
        print(f"Error starting simulator: {str(e)}")
        input("Press Enter to exit...")

if __name__ == "__main__":
    main() 