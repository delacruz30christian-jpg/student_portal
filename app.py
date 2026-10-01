import os


from datetime import date


from flask import Flask, render_template, request, redirect, url_for, flash, session


from supabase import create_client


from dotenv import load_dotenv


# ==========================================


# LOAD ENVIRONMENT VARIABLES


# ==========================================


load_dotenv()


SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")


supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
supabase_admin = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)


# ==========================================


# FLASK APP


# ==========================================


app = Flask(__name__)


app.secret_key = os.getenv("FLASK_SECRET_KEY")


# ==========================================


# HOME


# ==========================================


@app.route("/")
def home():

    if "user_id" in session:
        if session.get("role") == "teacher":
            return redirect(url_for("teacher_dashboard"))

        return redirect(url_for("student_dashboard"))

    return redirect(url_for("login"))


# ==========================================


# REGISTER


# ==========================================


@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":
        student_number = request.form.get("student_number")

        full_name = request.form.get("full_name")

        email = request.form.get("email")

        password = request.form.get("password")

        birthdate = request.form.get("birthdate")

        gender = request.form.get("gender")

        course = request.form.get("course")

        year_level = request.form.get("year_level")

        section = request.form.get("section")

        address = request.form.get("address")

        try:
            # Create account in Supabase Authentication

            auth_response = supabase.auth.sign_up(
                {"email": email, "password": password}
            )

            user = auth_response.user

            if not user:
                flash("Registration failed. Please try again.", "error")

                return redirect(url_for("register"))

            # Save student information

            supabase.table("students").insert(
                {
                    "user_id": user.id,
                    "student_number": student_number,
                    "full_name": full_name,
                    "email": email,
                    "birthdate": birthdate,
                    "gender": gender,
                    "course": course,
                    "year_level": year_level,
                    "section": section,
                    "address": address,
                }
            ).execute()

            flash("Registration successful! You can now login.", "success")

            return redirect(url_for("login"))

        except Exception as e:
            print("Registration error:", e)

            flash("Registration failed. Please check your information.", "error")

    return render_template("register.html")


@app.route("/teacher/register", methods=["GET", "POST"])
def teacher_register():

    if request.method == "POST":
        full_name = request.form.get("full_name", "").strip()

        email = request.form.get("email", "").strip().lower()

        password = request.form.get("password", "")

        confirm_password = request.form.get("confirm_password", "")

        # Check required fields

        if not full_name or not email or not password or not confirm_password:
            flash("Please complete all fields.", "error")

            return render_template("teacher_register.html")

        # Check password match

        if password != confirm_password:
            flash("Passwords do not match.", "error")

            return render_template("teacher_register.html")

        # Basic password length check

        if len(password) < 6:
            flash("Password must be at least 6 characters.", "error")

            return render_template("teacher_register.html")

        try:
            # Create Supabase Auth account

            auth_response = supabase.auth.sign_up(
                {"email": email, "password": password}
            )

            user = auth_response.user

            if not user:
                flash("Unable to create teacher account.", "error")

                return render_template("teacher_register.html")

            # Check if teacher record already exists

            existing_teacher = (
                supabase.table("teachers").select("*").eq("email", email).execute()
            )

            if existing_teacher.data:
                flash("A teacher account with this email already exists.", "error")

                return render_template("teacher_register.html")

            # Save teacher information

            supabase.table("teachers").insert(
                {"user_id": user.id, "full_name": full_name, "email": email}
            ).execute()

            flash("Teacher account created successfully!", "success")

            return redirect(url_for("login"))

        except Exception as e:
            print("Teacher registration error:", e)

            flash(
                "Unable to create teacher account. "
                "The email may already be registered.",
                "error",
            )

            return render_template("teacher_register.html")

    return render_template("teacher_register.html")


# ==========================================
# ADMIN LOGIN
# ==========================================


@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        if not email or not password:
            flash("Please enter your email and password.", "error")
            return render_template("admin_login.html")

        try:
            # Login using Supabase Authentication
            auth_response = supabase.auth.sign_in_with_password(
                {"email": email, "password": password}
            )

            user = auth_response.user

            if not user:
                flash("Invalid email or password.", "error")
                return render_template("admin_login.html")

            user_id = str(user.id)

            # Check if this account is an admin
            admin_response = (
                supabase.table("admins").select("*").eq("user_id", user_id).execute()
            )

            if not admin_response.data:
                # Sign out if the account is not an admin
                supabase.auth.sign_out()

                flash("This account is not authorized as an admin.", "error")
                return render_template("admin_login.html")

            admin = admin_response.data[0]

            # Save admin session
            session.clear()
            session["user_id"] = user_id
            session["email"] = user.email
            session["role"] = "admin"
            session["admin_id"] = admin["id"]

            return redirect(url_for("admin_dashboard"))

        except Exception as e:
            print("Admin login error:", e)

            flash("Invalid email or password.", "error")

            return render_template("admin_login.html")

    return render_template("admin_login.html")


# ==========================================
# ADMIN DASHBOARD
# ==========================================


@app.route("/admin/dashboard")
def admin_dashboard():

    if "user_id" not in session:
        return redirect(url_for("admin_login"))

    if session.get("role") != "admin":
        return redirect(url_for("login"))

    try:
        # COUNT STUDENTS
        students_response = supabase.table("students").select("id").execute()

        student_count = len(students_response.data or [])

        # COUNT INSTRUCTORS
        instructors_response = supabase.table("teachers").select("id").execute()

        instructor_count = len(instructors_response.data or [])

        # COUNT SUBJECTS
        subjects_response = supabase.table("subjects").select("id").execute()

        subject_count = len(subjects_response.data or [])

        return render_template(
            "admin_dashboard.html",
            admin_name=session.get("email"),
            student_count=student_count,
            instructor_count=instructor_count,
            subject_count=subject_count,
        )

    except Exception as e:
        print("Admin dashboard error:", e)

        flash("Unable to load dashboard statistics.", "error")

        return render_template(
            "admin_dashboard.html",
            admin_name=session.get("email"),
            student_count=0,
            instructor_count=0,
            subject_count=0,
        )


