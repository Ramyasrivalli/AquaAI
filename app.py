"""
app.py — Production Flask Application Entry Point & Route Handlers.
"""

from functools import wraps
from io import StringIO
import pandas as pd
from flask import (
    Flask,
    Response,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    session,
    url_for,
)

from config.settings import DEFAULT_HOST, DEFAULT_PORT, SECRET_KEY
from core.auth import (
    authenticate_user,
    get_user_security_question,
    register_user,
    update_user_password,
    verify_security_answer,
)
from core.database import (
    delete_prediction,
    get_analytics_summary,
    get_prediction_by_id,
    get_predictions_df,
    get_summary_stats,
    get_user_predictions,
    init_db,
)
from core.helpers import (
    FEATURE_COLS,
    VALIDATION_RANGES,
    record_to_feature_dict,
)
from core.prediction import (
    AnalysisResult,
    evaluate_parameters,
    load_artifacts,
    run_inference,
)
from core.report import generate_pdf_report
from core.validation import parse_form_features, validate_credentials, validate_gmail

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
        return redirect(url_for("analysis"))
    return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    """Handle user login and render authentication page."""
    if "user_id" in session:
        return redirect(url_for("analysis"))

    if request.method == "POST":
        email = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        is_valid, err_msg = validate_credentials(email, password)
        if not is_valid:
            flash(err_msg, "error")
            return render_template("login.html", active_tab="login", form_email=email)

        user, auth_msg = authenticate_user(email, password)
        if user:
            session["user_id"] = user["id"]
            session["username"] = user["email"]
            flash(f"Welcome back, {user['email']}!", "success")
            return redirect(url_for("analysis"))
        else:
            flash(auth_msg, "error")
            return render_template("login.html", active_tab="login", form_email=email)

    return render_template("login.html", active_tab="login")


@app.route("/register", methods=["POST"])
def register():
    """Handle new user account registration with strict Gmail validation."""
    if "user_id" in session:
        return redirect(url_for("analysis"))

    email = request.form.get("username", "").strip()
    password = request.form.get("password", "")
    confirm = request.form.get("confirm_password", "")
    sec_q = request.form.get("security_question", "What is your favorite color?")
    sec_a = request.form.get("security_answer", "blue").strip()

    if password != confirm:
        flash("Passwords do not match.", "error")
        return render_template("login.html", active_tab="register")

    ok, msg = register_user(email, password, sec_q, sec_a)
    if ok:
        flash("Account registered successfully.", "success")
        return render_template("login.html", active_tab="register", show_registration_modal=True)
    else:
        flash(msg, "error")
        return render_template("login.html", active_tab="register")


# ==============================================================================
# Security Question Password Reset Routes
# ==============================================================================

@app.route("/reset/init", methods=["POST"])
def reset_init():
    """Step 1: Check Gmail account existence and retrieve Security Question."""
    email = request.form.get("email", "").strip()
    ok, result = get_user_security_question(email)

    if ok:
        session["reset_email"] = email.lower()
        session["reset_attempts"] = 0
        session["reset_verified"] = False
        return jsonify({"success": True, "question": result})
    else:
        return jsonify({"success": False, "message": result})


@app.route("/reset/verify", methods=["POST"])
def reset_verify():
    """Step 2: Verify Security Answer against stored hash with 5-attempt limit."""
    email = session.get("reset_email")
    if not email:
        return jsonify({"success": False, "message": "Reset session expired. Please restart password reset."})

    attempts = session.get("reset_attempts", 0) + 1
    session["reset_attempts"] = attempts

    if attempts > 5:
        session.pop("reset_email", None)
        session.pop("reset_attempts", None)
        session.pop("reset_verified", None)
        return jsonify({
            "success": False,
            "message": "Too many failed attempts. Please restart the password reset process.",
            "restart": True
        })

    security_answer = request.form.get("security_answer", "").strip()
    ok, msg = verify_security_answer(email, security_answer)

    if ok:
        session["reset_verified"] = True
        return jsonify({"success": True, "message": msg})
    else:
        remaining = 5 - attempts
        return jsonify({"success": False, "message": f"{msg} ({remaining} attempt(s) remaining)"})


