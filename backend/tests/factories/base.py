# https://github.com/FactoryBoy/factory_boy/issues/468#issuecomment-1536373442
from typing import Generic, Type, TypeVar, get_args

import factory
from factory.base import FactoryMetaClass

T = TypeVar("T")


class BaseFactoryMeta(FactoryMetaClass):  # type: ignore
    def __new__(mcs, class_name, bases: list[Type], attrs):  # type: ignore
        orig_bases = attrs.get("__orig_bases__", [])
        for t in orig_bases:
            if t.__name__ == "BaseFactory" and t.__module__ == __name__:
                type_args = get_args(t)
                if len(type_args) == 1:
                    if "Meta" not in attrs:
                        attrs["Meta"] = type("Meta", (), {})
                    attrs["Meta"].model = type_args[0]
        return super().__new__(mcs, class_name, bases, attrs)


class BaseFactory(Generic[T], factory.Factory, metaclass=BaseFactoryMeta):  # type: ignore
    class Meta:
        abstract = True

    @classmethod
    def create(cls, **kwargs) -> T:  # type: ignore
        return super().create(**kwargs)  # type: ignore

    @classmethod
    def build(cls, **kwargs) -> T:  # type: ignore
        return super().build(**kwargs)  # type: ignore
