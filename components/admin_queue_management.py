
import streamlit as st
from datetime import datetime

from sqlalchemy.exc import IntegrityError
from database import SessionLocal, DocumentRequest, ActivityLog


def has_queue_number(request):
    """Check whether a request already has a valid queue number."""
    return bool(
        request.queue_number
        and request.queue_number.strip()
    )


def get_next_queue_number(db):
    """Generate the next available queue number for today."""
    today = datetime.now().strftime("%Y%m%d")
    prefix = f"Q-{today}-"

    existing_numbers = (
        db.query(DocumentRequest.queue_number)
        .filter(
            DocumentRequest.queue_number.like(f"{prefix}%")
        )
        .all()
    )

    highest_number = 0

    for row in existing_numbers:
        queue_number = row[0]

        if not queue_number:
            continue

        try:
            number = int(queue_number.split("-")[-1])
            highest_number = max(highest_number, number)
        except (ValueError, IndexError):
            continue

    return f"{prefix}{highest_number + 1:03d}"


def assign_queue_number(request_id, admin_id):
    """Assign a unique queue number to a document request."""
    db = SessionLocal()

    try:
        request = (
            db.query(DocumentRequest)
            .filter(DocumentRequest.id == request_id)
            .with_for_update()
            .first()
        )

        if not request:
            return False, "Request not found."

        if has_queue_number(request):
            return False, "This request already has a queue number."

        if request.request_status not in [
            "Approved",
            "Waiting in Queue",
            "Processing"
        ]:
            return False, "This request is not eligible for queue assignment."

        new_queue_number = get_next_queue_number(db)

        request.queue_number = new_queue_number

        if request.request_status == "Approved":
            request.request_status = "Waiting in Queue"

        request.updated_at = datetime.now()

        if admin_id:
            log = ActivityLog(
                user_id=admin_id,
                action="Queue Number Assigned",
                details=(
                    f"Assigned {new_queue_number} "
                    f"to request {request.request_number}"
                )
            )
            db.add(log)

        db.commit()

        return True, new_queue_number

    except IntegrityError:
        db.rollback()
        return False, "Queue number conflict. Please try again."

    except Exception as error:
        db.rollback()
        return False, str(error)

    finally:
        db.close()


def show_admin_queue_management():

    st.title("Queue Management")
    st.caption(
        "Assign and manage queue numbers for approved document requests."
    )

    db = SessionLocal()

    try:
        requests = (
            db.query(DocumentRequest)
            .filter(
                DocumentRequest.request_status.in_([
                    "Approved",
                    "Waiting in Queue",
                    "Processing"
                ])
            )
            .order_by(DocumentRequest.submitted_at.asc())
            .all()
        )

        assigned_requests = [
            request for request in requests
            if has_queue_number(request)
        ]

        unassigned_requests = [
            request for request in requests
            if not has_queue_number(request)
        ]

        # Summary
        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("Eligible Requests", len(requests))

        with col2:
            st.metric("Assigned Queue", len(assigned_requests))

        with col3:
            st.metric("Not Yet Assigned", len(unassigned_requests))

        st.divider()

        # Search and filter
        st.subheader("Queue Requests")

        search = st.text_input(
            "Search Request",
            placeholder=(
                "Search request number, student name, "
                "student ID, or document type..."
            )
        )

        queue_filter = st.selectbox(
            "Queue Status",
            ["All", "Assigned", "Not Assigned"]
        )

        displayed_requests = requests

        if search:
            search_text = search.lower().strip()

            displayed_requests = [
                request for request in displayed_requests
                if (
                    search_text in str(
                        request.request_number or ""
                    ).lower()
                    or search_text in str(
                        request.document_type or ""
                    ).lower()
                    or search_text in str(
                        request.student.student_id
                        if request.student else ""
                    ).lower()
                    or search_text in str(
                        request.student.first_name or ""
                    ).lower()
                    if request.student else (
                        search_text in str(
                            request.request_number or ""
                        ).lower()
                        or search_text in str(
                            request.document_type or ""
                        ).lower()
                    )
                )
            ]

        if queue_filter == "Assigned":
            displayed_requests = [
                request for request in displayed_requests
                if has_queue_number(request)
            ]

        elif queue_filter == "Not Assigned":
            displayed_requests = [
                request for request in displayed_requests
                if not has_queue_number(request)
            ]

        # Request list
        if not displayed_requests:
            st.info("No requests found.")

        for request in displayed_requests:

            student = request.student

            if student:
                student_name = (
                    f"{student.first_name or ''} "
                    f"{student.middle_name or ''} "
                    f"{student.last_name or ''}"
                ).strip()

                student_id = student.student_id or "Not specified"
            else:
                student_name = "Student information unavailable"
                student_id = "Not available"

            queue_status = (
                request.queue_number
                if has_queue_number(request)
                else "Not Assigned"
            )

            with st.container(border=True):

                left, right = st.columns([3, 1])

                with left:
                    st.markdown(f"**{request.document_type}**")

                    st.caption(
                        f"Request No.: {request.request_number}"
                    )

                    st.write(f"Student: {student_name}")
                    st.write(f"Student ID: {student_id}")
                    st.write(f"Copies: {request.copies}")
                    st.write(
                        f"Request Status: {request.request_status}"
                    )

                with right:
                    st.markdown("**Queue Number**")
                    st.subheader(queue_status)

                    if not has_queue_number(request):

                        if st.button(
                            "Assign Queue",
                            key=f"assign_queue_{request.id}",
                            use_container_width=True
                        ):

                            admin_id = st.session_state.get("user_id")

                            success, result = assign_queue_number(
                                request.id,
                                admin_id
                            )

                            if success:
                                st.success(
                                    f"Queue number {result} assigned!"
                                )
                            else:
                                st.error(result)

                            st.rerun()

                    else:
                        st.success("Queue Assigned")

        st.divider()

        # Guidelines
        st.subheader("Queue Guidelines")

        st.markdown(
            """
            - Only approved, waiting, or processing requests appear here.
            - Each new queue number is generated automatically.
            - Queue numbers follow the format `Q-YYYYMMDD-001`.
            - Requests are listed according to their submission date.
            - Assigning a queue number to an approved request changes
              its status to **Waiting in Queue**.
            - Existing queue numbers cannot be assigned again.
            """
        )

    except Exception as error:
        st.error(f"Unable to load queue management: {error}")

    finally:
        db.close()
