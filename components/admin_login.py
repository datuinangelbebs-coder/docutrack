
import streamlit as st

from werkzeug.security import check_password_hash
from database import SessionLocal, User


def admin_login(email, password):

    email = email.strip().lower()

    if not email or not password:
        return False, "Please complete all fields."

    with SessionLocal() as db:

        admin = db.query(User).filter_by(
            email=email,
            role="admin",
            is_active=True
        ).first()

        if not admin:
            return False, "Invalid admin email or password."

        if not check_password_hash(
            admin.password_hash,
            password
        ):
            return False, "Invalid admin email or password."

        st.session_state["logged_in"] = True
        st.session_state["user_id"] = admin.id
        st.session_state["user_name"] = (
            f"{admin.first_name} {admin.last_name}"
        )
        st.session_state["user_role"] = "admin"
        st.session_state["user_email"] = admin.email

    return True, "Admin login successful!"


def show_admin_login():

    st.markdown(
        """
        <style>
        .admin-login-banner {
            background: linear-gradient(135deg, #842640, #3B0D1A);
            padding: 35px;
            border-radius: 20px;
            text-align: center;
            border: 1px solid #D8AE4B;
            margin-bottom: 25px;
        }

        .admin-login-banner h1 {
            color: #F5D987;
            font-size: 30px;
            font-weight: 850;
        }

        .admin-login-banner p {
            color: #FFF9EF;
            font-size: 14px;
        }
        </style>

        <div class="admin-login-banner">
            <h1>UMTC ADMIN PORTAL</h1>
            <p>Registrar Administration and Management System</p>
        </div>
        """,
        unsafe_allow_html=True
    )

    left, right = st.columns([1.1, 1])

    with left:

        st.markdown("## Welcome, Administrator")

        st.write(
            "Access the administration portal to manage "
            "student document requests, payments, queues, "
            "and document releases."
        )

        st.info(
            "Authorized Registrar and administrative personnel only."
        )

    with right:

        st.subheader("Admin Login")

        with st.form("admin_login_form"):

            email = st.text_input(
                "UM Institutional Email",
                placeholder="Enter your admin email"
            )

            password = st.text_input(
                "Password",
                type="password"
            )

            login_button = st.form_submit_button(
                "ADMIN LOGIN",
                use_container_width=True
            )

            if login_button:

                success, message = admin_login(
                    email,
                    password
                )

                if success:
                    st.success(message)
                    st.rerun()

                else:
                    st.error(message)
