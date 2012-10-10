=======
Condent
=======

``condent`` is a quick hack to reindent containers the way that I like them.

This is what I use as my ``equalprg`` in ``vim``. It *should* be ``pep8``
compliant with the exception that I like my ``dict`` key and value to be
symmetric around the ``:``, which might be considered clashing with ``pep8``
discouraging additional whitespace. So, this will produce ``{"foo" : "bar"}``
rather than ``{"foo": "bar"}`` (this can be disabled with
``--no-symmetric-colon``).
