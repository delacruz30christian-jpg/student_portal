import os

from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    session
)

from supabase import create_client
from dotenv import load_dotenv


# ==========================================
# LOAD ENVIRONMENT VARIABLES
# ==========================================

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase = create_client(
    SUPABASE_URL,
    SUPABASE_KEY
)


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
        age = request.form.get("age")
        birthdate = request.form.get("birthdate")
        gender = request.form.get("gender")
        skills = request.form.getlist("skills")
        course = request.form.get("course")
        year_level = request.form.get("year_level")
        section = request.form.get("section")
        address = request.form.get("address")

        try:

            # Create account in Supabase Authentication
            auth_response = supabase.auth.sign_up({
                "email": email,
                "password": password
            })

            user = auth_response.user

            if not user:

                flash(
                    "Registration failed. Please try again.",
                    "error"
                )

                return redirect(url_for("register"))

            # Save student information
            supabase.table("students").insert({
                "user_id": user.id,
                "student_number": student_number,
                "full_name": full_name,
                "email": email,
                "age": int(age),
                "birthdate": birthdate,
                "gender": gender,
                "skills": skills,
                "course": course,
                "year_level": year_level,
                "section": section,
                "address": address
            }).execute()

            flash(
                "Registration successful! You can now login.",
                "success"
            )

            return redirect(url_for("login"))

        except Exception as e:

            print("Registration error:", e)

            flash(
                "Registration failed. Please check your information.",
                "error"
            )

    return render_template("register.html")


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
            auth_response = supabase.auth.sign_in_with_password({
                "email": email,
                "password": password
            })

            user = auth_response.user

            if not user:

                flash(
                    "Invalid email or password.",
                    "error"
                )

                return redirect(url_for("login"))

            user_id = str(user.id)

            # Save session
            session["user_id"] = user_id
            session["email"] = user.email

            # ==========================================
            # CHECK IF TEACHER
            # ==========================================

            teacher_response = (
                supabase
                .table("teachers")
                .select("*")
                .eq("user_id", user_id)
                .execute()
            )

            if teacher_response.data:

                session["role"] = "teacher"

                return redirect(
                    url_for("teacher_dashboard")
                )

            # ==========================================
            # OTHERWISE STUDENT
            # ==========================================

            session["role"] = "student"

            return redirect(
                url_for("student_dashboard")
            )

        except Exception as e:

            print("Login error:", e)

            flash(
                "Invalid email or password.",
                "error"
            )

    return render_template("login.html")

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

        # ==========================================
        # GET STUDENT INFORMATION
        # ==========================================

        student_response = (
            supabase
            .table("students")
            .select("*")
            .eq("user_id", user_id)
            .single()
            .execute()
        )

        student = student_response.data

        if not student:
            flash(
                "Student information not found.",
                "error"
            )

            return redirect(url_for("login"))

        student_id = student["id"]

        # ==========================================
        # GET STUDENT GRADES
        # ==========================================

        grades_response = (
            supabase
            .table("grades")
            .select("*")
            .eq("student_id", student_id)
            .execute()
        )

        grades_data = grades_response.data or []

        # ==========================================
        # GET SUBJECTS
        # ==========================================

        subjects_response = (
            supabase
            .table("subjects")
            .select("*")
            .execute()
        )

        subjects = {
            subject["id"]: subject
            for subject in (subjects_response.data or [])
        }

        # ==========================================
        # COMBINE GRADES + SUBJECT INFORMATION
        # ==========================================

        student_grades = []

        for grade in grades_data:

            subject = subjects.get(
                grade["subject_id"]
            )

            if subject:

                student_grades.append({
                    "subject_code": subject["subject_code"],
                    "subject_name": subject["subject_name"],
                    "prelim": grade["prelim"],
                    "midterm": grade["midterm"],
                    "finals": grade["finals"],
                    "average": grade["average"]
                })

        # Sort by subject code
        student_grades.sort(
            key=lambda x: x["subject_code"]
        )

        return render_template(
            "student_dashboard.html",
            student=student,
            grades=student_grades
        )

    except Exception as e:

        print(
            "Student dashboard error:",
            e
        )

        flash(
            "Unable to load student information.",
            "error"
        )

        return redirect(url_for("login"))

# ==========================================
# TEACHER DASHBOARD
# ==========================================

@app.route("/teacher/dashboard")
def teacher_dashboard():

    if "user_id" not in session:

        return redirect(url_for("login"))

    if session.get("role") != "teacher":

        return redirect(
            url_for("student_dashboard")
        )

    user_id = session["user_id"]

    try:

        response = (
            supabase
            .table("teachers")
            .select("*")
            .eq("user_id", user_id)
            .single()
            .execute()
        )

        teacher = response.data

        return render_template(
            "teacher_dashboard.html",
            teacher=teacher
        )

    except Exception as e:

        print("Teacher dashboard error:", e)

        flash(
            "Unable to load teacher information.",
            "error"
        )

        return redirect(url_for("login"))


# ==========================================
# TEACHER GRADEBOOK
# ==========================================

