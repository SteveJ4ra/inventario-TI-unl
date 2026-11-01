import { expect, test, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { Movements } from "../components/Movements";
import { asset, options, person } from "./fixtures";
test("entrega incluye revisión vista, custodio y destino", async () => {
  const submit = vi.fn().mockResolvedValue(undefined);
  const user = userEvent.setup();
  render(
    <Movements
      asset={asset}
      people={[person]}
      options={options}
      onSubmit={submit}
    />,
  );
  expect(screen.queryByRole("button", { name: "Devolver" })).toBeNull();
  await user.click(screen.getByRole("button", { name: "Entregar" }));
  await user.selectOptions(
    screen.getByLabelText("Custodio"),
    String(person.id),
  );
  await user.type(screen.getByLabelText("Destino"), "Aula");
  await user.click(screen.getByRole("button", { name: "Confirmar entrega" }));
  expect(submit).toHaveBeenCalledWith(
    "deliver",
    expect.objectContaining({
      expected_revision: 0,
      custodian_id: 1,
      destination: "Aula",
    }),
  );
});
test("no ofrece entrega para equipo averiado", () => {
  render(
    <Movements
      asset={{ ...asset, condition: "averiado" }}
      people={[]}
      options={options}
      onSubmit={vi.fn()}
    />,
  );
  expect(screen.queryByRole("button", { name: "Entregar" })).toBeNull();
});
