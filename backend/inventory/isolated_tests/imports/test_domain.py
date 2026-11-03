"""Pruebas puras de 008: no requieren Django, ORM ni 003/006.

Ejecutar desde la raíz:
  python -m unittest discover -s backend/inventory/isolated_tests/imports -p "test_*.py" -v
"""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from inventory.imports import domain, schemas  # noqa: E402

MAX_BYTES = 2_000_000
MAX_ROWS = 2000


def parse(kind, raw, max_rows=MAX_ROWS):
    return domain.parse_csv(
        kind,
        schemas.default_version(kind),
        raw.encode("utf-8"),
        max_bytes=MAX_BYTES,
        max_rows=max_rows,
    )


def asset_csv(*rows, header=None):
    header = header or ",".join(schemas.ASSET_COLUMNS)
    return "\n".join([header, *rows]) + "\n"


VALID_ASSET_ROW = (
    "Portátil,Equipo de práctica,portatil,Marca,Modelo A,SER-1,Laboratorio,"
    "operativo,1,,FACT-1,compra,FAC-1,2026-01-15,Proveedor,1000.00,,500.00,"
    "2026-01-20,"
)


class AssetParsingTests(unittest.TestCase):
    def test_ejemplo_versionado_es_valido(self):
        result = parse(
            schemas.ASSETS,
            schemas.EXAMPLE_FILES[schemas.ASSETS].read_text(encoding="utf-8"),
        )
        self.assertEqual(result.errors, [])
        self.assertEqual(result.summary["record_count"], 3)
        self.assertEqual(result.summary["new_documents"], 2)
        self.assertEqual(len(result.content_hash), 64)
        self.assertTrue(all(row["valid"] for row in result.rows))

    def test_hash_es_estable_y_las_limpiezas_no_lo_cambian(self):
        first = parse(schemas.ASSETS, asset_csv(VALID_ASSET_ROW))
        second = parse(
            schemas.ASSETS,
            "\ufeff" + asset_csv("  " + VALID_ASSET_ROW + "  "),
        )
        self.assertEqual(first.content_hash, second.content_hash)

    def test_identificadores_deben_ser_positivos(self):
        values = VALID_ASSET_ROW.split(",")
        values[8] = "0"
        result = parse(schemas.ASSETS, asset_csv(",".join(values)))
        self.assertIn(
            (2, "faculty_id"),
            {(error["row"], error["field"]) for error in result.errors},
        )
        values = VALID_ASSET_ROW.split(",")
        values[9] = "0"
        values[10] = ""
        for index in range(11, 17):
            values[index] = ""
        result = parse(schemas.ASSETS, asset_csv(",".join(values)))
        self.assertIn(
            (2, "acquisition_document_id"),
            {(error["row"], error["field"]) for error in result.errors},
        )

    def test_cabecera_faltante_y_columna_extra(self):
        header = ",".join(schemas.ASSET_COLUMNS[:-1])
        result = parse(schemas.ASSETS, header + "\n")
        self.assertTrue(result.errors)
        self.assertIn("Falta la columna date_unknown_reason.", str(result.errors))
        result = parse(
            schemas.ASSETS,
            ",".join(schemas.ASSET_COLUMNS) + ",extra\n",
        )
        self.assertIn("Columna no permitida: extra.", str(result.errors))

    def test_version_no_soportada_y_archivo_vacio(self):
        with self.assertRaises(domain.UnsupportedSchema):
            domain.parse_csv(schemas.ASSETS, "assets-v2", b"", 10, 10)
        result = parse(schemas.ASSETS, "")
        self.assertEqual(result.summary["record_count"], 0)
        self.assertIn("falta la cabecera", str(result.errors))

    def test_utf8_invalido_y_bytes_nulos(self):
        result = domain.parse_csv(
            schemas.ASSETS, "assets-v1", b"\xff\xfe", MAX_BYTES, MAX_ROWS
        )
        self.assertIn("UTF-8", str(result.errors))
        result = domain.parse_csv(
            schemas.ASSETS, "assets-v1", b"a\x00b", MAX_BYTES, MAX_ROWS
        )
        self.assertIn("bytes nulos", str(result.errors))

    def test_errores_multiples_por_fila_se_listan_completos(self):
        row = ",".join(
            [
                "",
                "Equipo de práctica",
                "portatil",
                "Marca",
                "Modelo A",
                "",
                "Laboratorio",
                "otra",
                "abc",
                "12",
                "clave",
                "compra",
                "",
                "fecha-mala",
                "Proveedor",
                "10.555",
                "",
                "1.234",
                "fecha-otra",
                "",
            ]
        )
        result = parse(schemas.ASSETS, asset_csv(row))
        messages = {(error["row"], error["field"]) for error in result.errors}
        self.assertIn((2, "name"), messages)
        self.assertIn((2, "serial_number"), messages)
        self.assertIn((2, "condition"), messages)
        self.assertIn((2, "faculty_id"), messages)
        self.assertIn((2, "document_key"), messages)
        self.assertIn((2, "document_date"), messages)
        self.assertIn((2, "invoice_total"), messages)
        self.assertIn((2, "item_value"), messages)
        self.assertIn((2, "acquired_on"), messages)
        self.assertFalse(result.rows[0]["valid"])

    def test_documentos_compartidos_exigen_metadatos_iguales(self):
        first = VALID_ASSET_ROW
        second = VALID_ASSET_ROW.replace("SER-1", "SER-2").replace(
            "Proveedor", "Otro proveedor"
        )
        result = parse(schemas.ASSETS, asset_csv(first, second))
        self.assertTrue(result.errors)
        self.assertEqual(result.errors[0]["field"], "document_key")
        self.assertEqual(result.errors[0]["row"], 3)

    def test_documento_existente_y_key_son_excluyentes(self):
        row = VALID_ASSET_ROW.replace(",1,,FACT-1,", ",1,10,FACT-1,")
        result = parse(schemas.ASSETS, asset_csv(row))
        self.assertIn("nunca ambos", str(result.errors))

    def test_duplicado_de_identidad_dentro_del_archivo(self):
        second = VALID_ASSET_ROW.replace("SER-1", "ser-1")
        result = parse(schemas.ASSETS, asset_csv(VALID_ASSET_ROW, second))
        self.assertIn("se repiten dentro del archivo", str(result.errors))

    def test_fecha_y_motivo_desconocido_son_alternativas(self):
        row = VALID_ASSET_ROW.replace("2026-01-20,", ",Sin fecha")
        result = parse(schemas.ASSETS, asset_csv(row))
        self.assertEqual(result.errors, [])
        both = VALID_ASSET_ROW.replace("2026-01-20,", "2026-01-20,Sin fecha")
        result = parse(schemas.ASSETS, asset_csv(both))
        self.assertIn("no ambos", str(result.errors))

    def test_limites_de_bytes_y_filas(self):
        with self.assertRaises(domain.CsvLimitExceeded):
            domain.parse_csv(
                schemas.ASSETS,
                "assets-v1",
                asset_csv(VALID_ASSET_ROW).encode(),
                max_bytes=10,
                max_rows=10,
            )
        with self.assertRaises(domain.CsvLimitExceeded):
            parse(schemas.ASSETS, asset_csv(VALID_ASSET_ROW, VALID_ASSET_ROW), 1)

    def test_lineas_en_blanco_se_omiten_sin_alterar_numeracion(self):
        raw = asset_csv(VALID_ASSET_ROW, "", VALID_ASSET_ROW.replace("SER-1", "SER-2"))
        result = parse(schemas.ASSETS, raw)
        self.assertEqual([row["row"] for row in result.rows], [2, 4])


