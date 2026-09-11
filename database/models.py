from datetime import datetime

from sqlalchemy import (
    Column,
    Integer,
    String,
    Boolean,
    DateTime,
    Date,
    Float,
    Text,
    ForeignKey,
    UniqueConstraint,
    func,
    Index,
    CheckConstraint,
)

from sqlalchemy.dialects.postgresql import (
    JSONB,
)

from sqlalchemy.orm import (
    Mapped,
    mapped_column,
)

from database.database import Base


class Camera(Base):

    __tablename__ = "cameras"
    
    
    
    __table_args__ = (

        CheckConstraint(
            "status IN ('active', 'inactive')",
            name="chk_camera_status"
        ),

    )

    # ==================================================
    # INTERNAL DATABASE ID
    #
    # PostgreSQL automatically increments this:
    #
    # 1
    # 2
    # 3
    # ...
    #
    # Frontend does NOT use this directly.
    # ==================================================

    db_id: Mapped[int] = mapped_column(

        Integer,

        primary_key=True,

        autoincrement=True
    )

# ==================================================
# PUBLIC CAMERA ID
#
# The user-entered camera name itself is used
# as the public camera ID.
#
# Examples:
#
# "Main Gate"
# "Production Camera"
# "Loading Area Camera"
#
# db_id remains the internal PostgreSQL key.
# ==================================================

    id: Mapped[str] = mapped_column(

        String(150),

        unique=True,

        nullable=False,

        index=True
    )


    # ==================================================
    # CAMERA NAME
    # ==================================================

    name: Mapped[str] = mapped_column(

        String(150),

        nullable=False
    )


    # ==================================================
    # SOURCE
    # ==================================================

    source_type: Mapped[str] = mapped_column(

        String(20),

        nullable=False,

        default="cctv"
    )


    # ==================================================
    # CCTV
    # ==================================================

    brand: Mapped[str | None] = mapped_column(

        String(50),

        nullable=True
    )


    camera_ip: Mapped[str | None] = mapped_column(

        String(100),

        nullable=True
    )


    username: Mapped[str | None] = mapped_column(

        String(150),

        nullable=True
    )


    password: Mapped[str | None] = mapped_column(

        Text,

        nullable=True
    )


    rtsp_port: Mapped[int | None] = mapped_column(

        Integer,

        nullable=True,

        default=554
    )


    # ==================================================
    # NVR / DVR CHANNEL
    #
    # Example:
    #
    # same NVR IP
    #
    # CAM001 -> channel 1
    # CAM002 -> channel 2
    # CAM003 -> channel 3
    # ==================================================

    channel: Mapped[int | None] = mapped_column(

        Integer,

        nullable=True,

        default=1
    )


    stream_path: Mapped[str | None] = mapped_column(

        String(500),

        nullable=True
    )


    rtsp_url: Mapped[str | None] = mapped_column(

        Text,

        nullable=True
    )


    # ==================================================
    # VIDEO
    #
    # Kept for compatibility/testing.
    # ==================================================

    video_path: Mapped[str | None] = mapped_column(

        Text,

        nullable=True
    )


    # ==================================================
    # WEBCAM
    #
    # Kept for compatibility/testing.
    # ==================================================

    webcam_index: Mapped[int | None] = mapped_column(

        Integer,

        nullable=True,

        default=0
    )


    # ==================================================
    # AI CONFIGURATION
    #
    # Keep list/JSONB architecture.
    #
    # ["helmet"]
    #
    # ["helmet", "fire"]
    #
    # ["all"]
    # ==================================================

    modules: Mapped[list] = mapped_column(

        JSONB,

        nullable=False,

        default=lambda: ["all"]
    )


    # ==================================================
    # OTHER SETTINGS
    # ==================================================

    enabled: Mapped[bool] = mapped_column(

        Boolean,

        nullable=False,

        default=True
    )

    # ==================================================
    # CAMERA OPERATIONAL STATUS
    #
    # Backend-controlled values:
    #
    # active
    # inactive
    # standby
    # ==================================================

    status: Mapped[str] = mapped_column(

        String(20),

        nullable=False,

        default="inactive"
    )
    
    
    save_output: Mapped[bool] = mapped_column(

        Boolean,

        nullable=False,

        default=False
    )
    
    resolution = Column(
        String(50),
        nullable=True
    )

    camera_model = Column(
        String(150),
        nullable=True
    )

    plant_id = Column(
        Integer,
        ForeignKey("plants.id"),
        nullable=True,
        index=True
    )

    department_id = Column(
        Integer,
        ForeignKey("departments.id"),
        nullable=True,
        index=True
    )

    workstation_id = Column(
        Integer,
        ForeignKey("workstations.id"),
        nullable=True,
        index=True
    )

    notifications_enabled = Column(
        Boolean,
        default=False,
        nullable=False
    )
    
    
    # ==================================================
    # TIMESTAMPS
    # ==================================================

    created_at: Mapped[datetime] = mapped_column(

        DateTime,

        nullable=False,

        default=datetime.utcnow
    )


    updated_at: Mapped[datetime] = mapped_column(

        DateTime,

        nullable=False,

        default=datetime.utcnow,

        onupdate=datetime.utcnow
    )
    
    
    
