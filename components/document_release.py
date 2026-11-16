
import streamlit as st
from datetime import datetime

from database import (
    SessionLocal,
    DocumentRequest,
    ActivityLog,
    User
)


# =====================================
# ADMIN INFORMATION
# =====================================

def get_current_admin(db):

    admin_id = st.session_state.get("user_id")

    if not admin_id:
        return None

    return (
        db.query(User)
        .filter(
            User.id == admin_id,
            User.role == "admin",
            User.is_active == True
        )
        .first()
    )


# =====================================
# WELCOME BANNER
# =====================================

def show_welcome_banner():

    with st.container(border=True):

        st.caption("UNIVERSITY OF MINDANAO · TAGUM COLLEGE")

        st.title("Document Release Management")

        st.write(
            "Manage, monitor, and record student academic "
            "document releases."
        )

        st.caption(
            "Ensure every released document has a recorded "
            "recipient and confirmation."
        )


# =====================================
# SUMMARY CARD
# =====================================

def show_summary_card(label, value, description):

    with st.container(border=True):

        st.caption(label)

        st.metric(
            label="",
            value=value,
            label_visibility="collapsed"
        )

        st.caption(description)


# =====================================
# PAYMENT ELIGIBILITY
# =====================================

def is_payment_eligible(request):

    payment = request.payment

    if not payment:
        return False

    return payment.payment_status in [
        "Verified",
        "Paid On-site"
    ]


# =====================================
# MAIN DOCUMENT RELEASE
# =====================================