# ==========================================


# LOGIN


# ==========================================


@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":
        email = request.form.get("email")

        password = request.form.get("password")

        try:
            # Login using Supabase Authentication

            auth_response = supabase.auth.sign_in_with_password(
                {"email": email, "password": password}
            )

            user = auth_response.user

            if not user:
                flash("Invalid email or password.", "error")

                return redirect(url_for("login"))

            user_id = str(user.id)

            # Save session

            session["user_id"] = user_id

            session["email"] = user.email

            # ==========================================

            # CHECK IF TEACHER

            # ==========================================

            teacher_response = (
                supabase.table("teachers").select("*").eq("user_id", user_id).execute()
            )

            if teacher_response.data:
                session["role"] = "teacher"

                return redirect(url_for("teacher_dashboard"))

            # ==========================================

            # OTHERWISE STUDENT

            # ==========================================

            session["role"] = "student"

            return redirect(url_for("student_dashboard"))

        except Exception as e:
            print("Login error:", e)

            flash("Invalid email or password.", "error")

    return render_template("login.html")


# ==========================================

# ==========================================
# STUDENT DASHBOARD
# ==========================================


@app.route("/student/dashboard")
def student_dashboard():

    if "user_id" not in session:
        return redirect(url_for("login"))

    if session.get("role") == "teacher":
        return redirect(url_for("teacher_dashboard"))

    user_id = session["user_id"]

    try:
        student_response = (
            supabase.table("students")
            .select("*")
            .eq("user_id", user_id)
            .single()
            .execute()
        )

        student = student_response.data

        if not student:
            flash("Student information not found.", "error")
            return redirect(url_for("login"))

        birthdate = student.get("birthdate")

        if birthdate:
            if isinstance(birthdate, str):
                birth_year, birth_month, birth_day = map(int, birthdate.split("-"))
            else:
                birth_year = birthdate.year
                birth_month = birthdate.month
                birth_day = birthdate.day

            today = date.today()
            age = today.year - birth_year

            if (today.month, today.day) < (birth_month, birth_day):
                age -= 1
        else:
            age = None

        student["age"] = age
        student_id = student["id"]

        enrollments_response = (
            supabase.table("enrollments")
            .select("*")
            .eq("student_id", student_id)
            .execute()
        )

        enrollments = enrollments_response.data or []

        subjects_response = supabase.table("subjects").select("*").execute()

        subjects = {
            subject["id"]: subject for subject in (subjects_response.data or [])
        }

        teachers_response = supabase.table("teachers").select("*").execute()

        teachers = {
            teacher["id"]: teacher for teacher in (teachers_response.data or [])
        }

        grades_response = (
            supabase.table("grades").select("*").eq("student_id", student_id).execute()
        )

        grades = {grade["subject_id"]: grade for grade in (grades_response.data or [])}

        enrolled_subjects = []

        for enrollment in enrollments:
            subject_id = enrollment["subject_id"]
            subject = subjects.get(subject_id)

            if not subject:
                continue

            teacher = teachers.get(subject.get("teacher_id"))
            grade = grades.get(subject_id)

            enrolled_subjects.append(
                {
                    "id": subject["id"],
                    "subject_code": subject.get("subject_code"),
                    "subject_name": subject.get("subject_name"),
                    "section": (enrollment.get("section") or subject.get("section")),
                    "teacher_name": (teacher.get("full_name") if teacher else "-"),
                    "prelim": (grade.get("prelim") if grade else None),
                    "midterm": (grade.get("midterm") if grade else None),
                    "finals": (grade.get("finals") if grade else None),
                    "average": (grade.get("average") if grade else None),
                }
            )

        enrolled_subjects.sort(key=lambda x: x["subject_code"] or "")

        return render_template(
            "student_dashboard.html",
            student=student,
            age=age,
            enrolled_subjects=enrolled_subjects,
        )

    except Exception as e:
        print("Student dashboard error:", e)

        flash("Unable to load student information.", "error")

        return redirect(url_for("login"))


# STUDENT SUBJECTS

# ==========================================


