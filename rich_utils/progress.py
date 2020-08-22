from rich.progress import Progress, ProgressColumn, BarColumn, Text


def ema(x, mu=None, alpha=0.3):
    """
    Exponential moving average: smoothing to give progressively lower
    weights to older values.
    Parameters
    ----------
    x  : float
        New value to include in EMA.
    mu  : float, optional
        Previous EMA value.
    alpha  : float, optional
        Smoothing factor in range [0, 1], [default: 0.3].
        Increase to give more weight to recent values.
        Ranges from 0 (yields mu) to 1 (yields x).
    """
    return x if mu is None else (alpha * x) + (1 - alpha) * mu


class SmartTimeRemainingColumn(ProgressColumn):

    max_refresh = 0.5
    avg_elapsed_seconds = 0
    avg_remaining_seconds = 0

    def __init__(self, *args, **kwargs):
        self.smoothing = kwargs.get("smoothing", 0.3)
        del kwargs["smoothing"]
        super().__init__(*args, **kwargs)

    def format_seconds(self, seconds):
        hours, remainder = divmod(seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        if hours:
            return f"{hours:>02.0f}h:{minutes:>02.0f}m"
        else:
            return f"{minutes:>02.0f}m:{seconds:>02.0f}s"

    def render(self, task):
        remaining = task.time_remaining
        if remaining is None:
            return Text("--m:--s<--m:--s", style="progress.remaining")
        self.avg_elapsed_seconds = ema(task.elapsed, self.avg_elapsed_seconds, self.smoothing)
        self.avg_remaining_seconds = ema(remaining, self.avg_remaining_seconds, self.smoothing)
        elapsed_delta = self.format_seconds(self.avg_elapsed_seconds)
        remaining_delta = self.format_seconds(self.avg_remaining_seconds)
        return Text(f"{elapsed_delta}<{remaining_delta}", style="progress.remaining")


class ItemsPerSecondColumn(ProgressColumn):

    max_refresh = 0.5
    avg_speed = 0

    def __init__(self, *args, **kwargs):
        self.smoothing = kwargs.get("smoothing", 0.3)
        kwargs.pop("smoothing", None)
        self.unit = kwargs.get("unit", "items")
        kwargs.pop("unit", None)
        super().__init__(*args, **kwargs)

    def render(self, task):
        speed = task.speed
        if speed is None:
            return Text(f"0{self.unit}/s", style="progress.remaining")
        self.avg_speed = ema(speed, self.avg_speed, self.smoothing)
        return Text(f"{self.avg_speed:>3.2f}{self.unit}/s", style="progress.remaining")


class GenericProgress(Progress):

    def __init__(self, *args, **kwargs):
        self.smoothing = kwargs.get("smoothing", 0.3)
        kwargs.pop("smoothing", None)
        self.unit = kwargs.get("unit", "items")
        kwargs.pop("unit", None)
        self.bar_width = kwargs.get("bar_width", 56)
        kwargs.pop("bar_width", None)
        if not args:
            args = ("[progress.description]{task.description}", BarColumn(bar_width=self.bar_width),
                    "[progress.percentage]{task.percentage:>3.0f}%",
                    "[progress.percentage]({task.completed}/{task.total})",
                    SmartTimeRemainingColumn(smoothing=self.smoothing),
                    ItemsPerSecondColumn(smoothing=self.smoothing, unit=self.unit))
        super().__init__(*args, **kwargs)
