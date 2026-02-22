"""
Cython Compute Plane — Build Configuration

Build with: python setup.py build_ext --inplace
Or: pip install -e .

Produces:
  - ehlers_dsp.so / ehlers_dsp.pyd
  - gann_math.so / gann_math.pyd
"""
from setuptools import setup, Extension
from Cython.Build import cythonize
import numpy as np

extensions = [
    Extension(
        "ehlers_dsp",
        ["ehlers_dsp.pyx"],
        include_dirs=[np.get_include()],
        define_macros=[("NPY_NO_DEPRECATED_API", "NPY_1_7_API_VERSION")],
    ),
    Extension(
        "gann_math",
        ["gann_math.pyx"],
        include_dirs=[np.get_include()],
        define_macros=[("NPY_NO_DEPRECATED_API", "NPY_1_7_API_VERSION")],
    ),
]

setup(
    name="cenayang_compute",
    version="1.0.0",
    description="Cenayang Market Cython Compute Plane — Ehlers DSP + Gann Math",
    ext_modules=cythonize(
        extensions,
        compiler_directives={
            "boundscheck": False,
            "wraparound": False,
            "cdivision": True,
            "nonecheck": False,
            "language_level": "3",
        },
    ),
)
