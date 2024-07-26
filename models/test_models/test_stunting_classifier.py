import pandas as pd
import joblib
from sklearn.preprocessing import LabelEncoder

# Load the saved model
#model = joblib.load('saved_models/stunting_classifier.pkl')

# Machine Learning Model (Load using joblib), Age in months, gender (laki-laki/perempuan), and height in cm
def stunting_classifier(model, age, gender, height):
    input_data = {
        'Umur (bulan)': [age],  
        'Jenis Kelamin': [gender],
        'Tinggi Badan (cm)': [height],
    }
    input_df = pd.DataFrame(input_data)
    label_encoder = LabelEncoder()
    input_df['Jenis Kelamin'] = label_encoder.fit_transform(input_df['Jenis Kelamin'])
    prediction = model.predict(input_df)
    classification = prediction[0]
    return classification

""" 
# Example input data
input_data = get_input_data(0, 'laki-laki', 43.5448720454205)


# Convert the input data into a DataFrame
input_df = pd.DataFrame(input_data)


# Encode the categorical variables
label_encoder = LabelEncoder()
input_df['Jenis Kelamin'] = label_encoder.fit_transform(input_df['Jenis Kelamin'])


# Make a prediction
prediction = model.predict(input_df)


# Print the prediction
print(f'Prediction: {prediction[0]}')

# Classification:
# 0: normal
# 1: severely stunted
# 2: stunted
# 3: tinggi

"""