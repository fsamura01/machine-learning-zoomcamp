from pydantic import BaseModel, Field


class WaterSample(BaseModel):
    ph: float = Field(..., ge=0, le=14, description="pH level")
    hardness: float = Field(..., ge=0, description="Hardness in mg/L")
    solids: float = Field(..., ge=0, description="Total dissolved solids")
    chloramines: float = Field(..., ge=0, description="Chloramines in ppm")
    sulfate: float = Field(..., ge=0, description="Sulfate in mg/L")
    conductivity: float = Field(..., ge=0, description="Electrical conductivity")
    organic_carbon: float = Field(..., ge=0, description="Organic carbon in ppm")
    trihalomethanes: float = Field(..., ge=0, description="Trihalomethanes in µg/L")
    turbidity: float = Field(..., ge=0, description="Turbidity in NTU")


class PredictionResponse(BaseModel):
    potable: bool
    confidence: float
    recommendation: str