@app.route("/student/subjects", methods=["GET", "POST"])
def student_subjects():

    if "user_id" not in session:
        return redirect(url_for("login"))

    if session.get("role") != "student":
        return redirect(url_for("teacher_dashboard"))

    user_id = session["user_id"]

    try:
        # ==========================================

        # GET CURRENT STUDENT

        # ==========================================

        student_response = (
            supabase.table("students")
            .select("*")
            .eq("user_id", user_id)
            .single()
            .execute()
        )

        student = student_response.data

        if not student:
            flash("Student information not found.", "error")

            return redirect(url_for("login"))

        student_id = student["id"]

        # ==========================================

        # ENROLL SUBJECT

        # ==========================================

        if request.method == "POST":
            subject_id = request.form.get("subject_id")

            if not subject_id:
                flash("Please select a subject.", "error")

                return redirect(url_for("student_subjects"))

            subject_response = (
                supabase.table("subjects")
                .select("*")
                .eq("id", int(subject_id))
                .single()
                .execute()
            )

            subject = subject_response.data

            if not subject:
                flash("Subject not found.", "error")

                return redirect(url_for("student_subjects"))

            # Only teacher-created subjects

            # with section are available

            if not subject.get("teacher_id") or not subject.get("section"):
                flash("This subject is not available for enrollment.", "error")

                return redirect(url_for("student_subjects"))

            # ==========================================

            # CHECK IF ALREADY ENROLLED

            # ==========================================

            existing_response = (
                supabase.table("enrollments")
                .select("*")
                .eq("student_id", student_id)
                .eq("subject_id", int(subject_id))
                .execute()
            )

            if existing_response.data:
                flash("You are already enrolled in this subject.", "error")

                return redirect(url_for("student_subjects"))

            # ==========================================

            # SAVE ENROLLMENT

            # ==========================================

            supabase.table("enrollments").insert(
                {
                    "student_id": student_id,
                    "subject_id": int(subject_id),
                    "section": subject.get("section"),
                }
            ).execute()

            flash("Subject enrolled successfully!", "success")

            return redirect(url_for("student_subjects"))

        # ==========================================

        # GET ALL SUBJECTS

        # ==========================================

        subjects_response = (
            supabase.table("subjects").select("*").order("subject_code").execute()
        )

        all_subjects = subjects_response.data or []

        # ==========================================

        # GET TEACHERS

        # ==========================================

        teachers_response = supabase.table("teachers").select("*").execute()

        teachers = {
            teacher["id"]: teacher for teacher in (teachers_response.data or [])
        }

        # ==========================================

        # ADD TEACHER NAME TO SUBJECTS

        # ==========================================

        subjects = []

        for subject in all_subjects:
            # Only teacher-created subjects

            if not subject.get("teacher_id"):
                continue

            # Only subjects with section

            if not subject.get("section"):
                continue

            teacher = teachers.get(subject.get("teacher_id"))

            subject["teacher_name"] = teacher.get("full_name") if teacher else "-"

            subjects.append(subject)

        # ==========================================

        # GET STUDENT ENROLLMENTS

        # ==========================================

        enrollments_response = (
            supabase.table("enrollments")
            .select("*")
            .eq("student_id", student_id)
            .execute()
        )

        enrolled_ids = {
            enrollment["subject_id"] for enrollment in (enrollments_response.data or [])
        }

        # ==========================================

        # DISPLAY PAGE

        # ==========================================

        return render_template(
            "student_subjects.html",
            subjects=subjects,
            enrolled_ids=enrolled_ids,
            student=student,
        )

    except Exception as e:
        print("Student subjects error:", e)

        flash("Unable to load subjects.", "error")

        return redirect(url_for("student_dashboard"))


# ==========================================

# REMOVE STUDENT ENROLLMENT

# ==========================================


@app.route("/student/subjects/<int:subject_id>/remove", methods=["POST"])
def student_remove_subject(subject_id):

    if "user_id" not in session:
        return redirect(url_for("login"))

    if session.get("role") != "student":
        return redirect(url_for("teacher_dashboard"))

    try:
        # ==========================================
        # GET CURRENT STUDENT
        # ==========================================

        student_response = (
            supabase.table("students")
            .select("*")
            .eq("user_id", session["user_id"])
            .single()
            .execute()
        )

        student = student_response.data

        if not student:
            flash("Student information not found.", "error")
            return redirect(url_for("login"))

        student_id = student["id"]

        # ==========================================
        # CHECK ENROLLMENT
        # ==========================================

        enrollment_response = (
            supabase.table("enrollments")
            .select("*")
            .eq("student_id", student_id)
            .eq("subject_id", subject_id)
            .execute()
        )

        if not enrollment_response.data:
            flash("You are not enrolled in this subject.", "error")
            return redirect(url_for("student_dashboard"))

        # ==========================================
        # REMOVE GRADES
        # ==========================================

        supabase.table("grades").delete().eq("student_id", student_id).eq(
            "subject_id", subject_id
        ).execute()

        # ==========================================
        # REMOVE ENROLLMENT
        # ==========================================

        supabase.table("enrollments").delete().eq("student_id", student_id).eq(
            "subject_id", subject_id
        ).execute()

        # ==========================================
        # SUCCESS
        # ==========================================

        flash("Subject enrollment and grades removed successfully.", "success")

        return redirect(url_for("student_dashboard"))

    except Exception as e:
        print("Student remove subject error:", e)

        flash("Unable to remove subject enrollment.", "error")

        return redirect(url_for("student_dashboard"))


# ==========================================
# TEACHER DASHBOARD
# ==========================================


@app.route("/teacher/dashboard")
def teacher_dashboard():

    if "user_id" not in session:
        return redirect(url_for("login"))

    if session.get("role") != "teacher":
        return redirect(url_for("student_dashboard"))

    user_id = session["user_id"]

    try:
        response = (
            supabase.table("teachers")
            .select("*")
            .eq("user_id", user_id)
            .single()
            .execute()
        )

        teacher = response.data

        if not teacher:
            flash("Teacher account not found.", "error")
            return redirect(url_for("login"))

        return render_template("teacher_dashboard.html", teacher=teacher)

    except Exception as e:
        print("Teacher dashboard error:", e)
        flash("Unable to load teacher information.", "error")
        return redirect(url_for("login"))


# TEACHER ADD SUBJECT


# ==========================================


@app.route("/teacher/subjects", methods=["GET", "POST"])
def teacher_subjects():

    if "user_id" not in session:
        return redirect(url_for("login"))

    if session.get("role") != "teacher":
        return redirect(url_for("student_dashboard"))

    user_id = session["user_id"]

    try:
        # GET CURRENT TEACHER

        teacher_response = (
            supabase.table("teachers")
            .select("*")
            .eq("user_id", user_id)
            .single()
            .execute()
        )

        teacher = teacher_response.data

        if not teacher:
            flash("Teacher account not found.", "error")

            return redirect(url_for("login"))

        teacher_id = teacher["id"]

        # ==========================================

        # ADD SUBJECT

        # ==========================================

        if request.method == "POST":
            subject_code = request.form.get("subject_code", "").strip().upper()

            subject_name = request.form.get("subject_name", "").strip()

            section = request.form.get("section", "").strip().upper()

            if not subject_code or not subject_name or not section:
                flash("Please complete all fields.", "error")

                return redirect(url_for("teacher_subjects"))

            # CHECK DUPLICATE

            existing_response = (
                supabase.table("subjects")
                .select("id")
                .eq("teacher_id", teacher_id)
                .eq("subject_code", subject_code)
                .eq("section", section)
                .execute()
            )

            if existing_response.data:
                flash("You already added this subject and section.", "error")

                return redirect(url_for("teacher_subjects"))

            # INSERT SUBJECT

            supabase.table("subjects").insert(
                {
                    "subject_code": subject_code,
                    "subject_name": subject_name,
                    "teacher_id": teacher_id,
                    "section": section,
                }
            ).execute()

            flash("Subject added successfully.", "success")

            return redirect(url_for("teacher_subjects"))

        # ==========================================

        # GET TEACHER SUBJECTS

        # ==========================================

        subjects_response = (
            supabase.table("subjects")
            .select("*")
            .eq("teacher_id", teacher_id)
            .order("subject_code")
            .execute()
        )

        subjects = subjects_response.data or []

        return render_template(
            "teacher_subjects.html", teacher=teacher, subjects=subjects
        )

    except Exception as e:
        print("Teacher subjects error:", e)

        flash("Unable to load subjects.", "error")

        return redirect(url_for("teacher_dashboard"))


