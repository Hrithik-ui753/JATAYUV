export type UserRole = "admin" | "analyst" | "viewer";

export interface User {
  id: string;
  email: string;
  full_name: string;
  role: UserRole;
  is_active: boolean;
  created_at: string;
}

export interface ExifTelemetry {
  camera_make?: string;
  camera_model?: string;
  focal_length_mm?: number;
  iso?: number;
  exposure_time?: string;
  altitude_m?: number;
  latitude?: number;
  longitude?: number;
  heading_deg?: number;
  capture_time?: string;
}

export interface AerialImage {
  id: string;
  project_id: string;
  filename: string;
  file_path: string;
  thumbnail_path: string;
  file_size_bytes: number;
  width: number;
  height: number;
  format: string;
  is_preprocessed: boolean;
  preprocessed_path?: string;
  telemetry: ExifTelemetry;
  created_at: string;
}

export interface Project {
  id: string;
  name: string;
  description: string;
  location_name: string;
  center_lat?: number;
  center_lon?: number;
  image_count: number;
  created_at: string;
  updated_at: string;
}

export type JobType = 
  | "preprocessing"
  | "depth_estimation"
  | "semantic_segmentation"
  | "damage_assessment"
  | "change_detection"
  | "reconstruction_3d";

export type JobStatus = "pending" | "processing" | "completed" | "failed";

export interface AnalysisJob {
  id: string;
  project_id: string;
  job_type: JobType;
  status: JobStatus;
  progress_pct: number;
  error_message?: string;
  celery_task_id?: string;
  created_at: string;
  updated_at: string;
}

/**
 * Depth Anything V2 Small outputs RELATIVE inverse depth. The `*_depth_m` fields are
 * null unless the backend used a checkpoint with a fitted metric calibration
 * (`depth_type === "metric_calibrated"`). Never render relative values as metres.
 */
export interface DepthResult {
  id: string;
  job_id: string;
  image_id: string;
  depth_map_path: string;
  colormap_path: string;
  min_depth_m: number | null;
  max_depth_m: number | null;
  mean_depth_m: number | null;
  mesh_obj_path?: string;
  depth_type: "relative" | "metric_calibrated";
  depth_unit: string;
  is_metric: boolean;
  relative_min?: number | null;
  relative_max?: number | null;
  relative_mean?: number | null;
  model_id?: string;
  model_label?: string;
  model_version?: string;
  checkpoint_path?: string;
  checkpoint_sha256?: string;
  input_size?: number;
  inference_ms?: number;
  raw_depth_path?: string;
  created_at: string;
}

export interface SegmentationResult {
  id: string;
  job_id: string;
  image_id: string;
  mask_path: string;
  overlay_path: string;
  class_distribution: Record<string, number>;
  geojson_path?: string;
  created_at: string;
}

export type DamageLevel = "no_damage" | "minor_damage" | "major_damage" | "destroyed";

export interface DamageFeature {
  id: string;
  building_id: number;
  damage_level: DamageLevel;
  confidence: number;
  polygon: number[][]; // [ [x, y], ... ]
  area_sqm: number;
}

export interface DamageAssessmentResult {
  id: string;
  job_id: string;
  pre_image_id: string;
  post_image_id: string;
  damage_overlay_path: string;
  total_buildings: number;
  counts_by_level: Record<DamageLevel, number>;
  damage_percentage: number;
  severity_index: number;
  features: DamageFeature[];
  created_at: string;
}

export interface ChangeDetectionResult {
  id: string;
  job_id: string;
  before_image_id: string;
  after_image_id: string;
  diff_mask_path: string;
  heatmap_path: string;
  changed_area_pct: number;
  changed_pixels: number;
  significance_score: number;
  created_at: string;
}

/**
 * Result of a real COLMAP reconstruction. `reprojection_error_px` is only present
 * when COLMAP reported it; `bounds` is null when the cloud bounds were unavailable.
 * COLMAP output is not georeferenced, so no DSM is produced.
 */
