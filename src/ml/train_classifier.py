
import json
import pandas as pd
import joblib
from pathlib import Path
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import MultiLabelBinarizer
from sklearn.pipeline import Pipeline
from sklearn.linear_model import LogisticRegression
from sklearn.multiclass import OneVsRestClassifier

def train_classifier(base_path):
    """
    Trains a multi-label classifier on the processed challenges dataset.
    """
    project_path = Path(base_path)
    data_file = project_path / 'data' / 'ml' / 'processed_challenges.json'
    models_path = project_path / 'models'

    if not data_file.exists():
        print(f"Error: Dataset not found at {data_file}")
        print("Please run process_data.py first.")
        return

    models_path.mkdir(exist_ok=True)

    # 1. Load Data
    with open(data_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    if not data:
        print("Dataset is empty. Cannot train model.")
        return

    df = pd.DataFrame(data)
    print(f"Loaded {len(df)} challenges from dataset.")

    X = df['description']
    y = df['labels']

    # 2. Binarize Labels
    # The `imports` are our labels. We need to convert the list of strings
    # into a binary matrix format.
    mlb = MultiLabelBinarizer()
    y_binarized = mlb.fit_transform(y)
    print(f"Found {len(mlb.classes_)} unique classes (crypto techniques).")

    # 3. Define the Model Pipeline
    # We create a pipeline that first vectorizes the text descriptions
    # and then applies a multi-label classifier.
    pipeline = Pipeline([
        ('tfidf', TfidfVectorizer(stop_words='english', ngram_range=(1, 2), max_features=2000)),
        ('clf', OneVsRestClassifier(LogisticRegression(solver='liblinear'), n_jobs=-1))
    ])

    # 4. Train the Model
    print("Training classifier...")
    pipeline.fit(X, y_binarized)
    print("Training complete.")

    # 5. Save the Model and Binarizer
    # We save the entire pipeline (vectorizer + classifier) and the label binarizer
    # so we can use them for prediction later.
    model_file = models_path / 'challenge_classifier.joblib'
    binarizer_file = models_path / 'label_binarizer.joblib'

    joblib.dump(pipeline, model_file)
    joblib.dump(mlb, binarizer_file)

    print(f"Classifier pipeline saved to {model_file}")
    print(f"Label binarizer saved to {binarizer_file}")

if __name__ == '__main__':
    import os
    project_root = os.getcwd()
    train_classifier(project_root)
