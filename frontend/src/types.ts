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
export type Body = Record<string, string | number>;
export type Action = "deliver" | "return" | "condition" | "rectify";
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
