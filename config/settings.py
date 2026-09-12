import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

# ---------------------------------------------------------
# GLOBAL CONFIGURATION
# ---------------------------------------------------------
SAMPLING_INTERVAL_SEC = 30
SAMPLING_INTERVAL_MIN = SAMPLING_INTERVAL_SEC / 60.0

# ---------------------------------------------------------
# TANK CONFIGURATION
# ---------------------------------------------------------
TANKS = [f"T-1{i:02d}" for i in range(1, 11)]  # T-101 to T-110

TANK_CAPACITIES_L = {
    f"T-1{i:02d}": 80000 + (i - 1) * 4000 for i in range(1, 11)
}

TANK_AREA_M2 = {
    f"T-1{i:02d}": 48 + (i - 1) * 3 for i in range(1, 11)
}

# ---------------------------------------------------------
# THERMAL PARAMETERS
# ---------------------------------------------------------
BETA_CRUDE_OIL = 0.0009  # Thermal expansion coefficient
BASE_TEMPERATURE_C = 15.0  # Standard temperature for volume correction

# ---------------------------------------------------------
# ML DETECTION PARAMETERS
# ---------------------------------------------------------
CONTAMINATION_RATE = 0.01  # Expected anomaly fraction in training (though it's clean data, so effectively outlier threshold)
ANOMALY_PERCENTILE_THRESHOLD = 99.5  # Percentile of negative decision scores to use as anomaly threshold

# ---------------------------------------------------------
# PERSISTENCE CONFIGURATION
# ---------------------------------------------------------
MIN_PERSISTENCE_INTERVALS = 3  # Alert triggers only if anomaly persists for this many consecutive intervals

# ---------------------------------------------------------
# RULE ENGINE THRESHOLDS
# ---------------------------------------------------------
THEFT_THRESHOLD_L_PER_INTERVAL = -15.0  # Unexplained loss per interval indicating theft
WATER_INGRESS_THRESHOLD_M_PER_INTERVAL = 0.02  # Sudden rise in water interface indicating ingress
LEAK_LEVEL_DROP_M_PER_INTERVAL = -0.005  # Dropping level while valves are closed

# ---------------------------------------------------------
# PATHS
# ---------------------------------------------------------
DATA_DIR = BASE_DIR / "data"
MODELS_DIR = BASE_DIR / "models"
RESULTS_DIR = BASE_DIR / "results"

DATA_DIR.mkdir(parents=True, exist_ok=True)
MODELS_DIR.mkdir(parents=True, exist_ok=True)
RESULTS_DIR.mkdir(parents=True, exist_ok=True)
