from core._native_loader import load_native_core


_native = load_native_core()
SynapseSTDP = _native.SynapseSTDP

__all__ = ["SynapseSTDP"]
