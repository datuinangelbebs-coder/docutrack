
import streamlit as st
from pathlib import Path
from datetime import datetime

from database import (
    SessionLocal,
    User,
    DocumentRequest,
    Payment,
    ActivityLog
)


# =====================================
# HELPER FUNCTIONS
# =====================================

def format_currency(amount):
    return f"₱{float(amount or 0):,.2f}"


def get_admin_name():
    return (
        st.session_state.get("full_name")
        or st.session_state.get("name")
        or st.session_state.get("email")
        or "Admin"
    )


def record_activity(db, admin_id, action, details):

    log = ActivityLog(
        user_id=admin_id,
        action=action,
        details=details
    )

    db.add(log)


# =====================================
# REQUEST VERIFICATION PAGE
# =====================================

def show_request_verification():

    st.title("Request Verification")

    st.write(
        "Review student payment receipts and verify "
        "or reject submitted payments."
    )

    st.divider()

    db = SessionLocal()

    try:

        # =================================
        # PENDING PAYMENT COUNT
        # =================================

        pending_count = (
            db.query(Payment)
            .filter(
                Payment.payment_status == "Awaiting Verification"
            )
            .count()
        )

        verified_count = (
            db.query(Payment)
            .filter(
                Payment.payment_status == "Verified"
            )
            .count()
        )

        rejected_count = (
            db.query(Payment)
            .filter(
                Payment.payment_status == "Rejected"
            )
            .count()
        )

        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("Pending Verification", pending_count)

        with col2:
            st.metric("Verified Payments", verified_count)

        with col3:
            st.metric("Rejected Payments", rejected_count)

        st.divider()

        # =================================
        # PENDING PAYMENTS
        # =================================

        st.subheader("Payments Awaiting Verification")

        pending_payments = (
            db.query(Payment)
            .join(Payment.request)
            .join(DocumentRequest.student)
            .filter(
                Payment.payment_status == "Awaiting Verification"
            )
            .order_by(DocumentRequest.submitted_at.desc())
            .all()
        )

        if not pending_payments:

            st.success("There are no pending payments to verify.")

        else:

            for payment in pending_payments:

                request = payment.request
                student = request.student

                full_name = " ".join(
                    part for part in [
                        student.first_name,
                        student.middle_name,
                        student.last_name
                    ]
                    if part
                )

                with st.container(border=True):

                    st.subheader(request.request_number)

                    st.warning("Awaiting Verification")

                    # STUDENT INFORMATION

                    st.markdown("### Student Information")

                    col1, col2 = st.columns(2)

                    with col1:
                        st.write("**Student Name**")
                        st.write(full_name)

                        st.write("**Student ID**")
                        st.write(student.student_id or "Not available")

                    with col2:
                        st.write("**Email**")
                        st.write(student.email)

                        st.write("**Document**")
                        st.write(request.document_type)

                    st.divider()

                    # PAYMENT INFORMATION

                    st.markdown("### Payment Information")

                    col1, col2, col3 = st.columns(3)

                    with col1:
                        st.write("**Payment Method**")
                        st.write(payment.payment_method)

                    with col2:
                        st.write("**Amount**")
                        st.write(format_currency(payment.amount))

                    with col3:
                        st.write("**Reference Number**")
                        st.write(
                            payment.reference_number or "Not available"
                        )

                    st.divider()

                    # RECEIPT

                    st.markdown("### Uploaded Payment Receipt")

                    receipt_path = (
                        Path(payment.receipt_file)
                        if payment.receipt_file
                        else None
                    )

                    if receipt_path and receipt_path.is_file():

                        extension = receipt_path.suffix.lower()

                        if extension in [".png", ".jpg", ".jpeg"]:

                            st.image(
                                str(receipt_path),
                                caption="Student Payment Receipt",
                                use_container_width=True
                            )

                        elif extension == ".pdf":

                            st.info("PDF receipt uploaded.")

                            with open(receipt_path, "rb") as file:
                                receipt_data = file.read()

                            st.download_button(
                                "Download PDF Receipt",
                                data=receipt_data,
                                file_name=receipt_path.name,
                                mime="application/pdf",
                                key=f"receipt_download_{payment.id}"
                            )

                    else:

                        st.error("Receipt file could not be found.")

                    st.divider()

                    # VERIFICATION ACTIONS

                    st.markdown("### Admin Verification")

                    admin_name = get_admin_name()
                    admin_id = st.session_state.get("user_id")

                    col1, col2 = st.columns(2)

                    with col1:

                        if st.button(
                            "VERIFY PAYMENT",
                            type="primary",
                            use_container_width=True,
                            key=f"verify_{payment.id}"
                        ):

                            try:

                                if not receipt_path or not receipt_path.is_file():

                                    st.error(
                                        "Cannot verify: receipt file is missing."
                                    )

                                else:

                                    payment.payment_status = "Verified"
                                    payment.verified_by = admin_name
                                    payment.payment_date = datetime.now()

                                    record_activity(
                                        db,
                                        admin_id,
                                        "Payment Verified",
                                        (
                                            f"Admin {admin_name} verified "
                                            f"payment for {request.request_number}."
                                        )
                                    )

                                    db.commit()

                                    st.success("Payment successfully verified!")

                                    st.rerun()

                            except Exception as error:

                                db.rollback()

                                st.error(
                                    "Unable to verify payment. Please try again."
                                )

                                print("Verification Error:", error)

                    with col2:

                        with st.popover(
                            "REJECT PAYMENT",
                            use_container_width=True
                        ):

                            rejection_reason = st.text_area(
                                "Reason for rejection",
                                placeholder="Enter the reason for rejecting this payment...",
                                key=f"reason_{payment.id}"
                            )

                            if st.button(
                                "CONFIRM REJECTION",
                                type="primary",
                                use_container_width=True,
                                key=f"reject_{payment.id}"
                            ):

                                if not rejection_reason.strip():

                                    st.error(
                                        "Please provide a rejection reason."
                                    )

                                else:

                                    try:

                                        payment.payment_status = "Rejected"
                                        payment.verified_by = admin_name

                                        record_activity(
                                            db,
                                            admin_id,
                                            "Payment Rejected",
                                            (
                                                f"Admin {admin_name} rejected "
                                                f"payment for {request.request_number}. "
                                                f"Reason: {rejection_reason.strip()}"
                                            )
                                        )

                                        db.commit()

                                        st.success("Payment rejected.")

                                        st.rerun()

                                    except Exception as error:

                                        db.rollback()

                                        st.error(
                                            "Unable to reject payment."
                                        )

                                        print("Rejection Error:", error)

        # =================================
        # PREVIOUSLY REVIEWED PAYMENTS
        # =================================

        st.divider()

        with st.expander("Previously Reviewed Payments"):

            reviewed_payments = (
                db.query(Payment)
                .join(Payment.request)
                .join(DocumentRequest.student)
                .filter(
                    Payment.payment_status.in_(
                        ["Verified", "Rejected"]
                    )
                )
                .order_by(Payment.id.desc())
                .all()
            )

            if not reviewed_payments:

                st.info("No reviewed payments yet.")

            else:

                for payment in reviewed_payments:

                    request = payment.request
                    student = request.student

                    st.markdown(
                        f"**{request.request_number}**"
                    )

                    st.write(
                        f"Student: {student.first_name} "
                        f"{student.last_name}"
                    )

                    st.write(
                        f"Document: {request.document_type}"
                    )

                    st.write(
                        f"Amount: {format_currency(payment.amount)}"
                    )

                    st.write(
                        f"Payment Status: {payment.payment_status}"
                    )

                    st.write(
                        f"Reviewed By: {payment.verified_by or 'Admin'}"
                    )

                    st.divider()

    except Exception as error:

        st.error(
            "Unable to load payment verification records."
        )

        print("Request Verification Error:", error)

    finally:

        db.close()
