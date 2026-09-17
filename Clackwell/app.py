"""Clackwell — a typing range.

Run locally with:  python app.py
"""

import os
from datetime import datetime

from flask import Flask, render_template, request, jsonify

from config import Config, BASE_DIR
from models import db, RANKS
from utils.security import csrf_token, verify_csrf, current_user
from utils.badges import seed_badges
from utils.levels import LEVELS, MAX_LEVEL


def create_app(config_object=Config):
    app = Flask(__name__)
    app.config.from_object(config_object)

    os.makedirs(os.path.join(BASE_DIR, "database"), exist_ok=True)
    db.init_app(app)

    from routes.auth import auth_bp
    from routes.main import main_bp
    from routes.api import api_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(api_bp)

    @app.before_request
    def guard():
        if request.endpoint != "static":
            verify_csrf()

    @app.context_processor
    def inject_globals():
        return {
            "csrf_token": csrf_token,
            "user": current_user(),
            "LEVELS": LEVELS,
            "MAX_LEVEL": MAX_LEVEL,
            "RANKS": RANKS,
            "now": datetime.utcnow(),
        }

    @app.errorhandler(400)
    def bad_request(err):
        return render_template("error.html", code=400,
                               headline="That request didn't go through",
                               detail=getattr(err, "description", "")), 400

    @app.errorhandler(403)
    def forbidden(err):
        return render_template("error.html", code=403,
                               headline="That isn't yours to open",
                               detail="Your analytics and results are visible only to you."), 403

    @app.errorhandler(404)
    def not_found(err):
        return render_template("error.html", code=404,
                               headline="Nothing lives at this address",
                               detail="Check the link, or head back to the dashboard."), 404

    @app.errorhandler(500)
    def server_error(err):
        db.session.rollback()
        return render_template("error.html", code=500,
                               headline="Something broke on our side",
                               detail="The run wasn't saved. Try that again."), 500

    with app.app_context():
        db.create_all()
        seed_badges()

    return app


app = create_app()


if __name__ == "__main__":
    app.run(debug=True, port=5000)
