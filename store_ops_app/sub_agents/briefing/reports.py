from typing import Literal, Optional

from pydantic import BaseModel


# What each helper must hand over. Code can read these fields; a sentence it would have to guess at.
class StockReport(BaseModel):
    status: Literal["ok", "error"]
    low_items: list[str]            # e.g. "Golden Ring: 0 left"
    note: Optional[str] = None      # why it failed, when status is "error"


class SalesReport(BaseModel):
    status: Literal["ok", "error"]
    top_sellers: list[str]          # e.g. "Apple cinnamon oatmeal cereal baby: 67 units"
    note: Optional[str] = None


class RevenueReport(BaseModel):
    status: Literal["ok", "error"]
    total_cad: Optional[float] = None   # only when status is "ok"
    note: Optional[str] = None
