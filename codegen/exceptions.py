
class CodegenError(Exception):
    pass

class InvalidConfigurationError(CodegenError):
    pass

class ModelPathError(CodegenError):
    pass

class TemplateCompilationError(CodegenError):
    pass

class TemplateRenderError(CodegenError):
    pass
