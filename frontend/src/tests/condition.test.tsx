import { expect, test, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { Movements } from "../components/Movements";
import { asset, options, person } from "./fixtures";
test("cambio real exige condición distinta y motivo", async () => {
  const submit = vi.fn().mockResolvedValue(undefined);
  const user = userEvent.setup();
  render(
    <Movements asset={asset} people={[]} options={options} onSubmit={submit} />,
  );
  await user.click(screen.getByRole("button", { name: "Cambiar condición" }));
  expect(screen.queryByRole("option", { name: "Operativo" })).toBeNull();
  await user.selectOptions(
    screen.getByLabelText("Nueva condición"),
    "averiado",
  );
  await user.type(screen.getByLabelText("Motivo"), "Falla detectada");
  await user.click(screen.getByRole("button", { name: "Guardar condición" }));
  expect(submit).toHaveBeenCalledWith(
    "condition",
    expect.objectContaining({
      condition: "averiado",
      reason: "Falla detectada",
    }),
  );
});
test("asignado solo ofrece devolución, sin cambio de condición", () => {
  render(
    <Movements
      asset={{ ...asset, assignment: "asignado", current_custodian: person }}
      people={[person]}
      options={options}
      onSubmit={vi.fn()}
    />,
  );
  expect(
    screen.queryByRole("button", { name: "Cambiar condición" }),
  ).toBeNull();
  expect(screen.getByRole("button", { name: "Devolver" })).toBeTruthy();
});
