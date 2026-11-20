/**
 * JATAYUV Phase 4: Digital Twin & Infrastructure Monitoring Type Definitions.
 */

export interface GeoJsonGeometry {
  type: "Point" | "LineString" | "Polygon";
  coordinates: any;
}

export interface GeoJsonFeature {
  type: "Feature";
  geometry: GeoJsonGeometry;
  properties: Record<string, any>;
}

export interface GeoJsonFeatureCollection {
  type: "FeatureCollection";
  crs?: {
    type: string;
    properties: { name: string };
  };
  features: GeoJsonFeature[];
}

export interface GeographicCorridorData {
  mission_id: string;
  crs: string;
  is_georeferenced: boolean;
  geojson: GeoJsonFeatureCollection;
  flight_path_geojson: GeoJsonFeatureCollection;
  metadata: {
    total_assets_mapped: number;
    is_metric_rtk: boolean;
    datum: string;
  };
  disclaimer: string;
}

export interface MissionTimelinePoint {
  mission_id: string;
  inspection_date: string;
  total_assets: number;
  anomalies_count: number;
  critical_count: number;
  mean_risk_score: number;
  clearance_bottleneck: number;
  overall_status: "BASELINE" | "STABLE" | "DEGRADING" | "IMPROVED";
}

export interface CorridorAssetHistory {
  asset_id: string;
  class_name: string;
  current_health_status: "HEALTHY" | "NEEDS_REVIEW" | "DEFECT_CONFIRMED";
  tilt_history: number[];
  defect_history: string[];
  observations_count: number;
}

export interface MultiMissionDigitalTwinData {
  corridor_id: string;
  mission_ids: string[];
  timeline_points: MissionTimelinePoint[];
  asset_histories: CorridorAssetHistory[];
  total_new_anomalies: number;
  total_persistent_anomalies: number;
  total_resolved_anomalies: number;
  overall_corridor_trajectory: "STABLE" | "DEGRADING" | "IMPROVING";
  summary_findings: string[];
}

export interface FindingVerificationData {
  id: string;
  mission_id: string;
  asset_track_id: string;
  anomaly_id: string;
  finding_type: "AI_OBSERVATION" | "VERIFIED_FINDING";
  verification_status: "UNVERIFIED" | "VERIFIED_DEFECT" | "FALSE_POSITIVE" | "ACCEPTED_CONDITION";
  verified_by_user_id: string | null;
  verified_at: string | null;
  engineer_notes: string;
  repair_status: "PENDING_REVIEW" | "WORK_ORDER_CREATED" | "IN_REPAIR" | "REPAIRED" | "RESOLVED";
  field_photo_path: string | null;
}

export interface InspectionTaskData {
  id: string;
  mission_id: string;
  title: string;
  description: string;
  priority: "LOW" | "MEDIUM" | "HIGH" | "URGENT";
  status: "OPEN" | "ASSIGNED" | "IN_PROGRESS" | "COMPLETED";
  assigned_to: string | null;
  due_date: string | null;
  target_asset_ids: string[];
  created_at: string;
  resolution_notes?: string | null;
}

export interface OperationalAnalyticsData {
  total_missions_inspected: number;
  total_assets_monitored: number;
  total_ai_observations: number;
  human_verified_defects: number;
  unresolved_observations_count: number;
  mean_corridor_risk_score: number;
  corridor_health_trajectory: string;
  risk_distribution: {
    NEGLIGIBLE: number;
    LOW: number;
    MODERATE: number;
    HIGH: number;
    CRITICAL: number;
  };
}
