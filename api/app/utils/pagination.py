import math
from typing import List, TypeVar

from app.schemas.common import Page
DataType = TypeVar('DataType')

def create_page(
    items: List[DataType],
    total_items: int,
    skip: int,
    limit: int,
) -> Page[DataType]:
    """
    Creates a Page response object with pagination metadata.

    Args:
        items: The list of items for the current page.
        total_items: The total number of items available across all pages.
        skip: The number of items skipped (offset).
        limit: The maximum number of items per page.

    Returns:
        A Page object containing the items and pagination metadata.
    """
    # Ensure limit is positive to avoid division by zero and handle edge case
    effective_limit = limit
    if effective_limit <= 0:
        # If limit is non-positive, return all items on page 1
        effective_limit = max(total_items, 1) # Ensure limit is at least 1
        page_number = 1
        total_pages = 1
    else:
        page_number = (skip // effective_limit) + 1
        total_pages = math.ceil(total_items / effective_limit)

    return Page(
        items=items,
        total_items=total_items,
        page_number=page_number,
        page_size=effective_limit, # Report the effective limit used
        total_pages=total_pages,
    )
