
import streamlit as st
import pandas as pd
import csv
import io

from datetime import date, datetime, timedelta
from database import SessionLocal, DocumentRequest


# ==============================
# HELPER FUNCTIONS
# ==============================

def get_payment_status(request):
    if request.payment:
        return request.payment.payment_status or "Unpaid"
    return "No Payment Record"


def get_percentage(value, total):
    if total == 0:
        return 0
    return (value / total) * 100


def get_report_data(start_date, end_date):
    db = SessionLocal()

    try:
        requests = (
            db.query(DocumentRequest)
            .filter(
                DocumentRequest.submitted_at >= datetime.combine(
                    start_date, datetime.min.time()
                ),
                DocumentRequest.submitted_at < datetime.combine(
                    end_date + timedelta(days=1),
                    datetime.min.time()
                )
            )
            .order_by(DocumentRequest.submitted_at.desc())
            .all()
        )

        return [
            {
                "Request Number": request.request_number,
                "Student Name": (
                    f"{request.student.first_name or ''} "
                    f"{request.student.last_name or ''}"
                    if request.student else "Unavailable"
                ),
                "Student ID": (
                    request.student.student_id
                    if request.student else "Unavailable"
                ),
                "Document Type": request.document_type,
                "Copies": request.copies,
                "Total Fee": request.total_fee,
                "Request Status": request.request_status,
                "Payment Status": get_payment_status(request),
                "Queue Number": request.queue_number or "Not Assigned",
                "Date Submitted": (
                    request.submitted_at.strftime("%Y-%m-%d %H:%M")
                    if request.submitted_at else "Unavailable"
                )
            }
            for request in requests
        ]

    finally:
        db.close()


# ==============================
# MAIN REPORTS PAGE
# ==============================

