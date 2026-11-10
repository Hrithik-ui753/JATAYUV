from __future__ import annotations

from backend.app.services.perception.models import (  # noqa: F401
    FrameDepthResult,
    FrameDynamicObjectResult,
    FramePerception,
    FrameSegmentationResult,
    PerceptionArtifact,
    PerceptionRun,
)

from backend.app.services.perception.schemas import (  # noqa: F401
    DynamicDetection,
    FrameDepthOutput,
    FrameDynamicOutput,
    FramePerceptionOutput,
    FrameSegmentationOutput,
    PerceptionModelInfo,
    PerceptionProcessRequest,
    PerceptionReport,
    PerceptionRunStatus,
)

from backend.app.services.perception.fusion import (  # noqa: F401
    build_perception_record_from_frame,
    persist_perception_record_to_db,
    sha256_file,
    sha256_bytes,
)

from backend.app.services.perception.depth import (  # noqa: F401
    DepthInferenceResult,
    describe_depth_model as describe_depth_model,
    infer_depth as infer_depth,
    is_depth_available as is_depth_available,
)

from backend.app.services.perception.segmentation import (  # noqa: F401
    SegmentationInferenceResult,
    describe_segmentation_model as describe_segmentation_model,
<<<<<<< HEAD
    describe_supported_segmentation_classes as describe_supported_segmentation_classes,
    map_segmentation_target_to_model_class as map_segmentation_target_to_model_class,
=======
>>>>>>> origin/main
    infer_segmentation as infer_segmentation,
    is_segmentation_available as is_segmentation_available,
)

from backend.app.services.perception.dynamic import (  # noqa: F402
    DynamicDetectionResult,
<<<<<<< HEAD
    build_dynamic_exclusion_mask as build_dynamic_exclusion_mask,
    describe_dynamic_model as describe_dynamic_model,
    infer_dynamic_objects as infer_dynamic_objects,
    is_dynamic_detection_available as is_dynamic_detection_available,
)

from backend.app.services.perception.integration import (  # noqa: F401
    describe_all_perception_models as describe_all_perception_models,
)
=======
    describe_dynamic_model as describe_dynamic_model,
    infer_dynamic_objects as infer_dynamic_objects,
    is_dynamic_detection_available as is_dynamic_detection_available,
)
>>>>>>> origin/main
