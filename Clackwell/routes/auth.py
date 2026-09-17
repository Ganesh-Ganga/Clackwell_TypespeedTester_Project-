from flask import Blueprint, render_template, request, redirect, url_for, flash, session

from models import db, User
from utils.security import (
    validate_registration, login_user, logout_user, current_user, login_required,
    password_problems,
)

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user():
        return redirect(url_for("main.dashboard"))

    errors, data = {}, {}
    if request.method == "POST":
        data, errors = validate_registration(request.form)
        if not errors:
            user = User(
                name=data["name"],
                username=data["username"],
                email=data["email"],
                avatar=data["name"][0].upper(),
            )
            user.set_password(data["password"])
            db.session.add(user)
            db.session.commit()
            login_user(user, remember=True)
            session["just_registered"] = True
            return redirect(url_for("main.dashboard"))

    return render_template("register.html", errors=errors, data=data)


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user():
        return redirect(url_for("main.dashboard"))

    error = None
    identifier = ""
    if request.method == "POST":
        identifier = (request.form.get("identifier") or "").strip()
        password = request.form.get("password") or ""
        remember = bool(request.form.get("remember"))

        user = User.query.filter(
            (User.username.ilike(identifier)) | (User.email.ilike(identifier))
        ).first()

        # One message for both cases so the form can't be used to discover accounts.
        if user and user.check_password(password):
            login_user(user, remember=remember)
            nxt = request.args.get("next")
            if nxt and nxt.startswith("/"):
                return redirect(nxt)
            return redirect(url_for("main.dashboard"))
        error = "That username and password don't match an account."

    return render_template("login.html", error=error, identifier=identifier)


@auth_bp.route("/logout", methods=["POST"])
@login_required
def logout():
    logout_user()
    flash("Signed out. Your progress is saved.", "success")
    return redirect(url_for("main.index"))


@auth_bp.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    """Local-first reset: verify the email, then set a new password.

    A production build would email a signed, expiring link instead — the hook
    point is the same place this form posts to.
    """
    stage = "identify"
    error = None
    email = (request.form.get("email") or "").strip().lower()

    if request.method == "POST":
        user = User.query.filter(User.email.ilike(email)).first()
        new_password = request.form.get("password")

        if not new_password:
            if not user:
                error = "No account uses that email."
            else:
                stage = "reset"
        else:
            problems = password_problems(new_password)
            if not user:
                error = "No account uses that email."
            elif problems:
                stage = "reset"
                error = "Password needs " + ", ".join(problems) + "."
            elif new_password != request.form.get("confirm_password"):
                stage = "reset"
                error = "Both passwords must match."
            else:
                user.set_password(new_password)
                db.session.commit()
                flash("Password updated. Sign in with the new one.", "success")
                return redirect(url_for("auth.login"))

    return render_template("forgot_password.html", stage=stage, error=error, email=email)
