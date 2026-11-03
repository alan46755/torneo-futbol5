"""
Validación de datos en el backend. Se valida formato, tipos y rangos
antes de ir a la base; las reglas de negocio se vuelven a controlar en
MySQL (CHECK, FK y triggers), que es la última línea de defensa.
"""
import re
from datetime import date, datetime

RE_EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def normalizar_ci(valor: str) -> str:
    return re.sub(r"[.\-\s]", "", valor or "")


def ci_valida(ci: str) -> bool:
    if not re.fullmatch(r"\d{7,8}", ci or ""):
        return False
    ci = ci.zfill(8)
    suma = sum(int(d) * int(p) for d, p in zip(ci[:7], "2987634"))
    return (10 - suma % 10) % 10 == int(ci[7])


class Validador:
    """Acumula errores y datos limpios a partir de un formulario."""

    def __init__(self, form):
        self.form = form
        self.errores: list[str] = []
        self.datos: dict = {}

    @property
    def ok(self) -> bool:
        return not self.errores

    def _crudo(self, campo):
        return (self.form.get(campo) or "").strip()

    def texto(self, campo, etiqueta, minimo=1, maximo=100, requerido=True, patron=None, msg_patron=None):
        v = self._crudo(campo)
        if not v:
            if requerido:
                self.errores.append(f"{etiqueta} es obligatorio.")
            self.datos[campo] = None
            return None
        if len(v) < minimo or len(v) > maximo:
            self.errores.append(f"{etiqueta} debe tener entre {minimo} y {maximo} caracteres.")
        if patron and not re.fullmatch(patron, v):
            self.errores.append(msg_patron or f"{etiqueta} tiene caracteres no permitidos.")
        self.datos[campo] = v
        return v

    def nombre_propio(self, campo, etiqueta, maximo=50):
        return self.texto(campo, etiqueta, 2, maximo, patron=r"[A-Za-zÁÉÍÓÚÜÑáéíóúüñ' \-]+",
                          msg_patron=f"{etiqueta} solo puede contener letras, espacios, apóstrofos y guiones.")

    def email(self, campo, etiqueta="El email"):
        v = self.texto(campo, etiqueta, 6, 100)
        if v and not RE_EMAIL.fullmatch(v):
            self.errores.append(f"{etiqueta} no tiene un formato válido.")
        if v:
            self.datos[campo] = v.lower()
        return self.datos.get(campo)

    def ci(self, campo, etiqueta="La cédula"):
        v = normalizar_ci(self._crudo(campo))
        if not v:
            self.errores.append(f"{etiqueta} es obligatoria.")
        elif not ci_valida(v):
            self.errores.append(f"{etiqueta} no es válida (verifique el dígito verificador).")
        self.datos[campo] = v
        return v

    def entero(self, campo, etiqueta, minimo=None, maximo=None, requerido=True):
        v = self._crudo(campo)
        if not v:
            if requerido:
                self.errores.append(f"{etiqueta} es obligatorio.")
            self.datos[campo] = None
            return None
        try:
            n = int(v)
        except ValueError:
            self.errores.append(f"{etiqueta} debe ser un número entero.")
            self.datos[campo] = None
            return None
        if (minimo is not None and n < minimo) or (maximo is not None and n > maximo):
            self.errores.append(f"{etiqueta} debe estar entre {minimo} y {maximo}.")
        self.datos[campo] = n
        return n

    def fecha(self, campo, etiqueta, requerido=True, minimo: date | None = None, maximo: date | None = None):
        v = self._crudo(campo)
        if not v:
            if requerido:
                self.errores.append(f"{etiqueta} es obligatoria.")
            self.datos[campo] = None
            return None
        try:
            d = datetime.strptime(v, "%Y-%m-%d").date()
        except ValueError:
            self.errores.append(f"{etiqueta} no es una fecha válida.")
            self.datos[campo] = None
            return None
        if minimo and d < minimo:
            self.errores.append(f"{etiqueta} no puede ser anterior al {minimo:%d/%m/%Y}.")
        if maximo and d > maximo:
            self.errores.append(f"{etiqueta} no puede ser posterior al {maximo:%d/%m/%Y}.")
        self.datos[campo] = d
        return d

    def opcion(self, campo, etiqueta, opciones):
        v = self._crudo(campo)
        if v not in [str(o) for o in opciones]:
            self.errores.append(f"{etiqueta}: seleccione una opción válida.")
            self.datos[campo] = None
            return None
        self.datos[campo] = v
        return v

    def booleano(self, campo):
        self.datos[campo] = self.form.get(campo) in ("1", "on", "true", "si")
        return self.datos[campo]

    def error(self, mensaje):
        self.errores.append(mensaje)


def edad(fecha_nac: date, hoy: date | None = None) -> int:
    hoy = hoy or date.today()
    return hoy.year - fecha_nac.year - ((hoy.month, hoy.day) < (fecha_nac.month, fecha_nac.day))
