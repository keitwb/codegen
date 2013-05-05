
class RendererExtension(object):
    """
    An extension to the base renderer that will enhace it with additional
    functionality.  It only has two methods it can implement, ``pre_render`` and
    ``post_render``.  The latter is required since otherwise an extension
    wouldn't actually be able to change the output.  A separate instance of the
    extension class will be created for each template that is rendered, so it
    can store state on ``self`` in the ``pre_render`` method and it will be
    available to the ``post_render`` method for that same template but none
    others. 
    """
    def __init__(self, template):
        self.template = template

    def pre_render(self):
        pass

    def post_render(self, output):
        raise NotImplementedError("You must override post_render in the "
            "renderer extension class %s" % (self.__class__,))
        
