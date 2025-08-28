# Seagrass & Blue Carbon Futuristic Analyzer

A local web app (Flask) with a futuristic UI to upload a photo, auto-segment **seagrass vs white sand**, and estimate **blue carbon**.

> ⚠️ **Blue carbon estimation is a placeholder** using a configurable areal carbon density. Replace with site-specific calibration for scientific use.

## Quickstart

1. Create and activate a virtual environment (recommended).
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the app:
   ```bash
   python app.py
   ```
4. Open http://127.0.0.1:5000 in your browser.

## How it works
- **Segmentation (HSV masks)**  
  - *Seagrass*: Hue in ~[35°, 95°], S > 50, V > 35 + morphology cleanup.  
  - *White sand*: Low saturation & high value (S < 60, V > 185), plus near-neutral hue.
- **Outputs**  
  - Percent cover for *Seagrass* and *White Sand* (relative to all pixels).  
  - Overlay preview images.  
  - **Blue carbon** estimate (see config).

## Configuration
Edit `config.json`:
```json
{
  "quadrat_area_m2": 0.25,
  "carbon_density_g_per_m2": 100.0
}
```
- `quadrat_area_m2`: area represented by the image (default 50×50 cm).  
- `carbon_density_g_per_m2`: grams of carbon per m² for fully vegetated seagrass (placeholder).  
> Estimated blue carbon = (seagrass_cover_fraction) × (quadrat_area_m2) × (carbon_density_g_per_m2)

## Notes
- Works best with nadir photos of small quadrats and good lighting.
- If highlights/glints appear, the pipeline includes specular suppression and morphology cleanup.
- For research-grade use, replace the simple masks with your trained model (e.g., U-Net) inside `model_pipeline.py`.