class LicenseParsingTests(unittest.TestCase):
    def test_ejemplo_versionado_es_valido(self):
        result = parse(
            schemas.LICENSE_LOTS,
            schemas.EXAMPLE_FILES[schemas.LICENSE_LOTS].read_text(encoding="utf-8"),
        )
        self.assertEqual(result.errors, [])
        self.assertEqual(result.summary["record_count"], 2)
        self.assertEqual(result.summary["purchased_total"], 75)
        self.assertEqual(result.summary["in_use_total"], 20)

    def test_inicio_obligatorio_y_cantidades(self):
        row = "Suite,Proveedor,USER_SEAT,10,11,,"
        result = parse(schemas.LICENSE_LOTS, "\n".join([
            ",".join(schemas.LICENSE_LOT_COLUMNS),
            row,
        ]))
        self.assertIn("no puede superar la comprada", str(result.errors))
        self.assertIn("Fecha de inicio es obligatorio", str(result.errors))

    def test_fin_anterior_al_inicio_y_modelo_invalido(self):
        row = "Suite,Proveedor,OTRO,10,1,2026-02-01,2026-01-01"
        result = parse(schemas.LICENSE_LOTS, "\n".join([
            ",".join(schemas.LICENSE_LOT_COLUMNS),
            row,
        ]))
        self.assertIn("no puede ser anterior", str(result.errors))
        self.assertIn("USER_SEAT o DEVICE_SEAT", str(result.errors))


if __name__ == "__main__":
    unittest.main()
