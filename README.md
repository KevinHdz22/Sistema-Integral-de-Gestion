# Software FJ — Sistema Integral de Gestión de Clientes, Servicios y Reservas

Aplicación de escritorio desarrollada en Python con interfaz gráfica en **Tkinter** para la gestión integral de clientes, catálogo de servicios especializados y reservas de la empresa **Software FJ**. El sistema está diseñado bajo los principios de la Programación Orientada a Objetos (POO) y opera exclusivamente mediante objetos en memoria, listas internas y persistencia de auditoría en archivo plano (`software_fj.log`), sin utilizar motores de bases de datos.

---

## Características Principales

* **Arquitectura Orientada a Objetos:** Implementación estricta de abstracción, encapsulación, herencia, polimorfismo y sobrecarga de métodos.
* **Persistencia sin Base de Datos:** Gestión de entidades mediante colecciones internas en memoria (`GestorSoftwareFJ`) y registro cronológico de eventos y errores en `software_fj.log`.
* **Manejo Robusto de Excepciones:** Jerarquía de excepciones personalizadas, bloques `try/except/else/finally` y encadenamiento de excepciones (`raise ... from ...`) que mantienen la aplicación estable ante fallos graves.
* **Simulación Integral Automatizada:** Ejecución de **12 operaciones completas** (6 válidas y 6 escenarios de error controlado) con un solo clic desde la interfaz.
* **Interfaz Gráfica Funcional en Tkinter:** Panel organizado en pestañas para administrar clientes, servicios, reservas y auditoría de logs en tiempo real.

---

## Requisitos e Instalación

* **Python:** Versión **3.8 o superior** (requerido para el decorador `@functools.singledispatchmethod`).
* **Dependencias:** Ninguna librería externa. Utiliza únicamente módulos de la biblioteca estándar de Python (`tkinter`, `abc`, `logging`, `re`, `functools`, `datetime`, `math`, `os`, `typing`).

### Ejecución

```bash
python software_fj_sistema.py
```

---

## Estructura del Proyecto

```text
proyecto_software_fj/
│
├── software_fj_sistema.py   # Código fuente completo (excepciones, logs, modelo POO, controlador e interfaz Tkinter)
├── software_fj.log          # Archivo de logs generado automáticamente al ejecutar el sistema
└── README.md                # Documentación técnica y guía de uso del proyecto
```

---

## Arquitectura Orientada a Objetos

### 1. Abstracción y Encapsulación
* **`EntidadSistema(ABC)`:** Clase abstracta raíz que encapsula el identificador único (`__id_entidad`) y la fecha de creación (`__fecha_creacion`), obligando a las subclases a implementar `validar()` y `obtener_resumen()`.
* **`Cliente`:** Encapsula los datos personales (`__nombre`, `__documento`, `__email`, `__telefono`, `__activo`) mediante propiedades (`@property`) y *setters* con validación estricta por expresiones regulares.

### 2. Herencia y Polimorfismo
* **`Servicio(EntidadSistema, ABC)`:** Clase abstracta base que define el contrato polimórfico `calcular_costo_base(duracion)`, `describir_servicio()` y `validar_parametros()`.
* **Clases Especializadas Derivadas:**
  * **`ReservaSala`:** Calcula el costo base según tarifa por hora, aforo (`$0.50` por persona) y equipamiento audiovisual (`+$15.00/h` si incluye videoconferencia).
  * **`AlquilerEquipo`:** Calcula el costo por cantidad de unidades y aplica un factor de `1.25x` para equipos de gama alta.
  * **`AsesoriaEspecializada`:** Aplica un factor de `1.40x` para consultores de nivel *Senior* y suma `$25.00` de viáticos cuando la modalidad es presencial.

### 3. Sobrecarga de Métodos
* **Por parámetros opcionales (`calcular_costo_total`):** Permite calcular el importe final con solo la duración o incorporando tasa de IVA, porcentaje de descuento y recargos fijos.
* **Por despacho de tipos (`@singledispatchmethod` en `aplicar_tarifa_personalizada`):** Adapta el cálculo según el tipo de argumento recibido:
  * `int` o `float`: aplica el valor como porcentaje de descuento directo.
  * `tuple`: interpreta `(tasa_iva, descuento_pct)`.
  * `dict`: procesa las claves opcionales `'iva'`, `'descuento'` y `'recargo'`.

