# KarlCam Model Evaluation

Compare Gemini Vision API vs trained MobileNet model performance for fog detection.

## Purpose

This evaluation system helps you:
1. Measure which model (Gemini or MobileNet) performs better for fog detection
2. Identify disagreements between models for active learning
3. Track confidence scores and accuracy metrics
4. Build a dataset of high-value training examples

## Files

- `compare_models.py` - Main comparison script that runs both models
- `comparisons.db` - SQLite database tracking all comparisons (created automatically)

## Running Evaluations

### Local Development

```bash
# Run comparison on recent images
python evaluation/compare_models.py
```

### On GKE Cluster

```bash
# First, ensure evaluation job is deployed
kubectl apply -f gke/evaluate-models.yaml

# Run evaluation on-demand
./gke/run-evaluation.sh run

# Schedule daily evaluations (runs at 2am)
./gke/run-evaluation.sh schedule

# View latest results
./gke/run-evaluation.sh results

# Export comparison database to analyze locally
./gke/run-evaluation.sh export
sqlite3 comparisons.db 'SELECT * FROM comparisons ORDER BY disagreement_score DESC LIMIT 10'
```

## Understanding Results

The comparison tracks:
- **fog_score**: 0.0 (clear) to 1.0 (heavy fog)
- **confidence**: How certain each model is
- **disagreement_score**: Difference between model predictions
- **needs_review**: Flagged when models disagree significantly

### Key Metrics

After human labeling, the system calculates:
- **mobilenet_avg_error**: Average error vs ground truth
- **gemini_avg_error**: Average error vs ground truth
- **better_model**: Which model has lower error

## Active Learning Workflow

1. **Run evaluation** to find disagreements
2. **Review flagged images** where models disagree most
3. **Add human labels** for ground truth
4. **Retrain MobileNet** on high-value examples
5. **Re-evaluate** to measure improvement

## Database Schema

```sql
CREATE TABLE comparisons (
    id INTEGER PRIMARY KEY,
    image_path TEXT,
    timestamp TEXT,
    gemini_fog_score REAL,
    gemini_confidence REAL,
    gemini_reasoning TEXT,
    mobilenet_fog_score REAL,
    mobilenet_confidence REAL,
    disagreement_score REAL,
    needs_review BOOLEAN,
    human_label REAL,  -- Ground truth when reviewed
    created_at DATETIME
);
```

## Improving the Models

### If MobileNet is Better
Once trained MobileNet consistently outperforms Gemini:
- Use MobileNet predictions to auto-correct Gemini labels
- Consider skipping Gemini for production inference
- Only use Gemini for bootstrapping new training data

### If Gemini is Better
If Gemini performs better:
- Continue using Gemini for labeling
- Retrain MobileNet with more Gemini-labeled data
- Consider model architecture improvements

## Cost Optimization

Running evaluations as Jobs (not continuous):
- Evaluation runs only when triggered
- Costs ~$0.01 per evaluation run
- Daily scheduled evaluation: ~$0.30/month