"""Import this module to invoke the interractive python debugger, ipydb, on any exception

  Resources:
    Based on http://stackoverflow.com/a/242531/623735

  Examples:
    >>> import debug
    >>> x=[][0]
""" 

# # from http://stackoverflow.com/a/242514/623735
# # Only works if you have a main function in your app
# if __name__ == '__main__':
#     try:
#         main()
#     except:
#         type, value, tb = sys.exc_info()
#         traceback.print_exc()
#         last_frame = lambda tb=tb: last_frame(tb.tb_next) if tb.tb_next else tb
#         frame = last_frame().tb_frame
#         ns = dict(frame.f_globals)
#         ns.update(frame.f_locals)
#         code.interact(local=ns)

import sys

def bug_info(type, value, tb):
    """Prints the traceback and invokes the ipython debugger on any exception
    
    References:
      http://stackoverflow.com/a/242531/623735
    """
    if hasattr(sys, 'ps1') or not sys.stderr.isatty():
        # We are in interactive mode or don't have a tty-like device, so we call the default hook
        sys.__excepthook__(type, value, tb)
    else:
        # TODO: Why not import pdb earlier, outside this function ?
        import traceback, ipdb
        # We are NOT in interactive mode, print the exception
        traceback.print_exception(type, value, tb)
        print
        # Start the debugger in post-mortem mode.
        # `ipdb.pm()` is deprecated so use `ipdb.post_mortem()` instead
        ipdb.post_mortem(tb)

# assign the `bug_info` function to the system exception hook/callback so it's called when there's an exception
sys.excepthook = bug_info