# ==========================================


# ==========================================


# TEACHER SUBJECT GRADEBOOK


# ==========================================


@app.route("/teacher/subjects/<int:subject_id>")
def teacher_subject_gradebook(subject_id):

    if "user_id" not in session:
        return redirect(url_for("login"))

    if session.get("role") != "teacher":
        return redirect(url_for("student_dashboard"))

    try:
        teacher_response = (
            supabase.table("teachers")
            .select("*")
            .eq("user_id", session["user_id"])
            .single()
            .execute()
        )

        teacher = teacher_response.data

        if not teacher:
            flash("Teacher account not found.", "error")

            return redirect(url_for("login"))

        subject_response = (
            supabase.table("subjects")
            .select("*")
            .eq("id", subject_id)
            .eq("teacher_id", teacher["id"])
            .single()
            .execute()
        )

        subject = subject_response.data

        if not subject:
            flash("You are not allowed to access this subject.", "error")

            return redirect(url_for("teacher_subjects"))

        return redirect(
            url_for("gradebook", subject_id=subject["id"], section=subject["section"])
        )

    except Exception as e:
        print("Teacher subject gradebook error:", e)

        flash("Unable to open subject.", "error")

        return redirect(url_for("teacher_subjects"))


@app.route("/teacher/subjects/<int:subject_id>/edit", methods=["GET", "POST"])
def teacher_edit_subject(subject_id):

    if "user_id" not in session:
        return redirect(url_for("login"))

    if session.get("role") != "teacher":
        return redirect(url_for("student_dashboard"))

    try:
        # Get current teacher

        teacher_response = (
            supabase.table("teachers")
            .select("*")
            .eq("user_id", session["user_id"])
            .single()
            .execute()
        )

        teacher = teacher_response.data

        if not teacher:
            flash("Teacher account not found.", "error")

            return redirect(url_for("login"))

        teacher_id = teacher["id"]

        # Get subject and verify ownership

        subject_response = (
            supabase.table("subjects")
            .select("*")
            .eq("id", subject_id)
            .eq("teacher_id", teacher_id)
            .single()
            .execute()
        )

        subject = subject_response.data

        if not subject:
            flash("Subject not found or you are not allowed to edit it.", "error")

            return redirect(url_for("teacher_subjects"))

        # UPDATE

        if request.method == "POST":
            subject_code = request.form.get("subject_code", "").strip().upper()

            subject_name = request.form.get("subject_name", "").strip()

            section = request.form.get("section", "").strip().upper()

            if not subject_code or not subject_name or not section:
                flash("Please complete all fields.", "error")

                return render_template("teacher_edit_subject.html", subject=subject)

            if section not in ["A", "B"]:
                flash("Invalid section.", "error")

                return render_template("teacher_edit_subject.html", subject=subject)

            # Check duplicate subject

            duplicate_response = (
                supabase.table("subjects")
                .select("*")
                .eq("teacher_id", teacher_id)
                .eq("subject_code", subject_code)
                .eq("section", section)
                .neq("id", subject_id)
                .execute()
            )

            if duplicate_response.data:
                flash("You already have this subject code and section.", "error")

                return render_template("teacher_edit_subject.html", subject=subject)

            # Update subject

            supabase.table("subjects").update(
                {
                    "subject_code": subject_code,
                    "subject_name": subject_name,
                    "section": section,
                }
            ).eq("id", subject_id).eq("teacher_id", teacher_id).execute()

            # Keep enrollment section synchronized

            supabase.table("enrollments").update({"section": section}).eq(
                "subject_id", subject_id
            ).execute()

            flash("Subject updated successfully!", "success")

            return redirect(url_for("teacher_subjects"))

        return render_template("teacher_edit_subject.html", subject=subject)

    except Exception as e:
        print("Teacher edit subject error:", e)

        flash("Unable to edit subject.", "error")

        return redirect(url_for("teacher_subjects"))


@app.route("/teacher/subjects/<int:subject_id>/delete", methods=["POST"])
def teacher_delete_subject(subject_id):

    if "user_id" not in session:
        return redirect(url_for("login"))

    if session.get("role") != "teacher":
        return redirect(url_for("student_dashboard"))

    try:
        # Get current teacher

        teacher_response = (
            supabase.table("teachers")
            .select("*")
            .eq("user_id", session["user_id"])
            .single()
            .execute()
        )

        teacher = teacher_response.data

        if not teacher:
            flash("Teacher account not found.", "error")

            return redirect(url_for("login"))

        teacher_id = teacher["id"]

        # Verify subject belongs to current teacher

        subject_response = (
            supabase.table("subjects")
            .select("*")
            .eq("id", subject_id)
            .eq("teacher_id", teacher_id)
            .single()
            .execute()
        )

        subject = subject_response.data

        if not subject:
            flash("Subject not found or you are not allowed to delete it.", "error")

            return redirect(url_for("teacher_subjects"))

        # Delete subject

        supabase.table("subjects").delete().eq("id", subject_id).eq(
            "teacher_id", teacher_id
        ).execute()

        flash("Subject deleted successfully.", "success")

        return redirect(url_for("teacher_subjects"))

    except Exception as e:
        print("Teacher delete subject error:", e)

        flash("Unable to delete subject.", "error")

        return redirect(url_for("teacher_subjects"))