def show_admin_reports():

    st.title("Reports and Analytics")
    st.caption(
        "Monitor document requests, payment activity, "
        "and registrar office performance."
    )

    # ==============================
    # DATE FILTER
    # ==============================

    with st.container(border=True):
        st.subheader("Report Period")

        today = date.today()
        first_day = today.replace(day=1)

        date_range = st.date_input(
            "Select date range",
            value=(first_day, today)
        )

    if not isinstance(date_range, (tuple, list)) or len(date_range) != 2:
        st.info("Please select a start date and end date.")
        return

    start_date, end_date = date_range

    if start_date > end_date:
        st.error("Start date cannot be later than end date.")
        return

    # ==============================
    # FETCH DATA
    # ==============================

    try:
        records = get_report_data(start_date, end_date)

    except Exception as error:
        st.error(f"Unable to generate reports: {error}")
        return

    df = pd.DataFrame(records)

    if df.empty:
        st.divider()
        st.info("No document requests found for the selected period.")
        return

    # ==============================
    # REQUEST COUNTS
    # ==============================

    total_requests = len(df)

    pending = int(df["Request Status"].isin([
        "Submitted",
        "Under Review",
        "Pending Requirements"
    ]).sum())

    processing = int(df["Request Status"].isin([
        "Approved",
        "Waiting in Queue",
        "Processing",
        "Ready for Claiming"
    ]).sum())

    released = int(
        (df["Request Status"] == "Released").sum()
    )

    rejected = int(
        (df["Request Status"] == "Rejected").sum()
    )

    # ==============================
    # REQUEST OVERVIEW
    # ==============================

    st.divider()
    st.subheader("Request Overview")

    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        st.metric(
            "Total Requests",
            total_requests
        )

    with col2:
        st.metric(
            "Pending",
            pending,
            f"{get_percentage(pending, total_requests):.1f}%"
        )

    with col3:
        st.metric(
            "Processing",
            processing,
            f"{get_percentage(processing, total_requests):.1f}%"
        )

    with col4:
        st.metric(
            "Released",
            released,
            f"{get_percentage(released, total_requests):.1f}%"
        )

    with col5:
        st.metric(
            "Rejected",
            rejected,
            f"{get_percentage(rejected, total_requests):.1f}%"
        )

    st.caption(
        "Percentages are calculated based on total document requests."
    )

    # ==============================
    # PAYMENT OVERVIEW
    # ==============================

    st.divider()
    st.subheader("Payment Overview")

    payment_statuses = df["Payment Status"].value_counts()

    verified_count = int(
        payment_statuses.get("Verified", 0)
    )

    awaiting_count = int(
        payment_statuses.get("Awaiting Verification", 0)
    )

    rejected_payments = int(
        payment_statuses.get("Rejected", 0)
    )

    total_payments = (
        verified_count + awaiting_count + rejected_payments
    )

    verified_amount = pd.to_numeric(
        df.loc[
            df["Payment Status"] == "Verified",
            "Total Fee"
        ],
        errors="coerce"
    ).fillna(0).sum()

    payment_col1, payment_col2 = st.columns([1, 2])

    with payment_col1:

        st.metric(
            "Verified Payments",
            verified_count,
            f"{get_percentage(verified_count, total_payments):.1f}%"
        )

        st.metric(
            "Awaiting Verification",
            awaiting_count,
            f"{get_percentage(awaiting_count, total_payments):.1f}%"
        )

        st.metric(
            "Rejected Payments",
            rejected_payments,
            f"{get_percentage(rejected_payments, total_payments):.1f}%"
        )

        st.caption("Verified request fees")
        st.subheader(f"₱{verified_amount:,.2f}")

    with payment_col2:

        payment_data = pd.DataFrame({
            "Payment Status": [
                "Verified",
                "Awaiting Verification",
                "Rejected"
            ],
            "Number of Payments": [
                verified_count,
                awaiting_count,
                rejected_payments
            ]
        })

        payment_data = payment_data[
            payment_data["Number of Payments"] > 0
        ]

        if not payment_data.empty:
            st.bar_chart(
                payment_data.set_index("Payment Status"),
                height=210
            )
        else:
            st.info("No payment records for this period.")

    st.caption(
        "Payment percentages are based on records with the three "
        "listed payment statuses. The amount shown is not a live GCash balance."
    )

    # ==============================
    # REQUEST STATUS GRAPH
    # ==============================

    st.divider()
    st.subheader("Request Status Statistics")

    status_data = (
        df["Request Status"]
        .value_counts()
        .rename_axis("Request Status")
        .reset_index(name="Number of Requests")
    )

    status_data["Percentage"] = (
        status_data["Number of Requests"]
        .apply(lambda value: get_percentage(value, total_requests))
        .round(1)
    )

    status_data["Label"] = status_data.apply(
        lambda row: (
            f"{row['Number of Requests']} "
            f"({row['Percentage']:.1f}%)"
        ),
        axis=1
    )

    st.bar_chart(
        status_data.set_index("Request Status")[
            ["Number of Requests"]
        ],
        height=250
    )

    st.dataframe(
        status_data[
            ["Request Status", "Number of Requests", "Percentage"]
        ].rename(columns={
            "Percentage": "Percentage (%)"
        }),
        use_container_width=True,
        hide_index=True
    )

    # ==============================
    # DOCUMENT AND DAILY STATISTICS
    # ==============================

    st.divider()

    chart_col1, chart_col2 = st.columns(2)

    with chart_col1:

        st.subheader("Most Requested Documents")

        document_data = (
            df["Document Type"]
            .value_counts()
            .rename_axis("Document Type")
            .reset_index(name="Requests")
        )

        document_data["Percentage"] = (
            document_data["Requests"]
            .apply(lambda value: get_percentage(value, total_requests))
            .round(1)
        )

        st.bar_chart(
            document_data.set_index("Document Type")[["Requests"]],
            height=260
        )

        st.dataframe(
            document_data.rename(columns={
                "Percentage": "Percentage (%)"
            }),
            use_container_width=True,
            hide_index=True
        )

    with chart_col2:

        st.subheader("Daily Requests")

        df["Submission Date"] = pd.to_datetime(
            df["Date Submitted"],
            errors="coerce"
        ).dt.date

        daily_data = (
            df.dropna(subset=["Submission Date"])
            .groupby("Submission Date")
            .size()
            .reset_index(name="Requests")
            .sort_values("Submission Date")
        )

        if not daily_data.empty:
            st.line_chart(
                daily_data.set_index("Submission Date"),
                height=260
            )
        else:
            st.info("No daily request data available.")

    # ==============================
    # REQUEST RECORDS
    # ==============================

    st.divider()
    st.subheader("Document Request Records")

    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True
    )

    # ==============================
    # CSV DOWNLOAD
    # ==============================

    st.divider()
    st.subheader("Download Reports")

    csv_buffer = io.StringIO()

    df.to_csv(
        csv_buffer,
        index=False,
        quoting=csv.QUOTE_MINIMAL
    )

    filename = (
        f"UMTC_Document_Requests_"
        f"{start_date}_{end_date}.csv"
    )

    st.download_button(
        label="Download CSV Report",
        data=csv_buffer.getvalue(),
        file_name=filename,
        mime="text/csv",
        type="primary",
        use_container_width=True
    )

    st.caption(
        f"Report period: {start_date} to {end_date}"
    )