export interface Reconstruction3DResult {
  id: string;
  job_id: string;
  project_id: string;
  pointcloud_ply_path: string;
  mesh_obj_path?: string;
  dsm_tiff_path?: string;
  num_points: number;
  camera_count: number;
  reprojection_error_px: number | null;
  bounds: {
    min_x: number;
    max_x: number;
    min_y: number;
    max_y: number;
    min_z: number;
    max_z: number;
  } | null;
  backend?: string | null;
  status?: string | null;
  georeferenced?: boolean | null;
  mesh_unavailable_reason?: string | null;
  dsm_unavailable_reason?: string | null;
  created_at: string;
}

// ---------------------------------------------------------------------------
// Mission video processing (P2) types
// ---------------------------------------------------------------------------

export type VideoProcessingStage =
  | "upload_validation"
  | "metadata_extraction"
  | "frame_extraction"
  | "quality_analysis"
  | "duplicate_detection"
  | "frame_selection"
  | "gps_association"
  | "completed"
  | "failed"
  | "cancelled"
  | "queued"
  | "processing"
  | "no_processing"
  | "pending"
  ;

export type FrameQualityStatus =
  | "unreviewed"
  | "accepted"
  | "warning"
  | "rejected"
  | "low_quality"
  ;

export type FrameDuplicateStatus =
  | "unique"
  | "exact_duplicate"
  | "near_duplicate"
  ;

export interface VideoMetadata {
  container_format?: string | null;
  duration_seconds?: number | null;
  width?: number | null;
  height?: number | null;
  nominal_fps?: number | null;
  avg_fps?: number | null;
  codec_name?: string | null;
  codec_long_name?: string | null;
  pixel_format?: string | null;
  stream_time_base?: string | null;
  nb_frames?: number | null;
  probe_duration_method?: string | null;
  truncated_probe?: boolean | null;
}

export interface VideoProcessingStatus {
  status: string;
  stage?: string | null;
  progress_pct?: number | null;
  celery_task_id?: string | null;
  processing_run_id?: string | null;
  error_message?: string | null;
  started_at?: string | null;
  completed_at?: string | null;
  jobs?: Array<{
    id: string;
    status: string;
    stage: string | null;
    progress_pct: number;
    created_at: string | null;
  }> | null;
}

export interface ProcessingReport {
  mission_id: string;
  processing_run_id?: string | null;
  job_id?: string | null;
  job_status?: string | null;
  job_stage?: string | null;
  progress_pct?: number | null;
  total_frames: number;
  frames_accepted: number;
  frames_warning: number;
  frames_rejected: number;
  frames_unreviewed: number;
  duplicate_frames: number;
  selected_frames: number;
  gps_associated_frames: number;
  gps_coverage_pct: number;
  error_message?: string | null;
  notes?: Array<string> | null;
}

export interface Frame {
  id: string;
  mission_id: string;
  video_id: string;
  frame_index: number;
  presentation_timestamp?: number | null;
  timestamp_seconds?: number | null;
  // Internal storage path is omitted from the API response.
  storage_path: null;
  width?: number | null;
  height?: number | null;
  blur_score?: number | null;
  exposure_score?: number | null;
  duplicate_status: string;
  quality_status: string;
  gps_latitude?: number | null;
  gps_longitude?: number | null;
  altitude?: number | null;
  altitude_datum?: string | null;
  duplicate_hash?: string | null;
  duplicate_of_frame_id?: string | null;
  duplicate_distance?: number | null;
  duplicate_reason?: string | null;
  quality_details_json?: string | null;
  is_selected?: boolean | null;
  selection_reason?: string | null;
  processing_run_id?: string | null;
  gps_timestamp_seconds?: number | null;
  gps_timestamp_str?: string | null;
  gps_quality?: string | null;
  gps_source?: string | null;
  gps_association_gap_seconds?: number | null;
  created_at: string;
}

export interface EnqueueProcessingResponse {
  job_id: string;
  celery_task_id?: string | null;
  processing_run_id?: string | null;
  status: string;
}