# TEACHER GRADEBOOK


# ==========================================


@app.route("/teacher/gradebook", methods=["GET", "POST"])
def gradebook():

    if "user_id" not in session:
        return redirect(url_for("login"))

    if session.get("role") != "teacher":
        return redirect(url_for("student_dashboard"))

    try:
        # ==========================================

        # GET CURRENT TEACHER

        # ==========================================

        teacher_response = (
            supabase.table("teachers")
            .select("*")
            .eq("user_id", session["user_id"])
            .single()
            .execute()
        )

        teacher = teacher_response.data

        if not teacher:
            flash("Teacher account not found.", "error")

            return redirect(url_for("login"))

        teacher_id = teacher["id"]

        # ==========================================

        # GET SELECTED SUBJECT

        # ==========================================

        selected_subject = request.form.get("subject_id") or request.args.get(
            "subject_id"
        )

        if not selected_subject:
            flash("Please select a subject first.", "error")

            return redirect(url_for("teacher_subjects"))

        selected_subject = int(selected_subject)

        # ==========================================

        # GET SUBJECT OWNED BY CURRENT TEACHER

        # ==========================================

        subject_response = (
            supabase.table("subjects")
            .select("*")
            .eq("id", selected_subject)
            .eq("teacher_id", teacher_id)
            .single()
            .execute()
        )

        subject = subject_response.data

        if not subject:
            flash("You are not allowed to access this subject.", "error")

            return redirect(url_for("teacher_subjects"))

        # ==========================================

        # AUTOMATIC SUBJECT INFORMATION

        # ==========================================

        selected_section = subject.get("section")

        # ==========================================

        # GET ENROLLED STUDENTS

        # ==========================================

        enrollments_response = (
            supabase.table("enrollments")
            .select("*")
            .eq("subject_id", selected_subject)
            .execute()
        )

        enrollments = enrollments_response.data or []

        enrolled_student_ids = {enrollment["student_id"] for enrollment in enrollments}

        # ==========================================

        # GET STUDENTS

        # ==========================================

        students_response = (
            supabase.table("students")
            .select("id, student_number, full_name, course, year_level, section")
            .order("full_name")
            .execute()
        )

        all_students = students_response.data or []

        # ==========================================

        # ONLY ENROLLED STUDENTS

        # ==========================================

        students = [
            student for student in all_students if student["id"] in enrolled_student_ids
        ]

        # ==========================================

        # SAVE GRADES

        # ==========================================

        if request.method == "POST" and request.form.get("action") == "save":
            valid_grades = [
                "1.00",
                "1.25",
                "1.50",
                "1.75",
                "2.00",
                "2.25",
                "2.50",
                "2.75",
                "3.00",
                "5.00",
            ]

            # Only save enrolled students

            for student in students:
                student_id = student["id"]

                prelim = request.form.get(f"prelim_{student_id}")

                midterm = request.form.get(f"midterm_{student_id}")

                finals = request.form.get(f"finals_{student_id}")

                # Skip completely empty rows

                if not prelim and not midterm and not finals:
                    continue

                # ==========================================

                # VALIDATE GRADES

                # ==========================================

                for grade in [prelim, midterm, finals]:
                    if grade and grade not in valid_grades:
                        flash(f"Invalid grade for {student['full_name']}.", "error")

                        return redirect(
                            url_for("gradebook", subject_id=selected_subject)
                        )

                # ==========================================

                # GET EXISTING GRADE

                # ==========================================

                existing_response = (
                    supabase.table("grades")
                    .select("*")
                    .eq("student_id", student_id)
                    .eq("subject_id", selected_subject)
                    .execute()
                )

                existing_grade = (
                    existing_response.data[0] if existing_response.data else None
                )

                # ==========================================

                # GET FINAL VALUES

                # ==========================================

                if existing_grade:
                    final_prelim = (
                        float(prelim) if prelim else existing_grade.get("prelim")
                    )

                    final_midterm = (
                        float(midterm) if midterm else existing_grade.get("midterm")
                    )

                    final_finals = (
                        float(finals) if finals else existing_grade.get("finals")
                    )

                else:
                    final_prelim = float(prelim) if prelim else None

                    final_midterm = float(midterm) if midterm else None

                    final_finals = float(finals) if finals else None

                # ==========================================

                # CALCULATE AVERAGE

                # ==========================================

                numeric_grades = []

                for grade in [final_prelim, final_midterm, final_finals]:
                    if grade is not None:
                        numeric_grades.append(float(grade))

                average = None

                if numeric_grades:
                    raw_average = sum(numeric_grades) / len(numeric_grades)

                    # Round to nearest 0.25

                    average = round(raw_average * 4) / 4

                # ==========================================

                # GRADE DATA

                # ==========================================

                grade_data = {
                    "prelim": final_prelim,
                    "midterm": final_midterm,
                    "finals": final_finals,
                    "average": average,
                }

                # ==========================================

                # UPDATE EXISTING GRADE

                # ==========================================

                if existing_grade:
                    (
                        supabase.table("grades")
                        .update(grade_data)
                        .eq("id", existing_grade["id"])
                        .execute()
                    )

                # ==========================================

                # INSERT NEW GRADE

                # ==========================================

                else:
                    grade_data["student_id"] = student_id

                    grade_data["subject_id"] = selected_subject

                    (supabase.table("grades").insert(grade_data).execute())

            flash("All grades saved successfully!", "success")

            return redirect(url_for("gradebook", subject_id=selected_subject))

        # ==========================================

        # GET SAVED GRADES

        # ==========================================

        grades = {}

        grades_response = (
            supabase.table("grades")
            .select("*")
            .eq("subject_id", selected_subject)
            .execute()
        )

        for grade in grades_response.data or []:
            grades[grade["student_id"]] = grade

        # ==========================================

        # DISPLAY GRADEBOOK

        # ==========================================

        return render_template(
            "gradebook.html",
            # Subject information
            subject=subject,
            selected_subject=selected_subject,
            selected_section=selected_section,
            # Students
            students=students,
            # Grades
            grades=grades,
        )

    except Exception as e:
        print("Gradebook error:", e)

        flash("Unable to load grade sheet.", "error")

        return redirect(url_for("teacher_subjects"))


