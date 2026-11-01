import { expect, test, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { AssetForm, CustodianForm } from "../components/Registration";
import { options } from "./fixtures";
test("no envía un activo vacío y conserva nombre/descripcion separados", async () => {
  const submit = vi.fn().mockResolvedValue(undefined);
  const user = userEvent.setup();
  render(<AssetForm options={options} onSubmit={submit} />);
  await user.click(screen.getByRole("button", { name: "Registrar activo" }));
  expect(submit).not.toHaveBeenCalled();
  for (const [label, value] of [
    ["Nombre", "Portátil"],
    ["Descripción", "Equipo de práctica"],
    ["Marca", "Ejemplo"],
    ["Modelo", "A1"],
    ["Número de serie", "LAB-001"],
    ["Ubicación", "Laboratorio"],
  ])
    await user.type(screen.getByLabelText(label), value);
  await user.selectOptions(screen.getByLabelText("Categoría"), "portatil");
  await user.selectOptions(screen.getByLabelText("Condición"), "operativo");
  await user.click(screen.getByRole("button", { name: "Registrar activo" }));
  expect(submit.mock.calls[0][0]).toMatchObject({
    name: "Portátil",
    description: "Equipo de práctica",
  });
  expect(submit.mock.calls[0][0].assignment).toBeUndefined();
});
test("acepta correo válido de otro dominio y dependencia opcional", async () => {
  const submit = vi.fn().mockResolvedValue(undefined);
  const user = userEvent.setup();
  render(<CustodianForm onSubmit={submit} />);
  await user.type(screen.getByLabelText("Nombre completo"), "Persona");
  await user.type(screen.getByLabelText("Correo"), "persona@otro.edu");
  await user.click(screen.getByRole("button", { name: "Registrar custodio" }));
  expect(submit.mock.calls[0][0]).toMatchObject({
    email: "persona@otro.edu",
    department: "",
  });
});
