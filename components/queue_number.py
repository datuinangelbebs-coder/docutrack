
import streamlit as st

from database import SessionLocal, DocumentRequest, ActivityLog


# =====================================
# REQUEST ID FROM ACTIVITY LOG
# =====================================

def get_request_id_from_log(log):

    if not log or not log.details:
        return None

    try:

        for item in log.details.split(";"):

            if item.startswith("request_id="):
                return int(item.split("=", 1)[1])

    except (ValueError, IndexError):
        return None

    return None


# =====================================
# GET CURRENTLY SERVING REQUEST
# =====================================

def get_current_serving(db):

    latest_event = (
        db.query(ActivityLog)
        .filter(
            ActivityLog.action.in_([
                "Now Serving",
                "Queue Call Completed"
            ])
        )
        .order_by(ActivityLog.created_at.desc())
        .first()
    )

    if not latest_event or latest_event.action != "Now Serving":
        return None

    request_id = get_request_id_from_log(latest_event)

    if not request_id:
        return None

    return (
        db.query(DocumentRequest)
        .filter(DocumentRequest.id == request_id)
        .first()
    )


# =====================================
# GET STUDENT QUEUE STATUS
# =====================================

def get_student_queue_status(db, request, current_serving):

    request_status = (
        request.request_status or "Submitted"
    ).strip().lower()

    # Document status takes priority over queue status.

    if request_status == "ready for claiming":
        return "Document Ready for Claiming"

    if request_status == "released":
        return "Document Released"

    if request_status == "rejected":
        return "Request Rejected"

    if request_status == "cancelled":
        return "Request Cancelled"

    # Check if this request is currently being served.

    if current_serving and current_serving.id == request.id:
        return "Currently Serving"

    # Check the latest queue event for this request.

    latest_request_event = (
        db.query(ActivityLog)
        .filter(
            ActivityLog.action.in_([
                "Now Serving",
                "Queue Call Completed"
            ]),
            ActivityLog.details.like(
                f"request_id={request.id};%"
            )
        )
        .order_by(ActivityLog.created_at.desc())
        .first()
    )

    if (
        latest_request_event
        and latest_request_event.action == "Queue Call Completed"
    ):
        return "Queue Call Completed"

    if request.queue_number and request.queue_number.strip():
        return "Waiting in Queue"

    return "Not Yet Assigned"


# =====================================
# QUEUE STATUS DISPLAY
# =====================================

def show_queue_status(status):

    st.markdown("**YOUR QUEUE STATUS**")

    if status == "Currently Serving":

        st.success("You are currently being served!")

    elif status == "Waiting in Queue":

        st.info("You are waiting in the queue.")

    elif status == "Queue Call Completed":

        st.success("Your queue call has been completed.")

    elif status == "Document Ready for Claiming":

        st.success(
            "Your document is ready for claiming. "
            "Please proceed to the Registrar's Office."
        )

    elif status == "Document Released":

        st.success("Your document has already been released.")

    elif status == "Request Rejected":

        st.error("Your document request has been rejected.")

    elif status == "Request Cancelled":

        st.warning("This document request has been cancelled.")

    else:

        st.warning("Waiting for queue number assignment.")


# =====================================
# MAIN QUEUE NUMBER PAGE
# =====================================