# ==========================================
# ADMIN STUDENTS MANAGEMENT
# ==========================================


@app.route("/admin/students")
def admin_students():

    if "user_id" not in session:
        return redirect(url_for("admin_login"))

    if session.get("role") != "admin":
        return redirect(url_for("login"))

    try:
        students_response = (
            supabase.table("students").select("*").order("full_name").execute()
        )

        students = students_response.data or []

        return render_template("admin_students.html", students=students)

    except Exception as e:
        print("Admin students error:", e)
        flash("Unable to load students.", "error")
        return redirect(url_for("admin_dashboard"))


# ==========================================
# ADMIN EDIT STUDENT
# ==========================================


@app.route("/admin/students/<int:student_id>/edit", methods=["GET", "POST"])
def admin_edit_student(student_id):

    if "user_id" not in session:
        return redirect(url_for("admin_login"))

    if session.get("role") != "admin":
        return redirect(url_for("login"))

    try:
        student_response = (
            supabase.table("students")
            .select("*")
            .eq("id", student_id)
            .single()
            .execute()
        )

        student = student_response.data

        if not student:
            flash("Student not found.", "error")
            return redirect(url_for("admin_students"))

        if request.method == "POST":
            student_number = request.form.get("student_number", "").strip()

            full_name = request.form.get("full_name", "").strip()

            email = request.form.get("email", "").strip().lower()

            birthdate = request.form.get("birthdate", "").strip()

            gender = request.form.get("gender", "").strip()

            course = request.form.get("course", "").strip()

            year_level = request.form.get("year_level", "").strip()

            section = request.form.get("section", "").strip()

            address = request.form.get("address", "").strip()

            if not full_name or not email:
                flash("Full Name and Email are required.", "error")

                return render_template("admin_edit_student.html", student=student)

            # ==========================================
            # UPDATE AUTH EMAIL
            # ==========================================

            if student.get("user_id"):
                supabase_admin.auth.admin.update_user_by_id(
                    student["user_id"], {"email": email}
                )

            # ==========================================
            # UPDATE STUDENT INFORMATION
            # ==========================================

            supabase.table("students").update(
                {
                    "student_number": student_number or None,
                    "full_name": full_name,
                    "email": email,
                    "birthdate": birthdate or None,
                    "gender": gender or None,
                    "course": course or None,
                    "year_level": year_level or None,
                    "section": section or None,
                    "address": address or None,
                }
            ).eq("id", student_id).execute()

            flash("Student information updated successfully.", "success")

            return redirect(url_for("admin_students"))

        return render_template("admin_edit_student.html", student=student)

    except Exception as e:
        print("Admin edit student error:", e)

        flash("Unable to update student.", "error")

        return redirect(url_for("admin_students"))


# ==========================================
# ADMIN DELETE STUDENT
# ==========================================


@app.route("/admin/students/<int:student_id>/delete", methods=["POST"])
def admin_delete_student(student_id):

    if "user_id" not in session:
        return redirect(url_for("admin_login"))

    if session.get("role") != "admin":
        return redirect(url_for("login"))

    try:
        # ==========================================
        # GET STUDENT
        # ==========================================

        student_response = (
            supabase.table("students")
            .select("id, user_id, full_name")
            .eq("id", student_id)
            .single()
            .execute()
        )

        student = student_response.data

        if not student:
            flash("Student not found.", "error")
            return redirect(url_for("admin_students"))

        user_id = student.get("user_id")

        # ==========================================
        # DELETE AUTHENTICATION ACCOUNT
        # ==========================================

        if user_id:
            supabase_admin.auth.admin.delete_user(user_id)

        # ==========================================
        # DELETE STUDENT DATABASE RECORD
        # ==========================================

        supabase.table("students").delete().eq("id", student_id).execute()

        flash("Student account deleted successfully.", "success")

        return redirect(url_for("admin_students"))

    except Exception as e:
        print("Admin delete student error:", e)

        flash("Unable to delete student account.", "error")

        return redirect(url_for("admin_students"))


# ==========================================
# ADMIN INSTRUCTORS MANAGEMENT
# ==========================================


@app.route("/admin/instructors")
def admin_instructors():

    if "user_id" not in session:
        return redirect(url_for("admin_login"))

    if session.get("role") != "admin":
        return redirect(url_for("login"))

    try:
        instructors_response = (
            supabase.table("teachers").select("*").order("full_name").execute()
        )

        instructors = instructors_response.data or []

        return render_template("admin_instructors.html", instructors=instructors)

    except Exception as e:
        print("Admin instructors error:", e)

        flash("Unable to load instructors.", "error")

        return redirect(url_for("admin_dashboard"))


# ==========================================
# ADMIN EDIT INSTRUCTOR
# ==========================================


@app.route("/admin/instructors/<int:instructor_id>/edit", methods=["GET", "POST"])
def admin_edit_instructor(instructor_id):

    if "user_id" not in session:
        return redirect(url_for("admin_login"))

    if session.get("role") != "admin":
        return redirect(url_for("login"))

    try:
        instructor_response = (
            supabase.table("teachers")
            .select("*")
            .eq("id", instructor_id)
            .single()
            .execute()
        )

        instructor = instructor_response.data

        if not instructor:
            flash("Instructor not found.", "error")
            return redirect(url_for("admin_instructors"))

        if request.method == "POST":
            full_name = request.form.get("full_name", "").strip()

            email = request.form.get("email", "").strip().lower()

            if not full_name or not email:
                flash("Full Name and Email are required.", "error")

                return render_template(
                    "admin_edit_instructor.html", instructor=instructor
                )

            # Update Supabase Authentication
            if instructor.get("user_id"):
                supabase_admin.auth.admin.update_user_by_id(
                    instructor["user_id"], {"email": email}
                )

            # Update teachers table
            supabase.table("teachers").update(
                {"full_name": full_name, "email": email}
            ).eq("id", instructor_id).execute()

            flash("Instructor information updated successfully.", "success")

            return redirect(url_for("admin_instructors"))

        return render_template("admin_edit_instructor.html", instructor=instructor)

    except Exception as e:
        print("Admin edit instructor error:", e)

        flash("Unable to update instructor.", "error")

        return redirect(url_for("admin_instructors"))


