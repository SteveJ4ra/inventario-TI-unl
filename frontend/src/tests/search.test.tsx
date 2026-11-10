import { expect, test, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { Filters } from "../components/Inventory";
import { options, person } from "./fixtures";
test("combina búsqueda y filtros y permite limpiar", async () => {
  const apply = vi.fn();
  const user = userEvent.setup();
  render(<Filters options={options} people={[person]} onApply={apply} />);
  await user.type(screen.getByLabelText("Buscar activos"), "LAB");
  await user.selectOptions(screen.getByLabelText("Categoría"), "portatil");
  await user.selectOptions(screen.getByLabelText("Situación"), "disponible");
  await user.selectOptions(screen.getByLabelText("Condición"), "operativo");
  await user.click(screen.getByRole("button", { name: "Aplicar" }));
  expect(apply).toHaveBeenLastCalledWith({
    search: "LAB",
    category: "portatil",
    condition: "operativo",
    situation: "disponible",
  });
  await user.click(screen.getByRole("button", { name: "Limpiar" }));
  expect(apply).toHaveBeenLastCalledWith({});
});
