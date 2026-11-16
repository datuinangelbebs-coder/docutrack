
import streamlit as st

from database import SessionLocal, DocumentRequest


PENDING_STATUSES = [
    "submitted",
    "pending",
    "under review",
    "pending requirements",
    "approved",
    "waiting in queue"
]


def show_request_history():

    st.title("Request History")

    st.write(
        "View all your submitted academic document requests "
        "and monitor their payment and processing status."
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

            st.info("You have no request history yet.")

            st.caption(
                "Your submitted document requests will appear here."
            )

            return

        # =====================================
        # SUMMARY STATISTICS
        # =====================================

        total_requests = len(requests)

        released_requests = sum(
            1 for r in requests
            if (r.request_status or "").strip().lower()
            == "released"
        )

        pending_requests = sum(
            1 for r in requests
            if (r.request_status or "").strip().lower()
            in PENDING_STATUSES
        )

        processing_requests = sum(
            1 for r in requests
            if (r.request_status or "").strip().lower()
            == "processing"
        )

        ready_requests = sum(
            1 for r in requests
            if (r.request_status or "").strip().lower()
            == "ready for claiming"
        )

        col1, col2, col3, col4 = st.columns(4)

        col1.metric(
            "Total Requests",
            total_requests
        )

        col2.metric(
            "Pending",
            pending_requests
        )

        col3.metric(
            "Processing",
            processing_requests
        )

        col4.metric(
            "Released",
            released_requests
        )

        st.caption(
            f"Ready for Claiming: {ready_requests}"
        )

        st.divider()

        # =====================================
        # SEARCH AND FILTER
        # =====================================

        st.subheader("All Requests")

        search_query = st.text_input(
            "Search Request",
            placeholder="Search request number or document type..."
        )

        status_options = [
            "All Statuses",
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

        selected_status = st.selectbox(
            "Filter by Status",
            status_options
        )

        filtered_requests = requests

        if search_query.strip():

            search_text = search_query.strip().lower()

            filtered_requests = [
                r for r in filtered_requests
                if search_text in (
                    r.request_number or ""
                ).lower()
                or search_text in (
                    r.document_type or ""
                ).lower()
            ]

        if selected_status != "All Statuses":

            filtered_requests = [
                r for r in filtered_requests
                if (r.request_status or "").strip().lower()
                == selected_status.lower()
            ]

        st.caption(
            f"Showing {len(filtered_requests)} "
            f"of {total_requests} requests"
        )

        st.divider()

        # =====================================
        # REQUEST RECORDS
        # =====================================

        if not filtered_requests:

            st.info(
                "No requests match your search or selected filter."
            )

            return

        for request in filtered_requests:

            status = (
                request.request_status or "Submitted"
            ).strip()

            normalized_status = status.lower()

            document_type = request.document_type or "Unknown Document"

            request_number = request.request_number or "Not available"

            # =====================================
            # REQUEST CARD
            # =====================================

            with st.container(border=True):

                col1, col2 = st.columns([2, 1])

                with col1:

                    st.markdown(
                        f"**{document_type}**"
                    )

                    st.caption(
                        f"Request No.: {request_number}"
                    )

                with col2:

                    st.caption("REQUEST STATUS")

                    if normalized_status == "released":

                        st.success(status)

                    elif normalized_status == "rejected":

                        st.error(status)

                    elif normalized_status == "cancelled":

                        st.warning(status)

                    elif normalized_status in [
                        "ready for claiming",
                        "processing"
                    ]:

                        st.info(status)

                    else:

                        st.warning(status)

                # =====================================
                # BASIC REQUEST INFORMATION
                # =====================================

                st.divider()

                st.markdown("**Request Summary**")

                fee1, fee2, fee3 = st.columns(3)

                with fee1:

                    st.caption("DOCUMENT TYPE")

                    st.write(document_type)

                with fee2:

                    st.caption("NUMBER OF COPIES")

                    st.write(request.copies or 0)

                with fee3:

                    st.caption("TOTAL AMOUNT")

                    st.markdown(
                        f"**₱{float(request.total_fee or 0):,.2f}**"
                    )

                # =====================================
                # QUEUE INFORMATION
                # =====================================

                st.divider()

                st.markdown("**Queue Information**")

                if request.queue_number:

                    st.write(
                        f"Queue Number: **{request.queue_number}**"
                    )

                else:

                    st.write(
                        "Queue Number: Not yet assigned"
                    )

                # =====================================
                # PAYMENT INFORMATION
                # =====================================

                payment = request.payment

                st.divider()

                st.markdown("**Payment Information**")

                if payment:

                    pay1, pay2, pay3 = st.columns(3)

                    with pay1:

                        st.caption("PAYMENT METHOD")

                        st.write(
                            payment.payment_method or "Not specified"
                        )

                    with pay2:

                        st.caption("PAYMENT AMOUNT")

                        st.write(
                            f"₱{float(payment.amount or 0):,.2f}"
                        )

                    with pay3:

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

                        elif normalized_payment == "rejected":

                            st.error(payment_status)

                        else:

                            st.info(payment_status)

                    if payment.reference_number:

                        st.caption(
                            f"Reference Number: {payment.reference_number}"
                        )

                else:

                    st.info(
                        "No payment record is available."
                    )

                # =====================================
                # ADDITIONAL REQUEST DETAILS
                # =====================================

                with st.expander("View More Details"):

                    # Submission date

                    st.markdown("**Submission Information**")

                    if request.submitted_at:

                        st.write(
                            "Submitted: "
                            + request.submitted_at.strftime(
                                "%B %d, %Y at %I:%M %p"
                            )
                        )

                    else:

                        st.write("Submission date not available.")

                    if request.updated_at:

                        st.write(
                            "Last Updated: "
                            + request.updated_at.strftime(
                                "%B %d, %Y at %I:%M %p"
                            )
                        )

                    # Release information

                    if normalized_status == "released":

                        st.divider()

                        st.markdown("**Document Release Information**")

                        if request.released_to:

                            st.write(
                                f"Released To: **{request.released_to}**"
                            )

                        if request.released_by:

                            st.write(
                                f"Released By: **{request.released_by}**"
                            )

                        if request.released_at:

                            st.write(
                                "Release Date: "
                                + request.released_at.strftime(
                                    "%B %d, %Y at %I:%M %p"
                                )
                            )

                        if not any([
                            request.released_to,
                            request.released_by,
                            request.released_at
                        ]):

                            st.info(
                                "Release confirmation information "
                                "has not been recorded."
                            )

        st.divider()

        # =====================================
        # FOOTER
        # =====================================

        st.caption(
            "UMTC Queue Management System | Request History"
        )

    except Exception as e:

        st.error("Unable to load request history.")

        print("Request History Error:", e)

    finally:

        db.close()
