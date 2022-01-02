function timeSince(date) {
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

function getDateGroupTime(unixTimestamp) {
    let date = new Date(unixTimestamp);
    let seconds = Math.floor((new Date() - date) / 1000);
    if (seconds / (2592000 * 3) > 1) 
        return strftime("%B %o, %Y", date);
    return strftime("%B %o", date);
}


function getGlobalState() {
    return JSON.parse(localStorage.getItem(STORAGE_GLOBAL_STATE_NAME));
}

function setGlobalState(state) {
    localStorage.setItem(STORAGE_GLOBAL_STATE_NAME, JSON.stringify(state));
}

function getCookie(name) {
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    if (parts.length === 2) return parts.pop().split(';').shift();
}


function ordinalLast(string) {
    return string.charCodeAt(0) % 10;
}


function toUTC(date) {
    return new Date(
        date.getUTCFullYear(), date.getUTCMonth(), date.getUTCDate(), 
        date.getUTCHours(), date.getUTCMinutes(), date.getUTCSeconds()
    );    
}

function fromUTCString(s) {
    return new Date(Date.parse(s) - new Date().getTimezoneOffset() * 60 * 1000);
}

function fromLocaleString(params) {
    return new Date(Date.parse(s) + new Date().getTimezoneOffset() * 60 * 1000);
}