import sys
import os

sys.path.append(os.getcwd())
from courier import zones

print(f"Normalize: {zones.normalize_name('Ahmedabad', 'city')}")
print(f"Normalize: {zones.normalize_name('Vapi Ahmedabad', 'city')}")
