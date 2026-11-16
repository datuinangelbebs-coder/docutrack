
import streamlit as st
import html

from pathlib import Path
from database import SessionLocal, DocumentRequest


def format_currency(amount):
    try:
        return f"₱{float(amount or 0):,.2f}"
    except (TypeError, ValueError):
        return "₱0.00"


def normalize_status(status):
    return (status or "Unpaid").strip().lower()


def show_payment_status(status):

    normalized = normalize_status(status)

    if normalized in ["verified", "paid on-site", "paid onsite"]:
        st.success(status)

    elif normalized in [
        "awaiting verification",
        "pending verification"
    ]:
        st.warning(status)

    elif normalized in ["rejected", "failed"]:
        st.error(status)

    else:
        st.info(status)


def show_payments():

    st.title("Payments")

    st.write(
        "View your payment records, payment methods, "
        "receipt submissions, and verification status."
    )

    # =====================================
    # GCASH DEMO PAYMENT INFORMATION
    # =====================================

    with st.container(border=True):

        st.warning(
            "DEMO PAYMENT ONLY — NOT A REAL GCASH ACCOUNT"
        )

        st.subheader("GCash Payment Details")

        st.markdown(
            """
            **Account Name**

            UMTC Demo Registrar

            **GCash Number**

            `09XX-XXX-XXXX`

            **Payment Instructions**

            1. Check the total amount of your document request.
            2. Use the demo payment details for presentation purposes only.
            3. Keep your reference number and receipt information.
            4. Wait for the administrator to verify your demo payment.
            """
        )

        st.info(
            "This is a simulated payment process. "
            "No real money should be transferred."
        )

    st.divider()

    # =====================================
    # GET LOGGED-IN STUDENT
    # =====================================

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
                "You don't have any document requests yet. "
                "Payment records will appear here after "
                "you submit a document request."
            )
            return

        payments = [
            (request, request.payment)
            for request in requests
            if request.payment is not None
        ]

        # =====================================
        # PAYMENT SUMMARY
        # =====================================

        total_paid = sum(
            float(payment.amount or 0)
            for request, payment in payments
            if normalize_status(payment.payment_status)
            in [
                "verified",
                "paid on-site",
                "paid onsite"
            ]
        )

        awaiting = sum(
            1
            for request, payment in payments
            if normalize_status(payment.payment_status)
            in [
                "awaiting verification",
                "pending verification"
            ]
        )

        rejected = sum(
            1
            for request, payment in payments
            if normalize_status(payment.payment_status)
            in ["rejected", "failed"]
        )

        unpaid = sum(
            1
            for request, payment in payments
            if normalize_status(payment.payment_status)
            in ["unpaid", "not paid"]
        )

        total_records = len(payments)

        st.subheader("Payment Overview")

        col1, col2 = st.columns(2)

        col1.metric(
            "Confirmed Payments",
            format_currency(total_paid)
        )

        col2.metric(
            "Awaiting Verification",
            awaiting
        )

        col3, col4 = st.columns(2)

        col3.metric(
            "Rejected Payments",
            rejected
        )

        col4.metric(
            "Unpaid Records",
            unpaid
        )

        st.divider()

        # =====================================
        # PAYMENT RECORDS
        # =====================================

        st.subheader("Payment Records")

        if not payments:

            st.info(
                "No payment records are available yet. "
                "Your payment information will appear here "
                "after a payment record is created."
            )

            return

        # =====================================
        # SEARCH AND FILTER
        # =====================================

        search_query = st.text_input(
            "Search Payment Records",
            placeholder="Search by request number or document type..."
        )

        payment_status_options = [
            "All Payments",
            "Verified",
            "Awaiting Verification",
            "Paid On-site",
            "Rejected",
            "Unpaid"
        ]

        selected_status = st.selectbox(
            "Filter by Payment Status",
            payment_status_options
        )

        filtered_payments = []

        for request, payment in payments:

            status = normalize_status(
                payment.payment_status
            )

            search_text = (
                f"{request.request_number or ''} "
                f"{request.document_type or ''}"
            ).lower()

            matches_search = (
                search_query.strip().lower() in search_text
            )

            if selected_status == "All Payments":
                matches_status = True

            elif selected_status == "Paid On-site":
                matches_status = status in [
                    "paid on-site",
                    "paid onsite"
                ]

            elif selected_status == "Awaiting Verification":
                matches_status = status in [
                    "awaiting verification",
                    "pending verification"
                ]

            elif selected_status == "Rejected":
                matches_status = status in [
                    "rejected",
                    "failed"
                ]

            elif selected_status == "Unpaid":
                matches_status = status in [
                    "unpaid",
                    "not paid"
                ]

            else:
                matches_status = (
                    status == selected_status.lower()
                )

            if matches_search and matches_status:
                filtered_payments.append((request, payment))

        st.caption(
            f"Showing {len(filtered_payments)} "
            f"of {total_records} payment records"
        )

        st.divider()

        # =====================================
        # DISPLAY PAYMENT RECORDS
        # =====================================

        if not filtered_payments:

            st.info(
                "No payment records match your search or filter."
            )

        for request, payment in filtered_payments:

            with st.container(border=True):

                st.markdown(
                    f"### {html.escape(request.document_type or 'Document Request')}"
                )

                st.caption(
                    f"Request Number: "
                    f"{html.escape(request.request_number or 'Not available')}"
                )

                col1, col2 = st.columns(2)

                with col1:

                    st.caption("PAYMENT METHOD")

                    st.write(
                        payment.payment_method or "Not specified"
                    )

                    st.caption("PAYMENT AMOUNT")

                    st.markdown(
                        f"**{format_currency(payment.amount)}**"
                    )

                with col2:

                    st.caption("PAYMENT STATUS")

                    show_payment_status(
                        payment.payment_status or "Unpaid"
                    )

                    st.caption("REFERENCE NUMBER")

                    st.write(
                        payment.reference_number
                        or "Not available"
                    )

                st.divider()

                # =====================================
                # PAYMENT DATE
                # =====================================

                date_col1, date_col2 = st.columns(2)

                with date_col1:

                    st.caption("PAYMENT DATE")

                    if payment.payment_date:

                        st.write(
                            payment.payment_date.strftime(
                                "%B %d, %Y at %I:%M %p"
                            )
                        )

                    else:

                        st.write("Not yet recorded")

                with date_col2:

                    st.caption("DOCUMENT REQUEST STATUS")

                    st.write(
                        request.request_status or "Submitted"
                    )

                st.divider()

                # =====================================
                # RECEIPT INFORMATION
                # =====================================

                st.markdown("**Payment Receipt**")

                if payment.receipt_file:

                    st.success(
                        "Payment receipt submitted."
                    )

                    st.caption(
                        "Your receipt is subject to manual "
                        "verification by the Registrar."
                    )

                    receipt_path = Path(
                        payment.receipt_file
                    )

                    if not receipt_path.is_absolute():
                        receipt_path = (
                            Path(__file__).resolve().parent.parent
                            / receipt_path
                        )

                    if receipt_path.exists():

                        file_extension = (
                            receipt_path.suffix.lower()
                        )

                        if file_extension in [
                            ".png",
                            ".jpg",
                            ".jpeg"
                        ]:

                            with st.expander("View Uploaded Receipt"):

                                st.image(
                                    str(receipt_path),
                                    caption="Submitted Payment Receipt",
                                    use_container_width=True
                                )

                        elif file_extension == ".pdf":

                            with st.expander("Receipt File Information"):

                                st.write(
                                    f"PDF receipt: {receipt_path.name}"
                                )

                    else:

                        st.caption(
                            "The receipt file is not currently "
                            "available for preview."
                        )

                else:

                    st.info(
                        "No payment receipt has been submitted."
                    )

        st.divider()

        # =====================================
        # PAYMENT REMINDERS
        # =====================================

        st.subheader("Payment Reminders")

        with st.container(border=True):

            st.markdown(
                """
                - Keep your payment reference number for future reference.
                - Make sure your uploaded receipt is clear and readable.
                - Payments marked **Awaiting Verification** still need
                  to be checked by the Registrar.
                - Wait for confirmation before assuming your payment
                  has been verified.
                - Contact the Registrar if you have concerns about
                  your payment record.
                """
            )

    except Exception as e:

        st.error(
            "Unable to load payment records. "
            "Please try again."
        )

        print("Payment Page Error:", e)

    finally:

        db.close()