# ==========================================
# ADMIN DELETE INSTRUCTOR
# ==========================================


@app.route("/admin/instructors/<int:instructor_id>/delete", methods=["POST"])
def admin_delete_instructor(instructor_id):

    if "user_id" not in session:
        return redirect(url_for("admin_login"))

    if session.get("role") != "admin":
        return redirect(url_for("login"))

    try:
        # ------------------------------------------
        # GET INSTRUCTOR
        # ------------------------------------------

        instructor_response = (
            supabase.table("teachers")
            .select("id, user_id, full_name, email")
            .eq("id", instructor_id)
            .single()
            .execute()
        )

        instructor = instructor_response.data

        if not instructor:
            flash("Instructor not found.", "error")

            return redirect(url_for("admin_instructors"))

        # ------------------------------------------
        # CHECK ASSIGNED SUBJECTS
        # ------------------------------------------

        subjects_response = (
            supabase.table("subjects")
            .select("id, subject_code, subject_name")
            .eq("teacher_id", instructor_id)
            .execute()
        )

        subjects = subjects_response.data or []

        # ------------------------------------------
        # DELETE RELATED DATA
        # ------------------------------------------

        for subject in subjects:
            subject_id = subject["id"]

            # Delete grades
            supabase.table("grades").delete().eq("subject_id", subject_id).execute()

            # Delete enrollments
            supabase.table("enrollments").delete().eq(
                "subject_id", subject_id
            ).execute()

            # Delete subject
            supabase.table("subjects").delete().eq("id", subject_id).execute()

        # ------------------------------------------
        # DELETE SUPABASE AUTH ACCOUNT
        # ------------------------------------------

        user_id = instructor.get("user_id")

        if user_id:
            supabase_admin.auth.admin.delete_user(user_id)

        # ------------------------------------------
        # DELETE TEACHER RECORD
        # ------------------------------------------

        supabase.table("teachers").delete().eq("id", instructor_id).execute()

        # ------------------------------------------
        # SUCCESS MESSAGE
        # ------------------------------------------

        if subjects:
            flash(
                "Instructor and all assigned "
                "subjects, enrollments, and grades "
                "were deleted successfully.",
                "success",
            )

        else:
            flash("Instructor account deleted successfully.", "success")

        return redirect(url_for("admin_instructors"))

    except Exception as e:
        print("Admin delete instructor error:", e)

        flash("Unable to delete instructor.", "error")

        return redirect(url_for("admin_instructors"))


# ==========================================
# ADMIN SUBJECTS MANAGEMENT
# ==========================================


@app.route("/admin/subjects")
def admin_subjects():

    if "user_id" not in session:
        return redirect(url_for("admin_login"))

    if session.get("role") != "admin":
        return redirect(url_for("login"))

    try:
        # Get all subjects
        subjects_response = (
            supabase.table("subjects").select("*").order("subject_code").execute()
        )

        subjects = subjects_response.data or []

        # Get all instructors
        instructors_response = (
            supabase.table("teachers").select("id, full_name").execute()
        )

        instructors = {
            instructor["id"]: instructor["full_name"]
            for instructor in (instructors_response.data or [])
        }

        # Attach instructor name to each subject
        for subject in subjects:
            teacher_id = subject.get("teacher_id")

            subject["teacher_name"] = instructors.get(teacher_id, "No Instructor")

        return render_template("admin_subjects.html", subjects=subjects)

    except Exception as e:
        print("Admin subjects error:", e)

        flash("Unable to load subjects.", "error")

        return redirect(url_for("admin_dashboard"))


# ==========================================
# ADMIN EDIT SUBJECT
# ==========================================


@app.route("/admin/subjects/<int:subject_id>/edit", methods=["GET", "POST"])
def admin_edit_subject(subject_id):

    if "user_id" not in session:
        return redirect(url_for("admin_login"))

    if session.get("role") != "admin":
        return redirect(url_for("login"))

    try:
        # Get subject
        subject_response = (
            supabase.table("subjects")
            .select("*")
            .eq("id", subject_id)
            .single()
            .execute()
        )

        subject = subject_response.data

        if not subject:
            flash("Subject not found.", "error")
            return redirect(url_for("admin_subjects"))

        # Get instructors
        instructors_response = (
            supabase.table("teachers")
            .select("id, full_name")
            .order("full_name")
            .execute()
        )

        instructors = instructors_response.data or []

        # POST
        if request.method == "POST":
            subject_code = request.form.get("subject_code", "").strip().upper()

            subject_name = request.form.get("subject_name", "").strip()

            teacher_id = request.form.get("teacher_id", "").strip()

            section = request.form.get("section", "").strip().upper()

            # Validation
            if not subject_code or not subject_name or not teacher_id or not section:
                flash("Please complete all fields.", "error")

                return render_template(
                    "admin_edit_subject.html", subject=subject, instructors=instructors
                )

            if section not in ["A", "B"]:
                flash("Section must be A or B.", "error")

                return render_template(
                    "admin_edit_subject.html", subject=subject, instructors=instructors
                )

            # Check instructor exists
            instructor_response = (
                supabase.table("teachers")
                .select("id")
                .eq("id", int(teacher_id))
                .single()
                .execute()
            )

            instructor = instructor_response.data

            if not instructor:
                flash("Selected instructor was not found.", "error")

                return render_template(
                    "admin_edit_subject.html", subject=subject, instructors=instructors
                )

            # Check duplicate subject assignment
            duplicate_response = (
                supabase.table("subjects")
                .select("id")
                .eq("teacher_id", int(teacher_id))
                .eq("subject_code", subject_code)
                .eq("section", section)
                .execute()
            )

            duplicates = duplicate_response.data or []

            duplicate_exists = any(item["id"] != subject_id for item in duplicates)

            if duplicate_exists:
                flash("This instructor already has this subject and section.", "error")

                return render_template(
                    "admin_edit_subject.html", subject=subject, instructors=instructors
                )

            # Update subject
            supabase.table("subjects").update(
                {
                    "subject_code": subject_code,
                    "subject_name": subject_name,
                    "teacher_id": int(teacher_id),
                    "section": section,
                }
            ).eq("id", subject_id).execute()

            # Keep enrollment sections synchronized
            supabase.table("enrollments").update({"section": section}).eq(
                "subject_id", subject_id
            ).execute()

            flash("Subject information updated successfully.", "success")

            return redirect(url_for("admin_subjects"))

        return render_template(
            "admin_edit_subject.html", subject=subject, instructors=instructors
        )

    except Exception as e:
        print("Admin edit subject error:", e)

        flash("Unable to update subject.", "error")

        return redirect(url_for("admin_subjects"))


