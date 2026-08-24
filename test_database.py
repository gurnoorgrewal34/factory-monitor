from database.database import Base, engine
from database.models import Camera


print("Connecting to PostgreSQL...")

try:

    Base.metadata.create_all(
        bind=engine
    )

    print("DATABASE CONNECTION SUCCESSFUL")
    print("Camera table created / verified.")

except Exception as exc:

    print("DATABASE CONNECTION FAILED")
    print(repr(exc))

    raise