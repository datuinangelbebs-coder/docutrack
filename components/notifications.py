
import streamlit as st
from datetime import datetime

from database import SessionLocal, DocumentRequest


def show_notifications():

    st.title("Notifications")

    st.write(
        "Stay updated on your document requests, "
        "queue assignments, payments, and document releases."
    )

    user_id = st.session_state.get("user_id")

    if not user_id:
        st.error("Please log in again.")
        return

    db = SessionLocal()

    try:

        # =====================================
        # GET STUDENT REQUESTS
        # =====================================

        requests = (
            db.query(DocumentRequest)
            .filter(
                DocumentRequest.student_id == user_id
            )
            .order_by(
                DocumentRequest.updated_at.desc()
            )
            .all()
        )

        if not requests:
            st.info(
                "You don't have any notifications yet. "
                "Updates will appear here after you submit a request."
            )
            return

        notifications = []

        # =====================================
        # GENERATE NOTIFICATIONS
        # =====================================

        for request in requests:

            request_number = (
                request.request_number or "Not available"
            )

            document_type = (
                request.document_type or "Document"
            )

            status = (
                request.request_status or "Submitted"
            ).strip()

            normalized_status = status.lower()

            request_date = (
                request.updated_at or request.submitted_at
            )

            # REQUEST STATUS NOTIFICATION

            if normalized_status == "released":

                notifications.append({
                    "title": "Document Released",
                    "message": (
                        f"Your {document_type} request "
                        f"({request_number}) has been released."
                    ),
                    "date": (
                        request.released_at or request_date
                    ),
                    "type": "release",
                    "priority": 1
                })

            elif normalized_status == "ready for claiming":

                notifications.append({
                    "title": "Document Ready for Claiming",
                    "message": (
                        f"Your {document_type} request "
                        f"({request_number}) is ready for claiming."
                    ),
                    "date": request_date,
                    "type": "request",
                    "priority": 1
                })

            elif normalized_status == "rejected":

                notifications.append({
                    "title": "Request Rejected",
                    "message": (
                        f"Your {document_type} request "
                        f"({request_number}) has been rejected. "
                        "Please contact the Registrar for assistance."
                    ),
                    "date": request_date,
                    "type": "request",
                    "priority": 1
                })

            elif normalized_status == "cancelled":

                notifications.append({
                    "title": "Request Cancelled",
                    "message": (
                        f"Your {document_type} request "
                        f"({request_number}) has been cancelled."
                    ),
                    "date": request_date,
                    "type": "request",
                    "priority": 1
                })

            else:

                notifications.append({
                    "title": "Document Request Update",
                    "message": (
                        f"Your {document_type} request "
                        f"({request_number}) is currently {status}."
                    ),
                    "date": request_date,
                    "type": "request",
                    "priority": 2
                })

            # QUEUE NUMBER NOTIFICATION

            if (
                request.queue_number
                and request.queue_number.strip()
            ):

                notifications.append({
                    "title": "Queue Number Assigned",
                    "message": (
                        f"Queue number {request.queue_number} "
                        f"has been assigned to your {document_type} "
                        f"request ({request_number})."
                    ),
                    "date": request_date,
                    "type": "queue",
                    "priority": 1
                })

            # PAYMENT NOTIFICATION

            payment = request.payment

            if payment:

                payment_status = (
                    payment.payment_status or "Unpaid"
                ).strip()

                normalized_payment = payment_status.lower()

                if normalized_payment in [
                    "verified",
                    "paid on-site",
                    "paid onsite"
                ]:

                    payment_title = "Payment Confirmed"

                    payment_message = (
                        f"Payment for your {document_type} "
                        f"request ({request_number}) has been confirmed."
                    )

                elif normalized_payment in [
                    "awaiting verification",
                    "pending verification"
                ]:

                    payment_title = "Payment Awaiting Verification"

                    payment_message = (
                        f"Your payment for {document_type} "
                        f"({request_number}) is waiting for Registrar verification."
                    )

                elif normalized_payment in [
                    "rejected",
                    "failed"
                ]:

                    payment_title = "Payment Rejected"

                    payment_message = (
                        f"Your payment for {document_type} "
                        f"({request_number}) was rejected. "
                        "Please contact the Registrar."
                    )

                else:

                    payment_title = "Payment Update"

                    payment_message = (
                        f"Payment for your {document_type} "
                        f"request ({request_number}) is {payment_status}."
                    )

                notifications.append({
                    "title": payment_title,
                    "message": payment_message,
                    "date": (
                        payment.payment_date
                        or request_date
                    ),
                    "type": "payment",
                    "priority": 1
                })

        # =====================================
        # SORT NOTIFICATIONS
        # =====================================

        notifications.sort(
            key=lambda item: (
                item["date"] is not None,
                item["date"] or datetime.min
            ),
            reverse=True
        )

        # =====================================
        # NOTIFICATION SUMMARY
        # =====================================

        st.subheader("Notification Overview")

        total_notifications = len(notifications)

        request_count = sum(
            1 for item in notifications
            if item["type"] == "request"
        )

        payment_count = sum(
            1 for item in notifications
            if item["type"] == "payment"
        )

        queue_count = sum(
            1 for item in notifications
            if item["type"] == "queue"
        )

        col1, col2 = st.columns(2)

        col1.metric(
            "Total Updates",
            total_notifications
        )

        col2.metric(
            "Request Updates",
            request_count
        )

        col3, col4 = st.columns(2)

        col3.metric(
            "Payment Updates",
            payment_count
        )

        col4.metric(
            "Queue Assignments",
            queue_count
        )

        st.divider()

        # =====================================
        # FILTER NOTIFICATIONS
        # =====================================

        st.subheader("Recent Updates")

        filter_options = [
            "All Notifications",
            "Request Updates",
            "Payment Updates",
            "Queue Assignments",
            "Document Releases"
        ]

        selected_filter = st.selectbox(
            "Filter Notifications",
            filter_options
        )

        filter_mapping = {
            "All Notifications": None,
            "Request Updates": "request",
            "Payment Updates": "payment",
            "Queue Assignments": "queue",
            "Document Releases": "release"
        }

        selected_type = filter_mapping[selected_filter]

        filtered_notifications = [
            item for item in notifications
            if (
                selected_type is None
                or item["type"] == selected_type
            )
        ]

        st.caption(
            f"Showing {len(filtered_notifications)} "
            f"of {total_notifications} notifications."
        )

        # =====================================
        # DISPLAY NOTIFICATIONS
        # =====================================

        if not filtered_notifications:

            st.info(
                "No notifications match your selected filter."
            )

        for notification in filtered_notifications:

            with st.container(border=True):

                notification_type = notification["type"]

                if notification_type == "payment":

                    st.markdown(
                        "💳 **Payment Notification**"
                    )

                elif notification_type == "queue":

                    st.markdown(
                        "🎫 **Queue Notification**"
                    )

                elif notification_type == "release":

                    st.markdown(
                        "📦 **Document Release Notification**"
                    )

                else:

                    st.markdown(
                        "📄 **Request Notification**"
                    )

                st.markdown(
                    f"**{notification['title']}**"
                )

                st.write(
                    notification["message"]
                )

                if notification["date"]:

                    st.caption(
                        notification["date"].strftime(
                            "%B %d, %Y at %I:%M %p"
                        )
                    )

                else:

                    st.caption("Date not available")

        st.divider()

        # =====================================
        # NOTIFICATION REMINDER
        # =====================================

        st.subheader("Stay Updated")

        st.info(
            """
            Check this page regularly to monitor:

            - Document request progress
            - Payment verification
            - Queue number assignments
            - Documents ready for claiming
            - Document release updates
            """
        )

    except Exception as e:

        st.error(
            "Unable to load notifications. "
            "Please try again."
        )

        print("Notifications Error:", e)

    finally:

        db.close()
