from datetime import datetime

from database.database import SessionLocal
from database.models import VehicleLog


class VehicleLogRepository:

    def upsert_vehicle(
        self,
        camera_id,
        session_id,
        vehicle_track_id,
        vehicle_type,
        bbox=None,
        plate_number=None,
        plate_confidence=None,
    ):

        now = datetime.utcnow()

        with SessionLocal() as db:

            # ==================================================
            # 1. FIND CURRENT RUNTIME TRACK
            # ==================================================

            log = (
                db.query(VehicleLog)
                .filter(
                    VehicleLog.camera_id == camera_id,
                    VehicleLog.session_id == session_id,
                    VehicleLog.vehicle_track_id == vehicle_track_id,
                )
                .first()
            )

            # ==================================================
            # 2. EXISTING TRACK -> UPDATE
            # ==================================================

            if log is not None:

                log.last_seen_at = now

                if vehicle_type:
                    log.vehicle_type = vehicle_type

                if bbox is not None:
                    log.bbox = bbox

                # Only replace plate when we actually have one
                if plate_number:

                    # Prefer the higher-confidence OCR result
                    if (
                        log.plate_number is None
                        or log.plate_number == plate_number
                        or plate_confidence is None
                        or log.plate_confidence is None
                        or plate_confidence >= log.plate_confidence
                    ):

                        log.plate_number = plate_number
                        log.plate_confidence = plate_confidence

                db.commit()

                return log.id

            # ==================================================
            # 3. NEW TRACK
            # ==================================================

            log = VehicleLog(

                camera_id=camera_id,

                session_id=session_id,

                vehicle_track_id=vehicle_track_id,

                vehicle_type=vehicle_type or "unknown",

                plate_number=plate_number,

                plate_confidence=plate_confidence,

                bbox=bbox,

                first_seen_at=now,

                last_seen_at=now,
            )

            db.add(log)

            db.commit()

            db.refresh(log)

            return log.id