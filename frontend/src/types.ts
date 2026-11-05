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
  assignment: string;
  current_custodian: Custodian | null;
  revision: number;
  created_at: string;
  created_by: User;
  rectifiable_movement_id: number | null;
  faculty_id?: number | null;
  acquisition?: AcquisitionSnapshot | null;
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
export interface Page {
  count: number;
  next: string | null;
  previous: string | null;
  results: Asset[];
}
export type Fields = Record<string, string>;
export type JsonValue = string | number | boolean | null | JsonValue[] | { [key: string]: JsonValue };
export type Body = Record<string, JsonValue | undefined>;
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
  entrega: "Entrega",
  devolucion: "Devolución",
  cambio_condicion: "Cambio de condición",
  rectificacion: "Rectificación",
  computadora_escritorio: "Computadora de escritorio",
  portatil: "Portátil",
  monitor: "Monitor",
  impresora: "Impresora",
  equipo_red: "Equipo de red",
  periferico: "Periférico",
};

export interface SessionUser extends User {
  permissions: string[];
  must_change_password: boolean;
}
export interface Faculty { id: number; name: string; active: boolean }
export interface AcquisitionItem {
  asset_id: number; asset_code?: string; asset_revision?: number; item_value: string;
  acquired_on: string | null; date_unknown_reason: string;
}
export interface AcquisitionDocument {
  id: number; source: "PURCHASE" | "DONATION"; reference: string;
  document_date: string | null; supplier: string; invoice_total: string | null;
  support_type: string; currency: string; created_by: User; created_at: string; items: AcquisitionItem[];
}
export interface AcquisitionSnapshot {
  document_id: number; source: "PURCHASE" | "DONATION"; reference: string;
  document_date: string | null; supplier: string; invoice_total: string | null;
  support_type: string; currency: string; item_value: string;
  acquired_on: string | null; date_unknown_reason: string;
}
export type PurchaseExistingItem = { asset_id: number; expected_revision: number; reason: string; item_value: string } & ({ acquired_on: string } | { date_unknown_reason: string });
export interface PurchaseInvoiceInput {
  items?: PurchaseExistingItem[];
  reference: string; document_date: string; supplier: string; invoice_total: string;
}
export interface PurchaseAssetInput {
  name: string; description: string; category: string; brand: string; model: string;
  serial_number: string; location: string; condition: string;
  faculty_id: number; acquisition_document_id: number; item_value: string;
  acquired_on?: string; date_unknown_reason?: string;
}
export type PurchasedAsset = Asset & { faculty_id: number; acquisition: AcquisitionSnapshot };

export type DonationExistingItem = Omit<PurchaseExistingItem, "item_value" | "acquired_on" | "date_unknown_reason"> & { estimated_value: string } & ({ acquired_on: string } | { date_unknown_reason: string });
export interface DonationDocumentInput { reference: string; support_type: string; items?: DonationExistingItem[] }

export interface HistoryEvent { event_type: string; event_id: number; occurred_at: string; actor: User; resulting_revision: number | null; data: unknown }

export type DocumentSnapshot = Pick<AcquisitionDocument, "source" | "reference" | "document_date" | "supplier" | "invoice_total" | "support_type" | "currency">;