@app.route("/reset/confirm", methods=["POST"])
def reset_confirm():
    """Step 3: Update password after server-side security answer verification."""
    email = session.get("reset_email")
    verified = session.get("reset_verified")

    if not email or not verified:
        return jsonify({"success": False, "message": "Unauthorized reset attempt. Please verify your security answer first."})

    new_pwd = request.form.get("new_password", "")
    confirm_pwd = request.form.get("confirm_password", "")

    if not new_pwd or len(new_pwd) < 4:
        return jsonify({"success": False, "message": "New password must be at least 4 characters long."})

    if new_pwd != confirm_pwd:
        return jsonify({"success": False, "message": "New password and confirm password do not match."})

    ok, msg = update_user_password(email, new_pwd)

    if ok:
        session.pop("reset_email", None)
        session.pop("reset_attempts", None)
        session.pop("reset_verified", None)
        return jsonify({"success": True, "message": msg})
    else:
        return jsonify({"success": False, "message": msg})


@app.route("/logout")
def logout():
    """Clear Flask session and log out user."""
    session.clear()
    flash("Logout successful! You have been logged out.", "info")
    return redirect(url_for("login"))


@app.route("/analysis", methods=["GET", "POST"])
@login_required
def analysis():
    """Primary Water Quality Analysis Workspace."""
    user_id = session["user_id"]
    result = None
    record_id = None
    form_values = None

    if request.args.get("new") == "1":
        session.pop("active_prediction", None)
        session.pop("active_form_values", None)
        session.pop("active_record_id", None)
        return redirect(url_for("analysis"))

    load_id = request.args.get("load_id")
    if load_id and load_id.isdigit():
        rec = get_prediction_by_id(int(load_id))
        if rec:
            form_values = record_to_feature_dict(rec)
            res_obj, _ = run_inference(form_values, user_id=user_id, save_to_db=False)
            session["active_prediction"] = res_obj.to_dict()
            session["active_form_values"] = form_values
            session["active_record_id"] = rec["id"]
            flash(f"Loaded historical Analysis Record #{rec['id']}.", "info")

    if request.method == "POST":
        form_values = parse_form_features(request.form)
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
        "analysis.html",
        active_page="analysis",
        form_values=form_values,
        result=result,
        record_id=record_id,
        ranges=VALIDATION_RANGES,
    )


@app.route("/prediction", methods=["GET", "POST"])
@login_required
def prediction_alias():
    """Alias route forwarding to primary analysis route."""
    return redirect(url_for("analysis"))


@app.route("/simulator")
@login_required
def simulator():
    """Render What-If Parameter Simulator Workspace."""
    return render_template("simulator.html", active_page="simulator")


@app.route("/simulate_api", methods=["POST"])
@login_required
def simulate_api():
    """API Endpoint for real-time What-If parameter recalculation."""
    data = request.get_json() or {}
    clean_features = parse_form_features(data)
    res_obj, _ = run_inference(clean_features, user_id=None, save_to_db=False)
    return jsonify(res_obj.to_dict())


@app.route("/compare", methods=["GET", "POST"])
@login_required
def compare():
    """Compare two water quality samples side-by-side."""
    result_a = None
    result_b = None
    form_a = None
    form_b = None

    if request.method == "POST":
        dict_a = {col: request.form.get(f"a_{col}", "") for col in FEATURE_COLS}
        form_a = parse_form_features(dict_a)
        result_a, _ = run_inference(form_a, user_id=None, save_to_db=False)

        dict_b = {col: request.form.get(f"b_{col}", "") for col in FEATURE_COLS}
        form_b = parse_form_features(dict_b)
        result_b, _ = run_inference(form_b, user_id=None, save_to_db=False)

    return render_template(
        "compare.html",
        active_page="compare",
        result_a=result_a,
        result_b=result_b,
        form_a=form_a,
        form_b=form_b,
    )


