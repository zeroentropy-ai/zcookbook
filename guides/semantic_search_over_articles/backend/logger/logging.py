from coloredlogs import ColoredFormatter
import logging
import socket
import os


class CustomLogRecord(logging.LogRecord):
    """
    A custom log record class that extends logging.LogRecord.

    Attributes
    ----------
    hostname : str
        The hostname where the log record originated.
    """

    def __init__(self, *args, **kwargs):
        """
        Initialize the object with the hostname of the system.

        Parameters
        ----------
        *args : Variable length argument list.
        **kwargs : Keyword arguments.

        Returns
        -------
        None

        Notes
        -----
        This function initializes the object with the hostname of the system using the socket module.

        Raises
        ------
        None
        """
        super().__init__(*args, **kwargs)
        self.hostname = socket.gethostname()


def getLogger(name: str = "main", loglevel: str = "INFO", logdir: str = "./logs", stream=None, color_logs=True):
    """
    Get a logger object with custom settings and formatters.

    Parameters:
        name (str): Name of the logger.
        loglevel (str): Log level for the logger.
        logdir (str): Directory to store log files.
        stream (stream): Stream to write logs to.
        color_logs (bool): Whether to colorize logs.

    Returns:
        logger: A logger object with custom settings and formatters.
    """
    logging.setLogRecordFactory(CustomLogRecord)
    logger = logging.getLogger(name)
    logger.propagate = False

    if logger.handlers:
        return logger
    else:
        loglevel = getattr(logging, loglevel.upper(), logging.INFO)
        logger.setLevel(loglevel)

        log_format = "%(asctime)s | %(module)s | %(levelname)-8s | %(message)s [%(filename)s:%(lineno)s]"

        simple_formatter = logging.Formatter(log_format, datefmt="%Y-%m-%d %H:%M:%S")

        colored_formatter = ColoredFormatter(
            log_format,
            datefmt="%Y-%m-%d %H:%M:%S",
            level_styles={
                "critical": {"bold": True, "color": "red"},
                "debug": {"color": "green"},
                "error": {"color": "red"},
                "info": {"color": "white"},
                "notice": {"color": "magenta"},
                "spam": {"color": "green", "faint": True},
                "success": {"bold": True, "color": "green"},
                "verbose": {"color": "blue"},
                "warning": {"color": "yellow"},
            },
            field_styles={
                "asctime": {"color": "green"},
                "hostname": {"color": "magenta"},
                "levelname": {"bold": True, "color": "magenta"},
                "module": {"color": "blue"},
                "programname": {"color": "cyan"},
                "username": {"color": "yellow"},
            },
        )

        if not os.path.isdir(logdir):
            os.mkdir(logdir)

        fileHandler = logging.FileHandler(os.path.join(logdir, "logs.txt"))
        fileHandler.setLevel(logging.DEBUG)
        fileHandler.setFormatter(simple_formatter)

        streamHandler = logging.StreamHandler(stream=stream)
        streamHandler.setLevel(loglevel)
        if color_logs:
            streamHandler.setFormatter(colored_formatter)
        else:
            streamHandler.setFormatter(simple_formatter)

        logger.addHandler(fileHandler)
        logger.addHandler(streamHandler)

    return logger


# a simple usecase
if __name__ == "__main__":
    logger = getLogger(loglevel="DEBUG")
    logger.debug("A message only developers care about")
    logger.info("Curious users might want to know this")
    logger.warning("Something is wrong and any user should be informed")
    logger.error("Serious stuff, this is red for a reason")
    logger.critical("!OH NO everything is on fire")
