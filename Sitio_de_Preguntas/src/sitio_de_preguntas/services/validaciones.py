class ValidacionError(ValueError):
    """Base para todo error de validación de entrada (la ruta lo traduce a 400)."""


class IDInvalido(ValidacionError):
    pass


class NombreInvalido(ValidacionError):
    pass


class DescripcionInvalida(ValidacionError):
    pass


def validate_id(id_) -> None:
    if id_ is None:
        raise IDInvalido("id vacío")
    if type(id_) is not int:  # rechaza bool y strings
        raise IDInvalido(f"el id debe ser entero: {id_!r}")
    if id_ < 1:
        raise IDInvalido(f"el id debe ser positivo: {id_!r}")


def validar_nombre(nombre, max_largo: int, minusculas: bool = False) -> str:
    if type(nombre) is not str:
        raise NombreInvalido("el nombre debe ser texto")
    nombre = " ".join(nombre.split())  # strip + colapsa espacios internos
    if minusculas:
        nombre = nombre.lower()
    if not nombre:
        raise NombreInvalido("el nombre no puede estar vacío")
    if len(nombre) > max_largo:
        raise NombreInvalido(f"el nombre supera {max_largo} caracteres")
    return nombre


def validar_descripcion(descripcion, max_largo: int) -> str | None:
    if descripcion is None:
        return None
    if type(descripcion) is not str:
        raise DescripcionInvalida("la descripción debe ser texto")
    descripcion = descripcion.strip()
    if not descripcion:
        return None  # "" se guarda como NULL
    if len(descripcion) > max_largo:
        raise DescripcionInvalida(f"la descripción supera {max_largo} caracteres")
    return descripcion