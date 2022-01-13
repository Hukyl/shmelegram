import { getCookie } from '../utils/storage.js';


export default class State {
    #state;

    constructor() {
        this.load();
        if (Object.keys(this.#state || {}).length === 0) {
            this.empty();
            this.save();
        }
    }

    getMessage(chatId, messageId) {        
        return this.#state.messages[chatId]?.find(msg => msg.id === messageId);
    }

    getChatMessages(chatId) {
        return this.#state.messages[chatId];
    }

    getChatOrdering() {
        return [...this.#state.chats.listIds].sort((a, b) => {
            let last1 = this.getLastMessage(a);
            let last2 = this.getLastMessage(b);
            return Date.parse(last2?.created_at || 0) - Date.parse(last1?.created_at || 0);
        });
    }

    getUserOrdering(chatId) {
        return [...this.getChat(chatId).members].sort((a, b) => {
            let user1 = this.getUser(a);
            let user2 = this.getUser(b);
            return Date.parse(user1.last_online || 0) - Date.parse(user2.last_online || 0);
        });
    }

    getLastMessage(chatId) {
        const messages = this.getChatMessages(chatId);
        if (!messages) return null;
        return messages[messages.length - 1];
    }

    getUser(userId) {
        return this.#state.users[userId];
    }

    getUsers() {
        return Object.values(this.#state.users);
    } 

    getChat(chatId) {
        return this.#state.chats.byId[chatId];
    }

    getPrivateChatByUser(userId) {
        if (userId === this.currentUserId) return false;
        return Object.values(this.#state.chats.byId).filter((chat) => {
            return (
                chat.type === 'private' && 
                chat.members.includes(this.currentUserId) && 
                chat.members.includes(userId)
            )
        })[0]
    }

    userExists(userId) {
        return this.#state.users.hasOwnProperty(userId);
    }

    messageExists(chatId, messageId) {
        return this.getMessage(chatId, messageId) ? true : false;
    }

    removeChat(chatId) {
        delete this.#state.chats.byId[chatId];
        delete this.#state.messages[chatId];
        this.#state.chats.listIds.splice(
            this.#state.chats.listIds.findIndex(id => id === chatId),
            1
        )
    }

    removeMember(chatId, userId) {
        const members = this.#state.chats.byId[chatId]?.members;
        if (!members) return false;
        const userIndex = members.findIndex(id => id === userId);
        if (!userIndex) return false;
        members.splice(userIndex, 1);
        return true;
    }

    appendChat(chatData) {
        this.#state.chats.byId[chatData.id] = chatData;
        this.#state.chats.listIds.push(chatData.id);
        this.#state.messages[chatData.id] = [];
    }

    appendMember(chatId, userId) {
        if (!this.userExists(userId)) return false;
        const members = this.#state.chats.byId[chatId]?.members;
        if (!members) return false;
        members.push(userId);
        return true;
    }

    appendUser(userData) {
        this.#state.users[userData.id] = userData;
    }

    insertMessage(messageData) {
        const chatMessages = this.getChatMessages(messageData.chat);
        if (!chatMessages) return false;
        chatMessages.unshift(messageData);
        return true;
    }

    appendMessage(messageData) {
        const chatMessages = this.getChatMessages(messageData.chat);
        if (!chatMessages) return false;
        chatMessages.push(messageData);
        return true;
    } 

    unshiftMessages(messages) {
        for (let i = messages.length - 1; i >= 0; i--)
            this.insertMessage(messages[i]);
    }

    pushMessages(messages) {
        for (let message of messages)
            this.appendMessage(message);
    }

    removeMessage(chatId, messageId) {
        const chatMessages = this.getChatMessages(chatId);
        if (!chatMessages) return false;
        const messageArrayIndex = chatMessages.findIndex(
            msg => msg.id == messageId
        );
        if (messageArrayIndex === -1) return false;
        chatMessages.splice(messageArrayIndex, 1); 
        return true;
    }

    getOnlineMembers(chatId) {
        const chat = this.getChat(chatId);
        let count = 0;
        for (let memberId of chat.members) {
            if (this.getUser(memberId).last_online === null)
                count++;
        }
        return count;
    }

    get currentUserId() { return this.#state.currentUserId; }

    load() {
        this.#state = JSON.parse(localStorage.getItem('global-state'));
    }

    save() {
        localStorage.setItem('global-state', JSON.stringify(this.#state));        
    }

    empty() {
        this.#state = {
            currentUserId: parseInt(getCookie('userID')),
            chats: {byId: {}, listIds: []},
            users: {}, messages: {}
        };
    }

    extend(data) {
        this.#state = {...this.#state, ...data};
        this.save();
    }
}