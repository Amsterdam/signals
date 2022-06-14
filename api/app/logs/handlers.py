# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2022 Gemeente Amsterdam
import sys

from logging import LogRecord, Handler


class ColoredHandler(Handler):
    terminator = "\n"
    output = None

    def __init__(self) -> None:
        """
        Obligatory call to the Handler init.
        Uses system output, not prints!
        """
        Handler.__init__(self)
        self.output = sys.stderr

    def yellow(self, message: str) -> str:
        return "\033[93m{}\033[0m".format(message)

    def red(self, message: str) -> str:
        return "\033[91m{}\033[0m".format(message)

    def blue(self, message: str) -> str:
        return "\033[96m{}\033[0m".format(message)

    def green(self, message: str) -> str:
        return "\033[92m{}\033[0m".format(message)

    def colorize(self, record: LogRecord) -> str:
        """
        Add the correct colour depending on the level of the LogRecord.
        :param record:
        :return:
        """
        message = self.format(record=record)

        if record.levelname in ["ERROR", "WARNING"]:
            return self.yellow(message=message)
        elif record.levelname == "CRITICAL":
            return self.red(message=message)
        elif record.levelname == "INFO":
            return self.blue(message=message)
        else:
            return self.green(message=message)

    def flush(self):
        """
        Flushes the stream. This forces the output to print the buffered
        content to the console.
        """
        self.acquire()

        try:
            if self.output and hasattr(self.output, "flush"):
                self.output.flush()
        finally:
            self.release()

    def emit(self, record: LogRecord):
        """
        Adds colour to the message output to infer priority. If this fails for
        some reason it will fallback to a regular message.

        If that fails there is still the built-in error handler of the emit.

        :param record:
        :return:
        """
        try:
            try:
                parsed_message = self.colorize(record=record)
            except Exception:
                print('error called')
                parsed_message = self.format(record=record)

            stream = self.output
            stream.write(parsed_message)
            stream.write(self.terminator)
            self.flush()
        except Exception:
            print('error2 called')
            self.handleError(record)
