"""Concurrencia: locks por clave para serializar operaciones del mismo recurso.

Sirve para cerrar la ventana TOCTOU entre "¿existe?" y "guardar" (A08) cuando llegan envíos
concurrentes con la misma clave (evaluado + fecha).

Ámbito: un único proceso (el despliegue es de instancia única en servidor interno). NO garantiza
exclusión entre múltiples instancias/procesos; eso exigiría un lock distribuido o una restricción
de unicidad en el almacén (Notion no la ofrece).
"""
from __future__ import annotations

import asyncio
import weakref


class KeyedLocks:
    """Devuelve un `asyncio.Lock` por clave; el mismo por clave mientras esté en uso."""

    def __init__(self) -> None:
        # WeakValueDictionary: el lock se libera de memoria cuando ya nadie lo retiene.
        self._locks: weakref.WeakValueDictionary[str, asyncio.Lock] = (
            weakref.WeakValueDictionary()
        )

    def get(self, clave: str) -> asyncio.Lock:
        # Sin `await` entre lectura y escritura: atómico en el loop de asyncio.
        lock = self._locks.get(clave)
        if lock is None:
            lock = asyncio.Lock()
            self._locks[clave] = lock
        return lock
