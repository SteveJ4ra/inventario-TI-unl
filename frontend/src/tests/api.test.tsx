import { afterEach, expect, test, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { ApiError, request } from "../api";
import { Field, Form } from "../components/Form";
afterEach(() => vi.unstubAllGlobals());
test("escritura obtiene CSRF y transmite revisión con credenciales de sesión", async () => {
  const fetcher = vi
    .fn()
    .mockResolvedValueOnce(
      new Response(JSON.stringify({ csrfToken: "fixture-token" }), {
        status: 200,
      }),
    )
    .mockResolvedValueOnce(
      new Response(JSON.stringify({ ok: true }), { status: 201 }),
    );
  vi.stubGlobal("fetch", fetcher);
  await request("/assets/1/condition/", {
    body: { condition: "averiado", reason: "Falla", expected_revision: 2 },
  });
  expect(fetcher.mock.calls[1][1]).toMatchObject({
    method: "POST",
    credentials: "same-origin",
    headers: { "X-CSRFToken": "fixture-token" },
  });
  expect(JSON.parse(fetcher.mock.calls[1][1].body).expected_revision).toBe(2);
});
test("un conflicto conserva error y no reintenta la escritura", async () => {
  const fetcher = vi
    .fn()
    .mockResolvedValueOnce(
      new Response(JSON.stringify({ csrfToken: "fixture-token" }), {
        status: 200,
      }),
    )
    .mockResolvedValueOnce(
      new Response(
        JSON.stringify({ code: "stale_revision", detail: "La ficha cambió." }),
        { status: 409 },
      ),
    );
  vi.stubGlobal("fetch", fetcher);
  await expect(
    request("/assets/1/return/", { body: { expected_revision: 0 } }),
  ).rejects.toMatchObject({ status: 409, code: "stale_revision" });
  expect(fetcher).toHaveBeenCalledTimes(2);
});
test("403 de permiso avisa sesión vencida; CSRF no se confunde con logout", async () => {
  const expired = vi.fn();
  window.addEventListener("session-expired", expired);
  try {
    vi.stubGlobal(
      "fetch",
      vi
        .fn()
        .mockResolvedValueOnce(
          new Response(
            JSON.stringify({ code: "permission_denied", detail: "Sin acceso" }),
            { status: 403 },
          ),
        )
        .mockResolvedValueOnce(
          new Response(
            JSON.stringify({ code: "csrf_failed", detail: "Renovar CSRF" }),
            { status: 403 },
          ),
        ),
    );
    await expect(request("/auth/me/")).rejects.toBeInstanceOf(ApiError);
    await expect(request("/auth/me/")).rejects.toBeInstanceOf(ApiError);
    expect(expired).toHaveBeenCalledTimes(1);
  } finally {
    window.removeEventListener("session-expired", expired);
  }
});
test("formulario conserva espacios de contraseña y muestra errores comprensibles", async () => {
  const submit = vi
    .fn()
    .mockRejectedValue(
      new ApiError(400, "validation_error", "Revisa los datos.", {
        serial_number: ["Dato inválido."],
      }),
    );
  const user = userEvent.setup();
  render(
    <Form submit="Guardar" onSubmit={submit}>
      <Field label="Contraseña" name="password" type="password" />
    </Form>,
  );
  await user.type(screen.getByLabelText("Contraseña"), " clave con espacios ");
  await user.click(screen.getByRole("button", { name: "Guardar" }));
  expect(submit.mock.calls[0][0].password).toBe(" clave con espacios ");
  expect(screen.getByRole("alert").textContent).toContain(
    "Número de serie: Dato inválido.",
  );
});

test("fallo de red tras enviar no anuncia éxito ni reenvía automáticamente", async () => {
  const fetcher = vi
    .fn()
    .mockResolvedValueOnce(
      new Response(JSON.stringify({ csrfToken: "fixture-token" }), {
        status: 200,
      }),
    )
    .mockRejectedValueOnce(new TypeError("Failed to fetch"));
  vi.stubGlobal("fetch", fetcher);
  await expect(
    request("/assets/1/return/", { body: { expected_revision: 2 } }),
  ).rejects.toThrow("Consulta la ficha y el historial antes de repetirla");
  expect(fetcher).toHaveBeenCalledTimes(2);
});
test("una consulta cancelada conserva AbortError para ignorar resultados obsoletos", async () => {
  vi.stubGlobal(
    "fetch",
    vi.fn().mockRejectedValue(new DOMException("Cancelled", "AbortError")),
  );
  await expect(request("/assets/")).rejects.toMatchObject({
    name: "AbortError",
  });
});
test("respuesta de éxito no JSON se trata como resultado no confirmado", async () => {
  const fetcher = vi
    .fn()
    .mockResolvedValueOnce(
      new Response(JSON.stringify({ csrfToken: "fixture-token" }), {
        status: 200,
      }),
    )
    .mockResolvedValueOnce(new Response("<html>Proxy</html>", { status: 200 }));
  vi.stubGlobal("fetch", fetcher);
  await expect(request("/assets/", { body: { name: "Test" } })).rejects.toThrow(
    "No se pudo confirmar la operación",
  );
  expect(fetcher).toHaveBeenCalledTimes(2);
});
