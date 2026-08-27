from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    Integer,
    Index,
    String,
    Text,
    Float,
    UniqueConstraint,
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


    save_output: Mapped[bool] = mapped_column(

        Boolean,

        nullable=False,

        default=False
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