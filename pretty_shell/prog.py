# Sourced from this thread: https://stackoverflow.com/questions/32080382/using-click-progressbar-with-multiprocessing-in-python/37502830
# Authored by StackOverflow User "Khrall" (https://stackoverflow.com/users/4945524/khrall)

import time
from typing import Dict

import click
from click._termui_impl import ProgressBar as ClickProgressBar, BEFORE_BAR
from click._compat import term_len


class ProgressBar(ClickProgressBar):
    def render_progress(self, in_collection=False):
        # This is basically a copy of the default render_progress with the addition of in_collection
        # param which is only used at the very bottom to determine how to echo the bar
        from click.termui import get_terminal_size

        if self.is_hidden:
            return

        buf = []
        # Update width in case the terminal has been resized
        if self.autowidth:
            old_width = self.width
            self.width = 0
            clutter_length = term_len(self.format_progress_line())
            new_width = max(0, get_terminal_size()[0] - clutter_length)
            if new_width < old_width:
                buf.append(BEFORE_BAR)
                buf.append(" " * self.max_width)
                self.max_width = new_width
            self.width = new_width

        clear_width = self.width
        if self.max_width is not None:
            clear_width = self.max_width

        buf.append(BEFORE_BAR)
        line = self.format_progress_line()
        line_len = term_len(line)
        if self.max_width is None or self.max_width < line_len:
            self.max_width = line_len

        buf.append(line)
        buf.append(" " * (clear_width - line_len))
        line = "".join(buf)
        # Render the line only if it changed.

        if line != self._last_line and not self.is_fast():
            self._last_line = line
            click.echo(line, file=self.file, color=self.color, nl=in_collection)
            self.file.flush()
        elif in_collection:
            click.echo(self._last_line, file=self.file, color=self.color, nl=in_collection)
            self.file.flush()


class ProgressBarCollection(object):
    def __init__(self, bars: Dict[str, ProgressBar], bar_template=None, width=None):
        self.bars = bars
        if bar_template or width:
            for bar in self.bars.values():
                if bar_template:
                    bar.bar_template = bar_template
                if width:
                    bar.width = width

    def __enter__(self):
        self.render_progress()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.render_finish()

    def render_progress(self, clear=False):
        if clear:
            self._clear_bars()
        for bar in self.bars.values():
            bar.render_progress(in_collection=True)

    def render_finish(self):
        for bar in self.bars.values():
            bar.render_finish()

    def update(self, bar_name: str, n_steps: int):
        self.bars[bar_name].make_step(n_steps)
        self.render_progress(clear=True)

    def _clear_bars(self):
        for _ in range(0, len(self.bars)):
            click.echo('\x1b[1A\x1b[2K', nl=False)


def progressbar_collection(bars: Dict[str, ProgressBar]):
    return ProgressBarCollection(bars, bar_template="%(label)s  [%(bar)s]  %(info)s", width=36)