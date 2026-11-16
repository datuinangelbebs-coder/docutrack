
import re
import streamlit as st

from werkzeug.security import (
    generate_password_hash,
    check_password_hash
)

from database import SessionLocal, User


# =====================================
# UM INSTITUTIONAL EMAIL VALIDATION
# =====================================

UM_EMAIL_PATTERN = (
    r"^[a-z]\.[a-z]+(?:[.-][a-z]+)*\.\d+\.tc@umindanao\.edu\.ph$"
)


def validate_um_email(email):

    email = email.strip().lower()

    return bool(
        re.fullmatch(UM_EMAIL_PATTERN, email)
    )


# =====================================
# COURSE AND YEAR OPTIONS
# =====================================

COURSE_OPTIONS = [
    "Bachelor of Science in Information Technology (BSIT)",
    "Bachelor of Science in Computer Science (BSCS)",
    "Bachelor of Science in Accountancy (BSA)",
    "Bachelor of Science in Business Administration (BSBA)",
    "Bachelor of Science in Criminology (BSCrim)",
    "Bachelor of Science in Psychology (BS Psychology)",
    "Bachelor of Science in Hospitality Management (BSHM)",
    "Bachelor of Science in Tourism Management (BSTM)",
    "Bachelor of Elementary Education (BEEd)",
    "Bachelor of Secondary Education (BSEd)",
    "Other / Not Listed"
]

YEAR_OPTIONS = [
    "1st Year",
    "2nd Year",
    "3rd Year",
    "4th Year",
    "5th Year"
]


# =====================================
# STUDENT REGISTRATION
# =====================================

def register_student(
    first_name,
    middle_name,
    last_name,
    student_id,
    email,
    password,
    course,
    year_level
):

    first_name = first_name.strip()
    middle_name = middle_name.strip()
    last_name = last_name.strip()
    student_id = student_id.strip()
    email = email.strip().lower()

    if not all([
        first_name,
        last_name,
        student_id,
        email,
        password,
        course,
        year_level
    ]):
        return False, "Please complete all required fields."

    if not validate_um_email(email):
        return False, "Please use a valid UM institutional email."

    if len(password) < 8:
        return False, "Password must contain at least 8 characters."

    if course not in COURSE_OPTIONS:
        return False, "Please select a valid course."

    if year_level not in YEAR_OPTIONS:
        return False, "Please select a valid year level."

    with SessionLocal() as db:

        existing_email = db.query(User).filter_by(
            email=email
        ).first()

        if existing_email:
            return False, "This email is already registered."

        existing_student = db.query(User).filter_by(
            student_id=student_id
        ).first()

        if existing_student:
            return False, "This Student ID is already registered."

        new_student = User(
            first_name=first_name,
            middle_name=middle_name or None,
            last_name=last_name,
            student_id=student_id,
            email=email,
            course=course,
            year_level=year_level,
            password_hash=generate_password_hash(password),
            role="student"
        )

        db.add(new_student)
        db.commit()

    return True, "Registration successful! You can now log in."


# =====================================
# STUDENT LOGIN
# =====================================

def login_user(email, password):

    email = email.strip().lower()

    if not validate_um_email(email):
        return False, "Invalid UM institutional email or password."

    with SessionLocal() as db:

        user = db.query(User).filter_by(
            email=email,
            is_active=True
        ).first()

        if not user:
            return False, "Invalid UM institutional email or password."

        if not check_password_hash(
            user.password_hash,
            password
        ):
            return False, "Invalid UM institutional email or password."

        # SESSION INFORMATION

        st.session_state["logged_in"] = True
        st.session_state["user_id"] = user.id

        st.session_state["user_name"] = (
            f"{user.first_name} {user.last_name}"
        )

        st.session_state["user_role"] = user.role
        st.session_state["user_email"] = user.email

        st.session_state["user_course"] = (
            user.course or "Not specified"
        )

        st.session_state["user_year_level"] = (
            user.year_level or "Not specified"
        )

    return True, "Login successful!"


