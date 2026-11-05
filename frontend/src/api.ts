import type { Body, ImportIssue } from "./types";
export class ApiError extends Error {
  constructor(
    public status: number,
    public code: string,
    message: string,
    public fields?: Record<string, string[]>,
    public errors?: ImportIssue[],
    public batchId?: string,
    public payload?: unknown,
  ) {
    super(message);
  }
}
async function send<T>(
  path: string,
  options: {
    body?: Body;
    method?: "POST" | "PATCH";
    form?: FormData;
    signal?: AbortSignal;
  } = {},
): Promise<T> {
  const write =
    options.method === "PATCH" || Boolean(options.body || options.form);
  const headers: Record<string, string> = {};
  if (write) {
    let csrf: Response;
    try {
      csrf = await fetch("/api/auth/csrf/", { credentials: "same-origin" });
    } catch {
      throw new Error(
        "No se pudo preparar la sesión. Comprueba la conexión y vuelve a intentarlo.",
      );
    }
    if (!csrf.ok)
      throw new Error("No se pudo preparar la sesión. Vuelve a intentarlo.");
    headers["X-CSRFToken"] = (await csrf.json()).csrfToken;
    if (!options.form) headers["Content-Type"] = "application/json";
  }
  const uncertain = write
    ? "No se pudo confirmar la operación. Consulta la ficha y el historial antes de repetirla."
    : "No se pudo conectar con el servidor. Comprueba la conexión y vuelve a consultar.";
  let response: Response;
  try {
    response = await fetch("/api" + path, {
      method: options.method ?? (write ? "POST" : "GET"),
      credentials: "same-origin",
      headers,
      signal: options.signal,
      body: options.form
        ? options.form
        : options.body
          ? JSON.stringify(options.body)
          : undefined,
    });
  } catch (error) {
    if (
      error != null &&
      typeof error === "object" &&
      "name" in error &&
      error.name === "AbortError"
    )
      throw error;
    throw new Error(uncertain);
  }
  const data = await response.json().catch(() => {
    throw new Error(uncertain);
  });
  if (!response.ok) {
    if (response.status === 403 && data.code !== "csrf_failed")
      window.dispatchEvent(new Event("session-expired"));
    throw new ApiError(
      response.status,
      data.code || "request_error",
      data.detail || "No se pudo completar la operación.",
      flattenFields(data.fields),
      data.errors,
      data.batch_id,
      data,
    );
  }
  return data;
}
export async function request<T>(
  path: string,
  options: {
    body?: Body;
    method?: "POST" | "PATCH";
    signal?: AbortSignal;
  } = {},
): Promise<T> {
  return send<T>(path, options);
}
export async function upload<T>(path: string, form: FormData): Promise<T> {
  return send<T>(path, { form });
}


// Reutiliza el transporte de sesión/CSRF; los importes se mantienen como cadenas.
function confirmedDocument(document: import("./types").AcquisitionDocument) {
  if (!document || !Number.isSafeInteger(document.id) || document.id < 1 || !Array.isArray(document.items)
      || !["PURCHASE", "DONATION"].includes(document.source) || typeof document.currency !== "string"
      || typeof document.reference !== "string")
    throw new Error("No se pudo confirmar el documento. Consúltalo antes de volver a intentar el registro.");
  return document;
}
export const purchases = {
  createInvoice: async (data: import("./types").PurchaseInvoiceInput) => confirmedDocument(
    await request<import("./types").AcquisitionDocument>("/acquisitions/", { body: { ...data, items: data.items?.map(item => ({ ...item })), source: "PURCHASE" } })),
  invoice: async (id: number, signal?: AbortSignal) => confirmedDocument(
    await request<import("./types").AcquisitionDocument>("/acquisitions/" + id + "/", { signal })),
  faculties: (signal?: AbortSignal) => request<import("./types").Faculty[]>("/faculties/", { signal }),
  register: async (data: import("./types").PurchaseAssetInput) => {
    const asset = await request<import("./types").PurchasedAsset>("/assets/", { body: { ...data } });
    if (!asset || !Number.isSafeInteger(asset.id) || typeof asset.code !== "string"
        || asset.acquisition?.document_id !== data.acquisition_document_id || typeof asset.acquisition.item_value !== "string")
      throw new Error("No se pudo confirmar el activo. Consulta el documento antes de volver a intentar el registro.");
    return asset;
  },
};

function flattenFields(value: unknown, prefix = ""): Record<string, string[]> | undefined {
  if (value == null || typeof value !== "object") return undefined;
  const result: Record<string, string[]> = {};
  for (const [key, entry] of Object.entries(value)) {
    const path = prefix ? prefix + "." + key : key;
    if (Array.isArray(entry) && entry.every(item => typeof item === "string")) result[path] = entry;
    else Object.assign(result, flattenFields(entry, path));
  }
  return result;
}

// Metadatos distintos; transporte, lectura y alta de activo/línea compartidos.
export const donations = {
  createSupport: async (data: import("./types").DonationDocumentInput) => confirmedDocument(
    await request<import("./types").AcquisitionDocument>("/acquisitions/", { body: {
      ...data, items: data.items?.map(item => ({ ...item })), source: "DONATION",
    } })),
};
