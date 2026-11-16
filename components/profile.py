
import streamlit as st
import textwrap
import html

from database import SessionLocal, User


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
# HELPER FUNCTIONS
# =====================================

def format_middle_initial(middle_name):

    if not middle_name:
        return ""

    middle_name = middle_name.strip()

    if not middle_name:
        return ""

    return middle_name[0].upper() + "."


def show_profile():

    st.title("My Profile")

    st.write(
        "View and manage your registered student information."
    )

    user_id = st.session_state.get("user_id")

    if not user_id:
        st.error("Please log in again.")
        return

    if "edit_profile_mode" not in st.session_state:
        st.session_state.edit_profile_mode = False

    db = SessionLocal()

    try:

        # =====================================
        # GET STUDENT INFORMATION
        # =====================================

        student = db.query(User).filter(
            User.id == user_id
        ).first()

        if not student:
            st.error("Student account not found.")
            return

        middle_initial = format_middle_initial(
            student.middle_name
        )

        full_name = (
            f"{student.last_name}, "
            f"{student.first_name} "
            f"{middle_initial}"
        ).strip()

        safe_full_name = html.escape(full_name)

        # =====================================
        # STUDENT PROFILE CARD
        # =====================================

        profile_html = textwrap.dedent(f"""
        <div style="
            background: linear-gradient(135deg, #3B0D1A, #711D32);
            border: 2px solid #F5D987;
            border-radius: 18px;
            padding: 30px;
            color: white;
            margin-bottom: 20px;
            box-shadow: 0 10px 25px rgba(59, 13, 26, 0.22);
        ">
            <div style="
                color: #F5D987;
                font-size: 13px;
                font-weight: 800;
                letter-spacing: 2px;
            ">
                STUDENT PROFILE
            </div>

            <div style="
                color: white;
                font-size: 27px;
                font-weight: 900;
                margin-top: 10px;
            ">
                {safe_full_name}
            </div>

            <div style="
                color: #F5D987;
                font-size: 13px;
                margin-top: 6px;
            ">
                University of Mindanao - Tagum College
            </div>
        </div>
        """)

        st.html(profile_html)

        # =====================================
        # PERSONAL INFORMATION
        # =====================================

        st.subheader("Personal Information")

        st.text_input(
            "First Name",
            value=student.first_name or "",
            disabled=True,
            key="profile_first_name"
        )

        st.text_input(
            "Middle Name",
            value=student.middle_name or "",
            disabled=True,
            key="profile_middle_name"
        )

        st.text_input(
            "Last Name",
            value=student.last_name or "",
            disabled=True,
            key="profile_last_name"
        )

        st.text_input(
            "Student ID",
            value=student.student_id or "",
            disabled=True,
            key="profile_student_id"
        )

        st.text_input(
            "Course / Program",
            value=student.course or "Not specified",
            disabled=True,
            key="profile_course"
        )

        st.text_input(
            "Year Level",
            value=student.year_level or "Not specified",
            disabled=True,
            key="profile_year_level"
        )

        st.divider()

        # =====================================
        # ACCOUNT INFORMATION
        # =====================================

        st.subheader("Account Information")

        st.text_input(
            "UM Institutional Email",
            value=student.email or "",
            disabled=True,
            key="profile_email"
        )

        col1, col2 = st.columns(2)

        with col1:

            st.text_input(
                "Account Role",
                value=(student.role or "").title(),
                disabled=True,
                key="profile_role"
            )

        with col2:

            account_status = (
                "Active" if student.is_active else "Inactive"
            )

            st.text_input(
                "Account Status",
                value=account_status,
                disabled=True,
                key="profile_status"
            )

        if student.created_at:

            st.text_input(
                "Date Registered",
                value=student.created_at.strftime("%B %d, %Y"),
                disabled=True,
                key="profile_created_at"
            )

        st.divider()

        # =====================================
        # EDIT PROFILE BUTTON
        # =====================================

        if not st.session_state.edit_profile_mode:

            if st.button(
                "Edit Profile",
                use_container_width=True
            ):

                st.session_state.edit_profile_mode = True
                st.rerun()

        # =====================================
        # EDIT PROFILE FORM
        # =====================================

        if st.session_state.edit_profile_mode:

            st.subheader("Edit Profile")

            st.caption(
                "Update your personal and academic information."
            )

            # Preserve existing values even if they are
            # not included in the current dropdown options.

            course_options = ["Select Course / Program"]

            if student.course and student.course not in COURSE_OPTIONS:
                course_options.append(student.course)

            course_options.extend(COURSE_OPTIONS)

            year_options = ["Select Year Level"]

            if student.year_level and student.year_level not in YEAR_OPTIONS:
                year_options.append(student.year_level)

            year_options.extend(YEAR_OPTIONS)

            current_course = student.course or ""
            current_year = student.year_level or ""

            course_index = (
                course_options.index(current_course)
                if current_course in course_options
                else 0
            )

            year_index = (
                year_options.index(current_year)
                if current_year in year_options
                else 0
            )

            with st.form("edit_profile_form"):

                new_first_name = st.text_input(
                    "First Name",
                    value=student.first_name or ""
                )

                new_middle_name = st.text_input(
                    "Middle Name",
                    value=student.middle_name or ""
                )

                new_last_name = st.text_input(
                    "Last Name",
                    value=student.last_name or ""
                )

                new_course = st.selectbox(
                    "Course / Program",
                    options=course_options,
                    index=course_index
                )

                new_year_level = st.selectbox(
                    "Year Level",
                    options=year_options,
                    index=year_index
                )

                submitted = st.form_submit_button(
                    "Save Changes",
                    use_container_width=True
                )

            if submitted:

                # =====================================
                # VALIDATION
                # =====================================

                if (
                    not new_first_name.strip()
                    or not new_last_name.strip()
                ):

                    st.error(
                        "First Name and Last Name are required."
                    )

                elif new_course == "Select Course / Program":

                    st.error(
                        "Please select your Course / Program."
                    )

                elif new_year_level == "Select Year Level":

                    st.error(
                        "Please select your Year Level."
                    )

                else:

                    try:

                        # =====================================
                        # UPDATE DATABASE
                        # =====================================

                        student.first_name = new_first_name.strip()
                        student.middle_name = new_middle_name.strip()
                        student.last_name = new_last_name.strip()
                        student.course = new_course
                        student.year_level = new_year_level

                        db.commit()

                        # =====================================
                        # UPDATE SESSION INFORMATION
                        # =====================================

                        st.session_state["user_course"] = new_course
                        st.session_state["user_year_level"] = new_year_level

                        st.session_state.edit_profile_mode = False

                        st.success(
                            "Profile updated successfully!"
                        )

                        st.rerun()

                    except Exception as e:

                        db.rollback()

                        st.error(
                            "Unable to save profile changes."
                        )

                        print("Save Profile Error:", e)

            # =====================================
            # CANCEL BUTTON
            # =====================================

            if st.button(
                "Cancel",
                use_container_width=True
            ):

                st.session_state.edit_profile_mode = False
                st.rerun()

        # =====================================
        # PROFILE FOOTER
        # =====================================

        st.caption(
            "Student ID and institutional email cannot be edited here."
        )

    except Exception as e:

        db.rollback()

        st.error("Unable to load your profile.")

        print("Profile Error:", e)

    finally:

        db.close()
