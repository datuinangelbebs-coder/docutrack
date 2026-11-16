
import streamlit as st
from pathlib import Path
from datetime import datetime
from uuid import uuid4

from database import SessionLocal, User, DocumentRequest, Payment


# =====================================
# DOCUMENT SETTINGS
# =====================================

DOCUMENT_FEES = {
    "Transcript of Records": 15.00,
    "Form 137": 15.00,
    "Certificate of Enrollment": 10.00,
    "Certificate of Grades": 10.00,
    "Good Moral Certificate": 10.00,
    "Certificate of Graduation": 15.00,
    "Honorable Dismissal": 15.00
}


# =====================================
# GCASH DEMO SETTINGS
# =====================================

GCASH_ACCOUNT_NAME = "UMTC Demo Registrar"
GCASH_NUMBER = "09XX-XXX-XXXX"

UPLOAD_DIR = (
    Path(__file__).resolve().parent.parent
    / "uploads"
    / "receipts"
)

MAX_FILE_SIZE = 5 * 1024 * 1024

ALLOWED_EXTENSIONS = {
    "png",
    "jpg",
    "jpeg",
    "pdf"
}


# =====================================
# HELPER FUNCTIONS
# =====================================

def format_currency(amount):
    return f"₱{float(amount or 0):,.2f}"


def save_receipt(uploaded_file):

    if uploaded_file is None:
        raise ValueError("Please upload your payment receipt.")

    if "." not in uploaded_file.name:
        raise ValueError("Invalid receipt filename.")

    extension = uploaded_file.name.rsplit(".", 1)[-1].lower()

    if extension not in ALLOWED_EXTENSIONS:
        raise ValueError(
            "Only PNG, JPG, JPEG, and PDF files are allowed."
        )

    file_data = uploaded_file.getvalue()

    if not file_data:
        raise ValueError("The uploaded receipt is empty.")

    if len(file_data) > MAX_FILE_SIZE:
        raise ValueError("Receipt must not exceed 5 MB.")

    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

    filename = f"{uuid4().hex}.{extension}"
    file_path = UPLOAD_DIR / filename

    file_path.write_bytes(file_data)

    return str(file_path)


# =====================================
# DOCUMENT REQUEST PAGE
# =====================================

