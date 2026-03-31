# TypeScript 风格 TypeScript 注释 Python typing 指南

> 参考: Google TypeScript 风格 + Python typing 最佳实践

## 1. 基础类型标注

### 正确 ❌ (应该是 ✅)

```python
# ❌ 不好的写法
def process(data):
    return data.get("result")

# ✅ 好的写法
def process(data: dict[str, Any]) -> Any:
    return data.get("result")
```

### 基础类型

```python
def greet(name: str) -> str:
    return f"Hello, {name}"

def add(a: int, b: int) -> int:
    return a + b

def is_valid(flag: bool) -> bool:
    return flag
```

## 2. 复杂类型

### 列表、元组、字典

```python
from typing import List, Dict, Tuple, Optional, Union

# 列表
def get_names() -> List[str]:
    return ["Alice", "Bob"]

# 元组（固定长度）
def get_point() -> Tuple[float, float]:
    return (1.0, 2.0)

# 字典
def get_config() -> Dict[str, Union[str, int]]:
    return {"name": "app", "version": 1}

# 联合类型
def parse_value(value: Union[str, int, float]) -> str:
    return str(value)
```

### Optional（可选值）

```python
from typing import Optional

# Optional 等价于 Union[T, None]
def find_user(user_id: int) -> Optional[str]:
    if user_id > 0:
        return "found"
    return None
```

### Callable（函数类型）

```python
from typing import Callable

def apply(func: Callable[[int, int], int], a: int, b: int) -> int:
    return func(a, b)
```

## 3. 数据类（推荐）

```python
from dataclasses import dataclass

@dataclass
class User:
    name: str
    age: int
    email: Optional[str] = None

@dataclass
class VideoMetadata:
    path: str
    duration: float
    width: int
    height: int
    fps: float = 30.0
```

## 4. 泛型

```python
from typing import TypeVar, Generic, List

T = TypeVar("T")

class Stack(Generic[T]):
    def __init__(self) -> None:
        self._items: List[T] = []

    def push(self, item: T) -> None:
        self._items.append(item)

    def pop(self) -> Optional[T]:
        return self._items.pop() if self._items else None
```

## 5. Protocol（结构子类型）

```python
from typing import Protocol

class Drawable(Protocol):
    def draw(self) -> None:
        ...

    def get_bounds(self) -> Tuple[int, int, int, int]:
        ...

# 使用
def render(obj: Drawable) -> None:
    obj.draw()
```

## 6. 常用类型别名

```python
# 项目内类型别名
from typing import Alias

Timestamp = float
FrameNumber = int
VideoPath = str
JSON = Dict[str, Any]
```

## 7. TypeGuard（类型守卫）

```python
from typing import TypeGuard

def is_string_list(val: List[object]) -> TypeGuard[List[str]]:
    return all(isinstance(x, str) for x in val)
```

## 8. TypeVar 约束

```python
from typing import TypeVar

T = TypeVar("T", bound="BaseClass")

def get_first(items: List[T]) -> Optional[T]:
    return items[0] if items else None
```

## 9. Docstring 类型标注

```python
def calculate_distance(x1: float, y1: float, x2: float, y2: float) -> float:
    """
    计算两点间的欧几里得距离。
    
    Args:
        x1: 第一个点的 x 坐标
        y1: 第一个点的 y 坐标
        x2: 第二个点的 x 坐标
        y2: 第二个点的 y 坐标
    
    Returns:
        两点间的距离
    """
    return ((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5
```

## 10. 常见错误

### ❌ 避免使用 `Any` 除非必要

```python
# ❌ 滥用 Any
def process(data: Any) -> Any:
    ...

# ✅ 使用具体类型或 Union
def process(data: Union[str, bytes]) -> dict[str, Any]:
    ...
```

### ❌ 不要忘记返回类型

```python
# ❌ 没有返回类型
def get_default():
    return "default"

# ✅ 有返回类型
def get_default() -> str:
    return "default"
```

## 11. 类型检查配置

项目使用 mypy，配置见 `.mypy.ini`。

运行类型检查：
```bash
mypy app/
```

---

*参考: [Google TypeScript Style Guide](https://google.github.io/styleguide/tsguide.html) 和 [Python typing 文档](https://docs.python.org/3/library/typing.html)*
