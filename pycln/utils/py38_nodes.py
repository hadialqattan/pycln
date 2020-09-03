"""
Pycln node utility.
"""
import ast
from dataclasses import dataclass
from typing import List, Optional


@dataclass
class BaseImport:

    """Custom `_ast.AST` node. for Python < 3.8"""

    lineno: int
    col_offset: int

    # Support end_lineno for Python < 3.8.
    end_lineno: int

    #: Support end_col_offset for Python < 3.8.
    #:
    #: Won't be calculated correctly only if threre is a semicolon on the same line.
    #: ex:- `import os; import time; import foo`
    end_col_offset: int

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
