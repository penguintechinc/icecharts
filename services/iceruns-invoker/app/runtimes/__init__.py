"""Runtime implementations for all supported languages."""

from app.action_runtime import RuntimeManager
from app.runtimes.bash_runtime import BashRuntime
from app.runtimes.go_runtime import GoRuntime
from app.runtimes.nodejs_runtime import NodeJSRuntime
from app.runtimes.powershell_runtime import PowerShellRuntime
from app.runtimes.python_runtime import PythonRuntime
from app.runtimes.ruby_runtime import RubyRuntime
from app.runtimes.rust_runtime import RustRuntime

# Register all runtimes
RuntimeManager.register_runtime("python3.13", PythonRuntime)
RuntimeManager.register_runtime("nodejs", NodeJSRuntime)
RuntimeManager.register_runtime("go", GoRuntime)
RuntimeManager.register_runtime("ruby", RubyRuntime)
RuntimeManager.register_runtime("bash", BashRuntime)
RuntimeManager.register_runtime("powershell", PowerShellRuntime)
RuntimeManager.register_runtime("rust", RustRuntime)

__all__ = [
    "PythonRuntime",
    "NodeJSRuntime",
    "GoRuntime",
    "RubyRuntime",
    "BashRuntime",
    "PowerShellRuntime",
    "RustRuntime",
    "RuntimeManager",
]
