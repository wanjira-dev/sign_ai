import os
import cv2
import numpy as np
import tensorflow as tf
from tensorflow.keras.models import Model
from tensorflow.keras.layers import Input, Conv1D, MaxPooling1D, Flatten, Dense, Dropout
from tensorflow.keras.utils import to_categorical
from sklearn.model_selection import train_test_split
from model import extract_hand_landmarks

# Parameters
DATA_DIR = 'data/train/'
EMBEDDING_SIZE = 128

def load_landmark_data(data_dir):
    landmarks_data = []
    labels = []
    
    # To check if the directory exists
    if not os.path.isdir(data_dir):
        print(f"Error: Data directory not found at '{data_dir}'")
        return None, None, None
    
    class_names = sorted([d for d in os.listdir(data_dir) if os.path.isdir(os.path.join(data_dir,d))])
    if not class_names:
        print(f"Error: No class subdirectories (A, B, etc.) found in '{data_dir}'")
        return None, None, None
    
    label_map = {name: i for i, name in enumerate(class_names)}
    print(f"Found {len(class_names)} classes: {class_names}")
    
    print("Processing images into landmark data...")
    for class_name in class_names:
        class_dir = os.path.join(data_dir, class_name)
        image_files = os.listdir(class_dir)
        print(f" Processing class '{class_name}' ({len(image_files)} images)")
        
        for img_name in image_files:
            img_path = os.path.join(class_dir, img_name)
            image = cv2.imread(img_path)
            if image is not None:
                landmarks, _ = extract_hand_landmarks(image)
                if landmarks:
                    landmarks_data.append(landmarks)
                    labels.append(label_map[class_name])
                    
    print(f"Processed {len(landmarks_data)} images.")
    
    if not landmarks_data:
        return np.array([]), np.array([]), class_names
    
    return np.array(landmarks_data, dtype=np.float32), np.array(labels), class_names

# Model Architecture
def create_embedding_model(num_classes):
    # Input is the flattened list of 63 landmark coordinates
    input_shape = (63, 1)
    
    # Defining the full classification model
    input_layer = Input(shape=input_shape)
    
    # 1D CNNs for finding patterns in sequential data
    x = Conv1D(64, 3, activation='relu')(input_layer)
    x = MaxPooling1D(2)(x)
    x = Conv1D(128, 3, activation='relu')(x)
    x = MaxPooling1D(2)(x)
    x = Flatten()(x)
    
    # This dense layer is the embedding
    embedding_layer = Dense(EMBEDDING_SIZE, activation='relu', name='embedding')(x)
    x = Dropout(0.5)(embedding_layer)
    
    # Final classification layer for training
    output_layer = Dense(num_classes, activation='softmax')(x)

    # The full model used for training
    classification_model = Model(inputs=input_layer, outputs=output_layer)
    
    # The final model we will save and use for inference
    embedding_model = Model(input_layer, outputs=embedding_layer)

    return classification_model, embedding_model

# Main Training execution
if __name__ == "__main__":
    # Load and preprocess the data
    X, y, class_names = load_landmark_data(DATA_DIR)
    
    # Add robustness check
    if X.size == 0:
        print("\nCRITICAL ERROR: No data was loaded. Training cannot continue.")
        print("Please check the following:")
        print(f"1. Is the `DATA_DIR` path correct? (Currently: '{DATA_DIR}')")
        print("2. Does the directory contain subfolders for each class (A, B, C...)?")
        print("3. Do these subfolders contain valid image files?")
        print("4. Is MediaPipe able to detect hands in your images? ")
    
    else:
        NUM_CLASSES = len(class_names)
        print(f"\nDynamically set NUM_CLASSES to: {NUM_CLASSES}")
        # Reshaping X to be suitable for ConvID: (num_samples, steps, features)
        X = X.reshape(X.shape[0], X.shape[1], 1)
        
        # Encoding the labels
        y_categorical = to_categorical(y, num_classes=NUM_CLASSES)
        
        # Split data into training and validation sets
        X_train, X_val, y_train, y_val = train_test_split(X, y_categorical, test_size=0.2, random_state=42, stratify=y)
        
        print(f"\nTraining data shape: {X_train.shape}")
        print(f"Validation data shape: {X_val.shape}")
        
        # Create the models
        classification_model, embedding_model = create_embedding_model(NUM_CLASSES)
        
        classification_model.compile(optimizer='adam', loss='categorical_crossentropy', metrics=['accuracy'])
        classification_model.summary()
        
        # Training the classification model
        print("\n--- Starting Model Training ---")
        classification_model.fit(
            X_train, y_train,
            validation_data=(X_val, y_val),
            epochs=50,
            batch_size=32,
            callbacks=[tf.keras.callbacks.EarlyStopping(monitor='val_accuracy', patience=5, restore_best_weights=True)]
        )
        
        # Save EMBEDDING model
        embedding_model.save('landmark_model.h5')
        print("\n--- Training Complete ---")
        print("Embedding model saved as 'landmark_model.h5'")