# ==========================================
# ADMIN DELETE SUBJECT
# ==========================================


@app.route("/admin/subjects/<int:subject_id>/delete", methods=["POST"])
def admin_delete_subject(subject_id):

    if "user_id" not in session:
        return redirect(url_for("admin_login"))

    if session.get("role") != "admin":
        return redirect(url_for("login"))

    try:
        # Get subject
        subject_response = (
            supabase.table("subjects")
            .select("id, subject_code, subject_name")
            .eq("id", subject_id)
            .single()
            .execute()
        )

        subject = subject_response.data

        if not subject:
            flash("Subject not found.", "error")

            return redirect(url_for("admin_subjects"))

        # Delete related grades
        supabase.table("grades").delete().eq("subject_id", subject_id).execute()

        # Delete related enrollments
        supabase.table("enrollments").delete().eq("subject_id", subject_id).execute()

        # Delete subject
        supabase.table("subjects").delete().eq("id", subject_id).execute()

        flash(
            f"Subject {subject.get('subject_code', '')} "
            "and its related enrollments and grades "
            "were deleted successfully.",
            "success",
        )

        return redirect(url_for("admin_subjects"))

    except Exception as e:
        print("Admin delete subject error:", e)

        flash("Unable to delete subject.", "error")

        return redirect(url_for("admin_subjects"))


# ==========================================
# ADMIN ENROLLMENTS MANAGEMENT
# ==========================================


@app.route("/admin/enrollments")
def admin_enrollments():

    if "user_id" not in session:
        return redirect(url_for("admin_login"))

    if session.get("role") != "admin":
        return redirect(url_for("login"))

    try:
        # Get enrollments
        enrollments_response = (
            supabase.table("enrollments").select("*").order("id").execute()
        )

        enrollments = enrollments_response.data or []

        # Get students
        students_response = (
            supabase.table("students").select("id, student_number, full_name").execute()
        )

        students = {
            student["id"]: student for student in (students_response.data or [])
        }

        # Get subjects
        subjects_response = (
            supabase.table("subjects")
            .select("id, subject_code, subject_name, teacher_id")
            .execute()
        )

        subjects = {
            subject["id"]: subject for subject in (subjects_response.data or [])
        }

        # Get instructors
        instructors_response = (
            supabase.table("teachers").select("id, full_name").execute()
        )

        instructors = {
            instructor["id"]: instructor["full_name"]
            for instructor in (instructors_response.data or [])
        }

        # Attach related information
        for enrollment in enrollments:
            student = students.get(enrollment.get("student_id"))

            subject = subjects.get(enrollment.get("subject_id"))

            enrollment["student_number"] = (
                student.get("student_number") if student else "-"
            )

            enrollment["student_name"] = student.get("full_name") if student else "-"

            enrollment["subject_code"] = subject.get("subject_code") if subject else "-"

            enrollment["subject_name"] = subject.get("subject_name") if subject else "-"

            teacher_id = subject.get("teacher_id") if subject else None

            enrollment["teacher_name"] = instructors.get(teacher_id, "No Instructor")

            enrollment["display_section"] = (
                enrollment.get("section")
                or (subject.get("section") if subject else "-")
                or "-"
            )

        return render_template("admin_enrollments.html", enrollments=enrollments)

    except Exception as e:
        print("Admin enrollments error:", e)

        flash("Unable to load enrollments.", "error")

        return redirect(url_for("admin_dashboard"))


@app.route("/admin/enrollments/<int:enrollment_id>/delete", methods=["POST"])
def admin_delete_enrollment(enrollment_id):

    if "user_id" not in session:
        return redirect(url_for("admin_login"))

    if session.get("role") != "admin":
        return redirect(url_for("login"))

    try:
        enrollment_response = (
            supabase.table("enrollments")
            .select("*")
            .eq("id", enrollment_id)
            .single()
            .execute()
        )

        enrollment = enrollment_response.data

        if not enrollment:
            flash("Enrollment not found.", "error")
            return redirect(url_for("admin_enrollments"))

        # Remove enrollment only
        supabase.table("enrollments").delete().eq("id", enrollment_id).execute()

        flash("Student enrollment removed successfully.", "success")

        return redirect(url_for("admin_enrollments"))

    except Exception as e:
        print("Admin delete enrollment error:", e)

        flash("Unable to remove enrollment.", "error")

        return redirect(url_for("admin_enrollments"))


# ==========================================


# LOGOUT


# ==========================================


@app.route("/logout")
def logout():

    session.clear()

    return redirect(url_for("login"))


# ==========================================


# RUN APPLICATION


# ==========================================


if __name__ == "__main__":
    app.run(debug=True)
