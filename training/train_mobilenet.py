"""
Train MobileNet model for fog detection using Gemini-labeled data
"""
import os
import json
import numpy as np
from pathlib import Path
from datetime import datetime
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers
from tensorflow.keras.applications import MobileNetV3Small
from tensorflow.keras.preprocessing.image import ImageDataGenerator
from sklearn.model_selection import train_test_split
from PIL import Image
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FogMobileNetTrainer:
    def __init__(self, data_dir: str = "/app/data"):
        """Initialize the trainer"""
        self.data_dir = Path(data_dir)
        self.training_dir = self.data_dir / "training"
        self.models_dir = self.data_dir / "models"
        self.models_dir.mkdir(parents=True, exist_ok=True)
        
        # Model configuration
        self.input_shape = (224, 224, 3)
        self.batch_size = 32
        self.epochs = 10
        
    def load_training_data(self):
        """Load training data from Gemini labels"""
        logger.info("Loading training data...")
        
        images = []
        fog_scores = []
        fog_levels = []
        metadata = []
        
        # Load all training files
        training_files = sorted(self.training_dir.glob("training_*.json"))
        logger.info(f"Found {len(training_files)} training files")
        
        for file_path in training_files:
            with open(file_path, 'r') as f:
                data = json.load(f)
            
            # Load image
            image_path = data['image_path']
            if os.path.exists(image_path):
                img = Image.open(image_path)
                img = img.resize((224, 224))
                img_array = np.array(img) / 255.0  # Normalize to [0, 1]
                
                images.append(img_array)
                fog_scores.append(data['label']['fog_score'] / 100.0)  # Normalize to [0, 1]
                
                # Convert fog level to categorical
                level_map = {'none': 0, 'light': 1, 'moderate': 2, 'heavy': 3}
                fog_levels.append(level_map.get(data['label']['fog_level'], 0))
                
                metadata.append(data['metadata'])
        
        # Convert to numpy arrays
        X = np.array(images)
        y_regression = np.array(fog_scores)  # For regression (fog score)
        y_classification = np.array(fog_levels)  # For classification (fog level)
        
        logger.info(f"Loaded {len(X)} images")
        logger.info(f"Fog score distribution: min={y_regression.min():.2f}, "
                   f"max={y_regression.max():.2f}, mean={y_regression.mean():.2f}")
        
        return X, y_regression, y_classification, metadata
    
    def create_model(self, num_classes: int = 4):
        """Create MobileNet model for fog detection"""
        # Use MobileNetV3Small as base (pretrained on ImageNet)
        base_model = MobileNetV3Small(
            input_shape=self.input_shape,
            include_top=False,
            weights='imagenet',
            pooling='avg'
        )
        
        # Freeze base model layers initially
        base_model.trainable = False
        
        # Create model with both regression and classification outputs
        inputs = keras.Input(shape=self.input_shape)
        
        # Data augmentation
        x = layers.RandomFlip("horizontal")(inputs)
        x = layers.RandomRotation(0.1)(x)
        x = layers.RandomZoom(0.1)(x)
        
        # Base model
        x = base_model(x, training=False)
        x = layers.Dropout(0.2)(x)
        
        # Regression head (fog score 0-100)
        regression_output = layers.Dense(64, activation='relu')(x)
        regression_output = layers.Dropout(0.1)(regression_output)
        regression_output = layers.Dense(1, activation='sigmoid', 
                                        name='fog_score')(regression_output)
        
        # Classification head (fog level)
        classification_output = layers.Dense(64, activation='relu')(x)
        classification_output = layers.Dropout(0.1)(classification_output)
        classification_output = layers.Dense(num_classes, activation='softmax', 
                                           name='fog_level')(classification_output)
        
        # Create model
        model = keras.Model(
            inputs=inputs,
            outputs={
                'fog_score': regression_output,
                'fog_level': classification_output
            }
        )
        
        return model, base_model
    
    def train(self):
        """Train the model"""
        # Load data
        X, y_regression, y_classification, metadata = self.load_training_data()
        
        if len(X) < 100:
            logger.warning(f"Only {len(X)} training samples available. "
                         f"Recommend at least 100 for good results.")
        
        # Split data
        X_train, X_val, y_reg_train, y_reg_val, y_class_train, y_class_val = \
            train_test_split(X, y_regression, y_classification, 
                           test_size=0.2, random_state=42)
        
        logger.info(f"Training set: {len(X_train)} samples")
        logger.info(f"Validation set: {len(X_val)} samples")
        
        # Create model
        model, base_model = self.create_model()
        
        # Compile model
        model.compile(
            optimizer=keras.optimizers.Adam(learning_rate=0.001),
            loss={
                'fog_score': 'mse',
                'fog_level': 'sparse_categorical_crossentropy'
            },
            loss_weights={
                'fog_score': 1.0,
                'fog_level': 0.5
            },
            metrics={
                'fog_score': ['mae'],
                'fog_level': ['accuracy']
            }
        )
        
        logger.info("Model architecture created")
        logger.info(f"Total parameters: {model.count_params():,}")
        
        # Prepare data for training
        y_train = {
            'fog_score': y_reg_train,
            'fog_level': y_class_train
        }
        y_val = {
            'fog_score': y_reg_val,
            'fog_level': y_class_val
        }
        
        # Training callbacks
        callbacks = [
            keras.callbacks.EarlyStopping(
                monitor='val_loss',
                patience=3,
                restore_best_weights=True
            ),
            keras.callbacks.ReduceLROnPlateau(
                monitor='val_loss',
                factor=0.5,
                patience=2,
                min_lr=0.00001
            )
        ]
        
        # Train model (initial training with frozen base)
        logger.info("Starting initial training (frozen base)...")
        history = model.fit(
            X_train, y_train,
            validation_data=(X_val, y_val),
            batch_size=self.batch_size,
            epochs=min(5, self.epochs),
            callbacks=callbacks,
            verbose=1
        )
        
        # Fine-tune with unfrozen base (if enough data)
        if len(X_train) >= 500:
            logger.info("Fine-tuning with unfrozen base layers...")
            base_model.trainable = True
            
            # Re-compile with lower learning rate
            model.compile(
                optimizer=keras.optimizers.Adam(learning_rate=0.0001),
                loss={
                    'fog_score': 'mse',
                    'fog_level': 'sparse_categorical_crossentropy'
                },
                loss_weights={
                    'fog_score': 1.0,
                    'fog_level': 0.5
                },
                metrics={
                    'fog_score': ['mae'],
                    'fog_level': ['accuracy']
                }
            )
            
            # Continue training
            history_fine = model.fit(
                X_train, y_train,
                validation_data=(X_val, y_val),
                batch_size=self.batch_size,
                epochs=self.epochs - 5,
                initial_epoch=5,
                callbacks=callbacks,
                verbose=1
            )
        
        # Save model
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        model_path = self.models_dir / f"fog_mobilenet_{timestamp}.h5"
        model.save(model_path)
        logger.info(f"Model saved to {model_path}")
        
        # Save TFLite version for mobile/edge deployment
        converter = tf.lite.TFLiteConverter.from_keras_model(model)
        converter.optimizations = [tf.lite.Optimize.DEFAULT]
        tflite_model = converter.convert()
        
        tflite_path = self.models_dir / f"fog_mobilenet_{timestamp}.tflite"
        with open(tflite_path, 'wb') as f:
            f.write(tflite_model)
        logger.info(f"TFLite model saved to {tflite_path} "
                   f"(size: {len(tflite_model) / 1024:.1f} KB)")
        
        # Save training metadata
        metadata = {
            'timestamp': timestamp,
            'training_samples': len(X_train),
            'validation_samples': len(X_val),
            'epochs_trained': len(history.history['loss']),
            'final_metrics': {
                'train_loss': float(history.history['loss'][-1]),
                'val_loss': float(history.history['val_loss'][-1]),
                'fog_score_mae': float(history.history['fog_score_mae'][-1]),
                'fog_level_accuracy': float(history.history['fog_level_accuracy'][-1])
            },
            'model_path': str(model_path),
            'tflite_path': str(tflite_path)
        }
        
        metadata_path = self.models_dir / f"training_metadata_{timestamp}.json"
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        logger.info("Training complete!")
        logger.info(f"Final validation metrics:")
        logger.info(f"  Fog score MAE: {metadata['final_metrics']['fog_score_mae']:.3f}")
        logger.info(f"  Fog level accuracy: {metadata['final_metrics']['fog_level_accuracy']:.2%}")
        
        return model, metadata
    
    def evaluate_model(self, model, test_images_dir: str = None):
        """Evaluate model on test images"""
        if test_images_dir:
            # Load and evaluate test images
            pass  # Implementation for specific test set
        
        # Quick evaluation on a sample image
        logger.info("Testing model on sample prediction...")
        
        # Create a sample foggy image (gradient)
        test_img = np.zeros((224, 224, 3))
        for i in range(224):
            test_img[i, :, :] = i / 224.0  # Gradient from dark to light
        
        test_img = test_img.reshape(1, 224, 224, 3)
        
        predictions = model.predict(test_img)
        fog_score = predictions['fog_score'][0][0] * 100
        fog_level = predictions['fog_level'][0].argmax()
        
        level_names = ['none', 'light', 'moderate', 'heavy']
        logger.info(f"Sample prediction: Fog score={fog_score:.1f}, "
                   f"Level={level_names[fog_level]}")

def main():
    """Main training entry point"""
    trainer = FogMobileNetTrainer()
    
    # Check if we have enough data
    training_files = list(trainer.training_dir.glob("training_*.json"))
    
    if len(training_files) < 10:
        logger.warning(f"Only {len(training_files)} training files found.")
        logger.warning("Recommend collecting more data before training.")
        logger.info("Run the Gemini labeling pipeline to collect more data.")
        return
    
    logger.info(f"Found {len(training_files)} training files. Starting training...")
    
    model, metadata = trainer.train()
    trainer.evaluate_model(model)
    
    logger.info(f"\nModel ready for deployment!")
    logger.info(f"Model size: {os.path.getsize(metadata['model_path']) / 1024 / 1024:.1f} MB")
    logger.info(f"TFLite size: {os.path.getsize(metadata['tflite_path']) / 1024:.1f} KB")

if __name__ == "__main__":
    main()