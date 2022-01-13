export function toUTC(date) {
    return new Date(
        date.getUTCFullYear(), date.getUTCMonth(), date.getUTCDate(), 
        date.getUTCHours(), date.getUTCMinutes(), date.getUTCSeconds()
    );
}

export function fromUTCString(s) {
    return new Date(Date.parse(s) - new Date().getTimezoneOffset() * 60 * 1000);
}

export function fromLocaleString(s) {
    return new Date(Date.parse(s) + new Date().getTimezoneOffset() * 60 * 1000);
}

export function timeSince(date) {
    let seconds = Math.floor((new Date() - date) / 1000);
    let interval = seconds / 31536000;
    if (interval > 1) 
        return Math.floor(interval) + " year(s) ago";
    interval = seconds / 2592000;
    if (interval > 1) 
        return Math.floor(interval) + " month(s) ago";
    interval = seconds / 86400;
    if (interval > 1) 
        return Math.floor(interval) + " day(s) ago";
    interval = seconds / 3600;
    if (interval > 1) 
        return Math.floor(interval) + " hour(s) ago";
    interval = seconds / 60;
    if (interval > 1) 
        return Math.floor(interval) + " minute(s) ago";
    return "just now";
}


export function diffNow(date) {
    const dt = new Date(date);
    const diff = Math.floor((toUTC(new Date()) -  new Date(date)) / 1000);
    if (diff >= 365 * 24 * 60 * 60)
        return strftime("%b %d %Y", dt);
    else if (diff >= 7 * 24 * 60 * 60)
        return strftime("%b %d", dt);
    else if (diff >= 24 * 60 * 60)
        return strftime("%a", dt);
    else
        return strftime("%H:%M", dt);
}


export function getDateGroupTime(unixTimestamp) {
    let date = new Date(unixTimestamp);
    let seconds = Math.floor((new Date() - date) / 1000);
    if (seconds / (2592000 * 3) > 1) 
        return strftime("%B %o, %Y", date);
    return strftime("%B %o", date);
}