@app.route("/batch", methods=["GET", "POST"])
@login_required
def batch():
    """Batch CSV Upload & Processing."""
    batch_records = []
    batch_summary = None

    if request.method == "POST":
        if "csv_file" not in request.files:
            flash("No CSV file selected.", "error")
            return redirect(url_for("batch"))

        file = request.files["csv_file"]
        if not file or not file.filename.endswith(".csv"):
            flash("Invalid file format. Please upload a valid CSV file.", "error")
            return redirect(url_for("batch"))

        try:
            df = pd.read_csv(file)
            req_cols = [c.lower() for c in FEATURE_COLS]
            df_cols_lower = [str(c).lower() for c in df.columns]

            missing = [col for col in FEATURE_COLS if col.lower() not in df_cols_lower]
            if missing:
                flash(f"Missing required columns in CSV: {', '.join(missing)}", "error")
                return redirect(url_for("batch"))

            col_mapping = {c: c for c in df.columns}
            for col in df.columns:
                for req in FEATURE_COLS:
                    if col.lower() == req.lower():
                        col_mapping[col] = req
            df = df.rename(columns=col_mapping)

            processed_rows = []
            safe_cnt = 0
            unsafe_cnt = 0
            scores = []

            for _, row in df.iterrows():
                row_dict = {col: row.get(col, 0.0) for col in FEATURE_COLS}
                clean_features = parse_form_features(row_dict)
                res_obj, _ = run_inference(clean_features, user_id=None, save_to_db=False)

                rec = clean_features.copy()
                rec["predicted_potability"] = 1 if res_obj.is_potable else 0
                rec["quality_score"] = res_obj.quality_score
                rec["quality_status"] = res_obj.quality_status
                rec["confidence_pct"] = res_obj.confidence_pct
                processed_rows.append(rec)

                if res_obj.is_potable:
                    safe_cnt += 1
                else:
                    unsafe_cnt += 1
                scores.append(res_obj.quality_score)

            batch_records = processed_rows
            session["batch_processed_df"] = processed_rows

            avg_score = round(sum(scores) / len(scores), 1) if scores else 0.0
            batch_summary = {
                "total_rows": len(processed_rows),
                "safe_count": safe_cnt,
                "unsafe_count": unsafe_cnt,
                "avg_score": avg_score,
            }
            flash(f"Processed {len(processed_rows)} rows from CSV successfully!", "success")
        except Exception as err:
            flash(f"Failed to process CSV file: {err}", "error")

    return render_template(
        "batch.html",
        active_page="batch",
        batch_records=batch_records,
        batch_summary=batch_summary,
    )


@app.route("/batch/export")
@login_required
def batch_export():
    """Export processed batch predictions CSV."""
    records = session.get("batch_processed_df", [])
    if not records:
        flash("No processed batch dataset available for download.", "warning")
        return redirect(url_for("batch"))

    df = pd.DataFrame(records)
    csv_data = df.to_csv(index=False)
    return Response(
        csv_data,
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment;filename=aquaai_batch_predictions.csv"},
    )


@app.route("/history")
@login_required
def history():
    """Render historical predictions audit table isolated per logged-in user."""
    user_id = session["user_id"]
    search_query = request.args.get("q", "").strip()
    result_filter = request.args.get("result", "").strip()
    sort_order = request.args.get("sort", "newest").strip()

    records = get_user_predictions(user_id=user_id, limit=500)

    filtered = []
    for r in records:
        if result_filter == "1" and r["result"] != 1:
            continue
        if result_filter == "0" and r["result"] != 0:
            continue

        if search_query:
            q_low = search_query.lower()
            if q_low not in str(r["created_at"]).lower() and q_low not in str(r["quality_status"]).lower() and q_low not in str(r["id"]):
                continue

        filtered.append(r)

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
    """Export user historical prediction log as CSV."""
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
    analytics_data = get_analytics_summary(session["user_id"])
    stats_summary = get_summary_stats(session["user_id"])
    analytics_data.update(stats_summary)
    return render_template(
        "analytics.html",
        active_page="analytics",
        **analytics_data,
    )


@app.route("/report/<int:prediction_id>")
@login_required
def get_report(prediction_id):
    """Generate and return complete ReportLab PDF laboratory report."""
    rec = get_prediction_by_id(prediction_id)
    if not rec:
        flash("Prediction record not found.", "error")
        return redirect(url_for("history"))

    feature_dict = record_to_feature_dict(rec)
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
    print(f"[INFO] Starting AquaAI Flask Server on http://localhost:{DEFAULT_PORT}...")
    app.run(host=DEFAULT_HOST, port=DEFAULT_PORT, debug=False)
