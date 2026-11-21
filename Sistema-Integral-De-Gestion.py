# Kevin Caleb Hernandez Quiroga
# Grupo: 213023_645
# Programa: INGENIERÍA DE SISTEMAS
# Código fuente: autoría propia
# Ejercicio 1: Sistema Integral de Gestión de Clientes, Servicios y Reservas

"""
Sistema Integral de Gestión de Clientes, Servicios y Reservas - Software FJ.

Implementa programación orientada a objetos (abstracción, herencia, polimorfismo,
encapsulación y sobrecarga de métodos), manejo avanzado de excepciones con
encadenamiento, persistencia de auditoría en archivo de logs (sin base de datos)
e interfaz gráfica funcional en Tkinter.
"""

from abc import ABC, abstractmethod
from datetime import datetime
from functools import singledispatchmethod
import logging
import math
import os
import re
import tkinter as tk
from tkinter import messagebox, scrolledtext, ttk
from typing import Callable, Dict, List, Optional, Tuple, Union

# ==============================================================================
# 1. JERARQUÍA DE EXCEPCIONES PERSONALIZADAS
# ==============================================================================


class SoftwareFJError(Exception):
    """Excepción base para todos los errores controlados del sistema Software FJ."""

    def __init__(self, mensaje: str, codigo: str = "SFJ-000") -> None:
        super().__init__(mensaje)
        self.mensaje = mensaje
        self.codigo = codigo
        self.timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def __str__(self) -> str:
        return f"[{self.codigo}] {self.mensaje}"


class ParametroFaltanteError(SoftwareFJError):
    """Se lanza cuando un parámetro obligatorio es None o está vacío."""

    def __init__(self, mensaje: str) -> None:
        super().__init__(mensaje, codigo="SFJ-001")


class DatosInvalidosError(SoftwareFJError):
    """Se lanza cuando los datos ingresados no cumplen el formato o tipo esperado."""

    def __init__(self, mensaje: str) -> None:
        super().__init__(mensaje, codigo="SFJ-002")


class ServicioNoDisponibleError(SoftwareFJError):
    """Se lanza al intentar reservar un servicio ocupado o inhabilitado."""

    def __init__(self, mensaje: str) -> None:
        super().__init__(mensaje, codigo="SFJ-003")


class ReservaInvalidaError(SoftwareFJError):
    """Se lanza ante parámetros o condiciones incorrectas en una reserva."""

    def __init__(self, mensaje: str) -> None:
        super().__init__(mensaje, codigo="SFJ-004")


class OperacionNoPermitidaError(SoftwareFJError):
    """Se lanza cuando se intenta ejecutar una transición de estado ilegal."""

    def __init__(self, mensaje: str) -> None:
        super().__init__(mensaje, codigo="SFJ-005")


class CalculoInconsistenteError(SoftwareFJError):
    """Se lanza cuando los parámetros financieros generan montos incoherentes."""

    def __init__(self, mensaje: str) -> None:
        super().__init__(mensaje, codigo="SFJ-006")


# ==============================================================================
# 2. SISTEMA DE LOGS Y AUDITORÍA EN ARCHIVO PLANO
# ==============================================================================


