
import streamlit as st

from database import SessionLocal, User, ActivityLog


def get_admin_id():
    return st.session_state.get("user_id")


def get_account_data():
    db = SessionLocal()

    try:
        users = (
            db.query(User)
            .order_by(User.created_at.desc())
            .all()
        )

        return [
            {
                "id": user.id,
                "First Name": user.first_name or "",
                "Middle Name": user.middle_name or "",
                "Last Name": user.last_name or "",
                "Student ID": user.student_id or "",
                "Email": user.email or "",
                "Course": user.course or "",
                "Year Level": user.year_level or "",
                "Role": user.role or "student",
                "Status": (
                    "Active" if user.is_active else "Inactive"
                ),
                "Created At": (
                    user.created_at.strftime("%Y-%m-%d")
                    if user.created_at else "Unavailable"
                )
            }
            for user in users
        ]

    finally:
        db.close()


def update_account_status(user_id, new_status):
    db = SessionLocal()

    try:
        user = db.query(User).filter(
            User.id == user_id
        ).first()

        if not user:
            return False, "Account not found."

        # Only student accounts can be changed here.
        if (user.role or "").lower() != "student":
            return False, "Only student accounts can be modified."

        if bool(user.is_active) == new_status:
            return False, "No changes were made."

        user.is_active = new_status

        admin_id = get_admin_id()

        if admin_id:
            log = ActivityLog(
                user_id=admin_id,
                action=(
                    "Student Account Activated"
                    if new_status
                    else "Student Account Deactivated"
                ),
                details=(
                    f"Account: {user.email} | "
                    f"Student ID: {user.student_id}"
                )
            )
            db.add(log)

        db.commit()

        return True, (
            "Student account activated successfully."
            if new_status
            else "Student account deactivated successfully."
        )

    except Exception as error:
        db.rollback()
        return False, f"Unable to update account: {error}"

    finally:
        db.close()


def show_admin_account_management():

    st.title("Account Management")
    st.caption(
        "View registered accounts and manage student account access."
    )

    try:
        accounts = get_account_data()

    except Exception as error:
        st.error(f"Unable to load accounts: {error}")
        return

    if not accounts:
        st.info("No registered accounts found.")
        return

    # ACCOUNT SUMMARY
    total_accounts = len(accounts)

    active_accounts = sum(
        1 for account in accounts
        if account["Status"] == "Active"
    )

    inactive_accounts = total_accounts - active_accounts

    student_accounts = sum(
        1 for account in accounts
        if account["Role"].lower() == "student"
    )

    admin_accounts = sum(
        1 for account in accounts
        if account["Role"].lower() == "admin"
    )

    st.subheader("Account Overview")

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Total Accounts", total_accounts)
    col2.metric("Active Accounts", active_accounts)
    col3.metric("Inactive Accounts", inactive_accounts)
    col4.metric("Student Accounts", student_accounts)

    st.caption(f"Administrator accounts: {admin_accounts}")

    st.divider()

    # SEARCH AND FILTER
    st.subheader("Registered Accounts")

    search_text = st.text_input(
        "Search account",
        placeholder="Search name, Student ID, or email..."
    ).strip().lower()

    filter_col1, filter_col2 = st.columns(2)

    with filter_col1:
        role_filter = st.selectbox(
            "Account Role",
            ["All Roles", "Student", "Admin"]
        )

    with filter_col2:
        status_filter = st.selectbox(
            "Account Status",
            ["All Statuses", "Active", "Inactive"]
        )

    filtered_accounts = []

    for account in accounts:

        full_name = (
            f"{account['First Name']} "
            f"{account['Middle Name']} "
            f"{account['Last Name']}"
        ).lower()

        searchable_text = (
            f"{full_name} "
            f"{account['Student ID']} "
            f"{account['Email']}"
        ).lower()

        if search_text and search_text not in searchable_text:
            continue

        if (
            role_filter != "All Roles"
            and account["Role"].lower() != role_filter.lower()
        ):
            continue

        if (
            status_filter != "All Statuses"
            and account["Status"] != status_filter
        ):
            continue

        filtered_accounts.append(account)

    st.caption(
        f"Showing {len(filtered_accounts)} of {total_accounts} accounts"
    )

    if not filtered_accounts:
        st.info("No matching accounts found.")
        return

    # ACCOUNT TABLE
    table_data = []

    for account in filtered_accounts:
        table_data.append({
            "Name": (
                f"{account['First Name']} "
                f"{account['Last Name']}"
            ),
            "Student ID": account["Student ID"],
            "Email": account["Email"],
            "Course": account["Course"],
            "Year": account["Year Level"],
            "Role": account["Role"].title(),
            "Status": account["Status"],
            "Date Registered": account["Created At"]
        })

    st.dataframe(
        table_data,
        use_container_width=True,
        hide_index=True
    )

    # ACCOUNT DETAILS AND ACTIONS
    st.divider()
    st.subheader("Manage Student Account")

    student_options = {
        (
            f"{account['First Name']} {account['Last Name']} "
            f"({account['Student ID']})"
        ): account
        for account in filtered_accounts
        if account["Role"].lower() == "student"
    }

    if not student_options:
        st.info("No student accounts available in this filter.")
        return

    selected_label = st.selectbox(
        "Select student account",
        list(student_options.keys())
    )

    selected_account = student_options[selected_label]

    with st.container(border=True):

        st.markdown(
            f"**{selected_account['First Name']} "
            f"{selected_account['Last Name']}**"
        )

        st.write("Student ID:", selected_account["Student ID"])
        st.write("Email:", selected_account["Email"])
        st.write("Course:", selected_account["Course"])
        st.write("Year Level:", selected_account["Year Level"])
        st.write("Current Status:", selected_account["Status"])

        if selected_account["Status"] == "Active":

            if st.button(
                "Deactivate Account",
                type="secondary",
                use_container_width=True,
                key=f"deactivate_{selected_account['id']}"
            ):
                success, message = update_account_status(
                    selected_account["id"],
                    False
                )

                if success:
                    st.success(message)
                    st.rerun()
                else:
                    st.error(message)

        else:

            if st.button(
                "Activate Account",
                type="primary",
                use_container_width=True,
                key=f"activate_{selected_account['id']}"
            ):
                success, message = update_account_status(
                    selected_account["id"],
                    True
                )

                if success:
                    st.success(message)
                    st.rerun()
                else:
                    st.error(message)

    st.caption(
        "Only student accounts can be activated or deactivated. "
        "Administrator accounts cannot be modified from this page."
    )
