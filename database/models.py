from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    Integer,
    String,
    Text,
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
    # Examples:
    #
    # CAM001
    # CAM002
    # CAM003
    #
    # This is the ID used by:
    #
    # API
    # Frontend
    # CameraManager
    # CameraRuntime
    # ==================================================

    id: Mapped[str] = mapped_column(

        String(20),

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