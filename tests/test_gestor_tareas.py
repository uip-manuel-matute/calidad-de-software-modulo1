"""
Suite de pruebas unitarias y funcionales para el Sistema de Agenda de Tareas.

Organizada en tres categorías exigidas por la guía de Calidad de Software:
1. Flujos Correctos (Happy Path): CP-01 a CP-05
2. Manejo de Entradas Inválidas: CP-06 a CP-10
3. Casos Borde (Boundary Value Analysis): CP-11 a CP-15
"""

import unittest

from src.excepciones import (
    ErrorValidacionTarea,
    TareaNoEncontradaError,
    TransicionEstadoInvalidaError,
)
from src.gestor_tareas import GestorTareas
from src.modelos import EstadoTarea, Prioridad


class TestAgendaTareas(unittest.TestCase):
    """Pruebas sistemáticas del dominio y del servicio GestorTareas."""

    def setUp(self) -> None:
        """Inicializa un gestor limpio antes de cada caso de prueba."""
        self.gestor = GestorTareas()

    # =========================================================================
    # 1. FLUJOS CORRECTOS (HAPPY PATH)
    # =========================================================================

    def test_cp01_crear_tarea_valida_asigna_estado_pendiente_e_id_incremental(self) -> None:
        """CP-01: Crear una tarea válida con título, descripción y prioridad ALTA."""
        tarea = self.gestor.crear_tarea(
            titulo="Preparar entrega de calidad",
            descripcion="Consolidar informe técnico en PDF",
            prioridad="ALTA",
        )
        self.assertEqual(tarea.id_tarea, 1)
        self.assertEqual(tarea.titulo, "Preparar entrega de calidad")
        self.assertEqual(tarea.prioridad, Prioridad.ALTA)
        self.assertEqual(tarea.estado, EstadoTarea.PENDIENTE)

    def test_cp02_transicion_completa_estados_pendiente_a_en_progreso_a_completada(self) -> None:
        """CP-02: Validar el ciclo de vida completo PENDIENTE -> EN_PROGRESO -> COMPLETADA."""
        tarea = self.gestor.crear_tarea("Implementar pruebas unitarias")
        self.gestor.cambiar_estado_tarea(tarea.id_tarea, EstadoTarea.EN_PROGRESO)
        self.assertEqual(tarea.estado, EstadoTarea.EN_PROGRESO)

        self.gestor.cambiar_estado_tarea(tarea.id_tarea, EstadoTarea.COMPLETADA)
        self.assertEqual(tarea.estado, EstadoTarea.COMPLETADA)

    def test_cp03_filtrar_tareas_por_estado_y_prioridad(self) -> None:
        """CP-03: Filtrar tareas combinando criterios de estado y nivel de prioridad."""
        t1 = self.gestor.crear_tarea("Tarea crítica 1", prioridad="ALTA")
        t2 = self.gestor.crear_tarea("Tarea crítica 2", prioridad="ALTA")
        self.gestor.crear_tarea("Tarea rutinaria", prioridad="BAJA")

        self.gestor.cambiar_estado_tarea(t2.id_tarea, "EN_PROGRESO")

        altas_pendientes = self.gestor.listar_tareas(
            estado="PENDIENTE", prioridad="ALTA"
        )
        self.assertEqual(len(altas_pendientes), 1)
        self.assertEqual(altas_pendientes[0].id_tarea, t1.id_tarea)

    def test_cp04_eliminar_tarea_y_verificar_resumen_metricas(self) -> None:
        """CP-04: Eliminar una tarea existente y comprobar la actualización del resumen."""
        t1 = self.gestor.crear_tarea("Tarea temporal", prioridad="BAJA")
        self.gestor.crear_tarea("Tarea permanente", prioridad="ALTA")

        eliminada = self.gestor.eliminar_tarea(t1.id_tarea)
        self.assertEqual(eliminada.id_tarea, t1.id_tarea)

        resumen = self.gestor.obtener_resumen()
        self.assertEqual(resumen["total"], 1)
        self.assertEqual(resumen["alta_prioridad"], 1)

    def test_cp05_permitir_mismo_titulo_si_tarea_anterior_esta_completada(self) -> None:
        """CP-05: Permitir crear una tarea con igual título cuando la anterior ya fue COMPLETADA."""
        t1 = self.gestor.crear_tarea("Revisión semanal de código")
        self.gestor.cambiar_estado_tarea(t1.id_tarea, "COMPLETADA")

        t2 = self.gestor.crear_tarea("Revisión semanal de código")
        self.assertEqual(t2.id_tarea, 2)
        self.assertEqual(t2.estado, EstadoTarea.PENDIENTE)

    # =========================================================================
    # 2. MANEJO DE ENTRADAS INVÁLIDAS
    # =========================================================================

    def test_cp06_rechazar_titulo_vacio_o_solo_espacios(self) -> None:
        """CP-06: Rechazar creación de tarea con cadena vacía o compuesta solo por espacios."""
        with self.assertRaises(ErrorValidacionTarea):
            self.gestor.crear_tarea("     ")

    def test_cp07_rechazar_prioridad_inexistente(self) -> None:
        """CP-07: Rechazar creación o actualización con una prioridad fuera del Enum."""
        with self.assertRaises(ErrorValidacionTarea):
            self.gestor.crear_tarea("Configurar repositorio", prioridad="CRITICA_EXTREMA")

    def test_cp08_rechazar_tarea_activa_con_titulo_duplicado(self) -> None:
        """CP-08: Impedir el registro de dos tareas activas con el mismo título (case-insensitive)."""
        self.gestor.crear_tarea("Documentar arquitectura")
        with self.assertRaises(ErrorValidacionTarea):
            self.gestor.crear_tarea("  documentar ARQUITECTURA  ")

    def test_cp09_rechazar_cambio_de_estado_o_prioridad_en_tarea_completada(self) -> None:
        """CP-09: Impedir reabrir o cambiar prioridad de una tarea ya marcada como COMPLETADA."""
        tarea = self.gestor.crear_tarea("Cerrar sprint")
        self.gestor.cambiar_estado_tarea(tarea.id_tarea, "COMPLETADA")

        with self.assertRaises(TransicionEstadoInvalidaError):
            self.gestor.cambiar_estado_tarea(tarea.id_tarea, "PENDIENTE")

        with self.assertRaises(TransicionEstadoInvalidaError):
            self.gestor.actualizar_prioridad_tarea(tarea.id_tarea, "ALTA")

    def test_cp10_rechazar_id_inexistente_o_tipo_invalido(self) -> None:
        """CP-10: Lanzar error al consultar un ID no registrado (999) o un tipo inválido (bool/negativo)."""
        with self.assertRaises(TareaNoEncontradaError):
            self.gestor.obtener_tarea(999)

        with self.assertRaises(ErrorValidacionTarea):
            self.gestor.obtener_tarea(-5)

        with self.assertRaises(ErrorValidacionTarea):
            self.gestor.obtener_tarea(True)  # En Python bool hereda de int; debe rechazarse

    # =========================================================================
    # 3. CASOS BORDE (BOUNDARY CASES)
    # =========================================================================

    def test_cp11_limite_inferior_longitud_titulo_2_vs_3_caracteres(self) -> None:
        """CP-11: Caso borde inferior del título: 2 caracteres falla y exactamente 3 aprueba."""
        with self.assertRaises(ErrorValidacionTarea):
            self.gestor.crear_tarea("AB")

        tarea_minima = self.gestor.crear_tarea("ABC")
        self.assertEqual(len(tarea_minima.titulo), 3)

    def test_cp12_limite_superior_longitud_titulo_100_vs_101_caracteres(self) -> None:
        """CP-12: Caso borde superior del título: 100 caracteres aprueba y 101 caracteres falla."""
        titulo_100 = "T" * 100
        tarea_maxima = self.gestor.crear_tarea(titulo_100)
        self.assertEqual(len(tarea_maxima.titulo), 100)

        titulo_101 = "T" * 101
        with self.assertRaises(ErrorValidacionTarea):
            self.gestor.crear_tarea(titulo_101)

    def test_cp13_limite_superior_longitud_descripcion_300_vs_301_caracteres(self) -> None:
        """CP-13: Caso borde superior de descripción: 300 caracteres aprueba y 301 falla."""
        desc_300 = "D" * 300
        tarea = self.gestor.crear_tarea("Validar descripción máxima", descripcion=desc_300)
        self.assertEqual(len(tarea.descripcion), 300)

        desc_301 = "D" * 301
        with self.assertRaises(ErrorValidacionTarea):
            self.gestor.crear_tarea("Descripción excedida", descripcion=desc_301)

    def test_cp14_operaciones_sobre_agenda_vacia(self) -> None:
        """CP-14: Caso borde de colección vacía al listar y generar resumen estadístico."""
        self.assertEqual(self.gestor.listar_tareas(), [])
        resumen = self.gestor.obtener_resumen()
        self.assertEqual(
            resumen,
            {
                "total": 0,
                "pendientes": 0,
                "en_progreso": 0,
                "completadas": 0,
                "alta_prioridad": 0,
            },
        )

    def test_cp15_normalizacion_espacios_y_minusculas_en_entradas(self) -> None:
        """CP-15: Caso borde de formato: recorte de espacios laterales y conversión de minúsculas."""
        tarea = self.gestor.crear_tarea(
            titulo="   Tarea con bordes espaciados   ",
            prioridad="  alta  ",
        )
        self.assertEqual(tarea.titulo, "Tarea con bordes espaciados")
        self.assertEqual(tarea.prioridad, Prioridad.ALTA)

        self.gestor.cambiar_estado_tarea(tarea.id_tarea, "  en_progreso ")
        self.assertEqual(tarea.estado, EstadoTarea.EN_PROGRESO)


if __name__ == "__main__":
    unittest.main(verbosity=2)
