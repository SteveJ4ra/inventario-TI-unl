from .exceptions import ImportDependencyUnavailable


class UnavailableAssetAdapter:
    def apply(self, rows, *, actor):
        raise ImportDependencyUnavailable(
            "La integración con 003-fichas-adquisiciones aún no está disponible."
        )


class UnavailableLicenseLotAdapter:
    def apply(self, rows, *, actor):
        raise ImportDependencyUnavailable(
            "La integración con 006-lotes-licencias aún no está disponible."
        )
