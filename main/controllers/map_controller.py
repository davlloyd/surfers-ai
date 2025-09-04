from flask import Blueprint, render_template, current_app

# Main blueprint for the home page (no prefix)
map_bp = Blueprint('map_bp', __name__,
                  template_folder='../templates',
                  static_folder='../static')

# API blueprint for map-related endpoints
map_api_bp = Blueprint('map_api_bp', __name__, url_prefix='/api')

@map_bp.route('/')
def home():
    """Main home page route - shows the map interface."""
    try:
        # Render the map template which is the home screen
        return render_template('map.html')
    except Exception as render_exc:
        current_app.logger.error(f"Map template rendering error: {render_exc}")
        return "Welcome to Surfers AI - Your intelligent surf and weather assistant", 200

# Export aliases for app.py import
map_controller = map_bp
map_api_controller = map_api_bp
