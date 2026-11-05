import { useState } from "react";
import { request } from "../api";
import type { Asset, Body, Options } from "../types";
import { Field, FieldError, Form } from "./Form";
import { ReviewChanges } from "./ReviewChanges";

export function AssetEditForm({ asset, options, onSaved }: { asset: Asset; options: Options; onSaved: (asset: Asset) => void }) {
  const [pending, setPending] = useState<Body | null>(null);
  const [unknown, setUnknown] = useState(Boolean(asset.acquisition && !asset.acquisition.acquired_on));
  const before: Body = { name: asset.name, description: asset.description, category: asset.category,
    brand: asset.brand, model: asset.model, serial_number: asset.serial_number,
    ...(asset.acquisition ? { item_value: asset.acquisition.item_value,
      acquired_on: asset.acquisition.acquired_on, date_unknown_reason: asset.acquisition.date_unknown_reason } : {}) };
  return <section aria-label="Editar ficha">
    <p>Revisión consultada: {asset.revision}. Si cambió, consulta nuevamente la ficha antes de repetir. Los cambios no alteran movimientos anteriores.</p>
    <div hidden={pending !== null}><Form submit="Revisar cambios" onSubmit={async data => {
      const changes: Body = {};
      for (const key of ["name", "description", "category", "brand", "model", "serial_number", "item_value"])
        if (key in data && data[key] !== before[key]) changes[key] = data[key];
      if (asset.acquisition) {
        const acquired_on = unknown ? null : data.acquired_on;
        const date_unknown_reason = unknown ? data.date_unknown_reason : "";
        if (acquired_on !== before.acquired_on || date_unknown_reason !== before.date_unknown_reason)
          Object.assign(changes, { acquired_on, date_unknown_reason });
      }
      if (!Object.keys(changes).length) throw new Error("No hay cambios para guardar.");
      setPending({ ...changes, reason: data.reason, expected_revision: asset.revision });
    }}>
      <Field label="Nombre de activo" name="name" defaultValue={asset.name} />
      <Field label="Descripción" name="description" maxLength={2000} defaultValue={asset.description} />
      <label>Categoría<select name="category" defaultValue={asset.category}>
        {options.categories.map(choice => <option key={choice.value} value={choice.value}>{choice.label}</option>)}
      </select><FieldError name="category" /></label>
      <Field label="Marca" name="brand" maxLength={120} defaultValue={asset.brand} />
      <Field label="Modelo" name="model" maxLength={120} defaultValue={asset.model} />
      <Field label="Número de serie" name="serial_number" defaultValue={asset.serial_number} />
      {asset.acquisition && <>
        <Field label={(asset.acquisition.source === "DONATION" ? "Valor estimado (" : "Valor individual (") + asset.acquisition.currency + ")"}
          name="item_value" defaultValue={asset.acquisition.item_value} />
        <label><input type="checkbox" checked={unknown} onChange={e => setUnknown(e.target.checked)} />Fecha de adquisición desconocida</label>
        {unknown ? <Field label="Motivo de fecha desconocida" name="date_unknown_reason" maxLength={2000} defaultValue={asset.acquisition.date_unknown_reason} />
          : <Field label="Fecha de adquisición" name="acquired_on" type="date" defaultValue={asset.acquisition.acquired_on || ""} />}
      </>}
      <Field label="Motivo de edición" name="reason" maxLength={2000} />
    </Form></div>
    {pending && <ReviewChanges before={before} after={pending} onCancel={() => setPending(null)} onConfirm={async () => {
      const result = await request<Asset>("/assets/" + asset.id + "/", { body: pending, method: "PATCH" });
      if (result.id !== asset.id || result.revision !== asset.revision + 1) throw new Error("No se pudo confirmar la revisión. Consulta la ficha antes de repetir.");
      onSaved(result);
    }} />}
  </section>;
}
