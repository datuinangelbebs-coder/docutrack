
import streamlit as st

from datetime import datetime

from database import (
    SessionLocal,
    DocumentRequest,
    Payment,
    ActivityLog
)


# =====================================
# REQUEST STATUS OPTIONS
# =====================================

REQUEST_STATUSES = [
    "Submitted",
    "Under Review",
    "Pending Requirements",
    "Approved",
    "Waiting in Queue",
    "Processing",
    "Ready for Claiming",
    "Released",
    "Rejected",
    "Cancelled"
]


# =====================================
# PAGE DESIGN
# =====================================

def load_admin_requests_style():

    st.markdown(
        """
        <style>

        .requests-header {
            background: linear-gradient(
                120deg,
                #3B0D1A,
                #711D32
            );
            padding: 30px;
            border-radius: 18px;
            color: #FFF9EF;
            margin-bottom: 25px;
        }

        .requests-header h1 {
            color: #FFF9EF !important;
            font-size: 29px;
        }

        .requests-header p {
            color: #F1DDE0;
            margin: 0;
        }

        .section-heading {
            color: #3B0D1A;
            font-size: 21px;
            font-weight: 700;
            margin-top: 12px;
        }

        </style>
        """,
        unsafe_allow_html=True
    )


# =====================================
# SUMMARY CARD
# =====================================

def summary_card(label, value):

    with st.container(border=True):

        st.caption(label)

        st.metric(
            label="",
            value=value,
            label_visibility="collapsed"
        )


# =====================================
# STATUS DISPLAY
# =====================================

def display_status(status):

    status = (status or "Unknown").strip()

    normalized = status.lower()

    if normalized in ["released", "approved"]:
        st.success(status)

    elif normalized in ["rejected", "cancelled"]:
        st.error(status)

    elif normalized in [
        "processing",
        "ready for claiming"
    ]:
        st.info(status)

    else:
        st.warning(status)


# =====================================
# SAVE REQUEST STATUS
# =====================================

def save_request_status(
    request_id,
    selected_status,
    admin_id
):

    db_update = SessionLocal()

    try:

        target = (
            db_update.query(DocumentRequest)
            .filter(
                DocumentRequest.id == request_id
            )
            .first()
        )

        if target is None:

            return False, "Request record could not be found."

        old_status = (
            target.request_status or "Submitted"
        ).strip()

        new_status = selected_status.strip()

        # Check if the selected status is unchanged
        if old_status == new_status:

            return False, (
                f"The request is already marked as "
                f"'{old_status}'. No changes were made."
            )

        # Update request
        target.request_status = new_status
        target.updated_at = datetime.now()

        # Record activity
        log = ActivityLog(
            user_id=admin_id,
            action="Updated Document Request Status",
            details=(
                f"Request {target.request_number}: "
                f"{old_status} → {new_status}"
            )
        )

        db_update.add(log)

        db_update.commit()

        db_update.refresh(target)

        # Verify database update
        if target.request_status != new_status:

            return False, (
                "Database verification failed after saving."
            )

        return True, (
            f"Request status successfully changed "
            f"from {old_status} to {new_status}."
        )

    except Exception as e:

        db_update.rollback()

        return False, f"Database error: {e}"

    finally:

        db_update.close()


# =====================================
# ADMIN REQUESTS PAGE
# =====================================

