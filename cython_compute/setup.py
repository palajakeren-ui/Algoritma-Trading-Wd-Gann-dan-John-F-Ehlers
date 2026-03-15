"""
Cython Compute Plane — Build Configuration
============================================

Build with: python setup.py build_ext --inplace
Or: pip install -e .

Produces:
  - ehlers_dsp.so / ehlers_dsp.pyd
  - gann_math.so / gann_math.pyd
  - execution_engine_c.so / execution_engine_c.pyd
  - signal_engine_c.so / signal_engine_c.pyd
  - risk_engine_c.so / risk_engine_c.pyd
  - connectors_c.so / connectors_c.pyd
  - forecast_engine_c.so / forecast_engine_c.pyd

Modules:
  - ehlers_dsp: John F. Ehlers DSP indicators (Fisher, MAMA, FAMA, etc.)
  - gann_math: W.D. Gann mathematical analysis (Square of 9, Fan, etc.)
  - execution_engine_c: Order execution and position management
  - signal_engine_c: Signal generation and fusion
  - risk_engine_c: Risk calculations (VaR, CVaR, Sharpe, etc.)
  - connectors_c: Broker/exchange data processing
  - forecast_engine_c: Price forecasting and predictions

Performance Targets:
  - Ehlers DSP: <50μs per indicator per bar
  - Gann Math: <20μs per calculation
  - Execution: <10μs per order operation
  - Signal: <5μs per signal calculation
  - Risk: <15μs per risk metric
  - Connectors: <5μs per data packet
  - Forecast: <20μs per forecast
"""
from setuptools import setup, Extension
from Cython.Build import cythonize
import numpy as np
import os
import sys

# Compiler optimization flags
extra_compile_args = ['-O3', '-ffast-math', '-march=native']
extra_link_args = []

# Windows-specific settings
if sys.platform == 'win32':
    extra_compile_args = ['/O2', '/fp:fast']
    extra_link_args = []

extensions = [
    # Original modules
    Extension(
        "ehlers_dsp",
        ["ehlers_dsp.pyx"],
        include_dirs=[np.get_include()],
        define_macros=[("NPY_NO_DEPRECATED_API", "NPY_1_7_API_VERSION")],
        extra_compile_args=extra_compile_args,
        extra_link_args=extra_link_args,
    ),
    Extension(
        "gann_math",
        ["gann_math.pyx"],
        include_dirs=[np.get_include()],
        define_macros=[("NPY_NO_DEPRECATED_API", "NPY_1_7_API_VERSION")],
        extra_compile_args=extra_compile_args,
        extra_link_args=extra_link_args,
    ),
    # New acceleration modules for core/
    Extension(
        "execution_engine_c",
        ["execution_engine_c.pyx"],
        include_dirs=[np.get_include()],
        define_macros=[("NPY_NO_DEPRECATED_API", "NPY_1_7_API_VERSION")],
        extra_compile_args=extra_compile_args,
        extra_link_args=extra_link_args,
    ),
    Extension(
        "signal_engine_c",
        ["signal_engine_c.pyx"],
        include_dirs=[np.get_include()],
        define_macros=[("NPY_NO_DEPRECATED_API", "NPY_1_7_API_VERSION")],
        extra_compile_args=extra_compile_args,
        extra_link_args=extra_link_args,
    ),
    Extension(
        "risk_engine_c",
        ["risk_engine_c.pyx"],
        include_dirs=[np.get_include()],
        define_macros=[("NPY_NO_DEPRECATED_API", "NPY_1_7_API_VERSION")],
        extra_compile_args=extra_compile_args,
        extra_link_args=extra_link_args,
    ),
    # Connector acceleration module
    Extension(
        "connectors_c",
        ["connectors_c.pyx"],
        include_dirs=[np.get_include()],
        define_macros=[("NPY_NO_DEPRECATED_API", "NPY_1_7_API_VERSION")],
        extra_compile_args=extra_compile_args,
        extra_link_args=extra_link_args,
    ),
    # Forecast acceleration module
    Extension(
        "forecast_engine_c",
        ["forecast_engine_c.pyx"],
        include_dirs=[np.get_include()],
        define_macros=[("NPY_NO_DEPRECATED_API", "NPY_1_7_API_VERSION")],
        extra_compile_args=extra_compile_args,
        extra_link_args=extra_link_args,
    ),
]

setup(
    name="cenayang_compute",
    version="2.0.0",
    description="Cenayang Market Cython Compute Plane — High-Performance Trading Engine",
    author="Trading System",
    ext_modules=cythonize(
        extensions,
        compiler_directives={
            "boundscheck": False,
            "wraparound": False,
            "cdivision": True,
            "nonecheck": False,
            "language_level": "3",
            "initializedcheck": False,
        },
    ),
    install_requires=[
        "numpy>=1.20.0",
        "cython>=0.29.0",
    ],
    python_requires=">=3.8",
)
