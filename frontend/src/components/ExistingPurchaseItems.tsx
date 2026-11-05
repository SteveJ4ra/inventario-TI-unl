import { useRef, useState } from "react";
import { request } from "../api";
import type { Asset, PurchaseExistingItem } from "../types";
import { Field, Form } from "./Form";

export function ExistingPurchaseItems({ items, onChange, disabled, donation = false }: {
  items: (PurchaseExistingItem & { code: string })[];
  onChange: (items: (PurchaseExistingItem & { code: string })[]) => void;
  disabled: boolean;
  donation?: boolean;
}) {
  const [asset, setAsset] = useState<Asset | null>(null);
  const [unknown, setUnknown] = useState(false);
  const [loading, setLoading] = useState(false);
  const selectionLock = useRef(false);
  return <section aria-label="Asociaciones iniciales">
    <h3>Activos existentes (opcional)</h3>
    <p>Se asociarán al guardar el documento, sin crear activos ni reemplazar adquisiciones. Cada ficha conserva su facultad y sus movimientos.</p>
    <Form submit="Consultar activo existente" disabled={disabled || loading} onSubmit={async data => {
      const id = Number(data.existing_asset_id);
      if (!Number.isSafeInteger(id) || id < 1) throw new Error("Indica un identificador válido.");
      selectionLock.current = true; setLoading(true); setAsset(null);
      try {
        const current = await request<Asset>("/assets/" + id + "/");
        if (current.acquisition !== null || !Number.isSafeInteger(current.revision))
          throw new Error("El activo ya tiene adquisición o no se pudo confirmar su revisión.");
        if (items.some(item => item.asset_id === current.id)) throw new Error("El activo ya está en la lista.");
        setAsset(current);
      } finally { selectionLock.current = false; setLoading(false); }
    }}><Field name="existing_asset_id" label="Identificador del activo existente" /></Form>
    {asset && <Form key={asset.id} submit="Añadir asociación" disabled={disabled || loading} onSubmit={async data => {
      if (selectionLock.current || items.some(item => item.asset_id === asset.id)) throw new Error("El activo ya está en la lista o se está consultando.");
      onChange([...items, { asset_id: asset.id, code: asset.code, expected_revision: asset.revision,
        reason: data.reason, item_value: data.item_value,
        ...(unknown ? { date_unknown_reason: data.date_unknown_reason } : { acquired_on: data.acquired_on }) }]);
      setAsset(null);
    }}>
      <p>{asset.code} · {asset.name} · Revisión {asset.revision}</p>
      <Field name="item_value" label={donation ? "Valor estimado del activo existente (USD)" : "Valor del activo existente (USD)"} />
      <Field name="reason" label="Motivo de asociación" maxLength={2000} />
      <label><input type="checkbox" checked={unknown} onChange={e => setUnknown(e.target.checked)} />Fecha desconocida del activo existente</label>
      {unknown ? <Field name="date_unknown_reason" label="Motivo de fecha desconocida del activo existente" maxLength={2000} />
        : <Field name="acquired_on" label="Fecha de adquisición del activo existente" type="date" />}
    </Form>}
    <ol>{items.map(item => <li key={item.asset_id}>{item.code} · USD {item.item_value} · Revisión {item.expected_revision}
      <button type="button" disabled={disabled} onClick={() => onChange(items.filter(row => row.asset_id !== item.asset_id))}>Quitar {item.code}</button>
    </li>)}</ol>
    {items.length > 0 && <p>Ante un conflicto, quita y consulta nuevamente la ficha antes de confirmar. No se reintenta automáticamente.</p>}
  </section>;
}