@app.route("/teacher/gradebook", methods=["GET", "POST"])
def gradebook():

    if "user_id" not in session:
        return redirect(url_for("login"))

    if session.get("role") != "teacher":
        return redirect(url_for("student_dashboard"))

    try:

        # GET SUBJECTS
        subjects_response = (
            supabase
            .table("subjects")
            .select("*")
            .order("subject_code")
            .execute()
        )

        subjects = subjects_response.data or []

        # GET STUDENTS
        students_response = (
            supabase
            .table("students")
            .select(
                "id, student_number, full_name, course, year_level, section"
            )
            .order("full_name")
            .execute()
        )

        all_students = students_response.data or []

        # GET SECTIONS
        sections = sorted(
            list(
                set(
                    student.get("section")
                    for student in all_students
                    if student.get("section")
                )
            )
        )

        # SELECTED SUBJECT AND SECTION
        selected_subject = (
            request.form.get("subject_id")
            or request.args.get("subject_id")
        )

        selected_section = (
            request.form.get("section")
            or request.args.get("section")
        )

        # ==========================================
        # SAVE GRADES
        # ==========================================

        if request.method == "POST" and request.form.get("action") == "save":

            if not selected_subject or not selected_section:

                flash(
                    "Please select a subject and section.",
                    "error"
                )

                return redirect(
                    url_for("gradebook")
                )

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
                "5.00"
            ]

            students_in_section = [
                student
                for student in all_students
                if student.get("section") == selected_section
            ]

            for student in students_in_section:

                student_id = student["id"]

                prelim = request.form.get(
                    f"prelim_{student_id}"
                )

                midterm = request.form.get(
                    f"midterm_{student_id}"
                )

                finals = request.form.get(
                    f"finals_{student_id}"
                )

                # Skip completely empty rows
                if not prelim and not midterm and not finals:
                    continue

                # VALIDATE
                for grade in [prelim, midterm, finals]:

                    if grade and grade not in valid_grades:

                        flash(
                            f"Invalid grade for {student['full_name']}.",
                            "error"
                        )

                        return redirect(
                            url_for(
                                "gradebook",
                                subject_id=selected_subject,
                                section=selected_section
                            )
                        )

                # ==========================================
                # GET EXISTING GRADE
                # ==========================================

                existing_response = (
                    supabase
                    .table("grades")
                    .select("*")
                    .eq("student_id", student_id)
                    .eq("subject_id", int(selected_subject))
                    .execute()
                )

                if existing_response.data:

                    existing_grade = existing_response.data[0]

                    # Keep existing value when field is blank
                    final_prelim = (
                        float(prelim)
                        if prelim
                        else existing_grade.get("prelim")
                    )

                    final_midterm = (
                        float(midterm)
                        if midterm
                        else existing_grade.get("midterm")
                    )

                    final_finals = (
                        float(finals)
                        if finals
                        else existing_grade.get("finals")
                    )

                    # Calculate average
                    numeric_grades = []

                    for grade in [
                        final_prelim,
                        final_midterm,
                        final_finals
                    ]:

                        if grade is not None:
                            numeric_grades.append(
                                float(grade)
                            )

                    average = None

                    if numeric_grades:

                        raw_average = (
                            sum(numeric_grades)
                            / len(numeric_grades)
                        )

                        average = round(
                            raw_average * 4
                        ) / 4

                    grade_data = {
                        "prelim": final_prelim,
                        "midterm": final_midterm,
                        "finals": final_finals,
                        "average": average
                    }

                    (
                        supabase
                        .table("grades")
                        .update(grade_data)
                        .eq(
                            "id",
                            existing_grade["id"]
                        )
                        .execute()
                    )

                else:

                    # ==========================================
                    # NEW GRADE
                    # ==========================================

                    numeric_grades = []

                    for grade in [
                        prelim,
                        midterm,
                        finals
                    ]:

                        if grade:
                            numeric_grades.append(
                                float(grade)
                            )

                    average = None

                    if numeric_grades:

                        raw_average = (
                            sum(numeric_grades)
                            / len(numeric_grades)
                        )

                        average = round(
                            raw_average * 4
                        ) / 4

                    grade_data = {
                        "student_id": student_id,
                        "subject_id": int(selected_subject),
                        "prelim": (
                            float(prelim)
                            if prelim
                            else None
                        ),
                        "midterm": (
                            float(midterm)
                            if midterm
                            else None
                        ),
                        "finals": (
                            float(finals)
                            if finals
                            else None
                        ),
                        "average": average
                    }

                    (
                        supabase
                        .table("grades")
                        .insert(grade_data)
                        .execute()
                    )

            flash(
                "All grades saved successfully!",
                "success"
            )

            return redirect(
                url_for(
                    "gradebook",
                    subject_id=selected_subject,
                    section=selected_section
                )
            )

        # ==========================================
        # FILTER STUDENTS
        # ==========================================

        students = [
            student
            for student in all_students
            if (
                not selected_section
                or student.get("section") == selected_section
            )
        ]

        # ==========================================
        # GET SAVED GRADES
        # ==========================================

        grades = {}

        if selected_subject:

            grades_response = (
                supabase
                .table("grades")
                .select("*")
                .eq(
                    "subject_id",
                    int(selected_subject)
                )
                .execute()
            )

            for grade in grades_response.data or []:

                grades[
                    grade["student_id"]
                ] = grade

        return render_template(
            "gradebook.html",
            subjects=subjects,
            sections=sections,
            students=students,
            grades=grades,
            selected_subject=selected_subject,
            selected_section=selected_section
        )

    except Exception as e:

        print("Gradebook error:", e)

        flash(
            "Unable to load grade sheet.",
            "error"
        )

        return redirect(
            url_for("teacher_dashboard")
        )



# ==========================================
# LOGOUT
# ==========================================

@app.route("/logout")
def logout():

    session.clear()

    return redirect(
        url_for("login")
    )


# ==========================================
# RUN APPLICATION
# ==========================================

if __name__ == "__main__":

    app.run(
        debug=True
    )