# =====================================
# LOGOUT
# =====================================

def logout_user():

    keys = [
        "logged_in",
        "user_id",
        "user_name",
        "user_role",
        "user_email",
        "user_course",
        "user_year_level",
        "edit_profile_mode"
    ]

    for key in keys:
        st.session_state.pop(key, None)

    st.rerun()


# =====================================
# LOGIN AND REGISTRATION INTERFACE
# =====================================

def show_authentication():

    left, right = st.columns([1.1, 1])

    # =================================
    # LEFT WELCOME PANEL
    # =================================

    with left:

        st.markdown(
            """
            <div class="auth-welcome">
                <h2>Welcome to UMTC!</h2>
                <p>
                    A convenient way to request academic documents
                    and monitor your request progress.
                </p>
                <h3>Simple. Organized. Accessible.</h3>
            </div>
            """,
            unsafe_allow_html=True
        )

    # =================================
    # RIGHT AUTHENTICATION PANEL
    # =================================

    with right:

        login_tab, register_tab = st.tabs(
            ["Login", "Create Account"]
        )

        # =================================
        # LOGIN FORM
        # =================================

        with login_tab:

            st.subheader("Student Login")

            with st.form("student_login_form"):

                email = st.text_input(
                    "UM Institutional Email",
                    placeholder="a.lastname.123456.tc@umindanao.edu.ph"
                )

                password = st.text_input(
                    "Password",
                    type="password"
                )

                login_button = st.form_submit_button(
                    "LOGIN",
                    use_container_width=True
                )

                if login_button:

                    if not email or not password:
                        st.error("Please complete all fields.")

                    else:

                        success, message = login_user(
                            email,
                            password
                        )

                        if success:
                            st.success(message)
                            st.rerun()

                        else:
                            st.error(message)

        # =================================
        # REGISTRATION FORM
        # =================================

        with register_tab:

            st.subheader("Create Student Account")

            with st.form("student_registration_form"):

                first_name = st.text_input(
                    "First Name"
                )

                middle_name = st.text_input(
                    "Middle Name (Optional)"
                )

                last_name = st.text_input(
                    "Last Name"
                )

                student_id = st.text_input(
                    "Student ID Number"
                )

                st.divider()

                st.markdown("**Academic Information**")

                course = st.selectbox(
                    "Course / Program",
                    options=COURSE_OPTIONS,
                    index=None,
                    placeholder="Select your course"
                )

                year_level = st.selectbox(
                    "Year Level",
                    options=YEAR_OPTIONS,
                    index=None,
                    placeholder="Select your year level"
                )

                st.divider()

                email = st.text_input(
                    "UM Institutional Email",
                    placeholder="a.lastname.123456.tc@umindanao.edu.ph"
                )

                password = st.text_input(
                    "Create Password",
                    type="password"
                )

                confirm_password = st.text_input(
                    "Confirm Password",
                    type="password"
                )

                register_button = st.form_submit_button(
                    "CREATE ACCOUNT",
                    use_container_width=True
                )

                if register_button:

                    if not all([
                        first_name.strip(),
                        last_name.strip(),
                        student_id.strip(),
                        email.strip(),
                        password,
                        confirm_password,
                        course,
                        year_level
                    ]):

                        st.error(
                            "Please complete all required fields."
                        )

                    elif password != confirm_password:

                        st.error("Passwords do not match.")

                    else:

                        success, message = register_student(
                            first_name,
                            middle_name,
                            last_name,
                            student_id,
                            email,
                            password,
                            course,
                            year_level
                        )

                        if success:

                            st.success(message)

                            st.info(
                                "Go to the Login tab to access your account."
                            )

                        else:

                            st.error(message)


# =====================================
# END OF AUTHENTICATION MODULE
# =====================================
