class TTSError(Exception):
    """Base class for TTS errors."""


class ModelLoadError(TTSError):
    pass


class GenerationError(TTSError):
    pass


class InvalidInputError(TTSError):
    pass
