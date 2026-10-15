"""Return service: closing an open loan and freeing its copy.

The book's ``copies_available`` is a derived property (``copies_total`` minus the
book's open loans, see :class:`app.models.Book`). Closing a loan here therefore
frees exactly one copy: this module never writes a copy counter of its own.
"""

from datetime import UTC, datetime

from sqlalchemy.orm import Session

from ..errors import LibraryError
from ..models import Loan


def return_loan(db: Session, loan_id: int) -> Loan:
    """Close an open loan by setting its return timestamp.

    Args:
        db: the request-scoped session.
        loan_id: primary key of the loan to return.

    Returns:
        The updated :class:`~app.models.Loan`.

    Raises:
        LibraryError: 404 when no loan carries ``loan_id``; 409 when the loan has
            already been returned. Both rejections happen before the first write,
            so a failed call leaves the row and the session untouched.
    """
    loan = db.get(Loan, loan_id)
    if loan is None:
        raise LibraryError(
            status_code=404,
            code="not_found",
            message=f"Loan {loan_id} was not found.",
        )
    if loan.returned_at is not None:
        raise LibraryError(
            status_code=409,
            code="conflict",
            message=f"Loan {loan_id} has already been returned.",
        )

    loan.returned_at = datetime.now(UTC)
    db.commit()
    return loan
