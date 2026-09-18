"""Import all models so they register on Base.metadata.

`database.init_db()` imports this package before create_all().
"""

from app.models.anomaly import Anomaly
from app.models.contract import Contract
from app.models.document import Document
from app.models.invoice import Invoice
from app.models.review import Review
from app.models.timesheet import Timesheet

__all__ = [
    "Anomaly",
    "Contract",
    "Document",
    "Invoice",
    "Review",
    "Timesheet",
]
