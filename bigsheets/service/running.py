import atexit

exiting = False


@atexit.register
def set_exiting():
    global exiting
    exiting = True


def exit_if_asked():
    if exiting:
        raise Exiting


class Exiting(Exception):
    pass


def exit():
    global exiting
    exiting = True