class VehicleLog(Base):

    __tablename__ = "vehicle_logs"
    
    
    
    __table_args__ = (

        UniqueConstraint(
            "camera_id",
            "session_id",
            "vehicle_track_id",
            name="uq_vehicle_runtime_track"
        ),

        Index(
            "ix_vehicle_logs_camera_plate_seen",
            "camera_id",
            "plate_number",
            "last_seen_at"
        ),
    )

    # ==================================================
    # INTERNAL DATABASE ID
    # ==================================================

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True
    )

    # ==================================================
    # CAMERA
    # ==================================================

    camera_id: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
        index=True
    )

    # ==================================================
    # RUNTIME SESSION
    #
    # Important because vehicle_track_id starts again
    # when a camera/runtime is restarted.
    # ==================================================

    session_id: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        index=True
    )

    # ==================================================
    # VEHICLE TRACK
    #
    # Runtime ID only.
    # Do NOT treat this as permanent identity.
    # ==================================================

    vehicle_track_id: Mapped[int] = mapped_column(
        Integer,
        nullable=False
    )

    vehicle_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False
    )

    # ==================================================
    # NUMBER PLATE
    # ==================================================

    plate_number: Mapped[str | None] = mapped_column(
        String(32),
        nullable=True,
        index=True
    )

    plate_confidence: Mapped[float | None] = mapped_column(
        Float,
        nullable=True
    )

    # ==================================================
    # LAST KNOWN BOUNDING BOX
    # ==================================================

    bbox: Mapped[list | None] = mapped_column(
        JSONB,
        nullable=True
    )

    # ==================================================
    # TIMESTAMPS
    # ==================================================

    first_seen_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        index=True
    )

    last_seen_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        index=True
    )
    
    
class User(Base):

    __tablename__ = "users"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    email = Column(
        String(255),
        unique=True,
        nullable=False,
        index=True
    )

    password = Column(
        String(255),
        nullable=False
    )

    role = Column(
        String(100),
        nullable=False
    )
    
    
    role_id = Column(
        Integer,
        ForeignKey("roles.id"),
        nullable=True,
        index=True
    )

    full_name = Column(
        String(100),
        nullable=False
    )

    job_title = Column(
        String(100),
        nullable=True
    )

    phone_number = Column(
        String(20),
        unique=True,
        nullable=True
    )

    image_url = Column(
        Text,
        nullable=True
    )

    account_status = Column(
        Boolean,
        default=False,
        nullable=False
    )

    company = Column(
        String(200),
        nullable=True
    )

    plant = Column(
        String(100),
        nullable=True
    )

    department = Column(
        String(100),
        nullable=True
    )

    workstation = Column(
        String(100),
        nullable=True
    )

    created_time = Column(
        DateTime,
        server_default=func.now(),
        nullable=False
    )
    
    
# ==========================================================
# COMPANY
# ==========================================================

