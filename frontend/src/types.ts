export interface User {
  id: number;
  username: string;
}
export interface Custodian {
  id: number;
  full_name: string;
  email: string;
  department: string;
}
export interface Choice {
  value: string;
  label: string;
}
export interface Options {
  categories: Choice[];
  conditions: Choice[];
  assignments: Choice[];
  locations: string[];
}
export interface Snapshot {
  condition: string;
  assignment: string;
  custodian_id: number | null;
  location: string;
}
export interface Asset {
  id: number;
  code: string;
  name: string;
  description: string;
  category: string;
  brand: string;
  model: string;
  serial_number: string;
  location: string;
  condition: string;
  assignment: string | null;
  lifecycle_status: "localizado" | "no_localizado" | "baja";
  last_lifecycle_status: string | null;
  last_assignment: string | null;
  last_condition: string | null;
  last_location: string | null;
  last_custodian: Custodian | null;
  current_custodian: Custodian | null;
  revision: number;
  created_at: string;
  created_by: User;
  rectifiable_movement_id: number | null;
  active_maintenance_id: number | null;
}
export interface Movement {
  id: number;
  asset_id: number;
  type: string;
  occurred_at: string;
  actor: User & { recorded_label: string };
  custodian: Custodian | null;
  before: Snapshot;
  after: Snapshot;
  note: string;
  reason: string;
  rectifies_id: number | null;
  rectified_by_id: number | null;
  resulting_revision: number;
}
export interface Incident {
  id: number;
  asset_id: number;
  type: "damage" | "observation" | "lost" | "stolen";
  description: string;
  status: "open" | "resolved" | "recovered";
  reported_by: User;
  reported_at: string;
  resolution_note: string;
  resolved_by: User | null;
  resolved_at: string | null;
}
export interface Maintenance {
  id: number;
  asset_id: number;
  status: "in_progress" | "completed" | "interrupted_unlocated";
  description: string;
  previous_location: string;
  workshop_location: string;
  receiving_location: string;
  result: string;
  revision: number;
}
export type HistoryEntry = {
  event_id: number;
  occurred_at: string;
  actor: User;
  resulting_revision: number;
} & (
  | { event_type: "movement"; data: Movement }
  | {
      event_type: "incident";
      data: {
        projection_id: number;
        after: {
          event: Pick<Incident, "type" | "description" | "status" | "resolution_note"> & {
            last_location?: string;
            last_custodian_snapshot?: Custodian | null;
          };
        };
      };
    }
  | {
      event_type: "maintenance";
      data: { projection_id: number; after: { event: Omit<Maintenance, "revision"> } };
    }
  | {
      event_type: "recovery";
      data: {
        projection_id: number;
        after: {
          event: {
            incident_id: number;
            inspected_condition: string;
            recovered_location: string;
            note: string;
          };
        };
      };
    }
);
export interface Page {
  count: number;
  next: string | null;
  previous: string | null;
  results: Asset[];
}
export type Fields = Record<string, string>;
export type Body = Record<string, string | number | boolean>;
export type Action = "deliver" | "return" | "condition" | "rectify";
export type ImportKind = "assets" | "license_lots";
export interface ImportIssue {
  row: number | null;
  field: string;
  message: string;
}
export interface ImportRow {
  row: number;
  values: Record<string, string | number | null>;
  valid?: boolean;
}
export interface AppliedResult {
  kind?: string;
  created?: number;
  [key: string]: unknown;
}
export interface ImportBatch {
  batch_id: string;
  kind: ImportKind;
  schema_version: string;
  state: string;
  content_hash: string;
  summary: Record<string, number | string>;
  errors: ImportIssue[];
  rows: ImportRow[];
  row_count: number;
  page: number;
  next: string | null;
  previous: string | null;
  created_at: string;
  expires_at: string;
  confirmed_at: string | null;
  applied_at: string | null;
  applied_result: AppliedResult | null;
}
export const labels: Record<string, string> = {
  operativo: "Operativo",
  averiado: "Averiado",
  en_reparacion: "En reparación",
  disponible: "Disponible",
  asignado: "Asignado",
  in_progress: "En mantenimiento",
  entrega: "Entrega",
  devolucion: "Devolución",
  cambio_condicion: "Cambio de condición",
  rectificacion: "Rectificación",
  damage: "Daño",
  observation: "Observación",
  lost: "Pérdida",
  stolen: "Robo",
  localizado: "Localizado",
  no_localizado: "No localizado",
  baja: "Baja",
  computadora_escritorio: "Computadora de escritorio",
  portatil: "Portátil",
  monitor: "Monitor",
  impresora: "Impresora",
  equipo_red: "Equipo de red",
  periferico: "Periférico",
};
