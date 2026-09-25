"""mock-server —— 读取 mocks.json 静态契约的轻量本地 HTTP Mock 服务。"""

from .contract import Contract, ContractError, Route, load_contract

__version__ = "0.1.0"

__all__ = ["Contract", "ContractError", "Route", "__version__", "load_contract"]
