=======
Condent
=======

``condent`` is a quick hack to reindent containers the way that I like them.

It's mostly (currently entirely) for Python, but due to similar object literal
syntaxes it should work for other languages by chance, and is easily
generalizable to actually work with them in case it doesn't. I suspect over
time I'll add actual support for the other languages I use on a semi-regular
basis (mostly Ruby and JS).

It can fix basic things like:
    * Spacing
    * Moving something that fits on a single line onto one line
    * Moving something that doesn't onto multiple lines
    * Fixing indentation of multiple line containers

What it won't (shouldn't) do is change the semantics of your code. If it does,
please open a ticket.


Installation
------------

Install with ``pip install condent`` and you'll find a ``condent`` executable
installed.


Usage
-----

Sample invocation and output is:

.. code-block:: console

    $ echo 'd = {"foo":"bar","baz":"quux"}' | condent 
    d = {"foo" : "bar", "baz" : "quux"}

    $ condent <<EOF
    the_dict = {
    foo:bar,
    baz:quux,
    spam:eggs}'
    EOF
    the_dict = {foo : bar, baz : quux, spam : eggs}

    $ condent <<EOF
        an_already_indented_dict_that_does_not_fit_on_one_line = {
    foo:bar, baz:quux,
    spam:eggs}
    EOF
        an_already_indented_dict_that_does_not_fit_on_one_line = {
            foo : bar,
            baz : quux,
            spam : eggs,
        }

You can see full usage info with ``condent -h``.


Usage With Vim
--------------

The main reason this exists is to use with ``vim`` and its ``equalprg`` option.

To do so, put something like ``autocmd FileType python set equalprg=condent``
in your ``.vimrc`` or in an ``ftplugin`` file. You can then use it with ``=``
(see ``:help =`` for details).

I've tried a number of ``vim`` indent scripts over the past few years but never
found one that worked right. Maybe it exists and it's my (settings') fault,
but rather than figure out whether that's the case it was easy enough to throw
together in an afternoon.

You also might be interested in my ``ftplugin`` file for `Python
<https://github.com/Julian/dotfiles/blob/master/.vim/ftplugin/python.vim>`_
which has some more of what I do with this, like auto-reindenting when
inserting closing characters.


Style
-----

It *should* be ``pep8`` compliant with one exception. 

I like my ``dict`` key and value to be symmetric around the ``:``. Depending on
interpretation this might be in violation of ``pep8`` recommending avoiding
extra whitespace, but I've been doing it forever and I like the way it looks,
not to mention I've seen a ton of code that does it this way as well. To
illustrate, this will produce ``{"foo" : "bar"}`` rather than producing
``{"foo": "bar"}``. If you really don't like that you can disable it with the
command line flag ``--no-symmetric-colon``. There are a bunch of other
subjective style choices that can be toggled with command line flags.


Adding Features
---------------

Like many similar things, this is likely going to be a continual WIP. Like I
said, I use things like this daily, so as I find bugs or desired features I'll
probably fix or add them.

There are a few specific things I have in mind which will probably get added
in the next couple of days. If you have others, feel free to send a pull
request. Even if I don't like or use the style you desire, if it's sane enough
;) it probably be merged as an option anyhow.