### 4. Gestión de Reservas
* **`Reserva`:** Integra un `Cliente`, un `Servicio`, la duración en horas y su ciclo de vida (`PENDIENTE`, `CONFIRMADA`, `PROCESADA`, `CANCELADA`). Al confirmar una reserva bloquea automáticamente la disponibilidad del servicio, y la libera al procesarla o cancelarla.

---

## Manejo Avanzado de Excepciones y Logs

### Jerarquía de Excepciones Personalizadas
Todas las excepciones del dominio heredan de `SoftwareFJError`, incluyendo código de error y marca de tiempo:

| Excepción | Código | Condición que la dispara |
| :--- | :--- | :--- |
| `ParametroFaltanteError` | `SFJ-001` | Parámetros obligatorios vacíos o `None`. |
| `DatosInvalidosError` | `SFJ-002` | Formatos incorrectos (email, teléfono, nombres con números, tarifas no numéricas). |
| `ServicioNoDisponibleError` | `SFJ-003` | Intento de reservar o confirmar un servicio ocupado. |
| `ReservaInvalidaError` | `SFJ-004` | Cliente o servicio inexistente, o duración fuera de rango (`1-720h`). |
| `OperacionNoPermitidaError` | `SFJ-005` | Transiciones de estado ilegales (por ejemplo, procesar una reserva cancelada). |
| `CalculoInconsistenteError` | `SFJ-006` | Descuentos `>= 100%`, tasas negativas o totales financieros incoherentes. |

### Estructuras Implementadas
* **`try / except / else`:** En `registrar_cliente()`, asegurando que solo instancias válidas ingresen a la lista interna.
* **`try / except / finally`:** En `registrar_servicio()`, incrementando el contador de auditoría y dejando registro ante intentos fallidos.
* **`try / except / else / finally`:** En `crear_reserva()`.
* **Encadenamiento de excepciones (`raise ... from err`):** Envuelve errores nativos de conversión (`ValueError`, `TypeError`) en excepciones del sistema conservando la causa original (`__cause__`) en `software_fj.log`.

---

## Simulación Automatizada (12 Operaciones)

Al pulsar el botón **"▶ Ejecutar Simulación (12 Operaciones)"** en la barra superior, el método `ejecutar_simulacion_integral()` ejecuta **6 operaciones exitosas** y **6 errores graves controlados**:

1. **[Válida]** Registro de cliente 1 (*Laura Gómez*).
2. **[Error Controlado]** Registro de cliente con nombre vacío (`ParametroFaltanteError`).
3. **[Error Controlado]** Registro de cliente con correo electrónico sin formato válido (`DatosInvalidosError`).
4. **[Válida]** Registro de cliente 2 (*Carlos Mendoza*).
5. **[Válida]** Creación de servicio `ReservaSala` (*Sala Ejecutiva Alpha*).
6. **[Válida]** Creación de servicio `AlquilerEquipo` (*Pack Estaciones GPU*).
7. **[Válida]** Creación de servicio `AsesoriaEspecializada` (*Consultoría Arquitectura Cloud*).
8. **[Error Controlado]** Creación de sala con tarifa `"tarifa_invalida"` (`DatosInvalidosError` con excepción encadenada).
9. **[Válida]** Cálculo sobrecargado mediante tupla `(0.21, 10.0)`, creación y confirmación de reserva.
10. **[Error Controlado]** Intento de reservar la sala ya ocupada en la operación anterior (`ServicioNoDisponibleError`).
11. **[Error Controlado]** Intento de reserva con descuento del `150%` (`CalculoInconsistenteError`).
12. **[Error Controlado]** Cancelación de una reserva seguida de un intento ilegal de procesarla (`OperacionNoPermitidaError`).

---

## Guía de Uso de la Interfaz Gráfica

1. **Pestaña `1. Clientes`:** Permite registrar nuevos clientes con validación inmediata y consultar el listado actualizado en tabla.
2. **Pestaña `2. Servicios`:** Permite crear servicios de tipo `Sala`, `Equipo` o `Asesoría`, adaptando dinámicamente los campos del formulario según la subclase elegida.
3. **Pestaña `3. Reservas`:** Permite asociar un cliente y un servicio, calcular el total con IVA y descuento, y gestionar el estado de cada reserva mediante los botones **Confirmar**, **Procesar** y **Cancelar**.
4. **Pestaña `4. Auditoría y Logs`:** Muestra en tiempo real todos los eventos y errores capturados, e incluye el botón **Recargar desde Archivo .log** para consultar el historial persistido en disco.