def show_document_release():

    # =================================
    # ADMIN ACCESS CHECK
    # =================================

    if st.session_state.get("user_role") != "admin":

        st.error("Admin access only.")
        return

    db = SessionLocal()

    try:

        admin = get_current_admin(db)

        if not admin:

            st.error(
                "Admin account could not be verified. "
                "Please log in again."
            )
            return

        admin_name = (
            f"{admin.first_name or ''} "
            f"{admin.last_name or ''}"
        ).strip()

        admin_name = admin_name or admin.email

        # =================================
        # WELCOME BANNER
        # =================================

        show_welcome_banner()

        st.divider()

        # =================================
        # GET REQUESTS
        # =================================

        all_requests = (
            db.query(DocumentRequest)
            .filter(
                DocumentRequest.request_status.in_([
                    "Ready for Claiming",
                    "Released"
                ])
            )
            .order_by(
                DocumentRequest.submitted_at.desc()
            )
            .all()
        )

        # Only requests with verified payments
        requests = [
            request
            for request in all_requests
            if is_payment_eligible(request)
        ]

        ready_count = sum(
            1 for request in requests
            if request.request_status == "Ready for Claiming"
        )

        released_count = sum(
            1 for request in requests
            if request.request_status == "Released"
        )

        total_requests = len(requests)

        # =================================
        # RELEASE OVERVIEW
        # =================================

        st.subheader("Release Overview")

        col1, col2, col3 = st.columns(3)

        with col1:

            show_summary_card(
                "TOTAL REQUESTS",
                total_requests,
                "Eligible document requests"
            )

        with col2:

            show_summary_card(
                "READY FOR CLAIMING",
                ready_count,
                "Waiting for collection"
            )

        with col3:

            show_summary_card(
                "RELEASED DOCUMENTS",
                released_count,
                "Successfully handed over"
            )

        st.divider()

        # =================================
        # SEARCH AND FILTER
        # =================================

        st.subheader("Document Release Records")

        st.caption(
            "Search and manage student document release transactions."
        )

        col1, col2 = st.columns([2, 1])

        with col1:

            search = st.text_input(
                "Search Document Request",
                placeholder=(
                    "Request number, student name, "
                    "student ID, or document type..."
                ),
                key="release_search"
            )

        with col2:

            selected_status = st.selectbox(
                "Release Status",
                [
                    "All Records",
                    "Ready for Claiming",
                    "Released"
                ],
                key="release_status_filter"
            )

        # =================================
        # FILTER REQUESTS
        # =================================

        filtered_requests = []

        for request in requests:

            student = request.student

            student_name = ""

            if student:

                student_name = (
                    f"{student.first_name or ''} "
                    f"{student.last_name or ''}"
                ).strip()

            searchable_text = (
                f"{request.request_number or ''} "
                f"{student_name} "
                f"{request.student_id or ''} "
                f"{request.document_type or ''} "
                f"{request.released_to or ''}"
            ).lower()

            if search.strip().lower() not in searchable_text:
                continue

            if (
                selected_status != "All Records"
                and request.request_status != selected_status
            ):
                continue

            filtered_requests.append(request)

        st.caption(
            f"Showing {len(filtered_requests)} "
            f"of {total_requests} eligible records"
        )

        st.divider()

        if not filtered_requests:

            st.info(
                "No eligible document requests found."
            )
            return

        # =================================
        # DISPLAY REQUESTS
        # =================================

        for request in filtered_requests:

            student = request.student
            payment = request.payment

            student_name = "Unknown Student"
            student_email = "Not available"

            if student:

                student_name = (
                    f"{student.first_name or ''} "
                    f"{student.last_name or ''}"
                ).strip()

                student_email = student.email or "Not available"

            with st.container(border=True):

                # REQUEST HEADER

                col1, col2 = st.columns([3, 1])

                with col1:

                    st.subheader(
                        f"Request #{request.request_number}"
                    )

                    st.write(f"**Student:** {student_name}")
                    st.write(f"**Student Email:** {student_email}")
                    st.write(f"**Student ID:** {student.student_id if student else 'Not available'}")
                    st.write(f"**Document:** {request.document_type}")
                    st.write(f"**Copies:** {request.copies}")

                    st.write(
                        f"**Total Fee:** "
                        f"₱{float(request.total_fee or 0):,.2f}"
                    )

                    st.write(
                        f"**Payment Status:** "
                        f"{payment.payment_status}"
                    )

                with col2:

                    if request.request_status == "Released":

                        st.success("RELEASED")

                    else:

                        st.warning("READY FOR CLAIMING")

                    st.write(
                        f"**Queue Number:** "
                        f"{request.queue_number or 'Not assigned'}"
                    )

                st.divider()

                # =================================
                # RELEASE FORM
                # =================================

                if request.request_status == "Ready for Claiming":

                    with st.expander("Record Document Release"):

                        with st.form(
                            key=f"release_form_{request.id}"
                        ):

                            recipient_name = st.text_input(
                                "Name of Person Receiving Document",
                                placeholder="Enter complete recipient name"
                            )

                            recipient_type = st.selectbox(
                                "Recipient Type",
                                [
                                    "Requesting Student",
                                    "Authorized Representative"
                                ]
                            )

                            confirmed = st.checkbox(
                                "I confirm that the document "
                                "has actually been handed over."
                            )

                            submitted = st.form_submit_button(
                                "Confirm Document Release",
                                type="primary",
                                use_container_width=True
                            )

                            if submitted:

                                if not recipient_name.strip():

                                    st.error(
                                        "Please enter the recipient's name."
                                    )

                                elif len(recipient_name.strip()) < 2:

                                    st.error(
                                        "Please enter a valid recipient name."
                                    )

                                elif not confirmed:

                                    st.error(
                                        "Please confirm the actual handover."
                                    )

                                else:

                                    try:

                                        db.refresh(request)

                                        if (
                                            request.request_status
                                            != "Ready for Claiming"
                                        ):

                                            st.warning(
                                                "This request has already "
                                                "been updated."
                                            )

                                        elif not is_payment_eligible(request):

                                            st.error(
                                                "Payment is not verified. "
                                                "This document cannot be released."
                                            )

                                        else:

                                            release_time = datetime.now()

                                            request.released_to = (
                                                recipient_name.strip()
                                            )

                                            request.released_at = release_time
                                            request.released_by = admin_name
                                            request.request_status = "Released"
                                            request.updated_at = release_time

                                            log = ActivityLog(
                                                user_id=admin.id,
                                                action="Document Released",
                                                details=(
                                                    f"Request "
                                                    f"{request.request_number} "
                                                    f"released to "
                                                    f"{recipient_name.strip()}. "
                                                    f"Recipient type: "
                                                    f"{recipient_type}. "
                                                    f"Released by: {admin_name}."
                                                )
                                            )

                                            db.add(log)
                                            db.commit()

                                            st.success(
                                                "Document release "
                                                "recorded successfully!"
                                            )

                                            st.rerun()

                                    except Exception as e:

                                        db.rollback()

                                        st.error(
                                            f"Unable to record release: {e}"
                                        )

                # =================================
                # RELEASE INFORMATION
                # =================================

                elif request.request_status == "Released":

                    st.success(
                        "This document has already been released."
                    )

                    st.markdown("**Release Confirmation**")

                    col1, col2 = st.columns(2)

                    with col1:

                        st.write(
                            f"**Received By:** "
                            f"{request.released_to or 'Not recorded'}"
                        )

                    with col2:

                        st.write(
                            f"**Released By:** "
                            f"{request.released_by or 'Not recorded'}"
                        )

                    if request.released_at:

                        st.write(
                            "**Release Date and Time:** "
                            f"{request.released_at.strftime('%B %d, %Y at %I:%M %p')}"
                        )

    except Exception as e:

        st.error("Unable to load document releases.")
        st.exception(e)

    finally:

        db.close()
