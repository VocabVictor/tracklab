"""Module import/loading utilities and vendor package management."""

import importlib
import importlib.util
import sys
import threading
import types
from importlib import import_module
from typing import Any, Callable, Dict, List, Optional, Tuple, Union
from types import ModuleType

# Global variables for module management
_not_importable: List[str] = []

# Pre-import common modules
np = None  # Will be loaded lazily
pd_available = False  # Will be set based on pandas availability




class LazyModuleState:
    """State management for lazy module loading."""
    
    def __init__(self, module: types.ModuleType) -> None:
        self.module = module
        self.load_started = False
        self.lock = threading.RLock()

    def load(self) -> None:
        """Load the module if not already loaded."""
        with self.lock:
            if self.load_started:
                return
            self.load_started = True
            assert self.module.__spec__ is not None
            assert self.module.__spec__.loader is not None
            self.module.__spec__.loader.exec_module(self.module)
            self.module.__class__ = types.ModuleType

            # Set the submodule as an attribute on the parent module
            # This enables access to the submodule via normal attribute access.
            parent, _, child = self.module.__name__.rpartition(".")
            if parent:
                parent_module = sys.modules[parent]
                setattr(parent_module, child, self.module)


class LazyModule(types.ModuleType):
    """A module that loads lazily when first accessed."""
    
    def __getattribute__(self, name: str) -> Any:
        # Special handling for __lazy_module_state__ to avoid infinite recursion
        if name == "__lazy_module_state__":
            return object.__getattribute__(self, name)
        
        try:
            state = object.__getattribute__(self, "__lazy_module_state__")
            state.load()
        except AttributeError:
            # If __lazy_module_state__ doesn't exist, just return the attribute
            pass
        
        return object.__getattribute__(self, name)

    def __setattr__(self, name: str, value: Any) -> None:
        # Special handling for __lazy_module_state__ to avoid infinite recursion
        if name == "__lazy_module_state__":
            object.__setattr__(self, name, value)
            return
            
        try:
            state = object.__getattribute__(self, "__lazy_module_state__")
            state.load()
        except AttributeError:
            # If __lazy_module_state__ doesn't exist, just set the attribute
            pass
        
        object.__setattr__(self, name, value)

    def __delattr__(self, name: str) -> None:
        try:
            state = object.__getattribute__(self, "__lazy_module_state__")
            state.load()
        except AttributeError:
            # If __lazy_module_state__ doesn't exist, just delete the attribute
            pass
        
        object.__delattr__(self, name)


def import_module_lazy(name: str) -> types.ModuleType:
    """Import a module lazily, only when it is used.

    Inspired by importlib.util.LazyLoader, but improved so that the module loading is
    thread-safe. Circular dependency between modules can lead to a deadlock if the two
    modules are loaded from different threads.
    """
    spec = importlib.util.find_spec(name)
    if spec is None:
        raise ImportError(f"No module named {name}")
    
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    
    # Set the lazy state before changing the class
    object.__setattr__(module, "__lazy_module_state__", LazyModuleState(module))
    module.__class__ = LazyModule
    
    return module


def get_module(
    name: str,
    required: Optional[Union[str, bool]] = None,
    lazy: bool = True,
) -> Any:
    """Return module or None. Absolute import is required.

    Args:
        name: The absolute name of the module to import.
        required: If True, raise ImportError if module is not found.
                 If string, display that message if module is not found.
        lazy: If True, use lazy loading.

    Returns:
        The imported module, or None if not found and not required.
    """
    if name in _not_importable:
        return None
    
    if name in sys.modules:
        return sys.modules[name]
    
    try:
        if lazy:
            return import_module_lazy(name)
        else:
            return import_module(name)
    except ImportError:
        if required:
            if isinstance(required, str):
                raise ImportError(required)
            else:
                raise ImportError(f"No module named {name}")
        
        _not_importable.append(name)
        return None


def get_optional_module(name: str) -> Optional[ModuleType]:
    """Get module if available, otherwise return None."""
    return get_module(name)


class ImportMetaHook:
    """Meta hook for intercepting imports and running callbacks."""
    
    def __init__(self) -> None:
        self.modules: Dict[str, ModuleType] = dict()
        self.on_import: Dict[str, list] = dict()

    def add(self, fullname: str, on_import: Callable) -> None:
        """Add a callback to run when a module is imported."""
        self.on_import.setdefault(fullname, []).append(on_import)

    def install(self) -> None:
        """Install this hook in sys.meta_path."""
        sys.meta_path.insert(0, self)  # type: ignore

    def uninstall(self) -> None:
        """Remove this hook from sys.meta_path."""
        sys.meta_path.remove(self)  # type: ignore

    def find_module(
        self, fullname: str, path: Optional[str] = None
    ) -> Optional["ImportMetaHook"]:
        """Find module and return self if we have callbacks for it."""
        if fullname in self.on_import:
            return self
        return None

    def find_spec(
        self, fullname: str, path: Optional[str] = None, target: Optional[ModuleType] = None
    ) -> Optional[Any]:
        """Find module spec for newer Python versions."""
        if fullname in self.on_import:
            return None
        return None

    def load_module(self, fullname: str) -> ModuleType:
        """Load module and run callbacks."""
        if fullname in self.modules:
            return self.modules[fullname]
        
        # Import the module normally
        module = import_module(fullname)
        self.modules[fullname] = module
        
        # Run callbacks
        for callback in self.on_import.get(fullname, []):
            callback()
        
        return module

    def get_modules(self) -> Tuple[str, ...]:
        """Get all tracked module names."""
        return tuple(self.modules)

    def get_module(self, module: str) -> ModuleType:
        """Get a specific tracked module."""
        return self.modules[module]


# Global import hook instance
_import_hook: Optional[ImportMetaHook] = None


def add_import_hook(fullname: str, on_import: Callable) -> None:
    """Add an import hook that runs a callback when a module is imported."""
    global _import_hook
    if _import_hook is None:
        _import_hook = ImportMetaHook()
        _import_hook.install()
    _import_hook.add(fullname, on_import)


# Initialize common modules
def _initialize_common_modules() -> None:
    """Initialize commonly used modules."""
    global np, pd_available
    
    np = get_module("numpy")
    pandas_module = get_module("pandas")
    pd_available = pandas_module is not None


# Initialize on module load
_initialize_common_modules()


__all__ = [
    "LazyModuleState",
    "LazyModule",
    "import_module_lazy",
    "get_module",
    "get_optional_module",
    "ImportMetaHook",
    "add_import_hook",
    "np",
    "pd_available",
]