import pandas as pd
import joblib
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report

# Load the dataset
df = pd.read_csv('dataset/Stunting_Classification.csv')

# Encode categorical variables
label_encoder = LabelEncoder()
df['Jenis Kelamin'] = label_encoder.fit_transform(df['Jenis Kelamin'])
df['Status Gizi'] = label_encoder.fit_transform(df['Status Gizi'])

# Split the dataset into features (X) and target variable (y)
X = df.drop('Status Gizi', axis=1)
y = df['Status Gizi']

# Split the data into training and testing sets
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Choose the model
model = RandomForestClassifier(n_estimators=100, random_state=42)

# Train the model
model.fit(X_train, y_train)

# Make predictions on the test set
y_pred = model.predict(X_test)

# Additional evaluation metrics
print(classification_report(y_test, y_pred))

"""
              precision    recall  f1-score   support

           0       1.00      1.00      1.00     13382
           1       1.00      1.00      1.00      4130
           2       1.00      1.00      1.00      2790
           3       1.00      1.00      1.00      3898

    accuracy                           1.00     24200
   macro avg       1.00      1.00      1.00     24200
weighted avg       1.00      1.00      1.00     24200

Commentary : Good enough, let's save the model for future use.
"""

# Save the model
#joblib.dump(model, 'Model/stunting_classifier.pkl')   # ---> Uncomment this line to save the model