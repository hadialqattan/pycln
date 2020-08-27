"""
Pycln node utility.
"""
from dataclasses import dataclass
from typing import List, Optional
import ast


@dataclass
class BaseImport:

    """Custom `_ast.AST` node. for Python < 3.8"""

    lineno: int
    col_offset: int
    end_lineno: int  # Support end_lineno for Python < 3.8.
    names: List[ast.alias]


@dataclass
class Import(BaseImport):

    """Custom `ast.Import` node. for Python < 3.8"""

    def __hash__(self):
        return hash(self.lineno + self.col_offset + self.end_lineno)


@dataclass
class ImportFrom(BaseImport):

    """Custom `ast.ImportFrom` node. for Python < 3.8"""

    module: Optional[str]
    level: int

    def __hash__(self):
        return hash(self.lineno + self.col_offset + self.end_lineno)
