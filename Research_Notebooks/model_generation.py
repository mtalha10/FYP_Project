'''
Malicious Domain Detection Model Generation Python Script
Created by Angelina Tsuboi (angelinatsuboi.com)

Objective:
This script creates a Multilayer Perceptron Neural Network for malicious URL detection.

The code sequence is as follows:
1. Load and preprocess the dataset.
2. Use SMOTE to balance the class distribution.
3. Split the dataset into training and testing sets (80:20 ratio).
4. Initialize and train a Multilayer Perceptron model.
5. Save the trained model to a .keras file.
'''

import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, Input
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.callbacks import EarlyStopping
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from imblearn.over_sampling import SMOTE

# Load the dataset
urldata = pd.read_csv("./Url_Processed.csv")

# Clean up dataset and remove unnecessary columns
columns_to_drop = ["url", "label"]
if "Unnamed: 0" in urldata.columns:
    columns_to_drop.append("Unnamed: 0")
urldata.drop(columns=columns_to_drop, axis=1, inplace=True)

# Define required columns for x (matching the dataset column names)
required_columns = [
    'hostname_length', 'path_length', 'fd_length', 'count_-', 'count_@', 'count_?',
    'count_%', 'count_.', 'count_=', 'count_http', 'count_https', 'count_www',
    'count_digits', 'count_letters', 'count_dir', 'use_of_ip'
]

# Check for missing columns
missing_columns = [col for col in required_columns if col not in urldata.columns]
if missing_columns:
    print(f"Warning: Missing columns in dataset: {missing_columns}")
    # Option 1: Drop missing columns from required_columns
    required_columns = [col for col in required_columns if col in urldata.columns]
    # Option 2: Create placeholder columns with default values (e.g., 0)
    for col in missing_columns:
        urldata[col] = 0

# Configure dependent variables (x) and independent variable (y)
x = urldata[required_columns]
if 'result' in urldata.columns:
    y = urldata['result']
else:
    raise ValueError("'result' column not found in dataset")

# Use SMOTE to balance the dataset
smote = SMOTE(random_state=42)
x_sample, y_sample = smote.fit_resample(x, y)

# Split data into training and testing sets
x_train, x_test, y_train, y_test = train_test_split(x_sample, y_sample, test_size=0.2, random_state=42)

# Model Creation using Deep Learning (Multilayer Perceptron)
model = Sequential([
    Input(shape=(x_train.shape[1],)),  # Use Input layer to define input shape dynamically
    Dense(32, activation='relu'),
    Dense(16, activation='relu'),
    Dense(8, activation='relu'),
    Dense(1, activation='sigmoid')
])

model.summary()

# Compile the model
opt = Adam(learning_rate=0.0001)
model.compile(optimizer=opt, loss='binary_crossentropy', metrics=['accuracy'])

# Define early stopping callback
early_stopping = EarlyStopping(monitor='val_loss', patience=3, restore_best_weights=True)

# Train the model
history = model.fit(
    x_train, y_train,
    epochs=10,
    batch_size=256,
    validation_data=(x_test, y_test),
    callbacks=[early_stopping],
    verbose=1
)

# Evaluate the model
test_loss, test_accuracy = model.evaluate(x_test, y_test, verbose=0)
print(f"Test Loss: {test_loss}")
print(f"Test Accuracy: {test_accuracy}")

# Test the model with 10 examples
pred_test = model.predict(x_test)
pred_test = (pred_test > 0.5).astype(int)

# Display predicted and actual results
print("PREDICTED RESULTS: ")
print(np.where(pred_test[:10].flatten() == 1, "Malicious", "Safe"))
print("\nACTUAL RESULTS: ")
print(np.where(y_test[:10].values.flatten() == 1, "Malicious", "Safe"))

# Save the model
model.save("Malicious_URL_Prediction.keras")
print("Model saved as Malicious_URL_Prediction.keras")