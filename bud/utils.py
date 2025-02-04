import os.path
import time
from typing import *

from mcdreforged.api.decorator import new_thread
from mcdreforged.api.rtext import *
from mcdreforged.api.types import ServerInterface, PluginServerInterface, MCDReforgedLogger


gl_server: PluginServerInterface = ServerInterface.get_instance().as_plugin_server_interface()
TRANSLATION_KEY_PREFIX = gl_server.get_self_metadata().id
LOG_FILE = os.path.join(gl_server.get_data_folder(), 'logs', '{id}.log'.format(id=gl_server.get_self_metadata().id))
unnamed_thread_count = 0


class BloomingBlossomLogger(MCDReforgedLogger):
    __verbosity = False
    __instance: Optional["BloomingBlossomLogger"] = None

    @classmethod
    def should_log_debug(cls, option=None):
        if cls.__verbosity:
            return True
        return super().should_log_debug(option=option)

    @classmethod
    def set_verbose(cls, verbosity: bool):
        cls.__verbosity = verbosity
        cls.get_instance().debug('Verbose mode enabled')

    @classmethod
    def get_instance(cls):
        if cls.__instance is None:
            cls.__instance = cls(plugin_id=gl_server.get_self_metadata().id)
        return cls.__instance

    def set_file(self, file_name: str):
        self.unload_file()
        super().set_file(file_name=file_name)

    def unload_file(self):
        if self.file_handler is not None:
            self.removeHandler(self.file_handler)
            self.file_handler.close()
            self.file_handler = None


def tr(translation_key: str, *args, with_prefix=True, **kwargs) -> RTextMCDRTranslation:
    if with_prefix and not translation_key.startswith(TRANSLATION_KEY_PREFIX):
        translation_key = f"{TRANSLATION_KEY_PREFIX}.{translation_key}"
    return gl_server.rtr(translation_key, *args, **kwargs).set_translator(ntr)


def ntr(translation_key: str, *args, with_prefix: bool = True, language: Optional[str] = None,
        allow_failure: bool = True, fallback_language: bool = None, **kwargs) -> str:
    try:
        return gl_server.tr(
            translation_key, *args, language=language, fallback_language=None, allow_failure=False, **kwargs
        )
    except (KeyError, ValueError):
        return gl_server.tr(
            translation_key, *args, language='en_us', allow_failure=allow_failure, **kwargs
        )


def to_camel_case(name_with_underscore: str):
    return ''.join([element.capitalize() for element in name_with_underscore.split('_')])


# This could not be used in solo plugin
def named_thread(thread_name: Union[Callable, str, None] = None):
    prefix = f'{gl_server.get_self_metadata().name}_'.replace(' ', '')
    if isinstance(thread_name, Callable):
        # Directly called without bracket
        unnamed_thread_name = prefix + to_camel_case(thread_name.__name__)
        return new_thread(unnamed_thread_name)(thread_name)
    else:
        def wrap(func):
            nonlocal thread_name
            if thread_name is None:
                thread_name = to_camel_case(func.__name__)
            if not isinstance(thread_name, str):
                thread_name = str(thread_name)
            if not thread_name.startswith(prefix):
                thread_name = prefix + thread_name
            return new_thread(thread_name)(func)
        return wrap


def get_multi_layer_key(data: Any, keys: list):
    if len(keys) == 0:
        return data
    if not isinstance(data, dict):
        return None
    keys = keys.copy()
    next_layer = data[keys.pop(0)]
    if len(keys) == 0:
        return next_layer
    return get_multi_layer_key(next_layer, keys)


def ensure_dir(folder: str):
    if os.path.isfile(folder):
        raise FileExistsError('Data folder structure is occupied by existing file')
    if not os.path.isdir(folder):
        os.makedirs(folder)


ensure_dir(os.path.dirname(LOG_FILE))
logger = BloomingBlossomLogger.get_instance()
logger.set_file(LOG_FILE)
