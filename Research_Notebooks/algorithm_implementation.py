import numpy as np
from sklearn.model_selection import train_test_split
from keras.models import Sequential
from keras.layers import Dense, Input
import keras
from sklearn.metrics import f1_score
from imblearn.over_sampling import SMOTE
import pandas as pd

# Configuring Dataset and Values

# Reading in dataset from CSV file
urldata = pd.read_csv("./Url_Processed.csv")

# Clean up dataset and remove unnecessary columns
urldata.drop("Unnamed: 0", axis=1, inplace=True, errors='ignore')
if "url" in urldata.columns and "label" in urldata.columns:
    urldata.drop(["url", "label"], axis=1, inplace=True)

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

# Using SMOTE to resample dataset
x_sample, y_sample = SMOTE().fit_resample(x, y.values.ravel())
x_sample = pd.DataFrame(x_sample, columns=required_columns)
y_sample = pd.DataFrame(y_sample, columns=['result'])

# Split the data into train and test sets
x_train, x_test, y_train, y_test = train_test_split(x_sample, y_sample, test_size=0.2, random_state=42)

# Define the hyperparameter search space
hyperparameter_space = {
    'num_hidden_layers': [1, 2, 3],
    'hidden_layer_units': [8, 16, 32, 64],
    'learning_rate': [0.0001, 0.001, 0.01],
    'batch_size': [32, 64, 128, 256]
}

# Define the fitness function to evaluate the model
def evaluate_model(params):
    num_hidden_layers = params['num_hidden_layers']
    hidden_layer_units = params['hidden_layer_units']
    learning_rate = params['learning_rate']
    batch_size = params['batch_size']

    model = Sequential()
    model.add(Input(shape=(x_train.shape[1],)))  # Use Input layer to define input shape
    model.add(Dense(hidden_layer_units, activation='relu'))
    for _ in range(num_hidden_layers - 1):
        model.add(Dense(hidden_layer_units, activation='relu'))
    model.add(Dense(1, activation='sigmoid'))

    opt = keras.optimizers.Adam(learning_rate=learning_rate)  # Use learning_rate instead of lr
    model.compile(optimizer=opt, loss='binary_crossentropy', metrics=['accuracy'])

    # Use a smaller subset of the data for faster evaluation
    subset_size = 5000  # Adjust this value based on your system's capabilities
    x_train_sub = x_train[:subset_size]
    y_train_sub = y_train[:subset_size]

    history = model.fit(x_train_sub, y_train_sub, epochs=3, batch_size=batch_size, verbose=0)

    y_pred = model.predict(x_test)
    y_pred = (y_pred > 0.5).astype(int)
    f1 = f1_score(y_test, y_pred)

    return f1

# Genetic algorithm parameters
population_size = 10
num_generations = 1  # Reduce the number of generations for faster execution
elite_size = 2

# Initialize population randomly
population = []
for _ in range(population_size):
    individual = {
        'num_hidden_layers': np.random.choice(hyperparameter_space['num_hidden_layers']),
        'hidden_layer_units': np.random.choice(hyperparameter_space['hidden_layer_units']),
        'learning_rate': np.random.choice(hyperparameter_space['learning_rate']),
        'batch_size': np.random.choice(hyperparameter_space['batch_size'])
    }
    population.append(individual)

# Genetic algorithm loop
# Genetic algorithm loop
for generation in range(num_generations):
    print(f"Generation {generation + 1}/{num_generations}")

    # Evaluate individuals
    fitness_scores = []
    for individual in population:
        try:
            fitness = evaluate_model(individual)
            fitness_scores.append(fitness)
        except Exception as e:
            print(f"Error evaluating individual: {e}")
            fitness_scores.append(0)  # Assign a fitness score of 0 for invalid individuals

    # Debugging: Print fitness scores
    print("Fitness Scores:", fitness_scores)

    # Check if fitness_scores is empty
    if not fitness_scores:
        raise ValueError("No valid fitness scores found. Check the evaluate_model function.")

    # Select elite individuals
    elite_indices = np.argsort(fitness_scores)[-elite_size:]
    elite_population = [population[i] for i in elite_indices]

    # Debugging: Print elite population
    print("Elite Population:", elite_population)

    # Create new generation
    new_population = elite_population.copy()
    while len(new_population) < population_size:
        parent1 = np.random.choice(elite_population)
        parent2 = np.random.choice(elite_population)
        child = {}
        for param in hyperparameter_space:
            if np.random.rand() < 0.5:
                child[param] = parent1[param]
            else:
                child[param] = parent2[param]
        new_population.append(child)

    population = new_population

# Find the best individual
if not fitness_scores:
    raise ValueError("No valid fitness scores found. Check the evaluate_model function.")

best_fitness = max(fitness_scores)
best_individual = elite_population[np.argmax(fitness_scores)]
print("Best Fitness:", best_fitness)
print("Best Individual:", best_individual)

# Train and save the best model
best_model = Sequential()
best_model.add(Input(shape=(x_train.shape[1],)))  # Use Input layer to define input shape
best_model.add(Dense(best_individual['hidden_layer_units'], activation='relu'))
for _ in range(best_individual['num_hidden_layers'] - 1):
    best_model.add(Dense(best_individual['hidden_layer_units'], activation='relu'))
best_model.add(Dense(1, activation='sigmoid'))

opt = keras.optimizers.Adam(learning_rate=best_individual['learning_rate'])  # Use learning_rate instead of lr
best_model.compile(optimizer=opt, loss='binary_crossentropy', metrics=['accuracy'])

history = best_model.fit(x_train, y_train, epochs=10, batch_size=best_individual['batch_size'], verbose=0)

# Save the best model
best_model.save("Malicious_URL_Prediction.keras")
print("Best model saved as Malicious_URL_Prediction.keras")