def show_document_request():

    st.title("Request an Academic Document")

    st.write(
        "Complete the information below to submit "
        "your academic document request."
    )

    st.divider()

    user_id = st.session_state.get("user_id")

    if not user_id:
        st.error("Please log in again.")
        return

    # =================================
    # SHOW LAST SUBMISSION CONFIRMATION
    # =================================

    confirmation = st.session_state.pop(
        "last_request_confirmation",
        None
    )

    if confirmation:

        st.success(
            "Your document request was submitted successfully!"
        )

        st.subheader("Request Confirmation")

        st.write(
            f"**Request Number:** {confirmation['request_number']}"
        )

        st.write(
            f"**Document:** {confirmation['document_type']}"
        )

        st.write(
            f"**Number of Copies:** {confirmation['copies']}"
        )

        st.write(
            f"**Total Fee:** {format_currency(confirmation['total_fee'])}"
        )

        st.write(
            f"**Payment Method:** {confirmation['payment_method']}"
        )

        st.write(
            f"**Payment Status:** {confirmation['payment_status']}"
        )

        st.write(
            "**Request Status:** Submitted"
        )

        st.info(
            "Your queue number has not yet been assigned. "
            "Please monitor your request for updates."
        )

        if confirmation["payment_method"] == "GCash":

            st.warning(
                "Your demo payment is awaiting admin verification."
            )

        else:

            st.info(
                "Your on-site payment is awaiting confirmation "
                "from authorized personnel."
            )

        st.caption(
            "Your request has been saved. You may submit another request below."
        )

        st.divider()

    # =================================
    # FORM VERSION
    # =================================

    if "request_form_version" not in st.session_state:
        st.session_state["request_form_version"] = 0

    form_version = st.session_state["request_form_version"]

    # Dynamic widget keys allow a clean form reset
    # without deleting the saved database records.

    # =================================
    # STUDENT INFORMATION
    # =================================

    st.subheader("Student Information")

    db = SessionLocal()

    try:

        student = (
            db.query(User)
            .filter(
                User.id == user_id,
                User.role == "student",
                User.is_active == True
            )
            .first()
        )

        if not student:
            st.error("Student account could not be found.")
            return

        full_name = " ".join(
            part for part in [
                student.first_name,
                student.middle_name,
                student.last_name
            ]
            if part
        )

        col1, col2 = st.columns(2)

        with col1:
            st.text_input(
                "Student Name",
                value=full_name,
                disabled=True
            )

        with col2:
            st.text_input(
                "Student ID",
                value=student.student_id or "Not available",
                disabled=True
            )

        st.caption(
            "Student information is taken from your registered account."
        )

    finally:
        db.close()

    st.divider()

    # =================================
    # 1. DOCUMENT INFORMATION
    # =================================

    st.subheader("1. Document Information")

    document_type = st.selectbox(
        "Select Document Type",
        list(DOCUMENT_FEES.keys()),
        key=f"document_type_{form_version}"
    )

    copies = st.number_input(
        "Number of Copies",
        min_value=1,
        max_value=10,
        value=1,
        step=1,
        key=f"copies_{form_version}"
    )

    fee_per_copy = DOCUMENT_FEES[document_type]
    total_fee = fee_per_copy * int(copies)

    col1, col2 = st.columns(2)

    with col1:
        st.metric(
            "Fee per Copy",
            format_currency(fee_per_copy)
        )

    with col2:
        st.metric(
            "Estimated Total Fee",
            format_currency(total_fee)
        )

    st.warning(
        "The displayed fees are temporary demo amounts, "
        "not confirmed official UMTC fees."
    )

    st.divider()

    # =================================
    # 2. PAYMENT INFORMATION
    # =================================

    st.subheader("2. Payment Information")

    payment_method = st.radio(
        "Choose Payment Method",
        ["GCash", "On-site Payment"],
        horizontal=True,
        key=f"payment_method_{form_version}"
    )

    uploaded_receipt = None
    reference_number = ""

    # =================================
    # GCASH DEMO PAYMENT
    # =================================

    if payment_method == "GCash":

        st.warning(
            "DEMO PAYMENT ONLY — NOT A REAL GCASH ACCOUNT"
        )

        with st.container(border=True):

            st.subheader("GCash Demo Payment Details")

            st.markdown(
                f"""
                **Account Name**

                {GCASH_ACCOUNT_NAME}

                **GCash Number**

                `{GCASH_NUMBER}`
                """
            )

            st.metric(
                "Amount to Pay (Demo)",
                format_currency(total_fee)
            )

            st.info(
                "This is a fictional payment account for system "
                "demonstration. DO NOT send real money. "
                "Use a sample receipt for testing."
            )

            st.markdown(
                """
                **Demo Payment Instructions**

                1. Check the total amount displayed above.
                2. Use the demo details for presentation only.
                3. Upload a sample receipt.
                4. Enter a sample reference number.
                5. Submit your request for admin verification.
                """
            )

        uploaded_receipt = st.file_uploader(
            "Upload Demo Payment Receipt",
            type=["png", "jpg", "jpeg", "pdf"],
            accept_multiple_files=False,
            help="Accepted formats: PNG, JPG, JPEG, PDF. Maximum 5 MB.",
            key=f"receipt_{form_version}"
        )

        reference_number = st.text_input(
            "GCash Reference Number",
            placeholder="Enter sample reference number",
            max_chars=100,
            key=f"reference_{form_version}"
        )

    # =================================
    # ON-SITE PAYMENT
    # =================================

    else:

        with st.container(border=True):

            st.subheader("On-site Payment")

            st.metric(
                "Amount to Pay",
                format_currency(total_fee)
            )

            st.info(
                "Pay at the authorized UMTC cashier or "
                "designated payment office. Authorized "
                "personnel must confirm your payment "
                "before it is marked as paid."
            )

            st.caption(
                "Your payment status will remain Unpaid "
                "until confirmed by authorized personnel."
            )

    st.divider()

    # =================================
    # 3. IMPORTANT REMINDERS
    # =================================

    st.subheader("3. Important Reminders")

    st.markdown(
        """
        - Check your student information before submitting.
        - Select the correct academic document.
        - Choose the correct number of copies.
        - Check the estimated total fee.
        - Upload a readable receipt for demo GCash payments.
        - Keep your reference number.
        - Wait for admin payment verification.
        - Monitor your request through the tracking page.
        """
    )

    st.divider()

    
    # =================================
    # 4. REQUEST SUBMISSION
    # =================================

    st.subheader("4. Submit Your Request")

    confirm_information = st.checkbox(
        "I confirm that the information provided is correct.",
        key=f"confirm_{form_version}"
    )

    if st.button(
        "SUBMIT DOCUMENT REQUEST",
        use_container_width=True,
        type="primary",
        key=f"submit_{form_version}"
    ):

        # VALIDATION

        if not confirm_information:
            st.error(
                "Please confirm that your information is correct."
            )
            return

        if payment_method == "GCash" and uploaded_receipt is None:
            st.error("Please upload your demo payment receipt.")
            return

        if payment_method == "GCash" and not reference_number.strip():
            st.error("Please enter your GCash reference number.")
            return

        if (
            payment_method == "GCash"
            and not reference_number.strip().isalnum()
        ):
            st.error(
                "Reference number must contain only letters and numbers."
            )
            return

        receipt_path = None
        submission_success = False
        confirmation_data = None

        db = SessionLocal()

        try:

            student = (
                db.query(User)
                .filter(
                    User.id == user_id,
                    User.role == "student",
                    User.is_active == True
                )
                .first()
            )

            if not student:
                st.error("Student account could not be found.")
                return

            # CHECK DUPLICATE REFERENCE NUMBER

            if payment_method == "GCash":

                existing_payment = (
                    db.query(Payment)
                    .filter(
                        Payment.reference_number
                        == reference_number.strip()
                    )
                    .first()
                )

                if existing_payment:
                    st.error(
                        "This reference number has already been submitted."
                    )
                    return

                # SAVE RECEIPT

                receipt_path = save_receipt(uploaded_receipt)

            # GENERATE REQUEST NUMBER

            request_number = (
                f"UMTC-{datetime.now():%Y%m%d}-"
                f"{uuid4().hex[:6].upper()}"
            )

            payment_status = (
                "Awaiting Verification"
                if payment_method == "GCash"
                else "Unpaid"
            )

            # CREATE DOCUMENT REQUEST

            new_request = DocumentRequest(
                request_number=request_number,
                queue_number=None,
                student_id=user_id,
                document_type=document_type,
                copies=int(copies),
                total_fee=total_fee,
                request_status="Submitted"
            )

            db.add(new_request)
            db.flush()

            # CREATE PAYMENT RECORD

            new_payment = Payment(
                request_id=new_request.id,
                payment_method=payment_method,
                amount=total_fee,
                receipt_file=receipt_path,
                reference_number=(
                    reference_number.strip()
                    if payment_method == "GCash"
                    else None
                ),
                payment_status=payment_status
            )

            db.add(new_payment)

            # SAVE DATABASE RECORDS

            db.commit()

            # PREPARE CONFIRMATION

            confirmation_data = {
                "request_number": request_number,
                "document_type": document_type,
                "copies": int(copies),
                "total_fee": total_fee,
                "payment_method": payment_method,
                "payment_status": payment_status
            }

            submission_success = True

        except ValueError as error:

            db.rollback()
            st.error(str(error))

        except Exception as error:

            db.rollback()

            if receipt_path:
                try:
                    Path(receipt_path).unlink(missing_ok=True)
                except OSError:
                    pass

            st.error(
                "Unable to submit your request. "
                "Please try again."
            )

            print("Document Request Error:", error)

        finally:

            db.close()

        # =================================
        # RESET FORM AFTER SUCCESSFUL SAVE
        # =================================

        if submission_success:

            st.session_state["last_request_confirmation"] = (
                confirmation_data
            )

            # Generate new widget keys.
            # Old form values will no longer be used.

            st.session_state["request_form_version"] = (
                form_version + 1
            )

            # Reload page with fresh form widgets.

            st.rerun()