def show_queue_number():

    st.title("My Queue Number")

    st.write(
        "Monitor your queue number, current serving number, "
        "and document request status."
    )

    user_id = st.session_state.get("user_id")

    if not user_id:

        st.error("Please log in again.")
        return

    if st.button(
        "Refresh Queue Information",
        use_container_width=True
    ):
        st.rerun()

    db = SessionLocal()

    try:

        # =================================
        # GET STUDENT REQUESTS
        # =================================

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

        if not requests:

            st.info(
                "You don't have any document requests yet. "
                "Submit a document request to get started."
            )
            return

        # =================================
        # GET CURRENTLY SERVING REQUEST
        # =================================

        current_serving = get_current_serving(db)

        st.subheader("Registrar Queue Display")

        if current_serving:

            with st.container(border=True):

                st.caption("UNIVERSITY OF MINDANAO · TAGUM COLLEGE")

                st.markdown("### NOW SERVING")

                st.title(
                    str(
                        current_serving.queue_number
                        or "Not available"
                    )
                )

                st.caption(
                    "Please wait for your queue number to be called."
                )

        else:

            with st.container(border=True):

                st.info(
                    "The Registrar is not currently serving "
                    "a queue number."
                )

        # =================================
        # QUEUE SUMMARY
        # =================================

        assigned_requests = [
            request for request in requests
            if request.queue_number
            and request.queue_number.strip()
        ]

        queue_active_statuses = [
            "Submitted",
            "Under Review",
            "Pending Requirements",
            "Approved",
            "Waiting in Queue",
            "Processing"
        ]

        unassigned_requests = [
            request for request in requests
            if (
                not request.queue_number
                or not request.queue_number.strip()
            )
            and (
                request.request_status
                or "Submitted"
            ).strip() in queue_active_statuses
        ]

        st.divider()

        st.subheader("Queue Summary")

        col1, col2, col3 = st.columns(3)

        col1.metric(
            "Total Requests",
            len(requests)
        )

        col2.metric(
            "Assigned Queue Numbers",
            len(assigned_requests)
        )

        col3.metric(
            "Awaiting Queue Assignment",
            len(unassigned_requests)
        )

        st.divider()

        # =================================
        # STUDENT QUEUE INFORMATION
        # =================================

        st.subheader("Your Queue Information")

        for request in requests:

            with st.container(border=True):

                # REQUEST INFORMATION

                st.subheader(
                    request.document_type
                    or "Document Request"
                )

                st.caption(
                    f"Request Number: "
                    f"{request.request_number or 'Not available'}"
                )

                st.divider()

                # =================================
                # QUEUE NUMBER DISPLAY
                # =================================

                queue_status = get_student_queue_status(
                    db,
                    request,
                    current_serving
                )

                if request.queue_number and request.queue_number.strip():

                    with st.container(border=True):

                        st.caption("YOUR QUEUE NUMBER")

                        st.title(request.queue_number)

                elif queue_status == "Document Ready for Claiming":

                    with st.container(border=True):

                        st.success("DOCUMENT READY FOR CLAIMING")

                        st.write(
                            "Your document is ready. "
                            "You may proceed to the Registrar's Office "
                            "for the claiming process."
                        )

                elif queue_status == "Document Released":

                    with st.container(border=True):

                        st.success("DOCUMENT ALREADY RELEASED")

                        st.write(
                            "Your document request has been marked "
                            "as released."
                        )

                elif queue_status in [
                    "Request Rejected",
                    "Request Cancelled"
                ]:

                    with st.container(border=True):

                        st.warning(queue_status)

                        st.write(
                            "Please check your request details "
                            "or contact the Registrar's Office."
                        )

                else:

                    with st.container(border=True):

                        st.warning("QUEUE NUMBER NOT YET ASSIGNED")

                        st.write(
                            "Your queue number has not been assigned yet. "
                            "Please wait while the Registrar processes "
                            "your request."
                        )

                # =================================
                # QUEUE STATUS
                # =================================

                show_queue_status(queue_status)

                st.divider()

                # =================================
                # REQUEST DETAILS
                # =================================

                detail_col1, detail_col2 = st.columns(2)

                with detail_col1:

                    st.caption("DOCUMENT TYPE")

                    st.write(
                        request.document_type or "Not specified"
                    )

                with detail_col2:

                    st.caption("NUMBER OF COPIES")

                    st.write(request.copies or 0)

                # =================================
                # DOCUMENT REQUEST STATUS
                # =================================

                st.markdown("**DOCUMENT REQUEST STATUS**")

                status = request.request_status or "Submitted"
                normalized_status = status.strip().lower()

                if normalized_status == "released":

                    st.success(f"✓ {status}")

                elif normalized_status == "rejected":

                    st.error(status)

                elif normalized_status == "cancelled":

                    st.warning(status)

                elif normalized_status == "ready for claiming":

                    st.success(status)

                elif normalized_status == "processing":

                    st.info(status)

                else:

                    st.warning(status)

                # =================================
                # SUBMISSION DATE
                # =================================

                if request.submitted_at:

                    st.caption("SUBMITTED ON")

                    st.write(
                        request.submitted_at.strftime(
                            "%B %d, %Y at %I:%M %p"
                        )
                    )

                # =================================
                # LAST UPDATED
                # =================================

                if request.updated_at:

                    st.caption("LAST UPDATED")

                    st.write(
                        request.updated_at.strftime(
                            "%B %d, %Y at %I:%M %p"
                        )
                    )

        # =================================
        # QUEUE GUIDELINES
        # =================================

        st.divider()

        st.subheader("Queue Guidelines")

        with st.container(border=True):

            st.markdown(
                """
                **Please remember:**

                1. Wait for the Registrar to assign your queue number.
                2. Check the Now Serving display regularly.
                3. Pay attention when your queue number is called.
                4. Follow the instructions provided by the Registrar.
                5. Proceed to the Registrar's Office when your document
                   is marked Ready for Claiming.
                6. A queue number does not automatically mean that
                   your document is ready for release.
                """
            )

    except Exception as e:

        st.error(
            "Unable to load queue information. "
            "Please try again."
        )

        print("Queue Error:", e)

    finally:

        db.close()
