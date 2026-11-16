
import streamlit as st
from pathlib import Path

from database import (
    SessionLocal,
    User,
    DocumentRequest,
    Payment
)
from components.admin_account_management import show_admin_account_management
from components.admin_reports import show_admin_reports
from components.admin_login import show_admin_login
from components.authentication import logout_user
from components.request_verification import show_request_verification
from components.admin_now_serving import show_admin_now_serving
from components.admin_queue_management import show_admin_queue_management
from components.admin_payment_management import show_admin_payment_management
from components.admin_requests import show_admin_requests
from components.document_release import show_document_release


# =====================================
# PAGE CONFIGURATION
# =====================================

st.set_page_config(
    page_title="UMTC Admin Portal",
    page_icon="🛡️",
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


# =====================================
# ADMIN PORTAL DESIGN
# =====================================

def load_admin_design():

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
            box-shadow: 0 12px 25px rgba(0,0,0,0.20);
            margin-bottom: 24px;
        }

        .sidebar-brand h2 {
            color: #F5D987 !important;
            font-size: 19px;
            font-weight: 850;
            margin: 0;
        }

        .sidebar-brand p {
            color: #FFF9EF !important;
            font-size: 11px;
            letter-spacing: 1px;
            margin-bottom: 0;
        }

        .portal-banner {
            background: linear-gradient(
                120deg,
                #842640,
                #4A1021,
                #310A17
            );
            border: 1px solid #D8AE4B;
            border-radius: 22px;
            padding: 27px 30px;
            margin-bottom: 25px;
            box-shadow: 0 12px 28px rgba(0,0,0,0.18);
        }

        .portal-banner .eyebrow {
            color: #F5D987;
            font-size: 11px;
            font-weight: 800;
            letter-spacing: 2px;
        }

        .portal-banner h1 {
            color: #FFF9EF !important;
            font-size: 27px;
            font-weight: 850;
            margin: 8px 0;
        }

        .portal-banner p {
            color: #F5EBDD !important;
            font-size: 13px;
            margin-bottom: 0;
        }

        .section-label {
            color: #842640;
            font-size: 12px;
            font-weight: 800;
            letter-spacing: 1.5px;
            margin-bottom: 10px;
        }

        section[data-testid="stSidebar"] hr {
            border-color: rgba(216, 174, 75, 0.5);
        }

        </style>
        """,
        unsafe_allow_html=True
    )


# =====================================
# SIDEBAR BRAND
# =====================================

def show_sidebar_brand():

    st.sidebar.markdown(
        """
        <div class="sidebar-brand">
            <div style="font-size:36px;">🛡️</div>
            <h2>UMTC ADMIN</h2>
            <p>ADMINISTRATION PORTAL</p>
        </div>
        """,
        unsafe_allow_html=True
    )


# =====================================
# PORTAL HEADER
# =====================================

def show_portal_header():

    st.markdown(
        """
        <div class="portal-banner">
            <div class="eyebrow">
                UNIVERSITY OF MINDANAO · TAGUM COLLEGE
            </div>
            <h1>Admin Dashboard</h1>
            <p>
                Manage student document requests, payments,
                queues, and document releases.
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )


# =====================================
# VERIFY ADMIN ACCOUNT
# =====================================

def get_authenticated_admin():

    user_id = st.session_state.get("user_id")

    if not user_id:
        return None

    with SessionLocal() as db:

        admin = db.query(User).filter_by(
            id=user_id,
            role="admin",
            is_active=True
        ).first()

        if admin:
            return {
                "id": admin.id,
                "name": f"{admin.first_name} {admin.last_name}",
                "email": admin.email
            }

    return None


# =====================================
# REQUEST STATUS DISPLAY
# =====================================

def show_request_status(status):

    if status == "Released":
        st.success(status)

    elif status == "Rejected":
        st.error(status)

    elif status == "Cancelled":
        st.error(status)

    elif status == "Ready for Claiming":
        st.info(status)

    elif status in [
        "Processing",
        "Waiting in Queue"
    ]:
        st.warning(status)

    else:
        st.info(status)


# =====================================
# ADMIN DASHBOARD
# =====================================

