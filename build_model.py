"""
Run this ONCE before starting the app:
    python build_model.py

Reads cleaned_disease_dataset.csv and generates:
    symptom_vectorizer.pkl
    disease_vectors.npz
    disease_names.csv
"""

import pandas as pd
import pickle
import scipy.sparse as sp
from sklearn.feature_extraction.text import TfidfVectorizer

CSV_PATH = "cleaned_disease_dataset.csv"

print("Reading dataset...")
df = pd.read_csv(CSV_PATH)
df = df[["Disease", "All Symptoms Cleaned"]].dropna()
df["Disease"] = df["Disease"].str.strip().str.title()
print(f"Total diseases: {len(df)}")

print("Building TF-IDF vectors...")
vec = TfidfVectorizer(ngram_range=(1, 2), max_features=8000)
disease_vectors = vec.fit_transform(df["All Symptoms Cleaned"])

print("Saving files...")
with open("symptom_vectorizer.pkl", "wb") as f:
    pickle.dump(vec, f)

sp.save_npz("disease_vectors.npz", disease_vectors)
df[["Disease"]].to_csv("disease_names.csv", index=False)

print()
print("Done! Files created:")
print("  symptom_vectorizer.pkl")
print("  disease_vectors.npz")
print("  disease_names.csv")
print()
print("Now run:  streamlit run app.py")