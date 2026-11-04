import os
import json
from backend.app.workers.celery_app import celery_app
from backend.app.core.database import SessionLocal
from backend.app.core.config import settings
from backend.app.models.job import Job
from backend.app.models.image import Image
from backend.app.models.inference_result import DepthResult, SegmentationResult, DamageAssessmentResult, ChangeDetectionResult
from backend.app.models.reconstruction import Reconstruction3D
from backend.app.services.preprocessor import ImagePreprocessor
from backend.app.services.depth_estimation import depth_service
from backend.app.services.depth_engine import DepthModelError
from backend.app.services.segmentation import segmentation_service
from backend.app.services.damage_assessment import damage_service
from backend.app.services.change_detection import change_service
from backend.app.services.photogrammetry import photogrammetry_service

@celery_app.task(bind=True)
def task_preprocess_image(self, image_id: str, job_id: str):
    db = SessionLocal()
    try:
        job = db.query(Job).filter(Job.id == job_id).first()
        image = db.query(Image).filter(Image.id == image_id).first()
        if not image or not job:
            return {"status": "failed", "reason": "Not found"}

        job.status = "processing"
        job.progress_pct = 20
        db.commit()

        processed_path = os.path.join(settings.PROCESSED_DIR, f"prep_{image.filename}")
        ImagePreprocessor.preprocess_aerial_image(image.file_path, processed_path)

        image.is_preprocessed = True
        image.preprocessed_path = processed_path

        job.status = "completed"
        job.progress_pct = 100
        db.commit()
        return {"status": "success", "image_id": image_id}
    except Exception as e:
        if job:
            job.status = "failed"
            job.error_message = str(e)
            db.commit()
        raise e
    finally:
        db.close()

@celery_app.task(bind=True)
def task_run_depth_estimation(self, image_id: str, job_id: str, model_id: str = None, input_size: int = None):
    db = SessionLocal()
    try:
        job = db.query(Job).filter(Job.id == job_id).first()
        image = db.query(Image).filter(Image.id == image_id).first()
        if not image or not job:
            return {"status": "failed"}

        job.status = "processing"
        job.progress_pct = 40
        db.commit()

        depth_path = os.path.join(settings.PROCESSED_DIR, f"depth_{image.id}.png")
        colormap_path = os.path.join(settings.PROCESSED_DIR, f"colormap_{image.id}.png")
        mesh_path = os.path.join(settings.PROCESSED_DIR, f"mesh_{image.id}.obj")
        raw_path = os.path.join(settings.PROCESSED_DIR, f"depth_{image.id}.npy")

        try:
            res = depth_service.estimate_depth(
                image.file_path,
                depth_path,
                colormap_path,
                output_mesh_path=mesh_path,
                model_id=model_id,
                input_size=input_size,
                output_raw_path=raw_path,
            )
        except DepthModelError as exc:
            job.status = "failed"
            job.error_message = str(exc)
            db.commit()
            return {"status": "failed", "reason": str(exc)}

        record = DepthResult(
            job_id=job.id,
            image_id=image.id,
            depth_map_path=res["depth_map_path"],
            colormap_path=res["colormap_path"],
            min_depth_m=res["min_depth_m"] if res["min_depth_m"] is not None else 0.0,
            max_depth_m=res["max_depth_m"] if res["max_depth_m"] is not None else 0.0,
            mean_depth_m=res["mean_depth_m"] if res["mean_depth_m"] is not None else 0.0,
            mesh_obj_path=res["mesh_obj_path"],
            depth_type=res["depth_type"],
            depth_unit=res["depth_unit"],
            model_id=res["model_id"],
            model_label=res["model_label"],
            model_version=res["model_version"],
            checkpoint_path=res["checkpoint_path"],
            checkpoint_sha256=res["checkpoint_sha256"],
            input_size=res["input_size"],
            inference_ms=res["inference_ms"],
            relative_min=res["relative_min"],
            relative_max=res["relative_max"],
            relative_mean=res["relative_mean"],
            raw_depth_path=res["raw_depth_path"],
        )
        db.add(record)
        job.status = "completed"
        job.progress_pct = 100
        db.commit()
        return {"status": "success", "model_id": res["model_id"], "depth_type": res["depth_type"]}
    except Exception as e:
        if job:
            job.status = "failed"
            job.error_message = str(e)
            db.commit()
        raise e
    finally:
        db.close()

