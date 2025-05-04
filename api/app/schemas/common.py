# api/app/schemas/common.py
from typing import List, Generic, TypeVar
from pydantic import BaseModel, Field

# Generic TypeVar for the items in the page
DataType = TypeVar('DataType')

class Page(BaseModel, Generic[DataType]):
    """ Generic pagination schema """
    items: List[DataType]
    total_items: int = Field(..., description="Total number of items available")
    page_number: int = Field(..., description="Current page number (1-based)")
    page_size: int = Field(..., description="Number of items per page")
    total_pages: int = Field(..., description="Total number of pages")
