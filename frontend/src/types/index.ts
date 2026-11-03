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

export interface DepthResult {
  id: string;
  job_id: string;
  image_id: string;
  depth_map_path: string;
  colormap_path: string;
  min_depth_m: number;
  max_depth_m: number;
  mean_depth_m: number;
  mesh_obj_path?: string;
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

export interface Reconstruction3DResult {
  id: string;
  job_id: string;
  project_id: string;
  pointcloud_ply_path: string;
  mesh_obj_path?: string;
  dsm_tiff_path?: string;
  num_points: number;
  camera_count: number;
  reprojection_error_px: number;
  bounds: {
    min_x: number;
    max_x: number;
    min_y: number;
    max_y: number;
    min_z: number;
    max_z: number;
  };
  created_at: string;
}
