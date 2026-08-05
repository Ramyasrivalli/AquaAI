"""
app.py — Production Flask Web Application Entry Point & Authentication Handler.
"""

from functools import wraps
from flask import (
    Flask,
    Response,
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for,
)

from config.settings import DEFAULT_HOST, DEFAULT_PORT, SECRET_KEY
from core.auth import (
    authenticate_user,
    register_user,
    reset_password_with_security_answer,
)
from core.database import (
    delete_prediction,
    get_prediction_by_id,
    get_predictions_df,
    get_summary_stats,
    get_user_predictions,
    init_db,
)
from core.helpers import (
    FEATURE_COLS,
    FEATURE_LABELS,
    FEATURE_UNITS,
    VALIDATION_RANGES,
    WHO_STANDARDS,
)
from core.prediction import (
    AnalysisResult,
    evaluate_parameters,
    get_model_meta,
    get_model_name,
    load_artifacts,
    run_inference,
)
from core.report import generate_pdf_report
from core.validation import validate_credentials

app = Flask(__name__)
app.secret_key = SECRET_KEY


def login_required(f):
    """Decorator to enforce Flask session authentication on protected routes."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in to access the system.", "warning")
            return redirect(url_for("login"))
        return f(*args, **kwargs)

    return decorated_function


@app.route("/")
def index():
    """Application root route."""
    if "user_id" in session:
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    """Handle user login and render authentication page."""
    if "user_id" in session:
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        is_valid, err_msg = validate_credentials(username, password)
        if not is_valid:
            flash(err_msg, "error")
            return render_template("login.html", active_tab="login")

        user, auth_msg = authenticate_user(username, password)
        if user:
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            flash(f"Welcome back, {user['username']}!", "success")
            return redirect(url_for("dashboard"))
        else:
            flash(auth_msg, "error")
            return render_template("login.html", active_tab="login")

    return render_template("login.html", active_tab="login")


@app.route("/register", methods=["POST"])
def register():
    """Handle new user account registration."""
    if "user_id" in session:
        return redirect(url_for("dashboard"))

    username = request.form.get("username", "").strip()
    password = request.form.get("password", "")
    confirm = request.form.get("confirm_password", "")
    sec_q = request.form.get("security_question", "What is your favorite color?")
    sec_a = request.form.get("security_answer", "blue").strip()

    if password != confirm:
        flash("Passwords do not match.", "error")
        return render_template("login.html", active_tab="register")

    ok, msg = register_user(username, password, sec_q, sec_a)
    if ok:
        flash(msg, "success")
        return render_template("login.html", active_tab="login")
    else:
        flash(msg, "error")
        return render_template("login.html", active_tab="register")


@app.route("/forgot_password", methods=["POST"])
def forgot_password():
    """Handle local password reset verification via security question."""
    if "user_id" in session:
        return redirect(url_for("dashboard"))

    username = request.form.get("username", "").strip()
    sec_a = request.form.get("security_answer", "").strip()
    new_pwd = request.form.get("new_password", "")

    if not username or not sec_a or not new_pwd:
        flash("All password reset fields are required.", "error")
        return render_template("login.html", active_tab="forgot")

    ok, msg = reset_password_with_security_answer(username, sec_a, new_pwd)
    if ok:
        flash(msg, "success")
        return render_template("login.html", active_tab="login")
    else:
        flash(msg, "error")
        return render_template("login.html", active_tab="forgot")


@app.route("/logout")
def logout():
    """Clear Flask session and log out user."""
    session.clear()
    flash("Logout successful! You have been logged out.", "info")
    return redirect(url_for("login"))


@app.route("/dashboard")
@login_required
def dashboard():
    """Render executive metrics, dynamic database charts, and recent activity log."""
    user_id = session["user_id"]
    stats = get_summary_stats(user_id=user_id)
    recent_history = get_user_predictions(user_id=user_id, limit=5)

    df_user = get_predictions_df(user_id=user_id)
    chart_dates = []
    chart_scores = []
    if not df_user.empty and "created_at" in df_user.columns:
        chart_dates = df_user["created_at"].astype(str).tolist()
        chart_scores = df_user["quality_score"].tolist()

    return render_template(
        "dashboard.html",
        active_page="dashboard",
        stats=stats,
        recent_history=recent_history,
        chart_dates=chart_dates,
        chart_scores=chart_scores,
    )


@app.route("/prediction", methods=["GET", "POST"])
@login_required
def prediction():
    """Render parameter input form and persist active prediction state across page navigation."""
    user_id = session["user_id"]
    result = None
    record_id = None
    form_values = None

    # Option to explicitly start a fresh analysis
    if request.args.get("new") == "1":
        session.pop("active_prediction", None)
        session.pop("active_form_values", None)
        session.pop("active_record_id", None)
        return redirect(url_for("prediction"))

    # Option to load a historical analysis record by ID
    load_id = request.args.get("load_id")
    if load_id and load_id.isdigit():
        rec = get_prediction_by_id(int(load_id))
        if rec:
            form_values = {
                "ph": rec["ph"],
                "Hardness": rec["hardness"],
                "Solids": rec["solids"],
                "Chloramines": rec["chloramines"],
                "Sulfate": rec["sulfate"],
                "Conductivity": rec["conductivity"],
                "Organic_carbon": rec["organic_carbon"],
                "Trihalomethanes": rec["trihalomethanes"],
                "Turbidity": rec["turbidity"],
            }
            evals, recs, uses = evaluate_parameters(form_values)
            res_obj = AnalysisResult(
                is_potable=bool(rec["result"] == 1),
                confidence=rec["confidence"],
                confidence_pct=round(rec["confidence"] * 100.0, 1),
                quality_score=rec["quality_score"],
                quality_status=rec["quality_status"],
                parameter_evaluations=evals,
                recommendations=recs,
                suitable_uses=uses,
                model_used=rec.get("model_used", "Support Vector Machine"),
            )
            session["active_prediction"] = res_obj.to_dict()
            session["active_form_values"] = form_values
            session["active_record_id"] = rec["id"]
            flash(f"Loaded historical Analysis Record #{rec['id']}.", "info")

    if request.method == "POST":
        form_values = {}
        for col in FEATURE_COLS:
            val_str = request.form.get(col, "")
            try:
                form_values[col] = float(val_str)
            except ValueError:
                form_values[col] = VALIDATION_RANGES[col]["default"]

        try:
            res_obj, record_id = run_inference(form_values, user_id=user_id, save_to_db=True)
            result = res_obj
            session["active_prediction"] = res_obj.to_dict()
            session["active_form_values"] = form_values
            session["active_record_id"] = record_id
            flash("Water quality inference completed successfully!", "success")
        except Exception as err:
            flash(f"Analysis failed: {err}", "error")

    elif "active_prediction" in session:
        try:
            result = AnalysisResult.from_dict(session["active_prediction"])
            form_values = session.get("active_form_values")
            record_id = session.get("active_record_id")
        except Exception:
            session.pop("active_prediction", None)

    return render_template(
        "prediction.html",
        active_page="prediction",
        form_values=form_values,
        result=result,
        record_id=record_id,
        ranges=VALIDATION_RANGES,
    )


@app.route("/history")
@login_required
def history():
    """Render searchable, filterable historical predictions audit table."""
    user_id = session["user_id"]
    search_query = request.args.get("q", "").strip()
    result_filter = request.args.get("result", "").strip()
    sort_order = request.args.get("sort", "newest").strip()

    records = get_user_predictions(user_id=user_id, limit=500)

    # Search & Filter
    filtered = []
    for r in records:
        if result_filter == "1" and r["result"] != 1:
            continue
        if result_filter == "0" and r["result"] != 0:
            continue

        if search_query:
            q_low = search_query.lower()
            date_str = str(r["created_at"]).lower()
            status_str = str(r["quality_status"]).lower()
            id_str = str(r["id"])
            if q_low not in date_str and q_low not in status_str and q_low not in id_str:
                continue

        filtered.append(r)

    # Sorting
    if sort_order == "oldest":
        filtered.sort(key=lambda x: x["created_at"])
    elif sort_order == "score_desc":
        filtered.sort(key=lambda x: x["quality_score"], reverse=True)
    elif sort_order == "score_asc":
        filtered.sort(key=lambda x: x["quality_score"])
    else:
        filtered.sort(key=lambda x: x["created_at"], reverse=True)

    return render_template(
        "history.html",
        active_page="history",
        history_records=filtered,
        search_query=search_query,
        result_filter=result_filter,
        sort_order=sort_order,
    )


@app.route("/history/export")
@login_required
def export_history():
    """Export historical prediction log as downloadable CSV file."""
    user_id = session["user_id"]
    df = get_predictions_df(user_id=user_id)
    csv_data = df.to_csv(index=False)
    filename = f"water_history_{session.get('username', 'user')}.csv"
    return Response(
        csv_data,
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment;filename={filename}"},
    )


@app.route("/history/delete/<int:prediction_id>", methods=["POST"])
@login_required
def delete_history_record(prediction_id):
    """Safely delete a prediction record by primary key."""
    user_id = session["user_id"]
    if delete_prediction(prediction_id, user_id):
        if session.get("active_record_id") == prediction_id:
            session.pop("active_prediction", None)
            session.pop("active_form_values", None)
            session.pop("active_record_id", None)
        flash(f"Record #{prediction_id} deleted successfully.", "success")
    else:
        flash("Failed to delete record.", "error")
    return redirect(url_for("history"))


@app.route("/analytics")
@login_required
def analytics():
    """Render dynamic statistical charts generated from database history."""
    user_id = session["user_id"]
    df = get_predictions_df(user_id=user_id)

    chart_dates = []
    scores = []
    ph_values = []
    solids_values = []
    potable_count = 0
    non_potable_count = 0
    stats_table = []

    if not df.empty:
        chart_dates = df["created_at"].astype(str).tolist()
        scores = df["quality_score"].tolist()
        ph_values = df["ph"].tolist()
        solids_values = df["solids"].tolist()

        potable_count = int((df["result"] == 1).sum())
        non_potable_count = int((df["result"] == 0).sum())

        num_cols = ["ph", "hardness", "solids", "chloramines", "sulfate", "conductivity", "organic_carbon", "trihalomethanes", "turbidity", "quality_score"]
        desc = df[num_cols].describe().T.reset_index()
        for _, row in desc.iterrows():
            stats_table.append({
                "parameter": row["index"],
                "mean": row["mean"],
                "std": row["std"],
                "min": row["min"],
                "25%": row["25%"],
                "50%": row["50%"],
                "75%": row["75%"],
                "max": row["max"],
            })

    return render_template(
        "analytics.html",
        active_page="analytics",
        chart_dates=chart_dates,
        scores=scores,
        ph_values=ph_values,
        solids_values=solids_values,
        potable_count=potable_count,
        non_potable_count=non_potable_count,
        stats_table=stats_table,
    )


@app.route("/about")
@login_required
def about():
    """Render system metadata, model benchmark specs, and WHO guidelines reference."""
    model_name = get_model_name()
    meta = get_model_meta()
    meta_metrics = meta.get("metrics", {})

    return render_template(
        "about.html",
        active_page="about",
        model_name=model_name,
        meta_metrics=meta_metrics,
        who_standards=WHO_STANDARDS,
        feature_labels=FEATURE_LABELS,
    )


@app.route("/report/<int:prediction_id>")
@login_required
def get_report(prediction_id):
    """Generate and return complete ReportLab PDF laboratory report file attachment matching prediction page."""
    rec = get_prediction_by_id(prediction_id)
    if not rec:
        flash("Prediction record not found.", "error")
        return redirect(url_for("history"))

    feature_dict = {
        "ph": rec["ph"],
        "Hardness": rec["hardness"],
        "Solids": rec["solids"],
        "Chloramines": rec["chloramines"],
        "Sulfate": rec["sulfate"],
        "Conductivity": rec["conductivity"],
        "Organic_carbon": rec["organic_carbon"],
        "Trihalomethanes": rec["trihalomethanes"],
        "Turbidity": rec["turbidity"],
    }

    evals, recs, uses = evaluate_parameters(feature_dict)

    pdf_bytes = generate_pdf_report(
        username=session.get("username", "User"),
        feature_dict=feature_dict,
        is_potable=bool(rec["result"] == 1),
        confidence_pct=round(rec["confidence"] * 100.0, 1),
        quality_score=rec["quality_score"],
        quality_status=rec["quality_status"],
        parameter_evals=evals,
        recommendations=recs,
        suitable_uses=uses,
        model_name=rec.get("model_used", "Support Vector Machine"),
    )

    filename = f"water_report_record_{prediction_id}.pdf"
    return Response(
        pdf_bytes,
        mimetype="application/pdf",
        headers={"Content-Disposition": f"attachment;filename={filename}"},
    )


if __name__ == "__main__":
    init_db()
    load_artifacts()
    print(f"[INFO] Starting Flask Server on http://localhost:{DEFAULT_PORT}...")
    app.run(host=DEFAULT_HOST, port=DEFAULT_PORT, debug=True)