class GestorLogs:
    """
    Administra el registro persistente de eventos y errores en archivo plano,
    sin utilizar motores de bases de datos.
    """

    ARCHIVO_LOG = "software_fj.log"

    def __init__(self, archivo: str = ARCHIVO_LOG) -> None:
        self._archivo = archivo
        self._observadores: List[Callable[[str], None]] = []
        self._logger = logging.getLogger("SoftwareFJ")
        self._logger.setLevel(logging.DEBUG)

        # Evita duplicar manejadores si se instancia más de una vez
        if not self._logger.handlers:
            manejador_archivo = logging.FileHandler(
                self._archivo, mode="a", encoding="utf-8"
            )
            formato = logging.Formatter(
                "%(asctime)s | %(levelname)-8s | %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
            manejador_archivo.setFormatter(formato)
            self._logger.addHandler(manejador_archivo)

    def suscribir_vista(self, callback: Callable[[str], None]) -> None:
        """Permite que la interfaz gráfica reciba notificaciones en tiempo real."""
        self._observadores.append(callback)

    def _notificar(self, linea: str) -> None:
        for callback in self._observadores:
            callback(linea)

    def registrar_info(self, mensaje: str) -> None:
        """Registra una operación exitosa o evento informativo."""
        self._logger.info(mensaje)
        marca = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self._notificar(f"{marca} | INFO     | {mensaje}")

    def registrar_advertencia(self, mensaje: str) -> None:
        """Registra una alerta operativa no crítica."""
        self._logger.warning(mensaje)
        marca = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self._notificar(f"{marca} | WARNING  | {mensaje}")

    def registrar_error(self, error: Exception, contexto: str = "") -> None:
        """
        Registra un error detallado, incluyendo la causa original si existe
        encadenamiento de excepciones (__cause__).
        """
        detalle_causa = ""
        if error.__cause__ is not None:
            detalle_causa = f" | Causa encadenada: {type(error.__cause__).__name__}: {error.__cause__}"
        prefijo = f"[{contexto}] " if contexto else ""
        mensaje_completo = f"{prefijo}{type(error).__name__}: {error}{detalle_causa}"

        self._logger.error(mensaje_completo)
        marca = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self._notificar(f"{marca} | ERROR    | {mensaje_completo}")

    def leer_historial_archivo(self) -> str:
        """Lee el contenido completo del archivo de logs desde disco."""
        if not os.path.exists(self._archivo):
            return "Aún no existen registros en el archivo de logs."
        with open(self._archivo, "r", encoding="utf-8") as archivo:
            return archivo.read()


# ==============================================================================
# 3. ARQUITECTURA ORIENTADA A OBJETOS (ENTIDADES, CLIENTES, SERVICIOS, RESERVAS)
# ==============================================================================


class EntidadSistema(ABC):
    """
    Clase abstracta base que representa cualquier entidad identificable
    dentro del ecosistema de Software FJ.
    """

    def __init__(self, id_entidad: str) -> None:
        if not id_entidad or not str(id_entidad).strip():
            raise ParametroFaltanteError(
                "El identificador de la entidad es obligatorio."
            )
        self.__id_entidad: str = str(id_entidad).strip()
        self.__fecha_creacion: datetime = datetime.now()

    @property
    def id_entidad(self) -> str:
        """Retorna el identificador único encapsulado de la entidad."""
        return self.__id_entidad

    @property
    def fecha_creacion(self) -> str:
        """Retorna la fecha y hora de creación formateada."""
        return self.__fecha_creacion.strftime("%Y-%m-%d %H:%M:%S")

    @abstractmethod
    def validar(self) -> bool:
        """Valida la integridad interna de los atributos de la entidad."""

    @abstractmethod
    def obtener_resumen(self) -> str:
        """Devuelve una representación textual legible de la entidad."""


class Cliente(EntidadSistema):
    """
    Representa un cliente de Software FJ con encapsulación estricta
    y validaciones robustas de datos personales.
    """

    PATRON_EMAIL = re.compile(r"^[\w\.-]+@[\w\.-]+\.\w{2,}$")
    PATRON_TELEFONO = re.compile(r"^\+?\d{7,15}$")

    def __init__(
        self,
        id_cliente: str,
        nombre: str,
        documento: str,
        email: str,
        telefono: str,
        activo: bool = True,
    ) -> None:
        super().__init__(id_cliente)
        self.nombre = nombre
        self.documento = documento
        self.email = email
        self.telefono = telefono
        self.__activo: bool = bool(activo)
        self.validar()

    @property
    def nombre(self) -> str:
        return self.__nombre

    @nombre.setter
    def nombre(self, valor: str) -> None:
        if valor is None or not str(valor).strip():
            raise ParametroFaltanteError("El nombre del cliente no puede estar vacío.")
        limpio = str(valor).strip()
        if len(limpio) < 3 or any(char.isdigit() for char in limpio):
            raise DatosInvalidosError(
                f"Nombre inválido ('{limpio}'): debe tener al menos 3 letras y no contener números."
            )
        self.__nombre = limpio

    @property
    def documento(self) -> str:
        return self.__documento

    @documento.setter
    def documento(self, valor: str) -> None:
        if valor is None or not str(valor).strip():
            raise ParametroFaltanteError("El documento de identidad es obligatorio.")
        limpio = str(valor).strip()
        if len(limpio) < 5:
            raise DatosInvalidosError(
                f"Documento inválido ('{limpio}'): longitud mínima de 5 caracteres."
            )
        self.__documento = limpio

    @property
    def email(self) -> str:
        return self.__email

    @email.setter
    def email(self, valor: str) -> None:
        if valor is None or not str(valor).strip():
            raise ParametroFaltanteError("El correo electrónico es obligatorio.")
        limpio = str(valor).strip().lower()
        if not self.PATRON_EMAIL.match(limpio):
            raise DatosInvalidosError(
                f"Formato de correo electrónico inválido: '{limpio}'."
            )
        self.__email = limpio

    @property
    def telefono(self) -> str:
        return self.__telefono

    @telefono.setter
    def telefono(self, valor: str) -> None:
        if valor is None or not str(valor).strip():
            raise ParametroFaltanteError("El teléfono de contacto es obligatorio.")
        limpio = str(valor).strip().replace(" ", "")
        if not self.PATRON_TELEFONO.match(limpio):
            raise DatosInvalidosError(
                f"Teléfono inválido ('{limpio}'): debe contener entre 7 y 15 dígitos."
            )
        self.__telefono = limpio

    @property
    def activo(self) -> bool:
        return self.__activo

    def desactivar(self) -> None:
        """Inhabilita al cliente para futuras reservas."""
        self.__activo = False

    def validar(self) -> bool:
        """Verifica que todos los campos encapsulados sigan siendo consistentes."""
        return bool(
            self.__nombre and self.__documento and self.__email and self.__telefono
        )

    def obtener_resumen(self) -> str:
        estado = "Activo" if self.__activo else "Inactivo"
        return f"[{self.id_entidad}] {self.__nombre} | Doc: {self.__documento} | {self.__email} ({estado})"


class Servicio(EntidadSistema, ABC):
    """
    Clase abstracta que define el contrato polimórfico para todos los servicios
    ofrecidos por Software FJ e incorpora métodos sobrecargados de cálculo de costos.
    """

    def __init__(
        self,
        id_servicio: str,
        nombre: str,
        tarifa_base: Union[int, float, str],
        disponible: bool = True,
    ) -> None:
        super().__init__(id_servicio)
        if nombre is None or not str(nombre).strip():
            raise ParametroFaltanteError("El nombre del servicio es obligatorio.")
        self.__nombre: str = str(nombre).strip()

        # Conversión segura con encadenamiento de excepciones
        try:
            tarifa_num = float(tarifa_base)
        except (ValueError, TypeError) as err:
            raise DatosInvalidosError(
                f"La tarifa base '{tarifa_base}' no es un valor numérico válido."
            ) from err

        if math.isnan(tarifa_num) or math.isinf(tarifa_num) or tarifa_num <= 0:
            raise DatosInvalidosError(
                f"La tarifa base debe ser mayor a 0 (recibido: {tarifa_num})."
            )

        self.__tarifa_base: float = round(tarifa_num, 2)
        self.__disponible: bool = bool(disponible)

    @property
    def nombre(self) -> str:
        return self.__nombre

    @property
    def tarifa_base(self) -> float:
        return self.__tarifa_base

    @property
    def disponible(self) -> bool:
        return self.__disponible

    @disponible.setter
    def disponible(self, estado: bool) -> None:
        self.__disponible = bool(estado)

    @abstractmethod
    def calcular_costo_base(self, duracion: int) -> float:
        """Calcula el subtotal específico según las reglas de cada subclase."""

    @abstractmethod
    def describir_servicio(self) -> str:
        """Retorna las características técnicas particulares del servicio."""

    @abstractmethod
    def validar_parametros(self) -> bool:
        """Valida los parámetros especializados del servicio derivado."""

    def validar(self) -> bool:
        return self.__tarifa_base > 0 and self.validar_parametros()

    def calcular_costo_total(
        self,
        duracion: int,
        tasa_iva: float = 0.0,
        descuento_pct: float = 0.0,
        recargo_fijo: float = 0.0,
    ) -> float:
        """
        Método sobrecargado mediante parámetros opcionales para calcular el costo
        final en múltiples modalidades:
          1. Solo duración: calcular_costo_total(duracion)
          2. Con impuestos: calcular_costo_total(duracion, tasa_iva=0.21)
          3. Con descuento e IVA: calcular_costo_total(duracion, tasa_iva=0.21, descuento_pct=10)
          4. Completo con recargo fijo.
        """
        if not isinstance(duracion, int) or duracion <= 0:
            raise CalculoInconsistenteError(
                f"La duración para cálculo debe ser un entero positivo (recibido: {duracion})."
            )
        if tasa_iva < 0 or tasa_iva > 1:
            raise CalculoInconsistenteError(
                f"La tasa de impuesto debe estar entre 0.0 y 1.0 (recibido: {tasa_iva})."
            )
        if descuento_pct < 0 or descuento_pct >= 100:
            raise CalculoInconsistenteError(
                f"El porcentaje de descuento debe estar entre 0 y 99.9% (recibido: {descuento_pct})."
            )
        if recargo_fijo < 0:
            raise CalculoInconsistenteError(
                f"El recargo fijo no puede ser negativo (recibido: {recargo_fijo})."
            )

        subtotal = self.calcular_costo_base(duracion)
        monto_descuento = subtotal * (descuento_pct / 100.0)
        base_imponible = subtotal - monto_descuento + recargo_fijo
        total = round(base_imponible * (1.0 + tasa_iva), 2)

        if total <= 0 or math.isnan(total):
            raise CalculoInconsistenteError(
                "El cálculo arrojó un monto total inconsistente (<= 0 o NaN)."
            )
        return total

    @singledispatchmethod
    def aplicar_tarifa_personalizada(self, configuracion, duracion: int) -> float:
        """
        Sobrecarga por despacho de tipo (@singledispatchmethod) que permite
        calcular tarifas pasando un porcentaje directo (float/int), una tupla
        (iva, descuento) o un diccionario de reglas comerciales.
        """
        raise DatosInvalidosError(
            f"Tipo de configuración tarifaria no soportado: {type(configuracion).__name__}"
        )

    @aplicar_tarifa_personalizada.register(int)
    @aplicar_tarifa_personalizada.register(float)
    def _(self, configuracion: Union[int, float], duracion: int) -> float:
        """Variante 1: Recibe únicamente un porcentaje de descuento directo."""
        return self.calcular_costo_total(
            duracion=duracion, descuento_pct=float(configuracion)
        )

    @aplicar_tarifa_personalizada.register(tuple)
    def _(self, configuracion: Tuple[float, float], duracion: int) -> float:
        """Variante 2: Recibe una tupla (tasa_iva, descuento_pct)."""
        if len(configuracion) != 2:
            raise DatosInvalidosError(
                "La tupla tarifaria debe tener exactamente (iva, descuento)."
            )
        iva, desc = configuracion
        return self.calcular_costo_total(
            duracion=duracion, tasa_iva=iva, descuento_pct=desc
        )

    @aplicar_tarifa_personalizada.register(dict)
    def _(self, configuracion: Dict[str, float], duracion: int) -> float:
        """Variante 3: Recibe un diccionario con claves opcionales 'iva', 'descuento', 'recargo'."""
        return self.calcular_costo_total(
            duracion=duracion,
            tasa_iva=float(configuracion.get("iva", 0.0)),
            descuento_pct=float(configuracion.get("descuento", 0.0)),
            recargo_fijo=float(configuracion.get("recargo", 0.0)),
        )

    def obtener_resumen(self) -> str:
        estado = "Disponible" if self.__disponible else "Ocupado"
        return (
            f"[{self.id_entidad}] {self.__nombre} | Base: ${self.__tarifa_base:.2f}/h | "
            f"{self.describir_servicio()} | Estado: {estado}"
        )


class ReservaSala(Servicio):
    """Servicio especializado para reservas de salas de reuniones o capacitación."""

    def __init__(
        self,
        id_servicio: str,
        nombre: str,
        tarifa_base: Union[int, float, str],
        capacidad: int,
        videoconferencia: bool = True,
        disponible: bool = True,
    ) -> None:
        super().__init__(id_servicio, nombre, tarifa_base, disponible)
        try:
            self.__capacidad = int(capacidad)
        except (ValueError, TypeError) as err:
            raise DatosInvalidosError(
                "La capacidad de la sala debe ser un entero."
            ) from err
        self.__videoconferencia = bool(videoconferencia)
        self.validar_parametros()

    @property
    def capacidad(self) -> int:
        return self.__capacidad

    @property
    def videoconferencia(self) -> bool:
        return self.__videoconferencia

    def validar_parametros(self) -> bool:
        if self.__capacidad < 2 or self.__capacidad > 200:
            raise DatosInvalidosError(
                f"Capacidad de sala fuera de rango permitido (2-200): {self.__capacidad}."
            )
        return True

    def calcular_costo_base(self, duracion: int) -> float:
        cargo_av = 15.0 * duracion if self.__videoconferencia else 0.0
        cargo_aforo = self.__capacidad * 0.50
        return round((self.tarifa_base * duracion) + cargo_av + cargo_aforo, 2)

    def describir_servicio(self) -> str:
        av = "con Videoconferencia" if self.__videoconferencia else "estándar"
        return f"Sala ({self.__capacidad} pers., {av})"


class AlquilerEquipo(Servicio):
    """Servicio especializado para alquiler de hardware y equipamiento tecnológico."""

    def __init__(
        self,
        id_servicio: str,
        nombre: str,
        tarifa_base: Union[int, float, str],
        tipo_equipo: str,
        cantidad: int,
        gama_alta: bool = False,
        disponible: bool = True,
    ) -> None:
        super().__init__(id_servicio, nombre, tarifa_base, disponible)
        if not tipo_equipo or not str(tipo_equipo).strip():
            raise ParametroFaltanteError(
                "Debe especificar el tipo de equipo a alquilar."
            )
        self.__tipo_equipo = str(tipo_equipo).strip()
        try:
            self.__cantidad = int(cantidad)
        except (ValueError, TypeError) as err:
            raise DatosInvalidosError(
                "La cantidad de equipos debe ser un número entero."
            ) from err
        self.__gama_alta = bool(gama_alta)
        self.validar_parametros()

    def validar_parametros(self) -> bool:
        if self.__cantidad < 1 or self.__cantidad > 50:
            raise DatosInvalidosError(
                f"Cantidad de equipos inválida (debe estar entre 1 y 50): {self.__cantidad}."
            )
        return True

    def calcular_costo_base(self, duracion: int) -> float:
        factor_gama = 1.25 if self.__gama_alta else 1.0
        return round(self.tarifa_base * self.__cantidad * duracion * factor_gama, 2)

    def describir_servicio(self) -> str:
        gama = "Gama Alta" if self.__gama_alta else "Estándar"
        return f"Equipo: {self.__tipo_equipo} x{self.__cantidad} ({gama})"


class AsesoriaEspecializada(Servicio):
    """Servicio especializado para consultoría técnica e ingeniería de software."""

    MODALIDADES_VALIDAS = ("Remota", "Presencial")

    def __init__(
        self,
        id_servicio: str,
        nombre: str,
        tarifa_base: Union[int, float, str],
        especialidad: str,
        nivel_senior: bool = True,
        modalidad: str = "Remota",
        disponible: bool = True,
    ) -> None:
        super().__init__(id_servicio, nombre, tarifa_base, disponible)
        if not especialidad or not str(especialidad).strip():
            raise ParametroFaltanteError(
                "La especialidad de la asesoría es obligatoria."
            )
        self.__especialidad = str(especialidad).strip()
        self.__nivel_senior = bool(nivel_senior)
        self.__modalidad = str(modalidad).strip().capitalize()
        self.validar_parametros()

    def validar_parametros(self) -> bool:
        if self.__modalidad not in self.MODALIDADES_VALIDAS:
            raise DatosInvalidosError(
                f"Modalidad '{self.__modalidad}' inválida. Use: {self.MODALIDADES_VALIDAS}."
            )
        return True

    def calcular_costo_base(self, duracion: int) -> float:
        factor_senior = 1.40 if self.__nivel_senior else 1.0
        viaticos = 25.0 if self.__modalidad == "Presencial" else 0.0
        return round((self.tarifa_base * duracion * factor_senior) + viaticos, 2)

    def describir_servicio(self) -> str:
        nivel = "Senior" if self.__nivel_senior else "Semi-Senior"
        return f"Asesoría {self.__especialidad} ({nivel}, {self.__modalidad})"


class Reserva(EntidadSistema):
    """
    Integra un Cliente, un Servicio, la duración y el ciclo de vida de la reserva
    (PENDIENTE -> CONFIRMADA -> PROCESADA o CANCELADA).
    """

    ESTADOS_VALIDOS = ("PENDIENTE", "CONFIRMADA", "PROCESADA", "CANCELADA")

    def __init__(
        self,
        id_reserva: str,
        cliente: Cliente,
        servicio: Servicio,
        duracion: Union[int, str],
        tasa_iva: float = 0.21,
        descuento_pct: float = 0.0,
    ) -> None:
        super().__init__(id_reserva)

        if not isinstance(cliente, Cliente):
            raise ReservaInvalidaError("Se requiere una instancia válida de Cliente.")
        if not cliente.activo:
            raise OperacionNoPermitidaError(
                f"El cliente '{cliente.nombre}' se encuentra inactivo."
            )
        if not isinstance(servicio, Servicio):
            raise ReservaInvalidaError("Se requiere una instancia válida de Servicio.")
        if not servicio.disponible:
            raise ServicioNoDisponibleError(
                f"El servicio '{servicio.nombre}' no está disponible actualmente."
            )

        try:
            duracion_int = int(duracion)
        except (ValueError, TypeError) as err:
            raise ReservaInvalidaError(
                f"La duración '{duracion}' debe ser un número entero de horas."
            ) from err

        if duracion_int < 1 or duracion_int > 720:
            raise ReservaInvalidaError(
                f"Duración fuera de rango (1 a 720 horas): {duracion_int}h."
            )

        self.__cliente: Cliente = cliente
        self.__servicio: Servicio = servicio
        self.__duracion: int = duracion_int
        self.__estado: str = "PENDIENTE"
        self.__tasa_iva: float = tasa_iva
        self.__descuento_pct: float = descuento_pct
        self.__costo_total: float = self.__servicio.calcular_costo_total(
            duracion=self.__duracion,
            tasa_iva=self.__tasa_iva,
            descuento_pct=self.__descuento_pct,
        )

    @property
    def cliente(self) -> Cliente:
        return self.__cliente

    @property
    def servicio(self) -> Servicio:
        return self.__servicio

    @property
    def duracion(self) -> int:
        return self.__duracion

    @property
    def estado(self) -> str:
        return self.__estado

    @property
    def costo_total(self) -> float:
        return self.__costo_total

    def confirmar(self) -> None:
        """Confirma una reserva pendiente y bloquea la disponibilidad del servicio."""
        if self.__estado != "PENDIENTE":
            raise OperacionNoPermitidaError(
                f"No se puede confirmar la reserva {self.id_entidad} en estado '{self.__estado}'."
            )
        if not self.__servicio.disponible:
            raise ServicioNoDisponibleError(
                f"El servicio '{self.__servicio.nombre}' fue ocupado antes de confirmar."
            )
        self.__servicio.disponible = False
        self.__estado = "CONFIRMADA"

    def procesar(self) -> None:
        """Ejecuta y finaliza una reserva confirmada, liberando el servicio."""
        if self.__estado != "CONFIRMADA":
            raise OperacionNoPermitidaError(
                f"Solo se pueden procesar reservas CONFIRMADAS (estado actual: '{self.__estado}')."
            )
        self.__servicio.disponible = True
        self.__estado = "PROCESADA"

    def cancelar(self) -> None:
        """Cancela una reserva pendiente o confirmada, restaurando disponibilidad."""
        if self.__estado in ("PROCESADA", "CANCELADA"):
            raise OperacionNoPermitidaError(
                f"No es posible cancelar una reserva en estado '{self.__estado}'."
            )
        if self.__estado == "CONFIRMADA":
            self.__servicio.disponible = True
        self.__estado = "CANCELADA"

    def validar(self) -> bool:
        return self.__estado in self.ESTADOS_VALIDOS and self.__costo_total > 0

    def obtener_resumen(self) -> str:
        return (
            f"[{self.id_entidad}] Cliente: {self.__cliente.nombre} | "
            f"Servicio: {self.__servicio.nombre} | {self.__duracion}h | "
            f"Total: ${self.__costo_total:.2f} | Estado: {self.__estado}"
        )


# ==============================================================================
# 4. GESTOR CENTRAL Y SIMULADOR DE OPERACIONES (SIN BASE DE DATOS)
# ==============================================================================


class GestorSoftwareFJ:
    """
    Controlador principal que administra las colecciones en memoria (listas)
    y ejecuta las operaciones con manejo exhaustivo de excepciones.
    """

    def __init__(self, gestor_logs: GestorLogs) -> None:
        self.logs = gestor_logs
        self._clientes: List[Cliente] = []
        self._servicios: List[Servicio] = []
        self._reservas: List[Reserva] = []
        self._contador_operaciones: int = 0

    @property
    def clientes(self) -> List[Cliente]:
        return list(self._clientes)

    @property
    def servicios(self) -> List[Servicio]:
        return list(self._servicios)

    @property
    def reservas(self) -> List[Reserva]:
        return list(self._reservas)

    def registrar_cliente(
        self, nombre: str, documento: str, email: str, telefono: str
    ) -> Optional[Cliente]:
        """
        Registra un cliente utilizando bloque try / except / else.
        """
        id_generado = f"CLI-{len(self._clientes) + 1:03d}"
        try:
            if any(c.documento == str(documento).strip() for c in self._clientes):
                raise DatosInvalidosError(
                    f"Ya existe un cliente registrado con el documento '{documento}'."
                )
            nuevo_cliente = Cliente(id_generado, nombre, documento, email, telefono)
        except SoftwareFJError as err:
            self.logs.registrar_error(err, contexto="Registro Cliente")
            return None
        except Exception as err_inesperado:
            envuelto = DatosInvalidosError("Fallo inesperado al crear cliente.")
            envuelto.__cause__ = err_inesperado
            self.logs.registrar_error(envuelto, contexto="Registro Cliente")
            return None
        else:
            self._clientes.append(nuevo_cliente)
            self.logs.registrar_info(
                f"Cliente registrado exitosamente: {nuevo_cliente.obtener_resumen()}"
            )
            return nuevo_cliente

    def registrar_servicio(self, servicio: Servicio) -> Optional[Servicio]:
        """
        Registra un servicio ya instanciado utilizando bloque try / except / finally.
        """
        exito = False
        try:
            if not isinstance(servicio, Servicio):
                raise DatosInvalidosError(
                    "El objeto proporcionado no es un Servicio válido."
                )
            if any(s.id_entidad == servicio.id_entidad for s in self._servicios):
                raise DatosInvalidosError(
                    f"ID de servicio duplicado: {servicio.id_entidad}."
                )
            servicio.validar()
            self._servicios.append(servicio)
            exito = True
            self.logs.registrar_info(f"Servicio creado: {servicio.obtener_resumen()}")
            return servicio
        except SoftwareFJError as err:
            self.logs.registrar_error(err, contexto="Alta Servicio")
            return None
        finally:
            self._contador_operaciones += 1
            if not exito:
                self.logs.registrar_advertencia(
                    f"Auditoría: intento #{self._contador_operaciones} de alta de servicio no completado."
                )

    def crear_servicio_desde_datos(
        self,
        tipo: str,
        nombre: str,
        tarifa: Union[str, float],
        param1,
        param2,
        flag: bool,
    ) -> Optional[Servicio]:
        """
        Fábrica controlada de servicios que encapsula la instanciación y captura
        errores de construcción antes de registrarlos en la lista interna.
        """
        id_srv = f"SRV-{len(self._servicios) + 1:03d}"
        try:
            if tipo == "Sala":
                srv = ReservaSala(
                    id_srv, nombre, tarifa, capacidad=param1, videoconferencia=flag
                )
            elif tipo == "Equipo":
                srv = AlquilerEquipo(
                    id_srv,
                    nombre,
                    tarifa,
                    tipo_equipo=param1,
                    cantidad=param2,
                    gama_alta=flag,
                )
            elif tipo == "Asesoría":
                srv = AsesoriaEspecializada(
                    id_srv,
                    nombre,
                    tarifa,
                    especialidad=param1,
                    modalidad=param2,
                    nivel_senior=flag,
                )
            else:
                raise DatosInvalidosError(f"Tipo de servicio desconocido: '{tipo}'.")
        except SoftwareFJError as err:
            self.logs.registrar_error(err, contexto=f"Construcción Servicio ({tipo})")
            return None
        else:
            return self.registrar_servicio(srv)

    def crear_reserva(
        self,
        id_cliente: str,
        id_servicio: str,
        duracion: Union[int, str],
        tasa_iva: float = 0.21,
        descuento_pct: float = 0.0,
    ) -> Optional[Reserva]:
        """
        Crea una reserva integrando cliente y servicio mediante try / except / else / finally.
        """
        id_res = f"RES-{len(self._reservas) + 1:03d}"
        try:
            cliente = next(
                (c for c in self._clientes if c.id_entidad == id_cliente), None
            )
            if cliente is None:
                raise ReservaInvalidaError(
                    f"No se encontró el cliente con ID '{id_cliente}'."
                )

            servicio = next(
                (s for s in self._servicios if s.id_entidad == id_servicio), None
            )
            if servicio is None:
                raise ReservaInvalidaError(
                    f"No se encontró el servicio con ID '{id_servicio}'."
                )

            nueva_reserva = Reserva(
                id_reserva=id_res,
                cliente=cliente,
                servicio=servicio,
                duracion=duracion,
                tasa_iva=tasa_iva,
                descuento_pct=descuento_pct,
            )
        except SoftwareFJError as err:
            self.logs.registrar_error(err, contexto="Creación Reserva")
            return None
        else:
            self._reservas.append(nueva_reserva)
            self.logs.registrar_info(
                f"Reserva creada: {nueva_reserva.obtener_resumen()}"
            )
            return nueva_reserva
        finally:
            self._contador_operaciones += 1

    def gestionar_estado_reserva(self, id_reserva: str, accion: str) -> bool:
        """Ejecuta confirmar, procesar o cancelar sobre una reserva existente."""
        try:
            reserva = next(
                (r for r in self._reservas if r.id_entidad == id_reserva), None
            )
            if reserva is None:
                raise ReservaInvalidaError(f"Reserva '{id_reserva}' inexistente.")

            if accion == "CONFIRMAR":
                reserva.confirmar()
            elif accion == "PROCESAR":
                reserva.procesar()
            elif accion == "CANCELAR":
                reserva.cancelar()
            else:
                raise OperacionNoPermitidaError(
                    f"Acción de reserva desconocida: '{accion}'."
                )
        except SoftwareFJError as err:
            self.logs.registrar_error(err, contexto=f"Acción Reserva ({accion})")
            return False
        else:
            self.logs.registrar_info(
                f"Acción '{accion}' aplicada correctamente -> {reserva.obtener_resumen()}"
            )
            return True

    def ejecutar_simulacion_integral(self) -> Tuple[int, int]:
        """
        Simula 12 operaciones completas (6 válidas y 6 fallidas) demostrando
        resiliencia, manejo avanzado de excepciones, polimorfismo y sobrecarga.
        Retorna una tupla (exitosas, fallidas_controladas).
        """
        self.logs.registrar_info(
            "=== INICIO DE SIMULACIÓN INTEGRAL (12 OPERACIONES) ==="
        )
        exitosas = 0
        fallidas = 0

        # 1. [VÁLIDA] Registro de cliente 1
        c1 = self.registrar_cliente(
            "Laura Gómez", "10987654", "laura.gomez@empresa.com", "+34611223344"
        )
        exitosas += 1 if c1 else 0

        # 2. [INVÁLIDA - ParametroFaltanteError] Cliente con nombre vacío
        c_err1 = self.registrar_cliente(
            "", "99887766", "sin.nombre@empresa.com", "600112233"
        )
        fallidas += 1 if c_err1 is None else 0

        # 3. [INVÁLIDA - DatosInvalidosError] Cliente con email mal formado
        c_err2 = self.registrar_cliente(
            "Pedro Ruiz", "55443322", "pedro_sin_arroba.com", "600998877"
        )
        fallidas += 1 if c_err2 is None else 0

        # 4. [VÁLIDA] Registro de cliente 2
        c2 = self.registrar_cliente(
            "Carlos Mendoza", "20304050", "carlos.mendoza@tech.es", "+34699887766"
        )
        exitosas += 1 if c2 else 0

        # 5. [VÁLIDA] Creación de Servicio 1: ReservaSala
        s1 = self.crear_servicio_desde_datos(
            "Sala", "Sala Ejecutiva Alpha", 45.0, 12, None, True
        )
        exitosas += 1 if s1 else 0

        # 6. [VÁLIDA] Creación de Servicio 2: AlquilerEquipo
        s2 = self.crear_servicio_desde_datos(
            "Equipo", "Pack Estaciones GPU", 30.0, "Workstation RTX", 3, True
        )
        exitosas += 1 if s2 else 0

        # 7. [VÁLIDA] Creación de Servicio 3: AsesoriaEspecializada
        s3 = self.crear_servicio_desde_datos(
            "Asesoría",
            "Consultoría Arquitectura Cloud",
            80.0,
            "Cloud & DevOps",
            "Presencial",
            True,
        )
        exitosas += 1 if s3 else 0

        # 8. [INVÁLIDA - DatosInvalidosError con encadenamiento] Servicio con tarifa no numérica
        s_err = self.crear_servicio_desde_datos(
            "Sala", "Sala Defectuosa", "tarifa_invalida", 10, None, False
        )
        fallidas += 1 if s_err is None else 0

        # 9. [VÁLIDA] Reserva exitosa + Confirmación + Demostración de método sobrecargado
        if c1 and s1:
            costo_tupla = s1.aplicar_tarifa_personalizada((0.21, 10.0), duracion=4)
            self.logs.registrar_info(
                f"Cálculo sobrecargado (tupla IVA+Desc) para {s1.nombre}: ${costo_tupla:.2f}"
            )
            r1 = self.crear_reserva(
                c1.id_entidad,
                s1.id_entidad,
                duracion=4,
                tasa_iva=0.21,
                descuento_pct=10.0,
            )
            if r1 and self.gestionar_estado_reserva(r1.id_entidad, "CONFIRMAR"):
                exitosas += 1

        # 10. [INVÁLIDA - ServicioNoDisponibleError] Intento de reservar sala ya ocupada por r1
        if c2 and s1:
            r_err1 = self.crear_reserva(c2.id_entidad, s1.id_entidad, duracion=2)
            fallidas += 1 if r_err1 is None else 0

        # 11. [INVÁLIDA - CalculoInconsistenteError] Reserva con descuento absurdo (150%)
        if c2 and s2:
            r_err2 = self.crear_reserva(
                c2.id_entidad,
                s2.id_entidad,
                duracion=3,
                tasa_iva=0.21,
                descuento_pct=150.0,
            )
            fallidas += 1 if r_err2 is None else 0

        # 12. [INVÁLIDA - OperacionNoPermitidaError] Cancelar reserva y luego intentar procesarla
        if c2 and s3:
            r2 = self.crear_reserva(c2.id_entidad, s3.id_entidad, duracion=5)
            if r2:
                self.gestionar_estado_reserva(r2.id_entidad, "CANCELAR")
                procesado_ilegal = self.gestionar_estado_reserva(
                    r2.id_entidad, "PROCESAR"
                )
                fallidas += 1 if not procesado_ilegal else 0

        # Liberamos s1 procesando r1 para dejar el entorno listo para pruebas manuales
        if self._reservas:
            self.gestionar_estado_reserva(self._reservas[0].id_entidad, "PROCESAR")

        self.logs.registrar_info(
            f"=== FIN DE SIMULACIÓN | Exitosas: {exitosas} | Errores Controlados: {fallidas} ==="
        )
        return exitosas, fallidas


# ==============================================================================
# 5. INTERFAZ GRÁFICA DE USUARIO EN TKINTER
# ==============================================================================


class InterfazSoftwareFJ(tk.Tk):
    """Aplicación gráfica en Tkinter para operar el sistema Software FJ."""

    def __init__(self, gestor: GestorSoftwareFJ) -> None:
        super().__init__()
        self.gestor = gestor
        self.title("Software FJ — Gestión Integral de Clientes, Servicios y Reservas")
        self.geometry("1080x720")
        self.minsize(960, 640)

        self._configurar_estilos()
        self._construir_ui()

        # Suscribir la vista de logs en tiempo real
        self.gestor.logs.suscribir_vista(self._agregar_linea_log_ui)
        self.gestor.logs.registrar_info(
            "Interfaz gráfica de Software FJ iniciada correctamente."
        )
        self._refrescar_tablas()

    def _configurar_estilos(self) -> None:
        estilo = ttk.Style(self)
        if "clam" in estilo.theme_names():
            estilo.theme_use("clam")
        estilo.configure(
            "Header.TLabel", font=("Segoe UI", 14, "bold"), foreground="#1B365D"
        )
        estilo.configure(
            "Subheader.TLabel", font=("Segoe UI", 10), foreground="#4A5568"
        )
        estilo.configure("Accent.TButton", font=("Segoe UI", 10, "bold"))

    def _construir_ui(self) -> None:
        # Encabezado superior
        frame_top = ttk.Frame(self, padding=(15, 10))
        frame_top.pack(fill="x")

        ttk.Label(
            frame_top,
            text="Software FJ — Plataforma de Gestión Orientada a Objetos",
            style="Header.TLabel",
        ).pack(side="left")

        ttk.Button(
            frame_top,
            text="▶ Ejecutar Simulación (12 Operaciones)",
            style="Accent.TButton",
            command=self._accion_simular,
        ).pack(side="right")

        # Contenedor principal de pestañas
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True, padx=15, pady=(0, 10))

        self.tab_clientes = ttk.Frame(self.notebook, padding=10)
        self.tab_servicios = ttk.Frame(self.notebook, padding=10)
        self.tab_reservas = ttk.Frame(self.notebook, padding=10)
        self.tab_logs = ttk.Frame(self.notebook, padding=10)

        self.notebook.add(self.tab_clientes, text="  1. Clientes  ")
        self.notebook.add(self.tab_servicios, text="  2. Servicios  ")
        self.notebook.add(self.tab_reservas, text="  3. Reservas  ")
        self.notebook.add(self.tab_logs, text="  4. Auditoría y Logs  ")

        self._construir_tab_clientes()
        self._construir_tab_servicios()
        self._construir_tab_reservas()
        self._construir_tab_logs()

    # --- PESTAÑA 1: CLIENTES ---
    def _construir_tab_clientes(self) -> None:
        frame_form = ttk.LabelFrame(
            self.tab_clientes, text="Registrar Nuevo Cliente", padding=10
        )
        frame_form.pack(fill="x", pady=(0, 10))

        ttk.Label(frame_form, text="Nombre Completo:").grid(
            row=0, column=0, padx=5, pady=5, sticky="e"
        )
        self.ent_cli_nombre = ttk.Entry(frame_form, width=28)
        self.ent_cli_nombre.grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(frame_form, text="Documento ID:").grid(
            row=0, column=2, padx=5, pady=5, sticky="e"
        )
        self.ent_cli_doc = ttk.Entry(frame_form, width=20)
        self.ent_cli_doc.grid(row=0, column=3, padx=5, pady=5)

        ttk.Label(frame_form, text="Correo Electrónico:").grid(
            row=1, column=0, padx=5, pady=5, sticky="e"
        )
        self.ent_cli_email = ttk.Entry(frame_form, width=28)
        self.ent_cli_email.grid(row=1, column=1, padx=5, pady=5)

        ttk.Label(frame_form, text="Teléfono:").grid(
            row=1, column=2, padx=5, pady=5, sticky="e"
        )
        self.ent_cli_tel = ttk.Entry(frame_form, width=20)
        self.ent_cli_tel.grid(row=1, column=3, padx=5, pady=5)

        ttk.Button(
            frame_form, text="Guardar Cliente", command=self._accion_registrar_cliente
        ).grid(row=0, column=4, rowspan=2, padx=15, pady=5, sticky="ns")

        # Tabla de clientes
        cols = ("id", "nombre", "documento", "email", "telefono", "estado")
        self.tree_clientes = ttk.Treeview(
            self.tab_clientes, columns=cols, show="headings", height=14
        )
        encabezados = ["ID", "Nombre", "Documento", "Email", "Teléfono", "Estado"]
        anchos = [80, 220, 130, 230, 130, 100]
        for col, tit, ancho in zip(cols, encabezados, anchos):
            self.tree_clientes.heading(col, text=tit)
            self.tree_clientes.column(col, width=ancho, anchor="center")
        self.tree_clientes.pack(fill="both", expand=True)

    # --- PESTAÑA 2: SERVICIOS ---
    def _construir_tab_servicios(self) -> None:
        frame_form = ttk.LabelFrame(
            self.tab_servicios, text="Crear Servicio Especializado", padding=10
        )
        frame_form.pack(fill="x", pady=(0, 10))

        ttk.Label(frame_form, text="Tipo de Servicio:").grid(
            row=0, column=0, padx=5, pady=5, sticky="e"
        )
        self.cmb_srv_tipo = ttk.Combobox(
            frame_form,
            values=["Sala", "Equipo", "Asesoría"],
            state="readonly",
            width=18,
        )
        self.cmb_srv_tipo.current(0)
        self.cmb_srv_tipo.grid(row=0, column=1, padx=5, pady=5)
        self.cmb_srv_tipo.bind("<<ComboboxSelected>>", self._actualizar_campos_servicio)

        ttk.Label(frame_form, text="Nombre Servicio:").grid(
            row=0, column=2, padx=5, pady=5, sticky="e"
        )
        self.ent_srv_nombre = ttk.Entry(frame_form, width=25)
        self.ent_srv_nombre.grid(row=0, column=3, padx=5, pady=5)

        ttk.Label(frame_form, text="Tarifa Base ($/h):").grid(
            row=0, column=4, padx=5, pady=5, sticky="e"
        )
        self.ent_srv_tarifa = ttk.Entry(frame_form, width=12)
        self.ent_srv_tarifa.grid(row=0, column=5, padx=5, pady=5)

        # Parámetros dinámicos según subclase
        self.lbl_srv_p1 = ttk.Label(frame_form, text="Capacidad (pers.):")
        self.lbl_srv_p1.grid(row=1, column=0, padx=5, pady=5, sticky="e")
        self.ent_srv_p1 = ttk.Entry(frame_form, width=20)
        self.ent_srv_p1.grid(row=1, column=1, padx=5, pady=5)

        self.lbl_srv_p2 = ttk.Label(frame_form, text="N/A:")
        self.lbl_srv_p2.grid(row=1, column=2, padx=5, pady=5, sticky="e")
        self.ent_srv_p2 = ttk.Entry(frame_form, width=25, state="disabled")
        self.ent_srv_p2.grid(row=1, column=3, padx=5, pady=5)

        self.var_srv_flag = tk.BooleanVar(value=True)
        self.chk_srv_flag = ttk.Checkbutton(
            frame_form, text="Videoconferencia", variable=self.var_srv_flag
        )
        self.chk_srv_flag.grid(row=1, column=4, columnspan=2, padx=5, pady=5)

        ttk.Button(
            frame_form,
            text="Registrar Servicio",
            command=self._accion_registrar_servicio,
        ).grid(row=0, column=6, rowspan=2, padx=12, pady=5, sticky="ns")

        # Tabla de servicios
        cols = ("id", "tipo", "nombre", "tarifa", "detalle", "estado")
        self.tree_servicios = ttk.Treeview(
            self.tab_servicios, columns=cols, show="headings", height=14
        )
        encabezados = [
            "ID",
            "Clase Derivada",
            "Nombre",
            "Tarifa Base",
            "Descripción Polimórfica",
            "Estado",
        ]
        anchos = [80, 150, 190, 100, 290, 100]
        for col, tit, ancho in zip(cols, encabezados, anchos):
            self.tree_servicios.heading(col, text=tit)
            self.tree_servicios.column(col, width=ancho, anchor="center")
        self.tree_servicios.pack(fill="both", expand=True)

    # --- PESTAÑA 3: RESERVAS ---
    def _construir_tab_reservas(self) -> None:
        frame_form = ttk.LabelFrame(
            self.tab_reservas, text="Nueva Reserva de Servicio", padding=10
        )
        frame_form.pack(fill="x", pady=(0, 10))

        ttk.Label(frame_form, text="ID Cliente:").grid(
            row=0, column=0, padx=5, pady=5, sticky="e"
        )
        self.cmb_res_cliente = ttk.Combobox(frame_form, width=28, state="readonly")
        self.cmb_res_cliente.grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(frame_form, text="ID Servicio:").grid(
            row=0, column=2, padx=5, pady=5, sticky="e"
        )
        self.cmb_res_servicio = ttk.Combobox(frame_form, width=32, state="readonly")
        self.cmb_res_servicio.grid(row=0, column=3, padx=5, pady=5)

        ttk.Label(frame_form, text="Duración (horas):").grid(
            row=1, column=0, padx=5, pady=5, sticky="e"
        )
        self.ent_res_duracion = ttk.Entry(frame_form, width=12)
        self.ent_res_duracion.insert(0, "2")
        self.ent_res_duracion.grid(row=1, column=1, padx=5, pady=5, sticky="w")

        ttk.Label(frame_form, text="IVA (0.0 - 1.0):").grid(
            row=1, column=2, padx=5, pady=5, sticky="e"
        )
        self.ent_res_iva = ttk.Entry(frame_form, width=10)
        self.ent_res_iva.insert(0, "0.21")
        self.ent_res_iva.grid(row=1, column=3, padx=5, pady=5, sticky="w")

        ttk.Label(frame_form, text="Descuento (%):").grid(
            row=1, column=3, padx=5, pady=5, sticky="e"
        )
        self.ent_res_desc = ttk.Entry(frame_form, width=10)
        self.ent_res_desc.insert(0, "0")
        self.ent_res_desc.grid(row=1, column=4, padx=5, pady=5, sticky="w")

        ttk.Button(
            frame_form, text="Crear Reserva", command=self._accion_crear_reserva
        ).grid(row=0, column=5, rowspan=2, padx=12, pady=5, sticky="ns")

        # Barra de acciones sobre la reserva seleccionada
        frame_acciones = ttk.Frame(self.tab_reservas)
        frame_acciones.pack(fill="x", pady=(0, 8))

        ttk.Label(frame_acciones, text="Gestión de Reserva Seleccionada:").pack(
            side="left", padx=5
        )
        ttk.Button(
            frame_acciones,
            text="✔ Confirmar Reserva",
            command=lambda: self._accion_estado_reserva("CONFIRMAR"),
        ).pack(side="left", padx=5)
        ttk.Button(
            frame_acciones,
            text="⚙ Procesar Reserva",
            command=lambda: self._accion_estado_reserva("PROCESAR"),
        ).pack(side="left", padx=5)
        ttk.Button(
            frame_acciones,
            text="✖ Cancelar Reserva",
            command=lambda: self._accion_estado_reserva("CANCELAR"),
        ).pack(side="left", padx=5)

        # Tabla de reservas
        cols = ("id", "cliente", "servicio", "duracion", "total", "estado")
        self.tree_reservas = ttk.Treeview(
            self.tab_reservas, columns=cols, show="headings", height=12
        )
        encabezados = [
            "ID Reserva",
            "Cliente",
            "Servicio",
            "Duración",
            "Costo Total",
            "Estado",
        ]
        anchos = [90, 200, 230, 90, 120, 120]
        for col, tit, ancho in zip(cols, encabezados, anchos):
            self.tree_reservas.heading(col, text=tit)
            self.tree_reservas.column(col, width=ancho, anchor="center")
        self.tree_reservas.pack(fill="both", expand=True)

    # --- PESTAÑA 4: AUDITORÍA Y LOGS ---
    def _construir_tab_logs(self) -> None:
        frame_ctrl = ttk.Frame(self.tab_logs)
        frame_ctrl.pack(fill="x", pady=(0, 8))

        ttk.Label(
            frame_ctrl,
            text=f"Registro en tiempo real y archivo persistente ({GestorLogs.ARCHIVO_LOG}):",
            style="Subheader.TLabel",
        ).pack(side="left")

        ttk.Button(
            frame_ctrl,
            text="Recargar desde Archivo .log",
            command=self._recargar_log_desde_disco,
        ).pack(side="right")

        self.txt_logs = scrolledtext.ScrolledText(
            self.tab_logs, wrap="word", font=("Consolas", 9), bg="#1E1E1E", fg="#E2E8F0"
        )
        self.txt_logs.pack(fill="both", expand=True)

    # --- CALLBACKS Y ACTUALIZACIÓN DE INTERFAZ ---
    def _actualizar_campos_servicio(self, _evento=None) -> None:
        tipo = self.cmb_srv_tipo.get()
        self.ent_srv_p1.delete(0, tk.END)
        self.ent_srv_p2.delete(0, tk.END)

        if tipo == "Sala":
            self.lbl_srv_p1.config(text="Capacidad (pers.):")
            self.lbl_srv_p2.config(text="N/A:")
            self.ent_srv_p2.config(state="disabled")
            self.chk_srv_flag.config(text="Videoconferencia")
        elif tipo == "Equipo":
            self.lbl_srv_p1.config(text="Tipo de Equipo:")
            self.lbl_srv_p2.config(text="Cantidad:")
            self.ent_srv_p2.config(state="normal")
            self.chk_srv_flag.config(text="Gama Alta (+25%)")
        elif tipo == "Asesoría":
            self.lbl_srv_p1.config(text="Especialidad:")
            self.lbl_srv_p2.config(text="Modalidad (Remota/Presencial):")
            self.ent_srv_p2.config(state="normal")
            self.ent_srv_p2.insert(0, "Remota")
            self.chk_srv_flag.config(text="Consultor Senior (+40%)")

    def _accion_registrar_cliente(self) -> None:
        cliente = self.gestor.registrar_cliente(
            nombre=self.ent_cli_nombre.get(),
            documento=self.ent_cli_doc.get(),
            email=self.ent_cli_email.get(),
            telefono=self.ent_cli_tel.get(),
        )
        if cliente:
            self.ent_cli_nombre.delete(0, tk.END)
            self.ent_cli_doc.delete(0, tk.END)
            self.ent_cli_email.delete(0, tk.END)
            self.ent_cli_tel.delete(0, tk.END)
            self._refrescar_tablas()
            messagebox.showinfo(
                "Cliente Registrado", f"Se registró: {cliente.obtener_resumen()}"
            )
        else:
            messagebox.showwarning(
                "Validación Controlada",
                "No se pudo registrar el cliente. Revise el detalle en la pestaña de Auditoría y Logs.",
            )

    def _accion_registrar_servicio(self) -> None:
        tipo = self.cmb_srv_tipo.get()
        srv = self.gestor.crear_servicio_desde_datos(
            tipo=tipo,
            nombre=self.ent_srv_nombre.get(),
            tarifa=self.ent_srv_tarifa.get(),
            param1=self.ent_srv_p1.get(),
            param2=self.ent_srv_p2.get(),
            flag=self.var_srv_flag.get(),
        )
        if srv:
            self.ent_srv_nombre.delete(0, tk.END)
            self.ent_srv_tarifa.delete(0, tk.END)
            self.ent_srv_p1.delete(0, tk.END)
            self._refrescar_tablas()
            messagebox.showinfo("Servicio Creado", f"Se creó: {srv.obtener_resumen()}")
        else:
            messagebox.showwarning(
                "Error en Servicio",
                "Parámetros inválidos en el servicio. El incidente fue registrado en el log.",
            )

    def _accion_crear_reserva(self) -> None:
        sel_cli = self.cmb_res_cliente.get()
        sel_srv = self.cmb_res_servicio.get()
        if not sel_cli or not sel_srv:
            messagebox.showwarning(
                "Datos Incompletos", "Seleccione un cliente y un servicio."
            )
            return

        id_cliente = sel_cli.split(" - ")[0]
        id_servicio = sel_srv.split(" - ")[0]

        try:
            iva = float(self.ent_res_iva.get())
            desc = float(self.ent_res_desc.get())
        except ValueError as err:
            error_encadenado = CalculoInconsistenteError(
                "IVA o descuento no numérico en formulario."
            )
            error_encadenado.__cause__ = err
            self.gestor.logs.registrar_error(error_encadenado, contexto="UI Reserva")
            messagebox.showerror("Error Numérico", str(error_encadenado))
            return

        reserva = self.gestor.crear_reserva(
            id_cliente=id_cliente,
            id_servicio=id_servicio,
            duracion=self.ent_res_duracion.get(),
            tasa_iva=iva,
            descuento_pct=desc,
        )
        if reserva:
            self._refrescar_tablas()
            messagebox.showinfo("Reserva Creada", reserva.obtener_resumen())
        else:
            messagebox.showwarning(
                "Reserva Rechazada",
                "La reserva no pudo crearse (servicio ocupado o parámetros inválidos). Ver log.",
            )

    def _accion_estado_reserva(self, accion: str) -> None:
        seleccion = self.tree_reservas.selection()
        if not seleccion:
            messagebox.showinfo(
                "Selección Requerida", "Seleccione una reserva de la tabla."
            )
            return
        id_reserva = self.tree_reservas.item(seleccion[0], "values")[0]
        exito = self.gestor.gestionar_estado_reserva(id_reserva, accion)
        self._refrescar_tablas()
        if exito:
            messagebox.showinfo(
                "Operación Exitosa",
                f"Reserva {id_reserva}: acción '{accion}' aplicada.",
            )
        else:
            messagebox.showwarning(
                "Operación No Permitida",
                f"No se pudo aplicar '{accion}' sobre {id_reserva}. Evento registrado en log.",
            )

    def _accion_simular(self) -> None:
        exitosas, fallidas = self.gestor.ejecutar_simulacion_integral()
        self._refrescar_tablas()
        self.notebook.select(self.tab_logs)
        messagebox.showinfo(
            "Simulación Completada sin Interrupciones",
            f"Se ejecutaron 12 operaciones completas:\n"
            f"• Operaciones exitosas: {exitosas}\n"
            f"• Errores graves capturados y registrados en log: {fallidas}",
        )

    def _refrescar_tablas(self) -> None:
        # Refrescar Clientes
        for item in self.tree_clientes.get_children():
            self.tree_clientes.delete(item)
        for c in self.gestor.clientes:
            self.tree_clientes.insert(
                "",
                "end",
                values=(
                    c.id_entidad,
                    c.nombre,
                    c.documento,
                    c.email,
                    c.telefono,
                    "Activo" if c.activo else "Inactivo",
                ),
            )

        # Refrescar Servicios
        for item in self.tree_servicios.get_children():
            self.tree_servicios.delete(item)
        for s in self.gestor.servicios:
            self.tree_servicios.insert(
                "",
                "end",
                values=(
                    s.id_entidad,
                    type(s).__name__,
                    s.nombre,
                    f"${s.tarifa_base:.2f}/h",
                    s.describir_servicio(),
                    "Disponible" if s.disponible else "Ocupado",
                ),
            )

        # Refrescar Reservas
        for item in self.tree_reservas.get_children():
            self.tree_reservas.delete(item)
        for r in self.gestor.reservas:
            self.tree_reservas.insert(
                "",
                "end",
                values=(
                    r.id_entidad,
                    r.cliente.nombre,
                    r.servicio.nombre,
                    f"{r.duracion}h",
                    f"${r.costo_total:.2f}",
                    r.estado,
                ),
            )

        # Actualizar Comboboxes de Reservas
        self.cmb_res_cliente["values"] = [
            f"{c.id_entidad} - {c.nombre}" for c in self.gestor.clientes
        ]
        self.cmb_res_servicio["values"] = [
            f"{s.id_entidad} - {s.nombre} ({'Disp.' if s.disponible else 'Ocup.'})"
            for s in self.gestor.servicios
        ]

    def _agregar_linea_log_ui(self, linea: str) -> None:
        self.txt_logs.insert(tk.END, linea + "\n")
        self.txt_logs.see(tk.END)

    def _recargar_log_desde_disco(self) -> None:
        contenido = self.gestor.logs.leer_historial_archivo()
        self.txt_logs.delete("1.0", tk.END)
        self.txt_logs.insert(tk.END, contenido)
        self.txt_logs.see(tk.END)


# ==============================================================================
# PUNTO DE ENTRADA PRINCIPAL
# ==============================================================================

if __name__ == "__main__":
    gestor_logs = GestorLogs()
    sistema_software_fj = GestorSoftwareFJ(gestor_logs)
    app = InterfazSoftwareFJ(sistema_software_fj)
    app.mainloop()
