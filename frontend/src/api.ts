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
    form?: FormData;
    signal?: AbortSignal;
  } = {},
): Promise<T> {
  const write = Boolean(options.body || options.form);
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
      method: write ? "POST" : "GET",
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
      data.fields,
      data.errors,
      data.batch_id,
      data,
    );
  }
  return data;
}
export async function request<T>(
  path: string,
  options: { body?: Body; signal?: AbortSignal } = {},
): Promise<T> {
  return send<T>(path, options);
}
export async function upload<T>(path: string, form: FormData): Promise<T> {
  return send<T>(path, { form });
}
