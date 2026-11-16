
import streamlit as st
from datetime import datetime

from database import SessionLocal, DocumentRequest, ActivityLog


def get_current_serving(db):
    """Get the latest active queue call."""

    latest_event = (
        db.query(ActivityLog)
        .filter(
            ActivityLog.action.in_([
                "Now Serving",
                "Queue Call Completed"
            ])
        )
        .order_by(
            ActivityLog.created_at.desc(),
            ActivityLog.id.desc()
        )
        .first()
    )

    if not latest_event:
        return None

    if latest_event.action == "Queue Call Completed":
        return None

    try:
        details = latest_event.details or ""

        request_id_text = None

        for item in details.split(";"):
            if item.startswith("request_id="):
                request_id_text = item.split("=", 1)[1]
                break

        if not request_id_text:
            return None

        request_id = int(request_id_text)

        return (
            db.query(DocumentRequest)
            .filter(DocumentRequest.id == request_id)
            .first()
        )

    except (ValueError, IndexError, AttributeError):
        return None


def get_student_name(student):
    """Format student name."""

    if not student:
        return "Student information unavailable"

    return " ".join(
        part for part in [
            student.first_name,
            student.middle_name,
            student.last_name
        ]
        if part and part.strip()
    )


def complete_current_call(request, admin_id):
    """Record completion of the current queue call."""

    db = SessionLocal()

    try:
        if not admin_id:
            return False, "Admin account information is unavailable."

        log = ActivityLog(
            user_id=admin_id,
            action="Queue Call Completed",
            details=(
                f"request_id={request.id};"
                f"queue_number={request.queue_number}"
            )
        )

        db.add(log)
        db.commit()

        return True, "Current queue call completed."

    except Exception as error:
        db.rollback()
        return False, str(error)

    finally:
        db.close()


def call_next_student(request_id, admin_id):
    """Call the next waiting student."""

    db = SessionLocal()

    try:
        if not admin_id:
            return False, "Admin account information is unavailable."

        # Check if another student is already being served.
        active_request = get_current_serving(db)

        if active_request:
            return False, "Complete the current call first."

        request = (
            db.query(DocumentRequest)
            .filter(DocumentRequest.id == request_id)
            .first()
        )

        if not request:
            return False, "Request not found."

        if request.request_status != "Waiting in Queue":
            return False, "This request is no longer waiting in queue."

        if not request.queue_number:
            return False, "This request has no queue number."

        # Update request status to prevent duplicate calls.
        request.request_status = "Processing"
        request.updated_at = datetime.now()

        log = ActivityLog(
            user_id=admin_id,
            action="Now Serving",
            details=(
                f"request_id={request.id};"
                f"queue_number={request.queue_number}"
            )
        )

        db.add(log)
        db.commit()

        return True, f"Now calling {request.queue_number}."

    except Exception as error:
        db.rollback()
        return False, str(error)

    finally:
        db.close()


def show_admin_now_serving():

    st.title("Now Serving")
    st.caption(
        "Call the next student and manage the active queue."
    )

    db = SessionLocal()

    try:
        current_serving = get_current_serving(db)

        # CURRENTLY SERVING
        st.subheader("Currently Serving")

        if current_serving:

            student_name = get_student_name(
                current_serving.student
            )

            with st.container(border=True):

                st.markdown("### NOW SERVING")

                st.markdown(
                    f"# {current_serving.queue_number or 'No Queue Number'}"
                )

                st.write(f"**Student:** {student_name}")

                st.write(
                    f"**Student ID:** "
                    f"{current_serving.student.student_id if current_serving.student else 'Not available'}"
                )

                st.write(
                    f"**Request Number:** "
                    f"{current_serving.request_number}"
                )

                st.write(
                    f"**Document:** "
                    f"{current_serving.document_type}"
                )

                st.write(
                    f"**Request Status:** "
                    f"{current_serving.request_status}"
                )

                st.info(
                    "This student is currently being served."
                )

                if st.button(
                    "Complete Current Call",
                    type="primary",
                    use_container_width=True,
                    key="complete_current_call"
                ):

                    admin_id = st.session_state.get("user_id")

                    success, message = complete_current_call(
                        current_serving,
                        admin_id
                    )

                    if success:
                        st.success(message)
                    else:
                        st.error(message)

                    st.rerun()

        else:
            st.info("No student is currently being served.")

        st.divider()

        # WAITING QUEUE
        st.subheader("Waiting Queue")

        waiting_requests = (
            db.query(DocumentRequest)
            .filter(
                DocumentRequest.request_status == "Waiting in Queue",
                DocumentRequest.queue_number.isnot(None),
                DocumentRequest.queue_number != ""
            )
            .order_by(
                DocumentRequest.queue_number.asc()
            )
            .all()
        )

        col1, col2 = st.columns(2)

        with col1:
            st.metric(
                "Students Waiting",
                len(waiting_requests)
            )

        with col2:
            st.metric(
                "Currently Serving",
                1 if current_serving else 0
            )

        # NEXT STUDENT
        st.divider()
        st.subheader("Next Student")

        if current_serving:

            st.warning(
                "Complete the current call before calling the next student."
            )

        elif waiting_requests:

            next_request = waiting_requests[0]

            next_student_name = get_student_name(
                next_request.student
            )

            with st.container(border=True):

                st.markdown("**NEXT IN QUEUE**")

                st.markdown(
                    f"## {next_request.queue_number}"
                )

                st.write(
                    f"**Student:** {next_student_name}"
                )

                st.write(
                    f"**Document:** {next_request.document_type}"
                )

                st.write(
                    f"**Request No.:** {next_request.request_number}"
                )

                if st.button(
                    "Call Next Student",
                    type="primary",
                    use_container_width=True,
                    key="call_next_student"
                ):

                    admin_id = st.session_state.get("user_id")

                    success, message = call_next_student(
                        next_request.id,
                        admin_id
                    )

                    if success:
                        st.success(message)
                    else:
                        st.error(message)

                    st.rerun()

        else:

            st.info(
                "There are no students waiting in the queue."
            )

        # FULL QUEUE LIST
        st.divider()
        st.subheader("Queue List")

        if waiting_requests:

            for index, request in enumerate(
                waiting_requests,
                start=1
            ):

                student_name = get_student_name(
                    request.student
                )

                with st.container(border=True):

                    col1, col2 = st.columns([1, 3])

                    with col1:
                        st.markdown(
                            f"### {request.queue_number}"
                        )

                    with col2:
                        st.write(f"**{student_name}**")

                        st.caption(
                            f"{request.document_type} • "
                            f"Request No.: {request.request_number}"
                        )

                        st.caption(
                            f"Queue Position: {index}"
                        )

        else:
            st.info("No waiting requests available.")

        # GUIDELINES
        st.divider()
        st.subheader("Queue Guidelines")

        st.markdown(
            """
            - Only requests with **Waiting in Queue** status appear here.
            - Students are called according to their queue number.
            - Only one student can be actively served at a time.
            - Calling a student changes their request status to
              **Processing**.
            - Completing a call allows the next student to be called.
            - Completing a queue call does not mean the document
              has already been released.
            """
        )

    except Exception as error:
        db.rollback()
        st.error(f"Unable to load Now Serving: {error}")

    finally:
        db.close()
