/**
 * JATAYUV Spatial Intelligence & Infrastructure Inspection Type Definitions.
 * Phase 3: Advanced Infrastructure Inspection, Risk Intelligence & Historical Comparison.
 */

export type InfrastructureClassType =
  | "transmission_tower"
  | "transmission_line"
  | "insulator"
  | "crossarm"
  | "electrical_equipment"
  | "structural_damage";

export type AnomalySeverityType = "NORMAL" | "INFO" | "WARNING" | "CRITICAL";

export type RiskCategoryType = "NEGLIGIBLE" | "LOW" | "MODERATE" | "HIGH" | "CRITICAL";

export interface SpatialObservationDetail {
  frame_index: number;
  timestamp_s: number;
  camera_id: string;
  image_uv: [number, number];
  depth_val: number;
  world_xyz: [number, number, number];
  confidence: number;
}

export interface TowerComponentInstanceItem {
  component_id: string;
  component_type: "tower_body" | "tower_legs" | "crossarm" | "bracing_member" | "insulator_attachment_point" | "ground_wire_peak";
  confidence: number;
  bbox: [number, number, number, number];
  contour_polygon: [number, number][];
  area_px: number;
  aspect_ratio: number;
  attributes?: Record<string, any>;
}

export interface TowerSegmentationData {
  tower_track_id: string;
  frame_index: number;
  total_components_segmented: number;
  structural_completeness_pct: number;
  mask_shape: [number, number];
  components: TowerComponentInstanceItem[];
}

export interface CatenaryModelData {
  line_track_id: string;
  parameter_a: number;
  vertex_z0: number;
  vertex_y0: number;
  span_length: number;
  maximum_sag: number;
  is_continuous: boolean;
  continuity_status: "CONTINUOUS" | "SAG_WARNING" | "DISCONTINUITY_FLAGGED";
  discontinuity_gap_units: number;
  support_points: [number, number, number][];
  total_measured_points: number;
  total_interpolated_points: number;
  measured_points: { position: [number, number, number]; is_measured: boolean; confidence: number }[];
  interpolated_catenary_curve: { position: [number, number, number]; is_measured: boolean }[];
}

export interface InsulatorFindingItem {
  finding_id: string;
  insulator_track_id: string;
  defect_type: string;
  severity: "INFO" | "WARNING" | "CRITICAL";
  confidence: number;
  affected_disc_index: number | null;
  image_coords: [number, number, number, number];
  evidence_crop_path: string | null;
  description: string;
  recommendation: string;
  requires_field_verification: boolean;
}

export interface InsulatorAuditData {
  insulator_track_id: string;
  total_discs_detected: number;
  expected_disc_count: number;
  string_integrity_score_pct: number;
  findings: InsulatorFindingItem[];
  attributes?: Record<string, any>;
}

export interface ClearanceBottleneckData {
  conductor_point_3d: [number, number, number];
  terrain_point_3d: [number, number, number];
  clearance_distance: number;
  uncertainty_margin: number;
  clearance_status: "NORMAL" | "ADVISORY" | "CLEARANCE_WARNING";
  relative_elevation_delta: number;
}

export interface SpanClearanceData {
  line_track_id: string;
  minimum_clearance: number;
  average_clearance: number;
  maximum_clearance: number;
  clearance_status: "NORMAL" | "ADVISORY" | "CLEARANCE_WARNING";
  bottleneck: ClearanceBottleneckData;
  scale_metadata: Record<string, any>;
  disclaimer: string;
}

export interface AssetRiskEvaluationData {
  asset_id: string;
  class_name: string;
  risk_score: number;
  risk_category: RiskCategoryType;
  contributing_factors: string[];
  factor_breakdown: {
    confidence_weight: number;
    severity_weight: number;
    uncertainty_weight: number;
    temporal_support_weight: number;
    historical_drift_weight: number;
  };
  recommended_action: string;
  requires_human_verification: boolean;
}

export interface LocalizedInfrastructureItem {
  track_id: string;
  class_name: InfrastructureClassType | string;
  position: [number, number, number];
  extents: [number, number, number];
  uncertainty_radius: number;
  confidence: number;
  observations_count: number;
  severity: AnomalySeverityType;
  inspection_notes: string[];
  requires_field_verification: boolean;
  line_waypoints?: [number, number, number][];
  observations?: SpatialObservationDetail[];
  tower_components?: TowerSegmentationData;
  catenary_model?: CatenaryModelData;
  insulator_audit?: InsulatorAuditData;
  clearance_result?: SpanClearanceData;
  risk_evaluation?: AssetRiskEvaluationData;
}

export interface InspectionAnomalyItem {
  anomaly_id: string;
  target_track_id: string;
  class_name: string;
  anomaly_type: string;
  severity: "INFO" | "WARNING" | "CRITICAL";
  finding_type: "AI_OBSERVATION" | "VERIFIED_FINDING";
  confidence: number;
  position_3d: [number, number, number];
  description: string;
  engineering_recommendation: string;
  requires_field_verification: boolean;
  evidence_frame_indices: number[];
  evidence_crop_path?: string | null;
}

export interface InspectionReportData {
  mission_id: string;
  total_components_inspected: number;
  total_anomalies_detected: number;
  critical_count: number;
  warning_count: number;
  info_count: number;
  risk_index_pct: number;
  disclaimer: string;
  anomalies: InspectionAnomalyItem[];
}

export interface ClearanceSummaryData {
  total_spans_evaluated: number;
  minimum_corridor_clearance: number;
  bottleneck_span_id: string;
  encroachment_warnings_count: number;
  regulatory_disclaimer: string;
}

export interface RiskSummaryData {
  mean_risk_score: number;
  distribution: {
    NEGLIGIBLE: number;
    LOW: number;
    MODERATE: number;
    HIGH: number;
    CRITICAL: number;
  };
  total_assets_evaluated: number;
  requires_field_patrol_count: number;
}

export interface AssetMatchPairData {
  asset_id_a: string;
  asset_id_b: string;
  class_name: string;
  spatial_separation_units: number;
  confidence_delta: number;
  tilt_delta_deg: number;
  status_change: "UNCHANGED" | "DEGRADED" | "IMPROVED" | "NEW_DEFECT";
  notes: string[];
}

export interface HistoricalComparisonReportData {
  mission_id_a: string;
  mission_id_b: string;
  scale_ratio_b_to_a: number;
  total_matched_assets: number;
  unmatched_assets_a: string[];
  unmatched_assets_b: string[];
  new_anomalies_count: number;
  persistent_anomalies_count: number;
  resolved_anomalies_count: number;
  escalated_anomalies_count: number;
  overall_health_trend: "STABLE" | "DEGRADING" | "IMPROVED";
  summary_findings: string[];
  matched_pairs: AssetMatchPairData[];
}

export interface SpatialIntelligenceResponse {
  mission_id: string;
  total_frames_processed: number;
  total_tracked_objects: number;
  infrastructure_objects_3d: LocalizedInfrastructureItem[];
  inspection_report: InspectionReportData;
  clearance_summary?: ClearanceSummaryData;
  risk_summary?: RiskSummaryData;
  scale_metadata: {
    units: string;
    scale_type: string;
    metric_calibrated: boolean;
    scale_disclaimer: string;
  };
  timing_breakdown: Record<string, number>;
  output_json_path: string;
}
