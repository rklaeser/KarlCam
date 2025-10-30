"""
Test data factories for KarlCam API
"""
import factory
from datetime import datetime, timedelta
from faker import Faker
from unittest.mock import Mock

fake = Faker()

class WebcamFactory(factory.Factory):
    """Factory for creating webcam test data"""
    
    class Meta:
        model = Mock
    
    id = factory.LazyFunction(lambda: fake.uuid4())
    name = factory.LazyFunction(lambda: fake.city() + " Camera")
    latitude = factory.LazyFunction(lambda: fake.latitude())
    longitude = factory.LazyFunction(lambda: fake.longitude())
    url = factory.LazyFunction(lambda: fake.url() + "/camera.jpg")
    video_url = factory.LazyFunction(lambda: fake.url() + "/camera.mp4")
    description = factory.LazyFunction(lambda: fake.sentence())
    active = True

class ImageCollectionFactory(factory.DictFactory):
    """Factory for creating image collection test data"""
    
    id = factory.Sequence(lambda n: n + 1)
    webcam_id = factory.LazyFunction(lambda: fake.uuid4())
    timestamp = factory.LazyFunction(lambda: datetime.now().isoformat() + "Z")
    image_filename = factory.LazyAttribute(
        lambda obj: f"{obj['webcam_id']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
    )
    cloud_storage_path = factory.LazyAttribute(
        lambda obj: f"gs://karlcam-test/raw_images/{obj['image_filename']}"
    )

class ImageLabelFactory(factory.DictFactory):
    """Factory for creating image label test data"""
    
    id = factory.Sequence(lambda n: n + 1)
    image_id = factory.Sequence(lambda n: n + 1)
    labeler_name = "gemini-1.5"
    labeler_version = "1.5.0"
    fog_score = factory.LazyFunction(lambda: fake.random_int(min=0, max=100))
    fog_level = factory.LazyFunction(lambda: fake.random_element(
        elements=["Clear", "Light Fog", "Moderate Fog", "Heavy Fog", "Very Heavy Fog"]
    ))
    confidence = factory.LazyFunction(lambda: round(fake.random.uniform(0.5, 1.0), 2))
    reasoning = factory.LazyFunction(lambda: fake.sentence())

class ImageWithLabelsFactory(factory.DictFactory):
    """Factory for creating image data with associated labels"""
    
    webcam_id = factory.LazyFunction(lambda: fake.uuid4())
    timestamp = factory.LazyFunction(lambda: datetime.now().isoformat() + "Z")
    labels = factory.SubFactory(factory.ListFactory, factory.SubFactory(ImageLabelFactory), size=1)

class CameraConditionsFactory(factory.DictFactory):
    """Factory for creating camera conditions response data"""
    
    id = factory.LazyFunction(lambda: fake.uuid4())
    name = factory.LazyFunction(lambda: fake.city() + " Camera")
    lat = factory.LazyFunction(lambda: float(fake.latitude()))
    lon = factory.LazyFunction(lambda: float(fake.longitude()))
    description = factory.LazyFunction(lambda: fake.sentence())
    fog_score = factory.LazyFunction(lambda: fake.random_int(min=0, max=100))
    fog_level = factory.LazyFunction(lambda: fake.random_element(
        elements=["Clear", "Light Fog", "Moderate Fog", "Heavy Fog", "Very Heavy Fog"]
    ))
    confidence = factory.LazyFunction(lambda: round(fake.random.uniform(0.5, 1.0), 2))
    weather_detected = factory.LazyAttribute(lambda obj: obj['fog_score'] > 20)
    weather_confidence = factory.LazyFunction(lambda: round(fake.random.uniform(0.5, 1.0), 2))
    timestamp = factory.LazyFunction(lambda: datetime.now().isoformat() + "Z")
    active = True

class SystemStatusFactory(factory.DictFactory):
    """Factory for creating system status data"""
    
    karlcam_mode = factory.LazyFunction(lambda: fake.random_element(elements=[0, 1]))
    description = factory.LazyFunction(lambda: fake.sentence())
    updated_at = factory.LazyFunction(lambda: datetime.now().isoformat() + "Z")
    updated_by = factory.LazyFunction(lambda: fake.user_name())

class StatsResponseFactory(factory.DictFactory):
    """Factory for creating statistics response data"""
    
    total_assessments = factory.LazyFunction(lambda: fake.random_int(min=100, max=10000))
    active_cameras = factory.LazyFunction(lambda: fake.random_int(min=5, max=20))
    avg_fog_score = factory.LazyFunction(lambda: round(fake.random.uniform(0, 100), 2))
    avg_confidence = factory.LazyFunction(lambda: round(fake.random.uniform(0.5, 1.0), 2))
    foggy_conditions = factory.LazyFunction(lambda: fake.random_int(min=10, max=1000))
    last_update = factory.LazyFunction(lambda: datetime.now().isoformat() + "Z")
    period = "24 hours"

# Special factories for specific test scenarios
class FoggyImageFactory(ImageWithLabelsFactory):
    """Factory for creating images with high fog scores"""
    
    labels = factory.LazyFunction(lambda: [
        ImageLabelFactory(
            fog_score=fake.random_int(min=60, max=100),
            fog_level=fake.random_element(elements=["Heavy Fog", "Very Heavy Fog"]),
            confidence=fake.random.uniform(0.8, 1.0)
        )
    ])

class ClearImageFactory(ImageWithLabelsFactory):
    """Factory for creating images with low fog scores"""
    
    labels = factory.LazyFunction(lambda: [
        ImageLabelFactory(
            fog_score=fake.random_int(min=0, max=20),
            fog_level="Clear",
            confidence=fake.random.uniform(0.8, 1.0)
        )
    ])

class NightModeStatusFactory(SystemStatusFactory):
    """Factory for creating night mode system status"""
    
    karlcam_mode = 1
    description = "Night mode - collection paused"

class ActiveModeStatusFactory(SystemStatusFactory):
    """Factory for creating active mode system status"""
    
    karlcam_mode = 0
    description = "Active mode - normal operation"

# Utility functions for creating complex test scenarios
def create_webcam_with_recent_images(webcam_id=None, num_images=3, fog_scores=None):
    """Create a webcam with recent images for testing"""
    if webcam_id is None:
        webcam_id = fake.uuid4()
    
    webcam = WebcamFactory(id=webcam_id)
    
    if fog_scores is None:
        fog_scores = [fake.random_int(min=0, max=100) for _ in range(num_images)]
    
    images = []
    for i, score in enumerate(fog_scores):
        timestamp = datetime.now() - timedelta(minutes=i*10)
        images.append(ImageWithLabelsFactory(
            webcam_id=webcam_id,
            timestamp=timestamp.isoformat() + "Z",
            labels=[ImageLabelFactory(fog_score=score)]
        ))
    
    return webcam, images

def create_multi_camera_scenario(num_cameras=3):
    """Create multiple cameras with varying fog conditions"""
    cameras = []
    images_by_camera = {}
    
    for i in range(num_cameras):
        webcam_id = f"test-camera-{i+1}"
        webcam = WebcamFactory(id=webcam_id, name=f"Test Camera {i+1}")
        
        # Create varying fog conditions
        fog_score = fake.random_int(min=0, max=100)
        images = [ImageWithLabelsFactory(
            webcam_id=webcam_id,
            labels=[ImageLabelFactory(fog_score=fog_score)]
        )]
        
        cameras.append(webcam)
        images_by_camera[webcam_id] = images
    
    return cameras, images_by_camera