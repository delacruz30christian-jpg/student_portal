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





supabase = create_client(SUPABASE_URL, SUPABASE_KEY)





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
                birth_year, birth_month, birth_day = map(
                    int, birthdate.split("-")
                )
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

        subjects_response = (
            supabase.table("subjects")
            .select("*")
            .execute()
        )

        subjects = {
            subject["id"]: subject
            for subject in (subjects_response.data or [])
        }

        teachers_response = (
            supabase.table("teachers")
            .select("*")
            .execute()
        )

        teachers = {
            teacher["id"]: teacher
            for teacher in (teachers_response.data or [])
        }

        grades_response = (
            supabase.table("grades")
            .select("*")
            .eq("student_id", student_id)
            .execute()
        )

        grades = {
            grade["subject_id"]: grade
            for grade in (grades_response.data or [])
        }

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
                    "section": (
                        enrollment.get("section")
                        or subject.get("section")
                    ),
                    "teacher_name": (
                        teacher.get("full_name")
                        if teacher
                        else "-"
                    ),
                    "prelim": (
                        grade.get("prelim")
                        if grade
                        else None
                    ),
                    "midterm": (
                        grade.get("midterm")
                        if grade
                        else None
                    ),
                    "finals": (
                        grade.get("finals")
                        if grade
                        else None
                    ),
                    "average": (
                        grade.get("average")
                        if grade
                        else None
                    ),
                }
            )

        enrolled_subjects.sort(
            key=lambda x: x["subject_code"] or ""
        )

        return render_template(
            "student_dashboard.html",
            student=student,
            age=age,
            enrolled_subjects=enrolled_subjects,
        )

    except Exception as e:
        print("Student dashboard error:", e)

        flash(
            "Unable to load student information.",
            "error"
        )

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

        # REMOVE ENROLLMENT ONLY

        # ==========================================



        supabase.table("enrollments").delete().eq("student_id", student_id).eq(

            "subject_id", subject_id

        ).execute()



        flash("Subject enrollment removed successfully.", "success")



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

        return render_template(
            "teacher_dashboard.html",
            teacher=teacher
        )

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
