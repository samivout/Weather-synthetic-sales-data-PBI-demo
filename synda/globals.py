"""
Module for defining strings used in config files and inside this project, ensuring unified string usage and datatypes.
"""

from pandas import Int64Dtype

# Utilized ID string
LOC_ID_STR = "location_id"
PRS_ID_STR = "person_id"
PRD_ID_STR = "product_id"
PRD_CAT_ID_STR = "product_category_id"

# Utilized name strings
LOC_NAME_STR = "location_name"
PRS_NAME_STR = "person_name"
PRD_NAME_STR = "product_name"
TIMESTAMP_STR = "timestamp"

# Open/available time related string
LOC_AVB_HRS_BG_STR = "open_hours_start"
LOC_AVB_HRS_ED_STR = "open_hours_end"

# Utilized price strings
PRD_PRICE_STR = "product_price"

# Utilized computed column names
DAY_EFF_STR = "daytime_effect"
WTHR_IDX_STR = "weather_index"
SALES_STR = "sales"

# Dictionary keys
WTHR_OBS_STR = "weather_observation"

TARGET_DTYPES = {
    LOC_ID_STR: Int64Dtype(),
    PRS_ID_STR: Int64Dtype(),
    PRD_ID_STR: Int64Dtype(),
    DAY_EFF_STR: float,
    WTHR_IDX_STR: float,
    SALES_STR: Int64Dtype(),
    LOC_NAME_STR: str,
    PRS_NAME_STR: str,
    PRD_NAME_STR: str,
    PRD_PRICE_STR: float,
    LOC_AVB_HRS_BG_STR: Int64Dtype(),
    LOC_AVB_HRS_ED_STR: Int64Dtype(),
}

MAX_RANGE_DELTA = 440