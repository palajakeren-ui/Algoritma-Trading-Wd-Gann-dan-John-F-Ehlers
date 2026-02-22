"""
Cython Compute Plane — Python Fallback Wrapper

Attempts to import compiled Cython modules.
Falls back to pure-Python NumPy implementations if Cython is not compiled.

Usage:
    from cython_compute import ehlers, gann
    fisher, trigger = ehlers.fisher_transform(high, low, period=10)
    levels = gann.gann_square_of_9(67500.0)
"""
from loguru import logger

try:
    from . import ehlers_dsp as ehlers
    from . import gann_math as gann
    CYTHON_AVAILABLE = True
    logger.info("[Compute Plane] Cython modules loaded — ultra-low-latency mode")
except ImportError:
    CYTHON_AVAILABLE = False
    logger.warning("[Compute Plane] Cython not compiled — using Python fallback")
    logger.warning("[Compute Plane] Run: cd cython_compute && python setup.py build_ext --inplace")

    # Fallback: pure Python wrappers that delegate to existing core modules
    class _EhlersFallback:
        """Fallback Ehlers DSP using existing core.ehlers_engine"""
        def __getattr__(self, name):
            try:
                from core.ehlers_engine import EhlersEngine
                engine = EhlersEngine.__new__(EhlersEngine)
                if hasattr(engine, name):
                    return getattr(engine, name)
            except ImportError:
                pass
            raise AttributeError(f"Ehlers DSP function '{name}' not available")

    class _GannFallback:
        """Fallback Gann math using existing core.gann_engine"""
        def __getattr__(self, name):
            try:
                from core.gann_engine import GannEngine
                engine = GannEngine.__new__(GannEngine)
                if hasattr(engine, name):
                    return getattr(engine, name)
            except ImportError:
                pass
            raise AttributeError(f"Gann math function '{name}' not available")

    ehlers = _EhlersFallback()
    gann = _GannFallback()

__all__ = ['ehlers', 'gann', 'CYTHON_AVAILABLE']