def show_admin_dashboard():

    st.title("Overview")

    st.caption(
        "Monitor the current document request operations."
    )

    with SessionLocal() as db:

        # REQUEST STATISTICS

        total_requests = db.query(
            DocumentRequest
        ).count()

        pending_requests = db.query(
            DocumentRequest
        ).filter(
            DocumentRequest.request_status.in_([
                "Submitted",
                "Under Review",
                "Pending Requirements"
            ])
        ).count()

        processing_requests = db.query(
            DocumentRequest
        ).filter(
            DocumentRequest.request_status.in_([
                "Processing",
                "Waiting in Queue",
                "Ready for Claiming"
            ])
        ).count()

        released_requests = db.query(
            DocumentRequest
        ).filter(
            DocumentRequest.request_status == "Released"
        ).count()

        awaiting_payments = db.query(
            Payment
        ).filter(
            Payment.payment_status == "Awaiting Verification"
        ).count()

        # DISPLAY STATISTICS

        st.markdown(
            '<div class="section-label">REQUEST STATISTICS</div>',
            unsafe_allow_html=True
        )

        col1, col2, col3 = st.columns(3)

        col1.metric(
            "Total Requests",
            total_requests
        )

        col2.metric(
            "Pending Requests",
            pending_requests
        )

        col3.metric(
            "Processing",
            processing_requests
        )

        col4, col5 = st.columns(2)

        col4.metric(
            "Released Documents",
            released_requests
        )

        col5.metric(
            "Payments for Verification",
            awaiting_payments
        )

        st.divider()

        # RECENT DOCUMENT REQUESTS

        st.subheader("Recent Document Requests")

        recent_requests = (
            db.query(DocumentRequest)
            .order_by(
                DocumentRequest.submitted_at.desc()
            )
            .limit(10)
            .all()
        )

        if not recent_requests:

            st.info(
                "No document requests available."
            )

        else:

            for request in recent_requests:

                student = request.student

                student_name = "Unknown Student"

                if student:

                    student_name = (
                        f"{student.first_name or ''} "
                        f"{student.last_name or ''}"
                    ).strip()

                request_number = (
                    request.request_number or "N/A"
                )

                document_type = (
                    request.document_type or "N/A"
                )

                status = (
                    request.request_status or "N/A"
                )

                with st.container(border=True):

                    st.markdown(
                        f"**Request Number:** `{request_number}`"
                    )

                    col1, col2 = st.columns(2)

                    with col1:

                        st.caption("STUDENT")
                        st.write(student_name)

                    with col2:

                        st.caption("DOCUMENT")
                        st.write(document_type)

                    st.caption("REQUEST STATUS")
                    show_request_status(status)


# =====================================
# ADMIN APPLICATION
# =====================================

def main():

    load_global_css()
    load_admin_design()

    # VERIFY ADMIN ACCOUNT

    admin = get_authenticated_admin()

    if not admin:

        for key in [
            "logged_in",
            "user_id",
            "user_name",
            "user_role",
            "user_email",
            "user_course",
            "user_year_level"
        ]:

            st.session_state.pop(key, None)

        show_admin_login()
        st.stop()

    # ADMIN INTERFACE

    show_sidebar_brand()
    show_portal_header()

    st.sidebar.write(
        f"Welcome, **{admin['name']}**"
    )

    admin_menu = st.sidebar.radio(
        "ADMIN NAVIGATION",
        [
            "Dashboard",
            "All Requests",
            "Queue Management",
            "Now Serving",
            "Request Verification",
            "Payment Management",
            "Document Release",
            "Reports and Analytics",
            "Account Management"
        ]
    )

    st.sidebar.divider()

    if st.sidebar.button(
        "Logout",
        use_container_width=True
    ):

        logout_user()
        st.rerun()

    # =================================
    # ADMIN PAGE ROUTING
    # =================================

    if admin_menu == "Dashboard":

        show_admin_dashboard()

    elif admin_menu == "All Requests":

        show_admin_requests()

    elif admin_menu == "Queue Management":

        show_admin_queue_management()

    elif admin_menu == "Now Serving":

        show_admin_now_serving()

    elif admin_menu == "Request Verification":

        show_request_verification()

    elif admin_menu == "Payment Management":

        show_admin_payment_management()

    elif admin_menu == "Document Release":

        show_document_release()

    elif admin_menu == "Reports and Analytics":

        show_admin_reports()

    elif admin_menu == "Activity Logs":

        st.title("Activity Logs")
        st.info(
            "The Activity Logs module will be developed "
            "in the next stage."
        )

    elif admin_menu == "Account Management":
        show_admin_account_management()

        st.title("Account Management")
        st.info(
            "The Account Management module will be developed "
            "in the next stage."
        )


# =====================================
# RUN ADMIN APPLICATION
# =====================================

if __name__ == "__main__":

    main()
