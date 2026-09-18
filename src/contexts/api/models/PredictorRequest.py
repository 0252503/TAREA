from enum import Enum
from pydantic import BaseModel, validator


class SexEnum(str, Enum):
    M = "M"
    F = "F"


class PredictorRequest(BaseModel):
    sex: SexEnum
    nuevo: int

    @validator("sex")
    def validate_sex(cls, sex):
        sex_ranges = [SexEnum.F, SexEnum.M]
        if sex not in sex_ranges:
            raise ValueError("Invalid sex range")
        return sex
    
    @validator("nuevo")
    def validate_nuevo(cls, nuevo):
        try:
            int(nuevo)
        except ValueError:
            raise ValueError("nuevo must be an integer")
        return nuevo
    


