# KarlCam Label Module

Flexible labeling system for applying different fog detection techniques to collected images.

## Structure

```
label/
├── labelers/                    # Individual labeling techniques
│   ├── __init__.py             # Factory for creating labelers
│   ├── base.py                 # Base labeler class
│   ├── gemini.py               # Standard Gemini Vision API
│   └── gemini_masked.py        # Gemini with sky masking
├── label_images.py             # Main labeling script
├── test_labelers.py            # Testing and comparison tools
└── README.md                   # This file
```

## Usage

### Production Labeling

Label all collected images with standard Gemini labeler:
```bash
cd KarlCam/label
python label_images.py gemini
```

### Testing Individual Labelers

Test a specific labeler on an image:
```bash
# Standard Gemini
python labelers/gemini.py --image test_image.jpg

# Gemini with sky masking
python labelers/gemini_masked.py --image test_image.jpg --save-masked masked_output.jpg
```

### Comparison Testing (Vertex AI Workbench)

```python
from test_labelers import run_comparison_experiment, setup_environment

# Setup environment
setup_environment()

# Compare labelers on sample images
results, df = run_comparison_experiment(
    "gs://karlcam-fog-data",          # Cloud storage bucket
    ["gemini", "gemini_masked"],      # Labelers to compare
    limit=10                          # Number of test images
)

# Analyze results
print(df.groupby('labeler')[['fog_score', 'confidence']].describe())
```

## Adding New Labelers

1. Create new labeler file in `labelers/` inheriting from `BaseLabeler`
2. Add to factory in `labelers/__init__.py`
3. Test using individual labeler script or comparison tool

## Database Schema

The labeling system uses these tables:

**image_collections** - Raw collected images:
- `id`, `webcam_id`, `timestamp`, `image_filename`, `cloud_storage_path`

**image_labels** - Multiple labels per image:
- `id`, `image_id`, `labeler_name`, `labeler_version`, `fog_score`, `fog_level`, `confidence`, `label_data`

This allows comparing different labeling techniques on the same images.