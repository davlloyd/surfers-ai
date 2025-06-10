from flask import Blueprint, render_template, current_app

map_bp = Blueprint('map_bp', __name__,
                  template_folder='../templates',
                  static_folder='../static')

@map_bp.route('/')
def show_map():
    try:
        return render_template('map.html')
    except Exception as render_exc:
        current_app.logger.error(f"Template rendering error: {render_exc}")
        return "An error occurred loading the map page.", 500
