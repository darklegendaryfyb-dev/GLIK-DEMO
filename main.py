from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import random
from typing import List, Optional

app = FastAPI(title="GLIK Backend API")

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Models
class PatientData(BaseModel):
    glucose: float
    insulin_units: float = 0.0
    carbs_grams: float = 0.0
    activity_level: float = 5.0  # 0-10
    stress_level: float = 5.0    # 0-10
    mood: str = "😐" # Emoji

class RiskResponse(BaseModel):
    risk_score: int
    risk_label: str
    explanation: str
    glucose_series_14d: List[int]

class ScanResponse(BaseModel):
    product_name: str
    estimated_carbs: float
    risk_label: str
    risk_score: int
    explanation: str

# Helper logic (Mock / Heuristic)
def calculate_risk(data: PatientData) -> (int, str, str):
    score = 0
    reasons = []

    # Base risk from glucose
    if data.glucose > 180:
        score += 60
        reasons.append("Current glucose is elevated.")
    elif data.glucose < 70:
        score += 50
        reasons.append("Risk of hypoglycemia.")
    else:
        score += 10
    
    # Impact contributors
    if data.carbs_grams > 60:
        score += 20
        reasons.append("High carb intake detected.")
    
    if data.stress_level > 7:
        score += 15
        reasons.append("High stress levels can spike glucose.")
        
    if data.activity_level < 3:
        score += 10
        reasons.append("Low activity increases persistence of high glucose.")
    
    if data.insulin_units == 0 and data.glucose > 150:
        score += 10
        reasons.append("Missed insulin correction?")

    # Clamp score
    score = min(max(score, 0), 100)

    # Label
    if score < 30:
        label = "Low"
    elif score < 70:
        label = "Medium"
    else:
        label = "High"

    explanation = " ".join(reasons) if reasons else "Levels look stable."
    return score, label, explanation

def generate_trend(start_glucose: float) -> List[int]:
    # Generate 14 points representing a 14-day trend or future projection
    # For this MVP, let's treat it as a "future projection" over next few hours or past 14 days trend
    # The requirement says "glucose_series_14d", let's assume it's past 14 days daily avg or something similar for trend analysis
    # Randomized walk
    series = []
    current = start_glucose
    for _ in range(14):
        series.append(int(current))
        change = random.randint(-15, 15)
        current += change
        current = max(60, min(350, current)) # Clamp realistic values
    return series

@app.post("/predict", response_model=RiskResponse)
async def predict_risk(data: PatientData):
    score, label, explanation = calculate_risk(data)
    trend = generate_trend(data.glucose)
    
    return RiskResponse(
        risk_score=score,
        risk_label=label,
        explanation=explanation,
        glucose_series_14d=trend
    )

@app.post("/scan", response_model=ScanResponse)
async def scan_product(
    file: UploadFile = File(...),
    # In a real app we'd accept other patient context here via Form(), 
    # but for simple MVP scan demo we might just return product info + generic risk
):
    # Simulate image processing delay or logic
    # Heuristic: Randomly pick a 'product' to simulate detection
    products = [
        {"name": "Apple", "carbs": 25, "risk": "Low", "expl": "Natural sugars, high fiber."},
        {"name": "Soda Can", "carbs": 40, "risk": "High", "expl": "High glycemic index, liquid sugar."},
        {"name": "Pizza Slice", "carbs": 35, "risk": "Medium", "expl": "Fat/protein delays absorption, but high carb."},
        {"name": "Salad", "carbs": 10, "risk": "Low", "expl": "Very low impact."},
        {"name": "Donut", "carbs": 45, "risk": "High", "expl": "Refined carbs and fats."}
    ]
    
    detected = random.choice(products)
    
    # Calculate a mock score based on the random pick
    if detected["risk"] == "High":
        score = random.randint(70, 95)
    elif detected["risk"] == "Medium":
        score = random.randint(30, 69)
    else:
        score = random.randint(5, 29)
        
    return ScanResponse(
        product_name=detected["name"],
        estimated_carbs=detected["carbs"],
        risk_label=detected["risk"],
        risk_score=score,
        explanation=detected["expl"]
    )

@app.get("/")
def read_root():
    return {"message": "GLIK API is running"}
