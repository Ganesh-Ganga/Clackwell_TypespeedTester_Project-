"""Session auth, CSRF tokens and input validation.

Deliberately small and dependency-free so the flow is readable: a token is
minted per session, injected into every form and every fetch() header, and
compared with hmac.compare_digest on unsafe methods.
"""

import re
import secrets
from functools import wraps

from flask import session, redirect, url_for, flash, request, abort, g

from models import User

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[a-zA-Z]{2,}$")
USERNAME_RE = re.compile(r"^[a-zA-Z0-9_]{3,20}$")


# --- CSRF ------------------------------------------------------------------

def csrf_token():
    if "_csrf" not in session:
        session["_csrf"] = secrets.token_urlsafe(32)
    return session["_csrf"]


def verify_csrf():
    if request.method in ("GET", "HEAD", "OPTIONS"):
        return
    sent = request.headers.get("X-CSRF-Token") or request.form.get("csrf_token")
    if not sent or not secrets.compare_digest(sent, session.get("_csrf", "")):
        abort(400, description="Your session expired. Reload the page and try again.")


# --- Auth ------------------------------------------------------------------

def current_user():
    if "user" in g:
        return g.user
    uid = session.get("user_id")
    g.user = User.query.get(uid) if uid else None
    return g.user


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not current_user():
            flash("Sign in to open that page.", "warning")
            return redirect(url_for("auth.login", next=request.path))
        return view(*args, **kwargs)
    return wrapped


def login_user(user, remember=False):
    session.clear()
    session["user_id"] = user.id
    session.permanent = bool(remember)
    csrf_token()


def logout_user():
    session.clear()


# --- Validation ------------------------------------------------------------

def password_problems(password):
    issues = []
    if len(password) < 8:
        issues.append("at least 8 characters")
    if not re.search(r"[A-Za-z]", password):
        issues.append("a letter")
    if not re.search(r"\d", password):
        issues.append("a number")
    return issues


def validate_registration(form):
    """Returns (cleaned_dict, errors_dict)."""
    data = {k: (form.get(k) or "").strip() for k in ("name", "username", "email")}
    password = form.get("password") or ""
    confirm = form.get("confirm_password") or ""
    errors = {}

    if not data["name"]:
        errors["name"] = "Enter your full name."
    if not USERNAME_RE.match(data["username"]):
        errors["username"] = "3–20 characters, letters, numbers or underscores only."
    elif User.query.filter(User.username.ilike(data["username"])).first():
        errors["username"] = "That username is taken. Try another."

    if not EMAIL_RE.match(data["email"]):
        errors["email"] = "That doesn't look like an email address."
    elif User.query.filter(User.email.ilike(data["email"])).first():
        errors["email"] = "An account already uses this email."

    problems = password_problems(password)
    if problems:
        errors["password"] = "Password needs " + ", ".join(problems) + "."
    if password != confirm:
        errors["confirm_password"] = "Both passwords must match."

    data["password"] = password
    data["email"] = data["email"].lower()
    return data, errors
