import { expect, test, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { Movements } from "../components/Movements";
import { asset, options } from "./fixtures";
test("rectificación exige motivo y conserva objetivo sin editar original", async () => {
  const submit = vi.fn().mockResolvedValue(undefined);
  const user = userEvent.setup();
  render(
    <Movements
      asset={{ ...asset, revision: 2, rectifiable_movement_id: 7 }}
      people={[]}
      options={options}
      onSubmit={submit}
    />,
  );
  await user.click(
    screen.getByRole("button", { name: "Rectificar último movimiento" }),
  );
  await user.click(
    screen.getByRole("button", { name: "Anular efecto del movimiento" }),
  );
  expect(submit).not.toHaveBeenCalled();
  await user.type(screen.getByLabelText("Motivo"), "Registro por error");
  await user.click(
    screen.getByRole("button", { name: "Anular efecto del movimiento" }),
  );
  expect(submit).toHaveBeenCalledWith(
    "rectify",
    expect.objectContaining({
      movement_id: 7,
      expected_revision: 2,
      reason: "Registro por error",
    }),
  );
});
