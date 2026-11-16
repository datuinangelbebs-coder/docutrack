
import streamlit as st

from database import SessionLocal, DocumentRequest


REQUEST_STAGES = [
    "Submitted",
    "Under Review",
    "Pending Requirements",
    "Approved",
    "Waiting in Queue",
    "Processing",
    "Ready for Claiming",
    "Released"
]


def show_track_request():

    st.title("Track My Request")

    st.write(
        "Monitor the progress and payment information "
        "of your academic document requests."
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
                DocumentRequest.submitted_at.desc()
            )
            .all()
        )

        if not requests:

            st.info(
                "You don't have any document requests yet."
            )

            st.caption(
                "Your submitted document requests will appear here."
            )

            return

        # =====================================
        # SELECT REQUEST
        # =====================================

        request_numbers = [
            request.request_number
            for request in requests
        ]

        selected_number = st.selectbox(
            "Select Request Number",
            request_numbers
        )

        selected_request = next(
            request for request in requests
            if request.request_number == selected_number
        )

        status = (
            selected_request.request_status or "Submitted"
        ).strip()

        normalized_status = status.lower()

        st.divider()

        # =====================================
        # REQUEST SUMMARY
        # =====================================

        st.subheader("Request Information")

        col1, col2 = st.columns(2)

        with col1:

            st.caption("REQUEST NUMBER")

            st.write(
                f"**{selected_request.request_number}**"
            )

            st.caption("DOCUMENT TYPE")

            st.write(
                f"**{selected_request.document_type}**"
            )

            st.caption("NUMBER OF COPIES")

            st.write(
                f"**{selected_request.copies}**"
            )

        with col2:

            st.caption("CURRENT STATUS")

            if normalized_status == "released":

                st.success(status)

            elif normalized_status == "rejected":

                st.error(status)

            elif normalized_status == "cancelled":

                st.warning(status)

            else:

                st.info(status)

            st.caption("QUEUE NUMBER")

            st.write(
                f"**{selected_request.queue_number or 'Not yet assigned'}**"
            )

            st.caption("TOTAL FEE")

            st.write(
                f"**₱{float(selected_request.total_fee or 0):,.2f}**"
            )

        st.divider()

        # =====================================
        # REQUEST PROGRESS
        # =====================================

        st.subheader("Request Progress")

        if normalized_status == "rejected":

            st.error(
                "Your document request has been rejected. "
                "Please contact the Registrar's Office "
                "for more information."
            )

        elif normalized_status == "cancelled":

            st.warning(
                "This document request has been cancelled."
            )

        elif normalized_status in [
            stage.lower() for stage in REQUEST_STAGES
        ]:

            current_stage = next(
                index
                for index, stage in enumerate(REQUEST_STAGES)
                if stage.lower() == normalized_status
            )

            progress_value = (
                (current_stage + 1) / len(REQUEST_STAGES)
            )

            st.progress(progress_value)

            st.caption(
                f"Step {current_stage + 1} of "
                f"{len(REQUEST_STAGES)}"
            )

            for index, stage in enumerate(REQUEST_STAGES):

                if index < current_stage:

                    st.success(f"✓ {stage}")

                elif index == current_stage:

                    st.info(
                        f"● {stage} — Current Status"
                    )

                else:

                    st.caption(f"○ {stage}")

        else:

            st.warning(
                f"Current status: {status}. "
                "Please contact the Registrar's Office "
                "if you need assistance."
            )

        # =====================================
        # RELEASE INFORMATION
        # =====================================

        if normalized_status == "released":

            st.divider()

            st.subheader("Document Release Information")

            if selected_request.released_to:

                st.success(
                    "Your document has been marked as released."
                )

                release_col1, release_col2 = st.columns(2)

                with release_col1:

                    st.caption("RELEASED TO")

                    st.write(
                        f"**{selected_request.released_to}**"
                    )

                with release_col2:

                    st.caption("RELEASED BY")

                    st.write(
                        f"**{selected_request.released_by or 'Not available'}**"
                    )

                st.caption("RELEASE DATE AND TIME")

                if selected_request.released_at:

                    st.write(
                        selected_request.released_at.strftime(
                            "%B %d, %Y - %I:%M %p"
                        )
                    )

                else:

                    st.write("Not available")

            else:

                st.warning(
                    "The request is marked as Released, "
                    "but release confirmation information "
                    "has not been recorded."
                )

        st.divider()

        # =====================================
        # PAYMENT INFORMATION
        # =====================================

        st.subheader("Payment Information")

        payment = selected_request.payment

        if payment:

            pay1, pay2 = st.columns(2)

            with pay1:

                st.caption("PAYMENT METHOD")

                st.write(
                    payment.payment_method or "Not specified"
                )

                st.caption("PAYMENT STATUS")

                payment_status = (
                    payment.payment_status or "Not specified"
                )

                normalized_payment = payment_status.lower()

                if normalized_payment in [
                    "verified",
                    "paid",
                    "paid on-site"
                ]:

                    st.success(payment_status)

                elif normalized_payment in [
                    "rejected",
                    "unpaid"
                ]:

                    st.warning(payment_status)

                else:

                    st.info(payment_status)

            with pay2:

                st.caption("AMOUNT")

                st.write(
                    f"**₱{float(payment.amount or 0):,.2f}**"
                )

                st.caption("REFERENCE NUMBER")

                st.write(
                    payment.reference_number or "Not available"
                )

        else:

            st.info(
                "No payment information available for this request."
            )

        st.divider()

        # =====================================
        # REQUEST DATES
        # =====================================

        st.subheader("Request Dates")

        submitted = selected_request.submitted_at
        updated = selected_request.updated_at

        date1, date2 = st.columns(2)

        with date1:

            st.caption("DATE SUBMITTED")

            st.write(
                submitted.strftime("%B %d, %Y")
                if submitted else "Not available"
            )

            if submitted:

                st.caption(
                    submitted.strftime("%I:%M %p")
                )

        with date2:

            st.caption("LAST UPDATED")

            st.write(
                updated.strftime("%B %d, %Y")
                if updated else "Not available"
            )

            if updated:

                st.caption(
                    updated.strftime("%I:%M %p")
                )

        st.divider()

        # =====================================
        # HELP INFORMATION
        # =====================================

        st.subheader("Need Assistance?")

        st.info(
            "If your request status has not changed for "
            "a long time or you have questions about your "
            "document, please contact the Registrar's Office."
        )

        # =====================================
        # FOOTER
        # =====================================

        st.caption(
            "UMTC Queue Management System | Track My Request"
        )

    except Exception as e:

        st.error(
            "Unable to load request information."
        )

        print("Track Request Error:", e)

    finally:

        db.close()