def show_admin_requests():

    load_admin_requests_style()

    # ---------------------------------
    # ADMIN ACCESS CHECK
    # ---------------------------------

    if st.session_state.get("user_role") != "admin":

        st.error(
            "Access denied. Admin account required."
        )

        st.stop()

    admin_id = st.session_state.get("user_id")

    # ---------------------------------
    # SUCCESS MESSAGE AFTER SAVE
    # ---------------------------------

    saved_message = st.session_state.pop(
        "request_status_flash",
        None
    )

    if saved_message:

        st.success(saved_message)

    db = SessionLocal()

    try:

        # ---------------------------------
        # FETCH ALL REQUESTS
        # ---------------------------------

        requests = (
            db.query(DocumentRequest)
            .order_by(
                DocumentRequest.submitted_at.desc()
            )
            .all()
        )

        total_requests = len(requests)

        pending_requests = sum(
            1 for r in requests
            if (r.request_status or "").strip().lower()
            in [
                "submitted",
                "under review",
                "pending requirements"
            ]
        )

        processing_requests = sum(
            1 for r in requests
            if (r.request_status or "").strip().lower()
            in [
                "processing",
                "waiting in queue",
                "ready for claiming"
            ]
        )

        released_requests = sum(
            1 for r in requests
            if (r.request_status or "").strip().lower()
            == "released"
        )

        # ---------------------------------
        # PAGE HEADER
        # ---------------------------------

        st.markdown(
            """
            <div class="requests-header">
                <h1>Document Requests</h1>
                <p>
                    Manage, review, and monitor student
                    academic document requests.
                </p>
            </div>
            """,
            unsafe_allow_html=True
        )

        # ---------------------------------
        # REQUEST OVERVIEW
        # ---------------------------------

        st.markdown(
            '<div class="section-heading">Request Overview</div>',
            unsafe_allow_html=True
        )

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            summary_card(
                "Total Requests",
                total_requests
            )

        with col2:
            summary_card(
                "Pending",
                pending_requests
            )

        with col3:
            summary_card(
                "In Progress",
                processing_requests
            )

        with col4:
            summary_card(
                "Released",
                released_requests
            )

        st.write("")

        # ---------------------------------
        # SEARCH AND FILTER
        # ---------------------------------

        st.markdown(
            '<div class="section-heading">All Requests</div>',
            unsafe_allow_html=True
        )

        col_search, col_filter = st.columns([2, 1])

        with col_search:

            search_query = st.text_input(
                "Search Requests",
                placeholder=(
                    "Request number, student name, "
                    "or student ID..."
                ),
                key="admin_request_search"
            )

        with col_filter:

            selected_filter = st.selectbox(
                "Request Status",
                ["All Statuses"] + REQUEST_STATUSES,
                key="admin_request_filter"
            )

        # ---------------------------------
        # FILTER REQUESTS
        # ---------------------------------

        filtered_requests = []

        for request in requests:

            student = request.student

            student_name = ""
            student_number = ""

            if student:

                student_name = (
                    f"{student.first_name or ''} "
                    f"{student.last_name or ''}"
                ).strip()

                student_number = str(
                    student.student_id or ""
                )

            searchable_text = " ".join([
                str(request.request_number or ""),
                str(request.document_type or ""),
                student_name,
                student_number
            ]).lower()

            if search_query.strip().lower() not in searchable_text:
                continue

            request_status = (
                request.request_status or ""
            ).strip().lower()

            if selected_filter != "All Statuses":

                if request_status != selected_filter.lower():
                    continue

            filtered_requests.append(request)

        st.caption(
            f"Showing {len(filtered_requests)} "
            f"of {total_requests} requests"
        )

        st.divider()

        if not filtered_requests:

            st.info(
                "No document requests found."
            )

            return

        # ---------------------------------
        # DISPLAY REQUEST CARDS
        # ---------------------------------

        for request in filtered_requests:

            student = request.student
            payment = request.payment

            with st.container(border=True):

                # REQUEST HEADER
                col1, col2 = st.columns([2, 1])

                with col1:

                    st.markdown(
                        f"### {request.request_number or 'No Request Number'}"
                    )

                    st.caption(
                        request.document_type
                        or "Document not specified"
                    )

                with col2:

                    display_status(
                        request.request_status
                    )

                st.divider()

                # ---------------------------------
                # STUDENT INFORMATION
                # ---------------------------------

                st.markdown("**Student Information**")

                if student:

                    full_name = " ".join(
                        part for part in [
                            student.first_name,
                            student.middle_name,
                            student.last_name
                        ] if part
                    )

                    c1, c2, c3 = st.columns(3)

                    with c1:

                        st.caption("STUDENT NAME")

                        st.write(
                            full_name or "Not available"
                        )

                    with c2:

                        st.caption("STUDENT ID")

                        st.write(
                            student.student_id or "Not available"
                        )

                    with c3:

                        st.caption("EMAIL")

                        st.write(
                            student.email or "Not available"
                        )

                    c1, c2, c3 = st.columns(3)

                    with c1:

                        st.caption("COURSE")

                        st.write(
                            student.course or "Not specified"
                        )

                    with c2:

                        st.caption("YEAR LEVEL")

                        st.write(
                            student.year_level or "Not specified"
                        )

                    with c3:

                        st.caption("NUMBER OF COPIES")

                        st.write(
                            request.copies or 1
                        )

                else:

                    st.warning(
                        "Student information is unavailable."
                    )

                st.divider()

                # ---------------------------------
                # REQUEST DETAILS
                # ---------------------------------

                st.markdown("**Request Details**")

                c1, c2, c3 = st.columns(3)

                with c1:

                    st.caption("TOTAL FEE")

                    st.write(
                        f"₱{float(request.total_fee or 0):,.2f}"
                    )

                with c2:

                    st.caption("QUEUE NUMBER")

                    st.write(
                        request.queue_number or "Not assigned"
                    )

                with c3:

                    st.caption("DATE SUBMITTED")

                    if request.submitted_at:

                        st.write(
                            request.submitted_at.strftime(
                                "%b %d, %Y - %I:%M %p"
                            )
                        )

                    else:

                        st.write("Not available")

                # ---------------------------------
                # PAYMENT INFORMATION
                # ---------------------------------

                st.divider()

                st.markdown("**Payment Information**")

                if payment:

                    c1, c2, c3 = st.columns(3)

                    with c1:

                        st.caption("PAYMENT METHOD")

                        st.write(
                            payment.payment_method or "Not specified"
                        )

                    with c2:

                        st.caption("PAYMENT AMOUNT")

                        st.write(
                            f"₱{float(payment.amount or 0):,.2f}"
                        )

                    with c3:

                        st.caption("PAYMENT STATUS")

                        display_status(
                            payment.payment_status
                        )

                    st.caption("REFERENCE NUMBER")

                    st.write(
                        payment.reference_number or "Not available"
                    )

                    if payment.receipt_file:

                        st.success(
                            "Payment receipt submitted."
                        )

                    else:

                        st.info(
                            "No payment receipt submitted."
                        )

                else:

                    st.info(
                        "No payment record found."
                    )

                # ---------------------------------
                # MANAGE REQUEST STATUS
                # ---------------------------------

                st.divider()

                with st.expander("Manage Request Status"):

                    current_status = (
                        request.request_status or "Submitted"
                    ).strip()

                    status_options = REQUEST_STATUSES.copy()

                    # Preserve existing status if it is not
                    # included in the standard options.
                    if current_status not in status_options:

                        status_options.insert(
                            0,
                            current_status
                        )

                    new_status = st.selectbox(
                        "Update Status",
                        status_options,
                        index=status_options.index(current_status),
                        key=f"status_{request.id}"
                    )

                    if st.button(
                        "Save Status Update",
                        key=f"save_status_{request.id}",
                        type="primary",
                        use_container_width=True
                    ):

                        success, message = save_request_status(
                            request.id,
                            new_status,
                            admin_id
                        )

                        if success:

                            st.session_state[
                                "request_status_flash"
                            ] = message

                            st.rerun()

                        else:

                            st.warning(message)

    except Exception as e:

        st.error(
            "Unable to load document requests."
        )

        st.exception(e)

    finally:

        db.close()