class Company(Base):

    __tablename__ = "companies"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    company_name = Column(
        String(200),
        nullable=False
    )

    gstin = Column(
        String(20),
        unique=True,
        nullable=False,
        index=True
    )

    industry = Column(
        String(150),
        nullable=False
    )

    city = Column(
        String(100),
        nullable=False
    )

    state = Column(
        String(100),
        nullable=False
    )

    contact_name = Column(
        String(150),
        nullable=False
    )

    contact_email = Column(
        String(255),
        nullable=False
    )

    contact_phone = Column(
        String(30),
        nullable=True
    )

    registration_date = Column(
        Date,
        server_default=func.current_date(),
        nullable=False
    )
    
    
    status = Column(
        Boolean,
        default=True,
        nullable=False
    )

    company_logo = Column(
        Text,
        nullable=True
    )

    created_time = Column(
        DateTime,
        server_default=func.now(),
        nullable=False
    )


# ==========================================================
# PLANT
# ==========================================================

class Plant(Base):

    __tablename__ = "plants"

    __table_args__ = (
        UniqueConstraint(
            "company_id",
            "plant_name",
            name="uq_company_plant_name"
        ),
    )

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    company_id = Column(
        Integer,
        ForeignKey("companies.id"),
        nullable=False,
        index=True
    )
    
    
    company_name = mapped_column(
        String(200),
        nullable=False
    )

    plant_name = Column(
        String(200),
        nullable=False
    )

    plant_type = Column(
        String(100),
        nullable=False
    )

    area_sq_ft = Column(
        Float,
        nullable=True
    )

    location = Column(
        String(255),
        nullable=False
    )

    plant_head = Column(
        String(150),
        nullable=False
    )

    status = Column(
        Boolean,
        default=True,
        nullable=False
    )

    created_time = Column(
        DateTime,
        server_default=func.now(),
        nullable=False
    )


# ==========================================================
# DEPARTMENT
# ==========================================================

class Department(Base):

    __tablename__ = "departments"

    __table_args__ = (
        UniqueConstraint(
            "plant_id",
            "department_name",
            name="uq_plant_department_name"
        ),
    )

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    plant_id = Column(
        Integer,
        ForeignKey("plants.id"),
        nullable=False,
        index=True
    )
    
    
    plant_name = mapped_column(
        String(200),
        nullable=False
    )

    department_name = Column(
        String(200),
        nullable=False
    )

    department_head = Column(
        String(150),
        nullable=False
    )

    employee_count = Column(
        Integer,
        default=0,
        nullable=False
    )

    status = Column(
        Boolean,
        default=True,
        nullable=False
    )

    created_time = Column(
        DateTime,
        server_default=func.now(),
        nullable=False
    )


# ==========================================================
# WORKSTATION
# ==========================================================

class Workstation(Base):

    __tablename__ = "workstations"

    __table_args__ = (
        UniqueConstraint(
            "department_id",
            "workstation_name",
            name="uq_department_workstation_name"
        ),
    )

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    department_id = Column(
        Integer,
        ForeignKey("departments.id"),
        nullable=False,
        index=True
    )
    
    department_name = mapped_column(
        String(200),
        nullable=False
    )

    workstation_name = Column(
        String(200),
        nullable=False
    )

    workstation_type = Column(
        String(100),
        nullable=False
    )

    operator_name = Column(
        String(150),
        nullable=False
    )

    status = Column(
        Boolean,
        default=True,
        nullable=False
    )

    created_time = Column(
        DateTime,
        server_default=func.now(),
        nullable=False
    )
    
    
class Role(Base):

    __tablename__ = "roles"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    name = Column(
        String(100),
        unique=True,
        nullable=False,
        index=True
    )

    display_name = Column(
        String(150),
        nullable=False
    )

    hierarchy_level = Column(
        Integer,
        nullable=False
    )

    scope_type = Column(
        String(50),
        nullable=False
    )

    is_active = Column(
        Boolean,
        default=True,
        nullable=False
    )

    created_time = Column(
        DateTime,
        server_default=func.now(),
        nullable=False
    )
    
    
    
class AIProfile(Base):

    __tablename__ = "ai_profiles"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    name = Column(
        String(150),
        unique=True,
        nullable=False,
        index=True
    )
    
    
    
    model_path_or_url = Column(
        Text,
        nullable=True
    )

    description = Column(
        Text,
        nullable=True
    )

    modules = Column(
        JSONB,
        nullable=False
    )

    is_active = Column(
        Boolean,
        default=True,
        nullable=False
    )

    created_time = Column(
        DateTime,
        server_default=func.now(),
        nullable=False
    )

    updated_time = Column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )