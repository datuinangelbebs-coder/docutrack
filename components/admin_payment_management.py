
import streamlit as st
import html

from pathlib import Path
from datetime import datetime

from database import (
    SessionLocal,
    Payment,
    User,
    ActivityLog
)


# =====================================
# PAYMENT SETTINGS
# =====================================

PAYMENT_STATUSES = [
    "Unpaid",
    "Awaiting Verification",
    "Verified",
    "Paid On-site",
    "Rejected"
]

PROJECT_DIR = Path(__file__).resolve().parent.parent
RECEIPT_DIR = PROJECT_DIR / "uploads" / "receipts"


# =====================================
# CUSTOM DESIGN
# =====================================

def load_payment_management_style():

    st.markdown("""
    <style>

    .payment-header {
        background: linear-gradient(120deg, #3B0D1A, #711D32);
        padding: 30px;
        border-radius: 18px;
        color: #FFF9EF;
        margin-bottom: 25px;
        box-shadow: 0 8px 22px rgba(59, 13, 26, 0.13);
    }

    .payment-header h1 {
        color: #FFF9EF;
        font-size: 29px;
        margin-bottom: 8px;
    }

    .payment-header p {
        color: #F1DDE0;
        margin: 0;
        font-size: 14px;
    }

    .payment-summary {
        background: #FFFFFF;
        padding: 20px;
        border-radius: 15px;
        border: 1px solid #EEE8E3;
        box-shadow: 0 4px 14px rgba(59, 13, 26, 0.05);
        min-height: 115px;
    }

    .payment-label {
        color: #777078;
        font-size: 13px;
        margin-bottom: 9px;
    }

    .payment-value {
        color: #711D32;
        font-size: 27px;
        font-weight: 700;
    }

    .payment-section {
        color: #3B0D1A;
        font-size: 21px;
        font-weight: 700;
        margin-top: 15px;
        margin-bottom: 5px;
    }

    </style>
    """, unsafe_allow_html=True)


# =====================================
# SUMMARY CARD
# =====================================

def payment_summary_card(label, value):

    st.markdown(
        f"""
        <div class="payment-summary">
            <div class="payment-label">
                {html.escape(str(label))}
            </div>
            <div class="payment-value">
                {html.escape(str(value))}
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )


# =====================================
# PAYMENT STATUS DISPLAY
# =====================================

def show_payment_status(status):

    status = (status or "Unpaid").strip()
    normalized = status.lower()

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


# =====================================
# RECEIPT FILE VALIDATION
# =====================================

def get_receipt_path(receipt_file):

    if not receipt_file:
        return None

    try:

        stored_path = Path(receipt_file)

        if stored_path.is_absolute():
            file_path = stored_path.resolve()
        else:
            file_path = (PROJECT_DIR / stored_path).resolve()

        allowed_directory = RECEIPT_DIR.resolve()

        # Only allow files inside the receipt folder.
        file_path.relative_to(allowed_directory)

        if file_path.is_file():
            return file_path

    except (ValueError, OSError):
        return None

    return None


# =====================================
# DISPLAY PAYMENT RECEIPT
# =====================================

def display_payment_receipt(payment):

    st.markdown("**Payment Receipt**")

    if not payment.receipt_file:

        st.warning("No receipt file is attached.")
        return

    receipt_path = get_receipt_path(payment.receipt_file)

    if not receipt_path:

        st.error(
            "Receipt file could not be found or accessed."
        )
        return

    extension = receipt_path.suffix.lower()

    if extension in [".png", ".jpg", ".jpeg"]:

        st.image(
            str(receipt_path),
            caption="Uploaded Payment Receipt",
            use_container_width=True
        )

    elif extension == ".pdf":

        with open(receipt_path, "rb") as file:

            st.download_button(
                label="Download PDF Receipt",
                data=file.read(),
                file_name=receipt_path.name,
                mime="application/pdf",
                key=f"receipt_download_{payment.id}",
                use_container_width=True
            )

    else:

        st.warning("Unsupported receipt file format.")


# =====================================
# MAIN PAYMENT MANAGEMENT
# =====================================

def show_admin_payment_management():

    load_payment_management_style()

    # =================================
    # ACCESS CHECK
    # =================================

    if st.session_state.get("user_role") != "admin":

        st.error("Access denied. Admin account required.")
        st.stop()

    admin_id = st.session_state.get("user_id")

    db = SessionLocal()

    try:

        # =================================
        # GET PAYMENT RECORDS
        # =================================

        payments = (
            db.query(Payment)
            .order_by(Payment.id.desc())
            .all()
        )

        # =================================
        # PAGE HEADER
        # =================================

        st.markdown("""
        <div class="payment-header">
            <h1>Payment Management</h1>
            <p>
                Monitor student payment records,
                submitted receipts, and payment status.
            </p>
        </div>
        """, unsafe_allow_html=True)

        # =================================
        # PAYMENT SUMMARY
        # =================================

        total_records = len(payments)

        awaiting = sum(
            1 for p in payments
            if (p.payment_status or "").lower()
            in ["awaiting verification", "pending verification"]
        )

        verified = sum(
            1 for p in payments
            if (p.payment_status or "").lower() == "verified"
        )

        rejected = sum(
            1 for p in payments
            if (p.payment_status or "").lower() == "rejected"
        )

        paid_onsite = sum(
            1 for p in payments
            if (p.payment_status or "").lower()
            in ["paid on-site", "paid onsite"]
        )

        confirmed_amount = sum(
            float(p.amount or 0)
            for p in payments
            if (p.payment_status or "").lower()
            in ["verified", "paid on-site", "paid onsite"]
        )

        st.markdown(
            '<div class="payment-section">Payment Overview</div>',
            unsafe_allow_html=True
        )

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            payment_summary_card("Total Records", total_records)

        with col2:
            payment_summary_card("Awaiting Verification", awaiting)

        with col3:
            payment_summary_card("Verified", verified)

        with col4:
            payment_summary_card("Rejected", rejected)

        st.write("")

        col1, col2 = st.columns(2)

        with col1:
            payment_summary_card("Paid On-site", paid_onsite)

        with col2:
            payment_summary_card(
                "Confirmed Amount",
                f"₱{confirmed_amount:,.2f}"
            )

        st.divider()

        # =================================
        # SEARCH AND FILTER
        # =================================

        st.markdown(
            '<div class="payment-section">Payment Records</div>',
            unsafe_allow_html=True
        )

        col1, col2 = st.columns([2, 1])

        with col1:

            search_query = st.text_input(
                "Search Payment",
                placeholder="Request number, student name, or student ID...",
                key="admin_payment_search"
            )

        with col2:

            selected_status = st.selectbox(
                "Payment Status",
                ["All Payments"] + PAYMENT_STATUSES,
                key="admin_payment_filter"
            )

        # =================================
        # FILTER RECORDS
        # =================================

        filtered_payments = []

        for payment in payments:

            request = payment.request
            student = request.student if request else None

            student_name = ""
            student_number = ""
            request_number = ""

            if student:

                student_name = (
                    f"{student.first_name or ''} "
                    f"{student.last_name or ''}"
                )

                student_number = str(student.student_id or "")

            if request:

                request_number = str(
                    request.request_number or ""
                )

            searchable_text = " ".join([
                request_number,
                student_name,
                student_number,
                str(payment.reference_number or ""),
                str(payment.payment_method or "")
            ]).lower()

            if search_query.strip().lower() not in searchable_text:
                continue

            status = (payment.payment_status or "Unpaid").lower()

            if selected_status != "All Payments":

                if status != selected_status.lower():
                    continue

            filtered_payments.append(payment)

        st.caption(
            f"Showing {len(filtered_payments)} "
            f"of {total_records} payment records"
        )

        st.divider()

        # =================================
        # EMPTY STATE
        # =================================

        if not filtered_payments:

            st.info("No payment records found.")
            return

        # =================================
        # PAYMENT RECORD CARDS
        # =================================

        for payment in filtered_payments:

            request = payment.request
            student = request.student if request else None

            with st.container(border=True):

                # HEADER

                col1, col2 = st.columns([2, 1])

                with col1:

                    document_name = (
                        request.document_type
                        if request else "Unknown Document"
                    )

                    st.markdown(
                        f"### {html.escape(str(document_name))}"
                    )

                    st.caption(
                        f"Request Number: "
                        f"{html.escape(str(request.request_number if request else 'Unavailable'))}"
                    )

                with col2:

                    show_payment_status(payment.payment_status)

                st.divider()

                # STUDENT INFORMATION

                st.markdown("**Student Information**")

                col1, col2, col3 = st.columns(3)

                with col1:

                    st.caption("STUDENT NAME")

                    if student:

                        full_name = (
                            f"{student.first_name or ''} "
                            f"{student.last_name or ''}"
                        ).strip()

                        st.write(full_name or "Not available")

                    else:

                        st.write("Not available")

                with col2:

                    st.caption("STUDENT ID")

                    st.write(
                        student.student_id
                        if student else "Not available"
                    )

                with col3:

                    st.caption("EMAIL")

                    st.write(
                        student.email
                        if student else "Not available"
                    )

                st.divider()

                # PAYMENT INFORMATION

                st.markdown("**Payment Details**")

                col1, col2, col3 = st.columns(3)

                with col1:

                    st.caption("PAYMENT METHOD")

                    st.write(
                        payment.payment_method or "Not specified"
                    )

                with col2:

                    st.caption("AMOUNT")

                    st.write(
                        f"₱{float(payment.amount or 0):,.2f}"
                    )

                with col3:

                    st.caption("REFERENCE NUMBER")

                    st.write(
                        payment.reference_number or "Not available"
                    )

                # RECEIPT

                display_payment_receipt(payment)

                # VERIFICATION INFORMATION

                if payment.verified_by:

                    st.caption(
                        f"Verified/Processed by: {payment.verified_by}"
                    )

                if payment.payment_date:

                    st.caption("PAYMENT / CONFIRMATION DATE")

                    st.write(
                        payment.payment_date.strftime(
                            "%B %d, %Y at %I:%M %p"
                        )
                    )

                # =================================
                # ADMIN PAYMENT ACTIONS
                # =================================

                st.divider()

                with st.expander("Manage Payment"):

                    current_status = (
                        payment.payment_status or "Unpaid"
                    )

                    if current_status not in PAYMENT_STATUSES:
                        current_status = "Unpaid"

                    new_status = st.selectbox(
                        "Update Payment Status",
                        PAYMENT_STATUSES,
                        index=PAYMENT_STATUSES.index(current_status),
                        key=f"payment_status_{payment.id}"
                    )

                    if new_status == "Verified":

                        st.info(
                            "Verify only after checking the receipt "
                            "and confirming the payment through the "
                            "authorized payment process."
                        )

                    elif new_status == "Paid On-site":

                        st.info(
                            "Use this status only after confirmation "
                            "from the authorized cashier."
                        )

                    elif new_status == "Rejected":

                        st.warning(
                            "Check the submitted payment information "
                            "before rejecting it."
                        )

                    if st.button(
                        "Save Payment Update",
                        key=f"save_payment_{payment.id}",
                        type="primary",
                        use_container_width=True
                    ):

                        try:

                            old_status = payment.payment_status or "Unpaid"

                            if new_status == old_status:

                                st.info(
                                    "No payment status changes were made."
                                )

                            elif new_status == "Verified":

                                receipt_path = get_receipt_path(
                                    payment.receipt_file
                                )

                                if not receipt_path:

                                    st.error(
                                        "Cannot verify this payment "
                                        "because its receipt is missing."
                                    )

                                else:

                                    payment.payment_status = new_status
                                    payment.payment_date = datetime.now()

                                    admin = db.query(User).filter(
                                        User.id == admin_id
                                    ).first()

                                    payment.verified_by = (
                                        admin.email if admin
                                        else f"Admin ID: {admin_id}"
                                    )

                                    db.add(
                                        ActivityLog(
                                            user_id=admin_id,
                                            action="Updated Payment Status",
                                            details=(
                                                f"Payment ID {payment.id}: "
                                                f"{old_status} → {new_status}"
                                            )
                                        )
                                    )

                                    db.commit()

                                    st.success(
                                        "Payment status updated successfully."
                                    )

                                    st.rerun()

                            else:

                                payment.payment_status = new_status

                                if new_status == "Paid On-site":

                                    payment.payment_date = datetime.now()

                                    admin = db.query(User).filter(
                                        User.id == admin_id
                                    ).first()

                                    payment.verified_by = (
                                        admin.email if admin
                                        else f"Admin ID: {admin_id}"
                                    )

                                db.add(
                                    ActivityLog(
                                        user_id=admin_id,
                                        action="Updated Payment Status",
                                        details=(
                                            f"Payment ID {payment.id}: "
                                            f"{old_status} → {new_status}"
                                        )
                                    )
                                )

                                db.commit()

                                st.success(
                                    "Payment status updated successfully."
                                )

                                st.rerun()

                        except Exception as e:

                            db.rollback()

                            st.error(
                                f"Unable to update payment: {e}"
                            )

    except Exception as e:

        st.error("Unable to load payment management.")
        st.exception(e)

    finally:

        db.close()
