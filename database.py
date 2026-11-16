
from pathlib import Path
from datetime import datetime

from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    DateTime,
    ForeignKey,
    Float,
    Boolean
)

from sqlalchemy.orm import (
    declarative_base,
    relationship,
    sessionmaker
)


# =====================================
# DATABASE CONFIGURATION
# =====================================

BASE_DIR = Path(__file__).resolve().parent
DATABASE_DIR = BASE_DIR / "database"

DATABASE_DIR.mkdir(
    parents=True,
    exist_ok=True
)

DATABASE_PATH = DATABASE_DIR / "umtc_queue.db"

DATABASE_URL = f"sqlite:///{DATABASE_PATH.as_posix()}"

engine = create_engine(
    DATABASE_URL,
    connect_args={
        "check_same_thread": False
    },
    pool_pre_ping=True
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

Base = declarative_base()


# =====================================
# STUDENT AND ADMIN ACCOUNTS
# =====================================

class User(Base):

    __tablename__ = "users"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    first_name = Column(
        String(100),
        nullable=False
    )

    middle_name = Column(String(100))

    last_name = Column(
        String(100),
        nullable=False
    )

    course = Column(String(100))

    year_level = Column(String(50))

    student_id = Column(
        String(50),
        unique=True,
        nullable=True
    )

    email = Column(
        String(150),
        unique=True,
        nullable=False
    )

    password_hash = Column(
        String(255),
        nullable=False
    )

    role = Column(
        String(20),
        default="student"
    )

    is_active = Column(
        Boolean,
        default=True
    )

    created_at = Column(
        DateTime,
        default=datetime.now
    )

    requests = relationship(
        "DocumentRequest",
        back_populates="student"
    )


# =====================================
# DOCUMENT REQUESTS
# =====================================

class DocumentRequest(Base):

    __tablename__ = "document_requests"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    request_number = Column(
        String(50),
        unique=True,
        nullable=False
    )

    queue_number = Column(
        String(50),
        unique=True,
        nullable=True
    )

    student_id = Column(
        Integer,
        ForeignKey("users.id")
    )

    document_type = Column(
        String(150),
        nullable=False
    )

    copies = Column(
        Integer,
        default=1
    )

    total_fee = Column(
        Float,
        default=0
    )

    # DOCUMENT RELEASE INFORMATION

    released_to = Column(
        String(150),
        nullable=True
    )

    released_at = Column(
        DateTime,
        nullable=True
    )

    released_by = Column(
        String(150),
        nullable=True
    )

    request_status = Column(
        String(50),
        default="Submitted"
    )

    submitted_at = Column(
        DateTime,
        default=datetime.now
    )

    updated_at = Column(
        DateTime,
        default=datetime.now,
        onupdate=datetime.now
    )

    student = relationship(
        "User",
        back_populates="requests"
    )

    payment = relationship(
        "Payment",
        back_populates="request",
        uselist=False
    )


# =====================================
# PAYMENT RECORDS
# =====================================

class Payment(Base):

    __tablename__ = "payments"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    request_id = Column(
        Integer,
        ForeignKey("document_requests.id"),
        unique=True
    )

    payment_method = Column(String(30))

    amount = Column(
        Float,
        default=0
    )

    receipt_file = Column(String(255))

    reference_number = Column(String(100))

    payment_status = Column(
        String(50),
        default="Unpaid"
    )

    verified_by = Column(String(150))

    payment_date = Column(DateTime)

    request = relationship(
        "DocumentRequest",
        back_populates="payment"
    )


# =====================================
# SYSTEM ACTIVITY LOGS
# =====================================

class ActivityLog(Base):

    __tablename__ = "activity_logs"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    user_id = Column(
        Integer,
        ForeignKey("users.id")
    )

    action = Column(
        String(150),
        nullable=False
    )

    details = Column(String(500))

    created_at = Column(
        DateTime,
        default=datetime.now
    )


# =====================================
# DATABASE INITIALIZATION
# =====================================

def initialize_database():

    Base.metadata.create_all(bind=engine)

    with engine.begin() as connection:

        # ---------------------------------
        # USERS TABLE MIGRATION
        # ---------------------------------

        result = connection.exec_driver_sql(
            "PRAGMA table_info(users)"
        )

        user_columns = {
            row[1] for row in result.fetchall()
        }

        if "course" not in user_columns:

            connection.exec_driver_sql(
                "ALTER TABLE users "
                "ADD COLUMN course VARCHAR(100)"
            )

        if "year_level" not in user_columns:

            connection.exec_driver_sql(
                "ALTER TABLE users "
                "ADD COLUMN year_level VARCHAR(50)"
            )

        # ---------------------------------
        # UPDATE OLD COURSE NAME
        # ---------------------------------

        connection.exec_driver_sql("""
    UPDATE users
    SET course = 'Bachelor of Science in Tourism Management (BSTM)'
    WHERE LOWER(TRIM(course)) LIKE '%travel management%'
""")

        # ---------------------------------
        # VERIFY COURSE RECORDS
        # ---------------------------------

        result = connection.exec_driver_sql("""
            SELECT course, COUNT(*)
            FROM users
            GROUP BY course
        """)

        print("\n========== COURSE RECORDS ==========")

        for row in result.fetchall():
            print(f"{row[0]}: {row[1]} account(s)")

        print("====================================\n")

        # ---------------------------------
        # DOCUMENT REQUESTS MIGRATION
        # ---------------------------------

        result = connection.exec_driver_sql(
            "PRAGMA table_info(document_requests)"
        )

        request_columns = {
            row[1] for row in result.fetchall()
        }

        if "released_to" not in request_columns:

            connection.exec_driver_sql(
                "ALTER TABLE document_requests "
                "ADD COLUMN released_to VARCHAR(150)"
            )

        if "released_at" not in request_columns:

            connection.exec_driver_sql(
                "ALTER TABLE document_requests "
                "ADD COLUMN released_at DATETIME"
            )

        if "released_by" not in request_columns:

            connection.exec_driver_sql(
                "ALTER TABLE document_requests "
                "ADD COLUMN released_by VARCHAR(150)"
            )

    print("UMTC database initialized successfully!")


# =====================================
# RUN INITIALIZATION
# =====================================

initialize_database()
