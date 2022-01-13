export async function getMessage(messageId) {
    let message = null;
    await $.ajax({
        url: `/api/messages/${messageId}`,
        type: 'GET',
        success: function(response) { message = response; },
        error: function() { message = null; }
    });
    return message;
}

export async function getUsers(startwith = '', page = 1) {
    let users = [];
    await $.ajax({
        url: `/api/users?startwith=${startwith}&page=${page}`,
        type: 'GET',
        success: function(response) { users = response.users; },
        error: function() { users = []; }
    });
    return users;
}

export async function getUser(userId) {
    let user = null;
    await $.ajax({
        url: `/api/users/${userId}`,
        type: 'GET',
        success: function(response) { 
            user = response; 
            delete user.password;
        },
        error: function() { user = null; }
    });
    return user;
}

export async function getChats(startwith = '', page = 1) {
    let chats = [];
    await $.ajax({
        url: `/api/chats?startwith=${startwith}&page=${page}`,
        type: 'GET',
        success: function(response) { chats = response.chats; },
        error: function() { chats = []; }
    });
    return chats;
}

export async function getChat(chatId) {
    let chat = null;
    await $.ajax({
        url: `/api/chats/${chatId}`,
        type: 'GET',
        success: function(response) { chat = response; },
        error: function() { chat = null; }
    });
    return chat;
}

export async function getChatMessages(chatId, page = 1) {
    let messages = null;
    await $.ajax({
        url: `api/messages/chat/${chatId}?page=${page}`,
        type: "GET",
        success: function(response) { messages = response.messages.reverse(); },
        error: function() { messages = []; }            
    });
    return messages;   
}

export async function getUnreadMessagesCount(chatId, userId) {
    let unreadMessagesCount = null;
    await $.ajax({
        url: `api/users/${userId}/chats/${chatId}/unread`,
        type: "GET",
        success: function(response) { unreadMessagesCount = response.messages.length; },          
    });
    return unreadMessagesCount;
}

export async function getUserChats(userId) {
    let chats = null;
    await $.ajax({
        url: `/api/users/${userId}/chats`,
        type: 'GET',
        success: function(response) { chats = response.chats; },
        error: function() { chats = []; }
    });
    return chats;    
}