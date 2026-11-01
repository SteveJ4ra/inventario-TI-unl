import type { Asset, Options, Movement } from "../types";
export const options: Options = {
  categories: [{ value: "portatil", label: "Portátil" }],
  conditions: [
    { value: "operativo", label: "Operativo" },
    { value: "averiado", label: "Averiado" },
    { value: "en_reparacion", label: "En reparación" },
  ],
  assignments: [
    { value: "disponible", label: "Disponible" },
    { value: "asignado", label: "Asignado" },
  ],
  locations: ["Laboratorio"],
};
export const person = {
  id: 1,
  full_name: "Docente de prueba",
  email: "docente@example.org",
  department: "",
};
export const asset: Asset = {
  id: 1,
  code: "TI-000001",
  name: "Portátil",
  description: "Equipo de prácticas",
  category: "portatil",
  brand: "Ejemplo",
  model: "A1",
  serial_number: "LAB-001",
  location: "Laboratorio",
  condition: "operativo",
  assignment: "disponible",
  current_custodian: null,
  revision: 0,
  created_at: "2026-10-20T12:00:00Z",
  created_by: { id: 1, username: "gestor" },
  rectifiable_movement_id: null,
};
export const movement: Movement = {
  id: 1,
  asset_id: 1,
  type: "entrega",
  occurred_at: "2026-10-20T12:00:00Z",
  actor: { id: 1, username: "gestor", recorded_label: "gestor" },
  custodian: person,
  before: {
    condition: "operativo",
    assignment: "disponible",
    custodian_id: null,
    location: "Laboratorio",
  },
  after: {
    condition: "operativo",
    assignment: "asignado",
    custodian_id: 1,
    location: "Aula",
  },
  note: "",
  reason: "",
  rectifies_id: null,
  rectified_by_id: 2,
  resulting_revision: 1,
};
