function unselectActiveChat() {
    $('.active-chat')[0]?.classList.remove('active-chat');
}

function getCookie(name) {
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    if (parts.length === 2) return parts.pop().split(';').shift();
}

$(document).ready(async function() {
    let data = {
        currentUserId: getCookie('userID'),
        chats: {byId: {}, listIds: []},
        users: {}, settings: {}, messages: {}
    };
    for (let chat of $('.chat')) {
        let chatId = parseInt(chat.getAttribute('data-id'));
        data.chats.byId[chatId] = {id: chatId};
        data.chats.byId[chatId].type = chat.classList[1];
        data.chats.byId[chatId].title = chat.querySelector('.info > .title > h3').textContent;
        await $.get(`api/messages/chat/${chatId}`)
        .then(function(response) {
            data.messages[chatId] = response.messages;
        });
        await $.get(`api/users/${data.currentUserId}/chats/${chatId}/unread`)
        .then(function(response) {
            data.chats.byId[chatId].unreadMessagesCount = response.messages.length;
        });
        await $.get(`api/chats/${chatId}`).then(function(response) {
            data.chats.byId[chatId].members = response.members;
        });
        for (let memberId of data.chats.byId[chatId].members) {
            await $.get(`api/users/${memberId}`).then(function(response) {
                data.users[memberId] = {id: response.id, username: response.username};
            });
        }         
        data.chats.listIds.push(chatId);
    }
    localStorage.setItem('global-state', JSON.stringify(data));
});


$('.chat').click(function() {
    unselectActiveChat();
    this.classList.add('active-chat');
});

$(document).on('keydown', function(e) {
    if (e.key == "Escape") unselectActiveChat();
  });