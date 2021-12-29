from datetime import datetime

from shmelegram import app



@app.template_filter('ordinal_last')
def ordinal_last(title: str) -> str:
    return ord(title) % 10


@app.template_filter('diff_now')
def diff_now(dt: datetime) -> str:
    diff = datetime.utcnow() - dt
    if diff.days >= 365:
        return dt.strftime("%b %d %Y")
    elif diff.days >= 7:
        return dt.strftime("%b %d")
    elif diff.days >= 1:
        return dt.strftime("%a")
    else:
        return dt.strftime("%H:%M")
