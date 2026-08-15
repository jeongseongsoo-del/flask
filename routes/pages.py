from flask import Blueprint, render_template


pages_bp = Blueprint('pages', __name__)


@pages_bp.route('/')
def index():
    return render_template('pages/dashboard/index.html')


@pages_bp.route('/index.html')
def serve_index():
    return render_template('pages/dashboard/index.html')


@pages_bp.route('/ctx-single-collection.html')
def serve_page():
    return render_template('pages/ctx/single-collection.html')


@pages_bp.route('/channel-configs.html')
def serve_channel_configs_page():
    return render_template('pages/channel-configs/index.html')
