import os
import sys

script_dir = os.path.dirname(os.path.abspath(__file__))
# Fix name shadowing: Python automatically adds the script's directory to sys.path.
# Because this file is named app.py and is inside a folder named app/, Python 
# thinks the script itself is the 'app' module, causing imports to fail. 
if script_dir in sys.path:
    sys.path.remove(script_dir)

# Ensure the root directory is in sys.path
BASE_DIR = os.path.dirname(script_dir)
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from dash import Dash, html
from app.components.layout import create_filters, create_panels

# Initialize the Dash app
app = Dash(__name__)
app.title = "GitHub Repository Health Analytics"

# Set app.layout using functions from layout.py
app.layout = html.Div([
    create_filters(),
    create_panels()
], style={
    'backgroundColor': '#f1f5f9', 
    'height': '100vh', 
    'padding': '10px', 
    'margin': '-8px', # Negates default body margin
    'boxSizing': 'border-box',
    'overflow': 'hidden',
    'fontFamily': 'system-ui, -apple-system, sans-serif'
})

# Register callbacks
from app.callbacks import (
    streamgraph_cb,
    network_cb,
    sankey_cb,
    heatmap_cb,
    bot_bar_cb,
    dashboard_cb,
    modal_cb
)

streamgraph_cb.register(app)
network_cb.register(app)
sankey_cb.register(app)
heatmap_cb.register(app)
bot_bar_cb.register(app)
dashboard_cb.register(app)
modal_cb.register(app)

if __name__ == '__main__':
    app.run(debug=True)