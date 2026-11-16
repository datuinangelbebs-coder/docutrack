
import streamlit as st

from database import SessionLocal, DocumentRequest, User


# =====================================
# REQUEST STATUS GROUPS
# =====================================

PENDING_STATUSES = [
    "submitted",
    "pending",
    "under review",
    "pending requirements",
    "approved",
    "waiting in queue"
]


# =====================================
# COURSE NAME FORMATTER
# =====================================

def format_course_name(course):

    if not course:
        return "Not specified"

    normalized_course = course.strip().lower()

    if "travel management" in normalized_course:
        return "Bachelor of Science in Tourism Management (BSTM)"

    if "tourism management" in normalized_course:
        return "Bachelor of Science in Tourism Management (BSTM)"

    if normalized_course == "bstm":
        return "Bachelor of Science in Tourism Management (BSTM)"

    return course


# =====================================
# STUDENT DASHBOARD
# =====================================

def show_student_dashboard():

    user_id = st.session_state.get("user_id")

    if not user_id:
        st.error("Please log in again.")
        return

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

        user_name = (
            f"{student.first_name or ''} "
            f"{student.last_name or ''}"
        ).strip()

        student_id = student.student_id or "Not specified"

        course = format_course_name(student.course)

        year_level = student.year_level or "Not specified"

        # Refresh academic information in session
        st.session_state["user_course"] = course
        st.session_state["user_year_level"] = year_level

        # =====================================
        # GET DOCUMENT REQUESTS
        # =====================================

        requests = (
            db.query(DocumentRequest)
            .filter(
                DocumentRequest.student_id == user_id
            )
            .order_by(
                DocumentRequest.submitted_at.desc()
            )
            .all()
        )

        total = len(requests)

        # =====================================
        # REQUEST STATISTICS
        # =====================================

        pending = sum(
            1 for request in requests
            if (request.request_status or "").strip().lower()
            in PENDING_STATUSES
        )

        processing = sum(
            1 for request in requests
            if (request.request_status or "").strip().lower()
            == "processing"
        )

        ready = sum(
            1 for request in requests
            if (request.request_status or "").strip().lower()
            == "ready for claiming"
        )

        released = sum(
            1 for request in requests
            if (request.request_status or "").strip().lower()
            == "released"
        )

        rejected = sum(
            1 for request in requests
            if (request.request_status or "").strip().lower()
            == "rejected"
        )

        cancelled = sum(
            1 for request in requests
            if (request.request_status or "").strip().lower()
            == "cancelled"
        )

        # =====================================
        # WELCOME SECTION
        # =====================================

        st.title(f"Welcome, {user_name}!")

        st.write(
            "Welcome to your UMTC Student Dashboard. "
            "Monitor your academic document requests "
            "and check their latest progress here."
        )

        # =====================================
        # STUDENT INFORMATION
        # =====================================

        st.subheader("Student Information")

        col1, col2 = st.columns(2)

        with col1:
            with st.container(border=True):
                st.caption("STUDENT ID")
                st.markdown(f"**{student_id}**")

        with col2:
            with st.container(border=True):
                st.caption("COURSE / PROGRAM")
                st.markdown(f"**{course}**")

        col3, col4 = st.columns(2)

        with col3:
            with st.container(border=True):
                st.caption("YEAR LEVEL")
                st.markdown(f"**{year_level}**")

        with col4:
            with st.container(border=True):
                st.caption("ACCOUNT STATUS")

                status = (
                    "Active" if student.is_active else "Inactive"
                )

                st.markdown(f"**{status}**")

        if course == "Not specified" or year_level == "Not specified":

            st.warning(
                "Your academic information is incomplete. "
                "Please visit My Profile and update your Course "
                "and Year Level."
            )

        st.divider()

        # =====================================
        # DOCUMENT REQUEST OVERVIEW
        # =====================================

        st.subheader("Document Request Overview")

        col1, col2, col3 = st.columns(3)

        col1.metric(
            "Total Requests",
            total
        )

        col2.metric(
            "Pending",
            pending
        )

        col3.metric(
            "Processing",
            processing
        )

        col4, col5 = st.columns(2)

        col4.metric(
            "Ready for Claiming",
            ready
        )

        col5.metric(
            "Released",
            released
        )

        # Additional request information

        if rejected > 0 or cancelled > 0:

            st.caption(
                f"Rejected: {rejected} | Cancelled: {cancelled}"
            )

        st.divider()

        # =====================================
        # RECENT DOCUMENT REQUESTS
        # =====================================

        st.subheader("Recent Document Requests")

        if requests:

            for request in requests[:5]:

                with st.container(border=True):

                    col1, col2 = st.columns([2, 1])

                    with col1:

                        st.markdown(
                            f"**{request.document_type}**"
                        )

                        st.caption(
                            f"Request No.: {request.request_number}"
                        )

                        st.write(
                            f"Copies: {request.copies}"
                        )

                        st.write(
                            f"Total Fee: ₱{float(request.total_fee or 0):,.2f}"
                        )

                    with col2:

                        st.caption("REQUEST STATUS")

                        status = (
                            request.request_status or "Unknown"
                        )

                        normalized_status = status.strip().lower()

                        if normalized_status == "released":

                            st.success(status)

                        elif normalized_status in [
                            "rejected",
                            "cancelled"
                        ]:

                            st.error(status)

                        elif normalized_status == "ready for claiming":

                            st.info(status)

                        elif normalized_status == "processing":

                            st.info(status)

                        else:

                            st.warning(status)

                    if request.submitted_at:

                        st.caption(
                            "Submitted: "
                            + request.submitted_at.strftime(
                                "%B %d, %Y - %I:%M %p"
                            )
                        )

        else:

            st.info(
                "You don't have any document requests yet. "
                "Your submitted requests will appear here."
            )

            st.caption(
                "Go to Request a Document to submit your first request."
            )

        st.divider()

        # =====================================
        # DASHBOARD FOOTER
        # =====================================

        st.caption(
            "UMTC Queue Management System | "
            "Student Dashboard"
        )

    except Exception as e:

        st.error("Unable to load your dashboard.")

        print("Dashboard error:", e)

    finally:

        db.close()
