
import streamlit as st
from pathlib import Path

from database import SessionLocal, User

from components.authentication import (
    show_authentication,
    logout_user
)

from components.notifications import show_notifications
from components.student_dashboard import show_student_dashboard
from components.document_request import show_document_request
from components.track_request import show_track_request
from components.request_history import show_request_history
from components.payment_page import show_payments
from components.queue_number import show_queue_number
from components.profile import show_profile


# =====================================
# PAGE CONFIGURATION
# =====================================

st.set_page_config(
    page_title="UMTC Student Portal",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)


# =====================================
# LOAD GLOBAL CSS
# =====================================

def load_global_css():

    css_path = (
        Path(__file__).resolve().parent
        / "assets"
        / "style.css"
    )

    if css_path.exists():

        css = css_path.read_text(encoding="utf-8")

        st.markdown(
            f"<style>{css}</style>",
            unsafe_allow_html=True
        )

    else:
        st.warning("Global design stylesheet was not found.")


# =====================================
# STUDENT PORTAL DESIGN
# =====================================

def load_app_design():

    st.markdown(
        """
        <style>

        .sidebar-brand {
            background: linear-gradient(
                145deg,
                #842640,
                #3B0D1A
            );
            padding: 20px 14px;
            border-radius: 17px;
            border: 1px solid #D8AE4B;
            text-align: center;
            box-shadow:
                0 7px 0 rgba(25, 4, 12, 0.2),
                0 14px 25px rgba(0, 0, 0, 0.25);
            margin-bottom: 24px;
        }

        .sidebar-brand .brand-icon {
            font-size: 36px;
            margin-bottom: 8px;
        }

        .sidebar-brand h2 {
            color: #F5D987 !important;
            font-size: 19px;
            margin: 0;
            font-weight: 850;
        }

        .sidebar-brand p {
            color: #FFF9EF !important;
            font-size: 11px;
            margin-top: 6px;
            margin-bottom: 0;
            letter-spacing: 1px;
        }

        .portal-banner {
            position: relative;
            overflow: hidden;
            background: linear-gradient(
                120deg,
                #842640,
                #4A1021,
                #310A17
            );
            border: 1px solid rgba(245, 217, 135, 0.65);
            border-radius: 22px;
            padding: 27px 30px;
            margin-bottom: 25px;
            box-shadow:
                0 8px 0 rgba(25, 4, 12, 0.18),
                0 18px 32px rgba(0, 0, 0, 0.24);
        }

        .portal-banner::after {
            content: "";
            position: absolute;
            width: 180px;
            height: 180px;
            right: -50px;
            top: -65px;
            border-radius: 50%;
            border: 25px solid rgba(245, 217, 135, 0.08);
        }

        .portal-banner .eyebrow {
            color: #F5D987;
            font-size: 11px;
            font-weight: 800;
            letter-spacing: 2px;
            margin-bottom: 8px;
        }

        .portal-banner h1 {
            color: #FFF9EF !important;
            font-size: 27px;
            font-weight: 850;
            margin: 0;
        }

        .portal-banner p {
            color: #F5EBDD !important;
            font-size: 13px;
            margin-top: 7px;
            margin-bottom: 0;
        }

        section[data-testid="stSidebar"] hr {
            border-color: rgba(216, 174, 75, 0.4);
        }

        </style>
        """,
        unsafe_allow_html=True
    )


# =====================================
# STUDENT BRAND
# =====================================

def show_student_brand():

    st.sidebar.markdown(
        """
        <div class="sidebar-brand">
            <div class="brand-icon">🎓</div>
            <h2>UMTC STUDENT</h2>
            <p>STUDENT PORTAL</p>
        </div>
        """,
        unsafe_allow_html=True
    )


# =====================================
# STUDENT HEADER
# =====================================

def show_student_header():

    st.markdown(
        """
        <div class="portal-banner">
            <div class="eyebrow">
                UNIVERSITY OF MINDANAO · TAGUM COLLEGE
            </div>
            <h1>Student Portal</h1>
            <p>
                Request academic documents and monitor
                your request progress.
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )


# =====================================
# VERIFY STUDENT ACCOUNT
# =====================================

def get_authenticated_student():

    user_id = st.session_state.get("user_id")

    if not user_id:
        return None

    with SessionLocal() as db:

        student = db.query(User).filter_by(
            id=user_id,
            role="student",
            is_active=True
        ).first()

        if student is None:
            return None

        return {
            "id": student.id,
            "name": (
                f"{student.first_name} "
                f"{student.last_name}"
            ),
            "email": student.email,
            "role": student.role
        }


# =====================================
# CLEAR INVALID SESSION
# =====================================

def clear_invalid_session():

    session_keys = [
        "logged_in",
        "user_id",
        "user_name",
        "user_role",
        "user_email",
        "user_course",
        "user_year_level"
    ]

    for key in session_keys:

        st.session_state.pop(key, None)


# =====================================
# MAIN STUDENT APPLICATION
# =====================================

def main():

    load_global_css()
    load_app_design()

    # Show student login if not logged in
    if not st.session_state.get("logged_in", False):

        show_authentication()
        st.stop()

    # Verify account directly from database
    student = get_authenticated_student()

    if student is None:

        clear_invalid_session()

        st.error(
            "Access denied. This portal is only for "
            "active student accounts."
        )

        show_authentication()
        st.stop()

    # Student portal interface
    show_student_brand()
    show_student_header()

    student_menu = st.sidebar.radio(
        "STUDENT NAVIGATION",
        [
            "Dashboard",
            "Request a Document",
            "My Queue Number",
            "Track My Request",
            "Request History",
            "Payments",
            "Notifications",
            "My Profile",
            "Help and Guidelines"
        ]
    )

    st.sidebar.divider()

    st.sidebar.caption(
        f"Logged in as: {student['name']}"
    )

    if st.sidebar.button(
        "Logout",
        use_container_width=True
    ):

        logout_user()
        return

    # =================================
    # STUDENT PAGE ROUTING
    # =================================

    if student_menu == "Dashboard":

        show_student_dashboard()

    elif student_menu == "Request a Document":

        show_document_request()

    elif student_menu == "My Queue Number":

        show_queue_number()

    elif student_menu == "Track My Request":

        show_track_request()

    elif student_menu == "Request History":

        show_request_history()

    elif student_menu == "Payments":

        show_payments()

    elif student_menu == "Notifications":

        show_notifications()

    elif student_menu == "My Profile":

        show_profile()

    elif student_menu == "Help and Guidelines":

        st.title("Help and Guidelines")

        st.info(
            "This section provides instructions for "
            "submitting document requests, checking "
            "payments, and monitoring queue updates."
        )


# =====================================
# RUN APPLICATION
# =====================================

if __name__ == "__main__":

    main()
