from __future__ import annotations

from typing import TYPE_CHECKING, Any, NamedTuple, TypeVar

from typing_extensions import Protocol, Type, get_args, runtime_checkable

if TYPE_CHECKING:
    from pydantic import BaseModel

ModelT = TypeVar("ModelT")


@runtime_checkable
class PluginProtocol(Protocol[ModelT]):  # pragma: no cover
    def to_pydantic_model_class(self, model_class: Type[ModelT], **kwargs: Any) -> Type[BaseModel]:  # pragma: no cover
        """
        Given a model_class T, convert it to a subclass of the pydantic BaseModel
        """

    @staticmethod
    def is_plugin_supported_type(value: Any) -> bool:
        """
        Given a value of indeterminate type, determine if this value is supported by the plugin.
        """

    def from_pydantic_model_instance(self, model_class: Type[ModelT], pydantic_model_instance: BaseModel) -> ModelT:
        """
        Given an instance of a pydantic model created using a plugin's 'to_pydantic_model_class',
        return an instance of the class from which that pydantic model has been created.

        This class is passed in as the 'model_class' kwarg.
        """

    def to_dict(self, model_instance: ModelT) -> dict[str, Any]:
        """
        Given an instance of a model supported by the plugin, return a dictionary of serializable values.
        """

    def from_dict(self, model_class: Type[ModelT], **kwargs: Any) -> ModelT:
        """
        Given a class supported by this plugin and a dict of values, create an instance of the class
        """


def get_plugin_for_value(value: Any, plugins: list[PluginProtocol]) -> PluginProtocol | None:
    """Helper function to returns a plugin to handle a given value, if any plugin supports it"""
    if plugins:
        if value and isinstance(value, (list, tuple)):
            value = value[0]
        if get_args(value):
            value = get_args(value)[0]
        for plugin in plugins:
            if plugin.is_plugin_supported_type(value):
                return plugin
    return None


class PluginMapping(NamedTuple):
    plugin: PluginProtocol
    model_class: Any

    def value_to_model_instance(self, value: BaseModel | list[BaseModel] | tuple[BaseModel, ...]) -> Any:
        """
        Given a value generated by plugin, return instance of original class.
        Also can accept list or tuple of values.
        """

        def get_instance(value: BaseModel) -> Any:
            return self.plugin.from_pydantic_model_instance(self.model_class, pydantic_model_instance=value)

        if isinstance(value, (list, tuple)):
            return [get_instance(item) for item in value]
        return get_instance(value)
