import GLOBAL from './main.js';
import { toUTC } from '../utils/date.js';


export class Message {
    constructor(chatId) {
        this.chatId = chatId;
    }

    createData(text) {
        return {
            chat_id: this.chatId, text: text,
            created_at: strftime("%Y-%m-%dT%H:%M:%S", toUTC(new Date()))
        };
    }

    get event() { return 'message'; }

    send(text) {
        GLOBAL.socket.emit(this.event, this.createData(text));        
    }
}


export class ServiceMessage extends Message {
    createData(...data) {
        const message = super.createData(...data);
        message.is_service = true;
        return message;
    }
}


export class ReplyMessage extends Message {
    constructor(chatId, toMessageId) {
        super(chatId);
        this.toMessageId = toMessageId;
    }

    createData(...data) {
        const message = super.createData(...data);
        message.reply_to = this.toMessageId;
        return message;
    }
}

export class EditMessage extends Message {
    constructor(chatId, messageId) {
        super(chatId);
        this.messageId = messageId;
    }

    createData(text) {
        return {
            message_id: this.messageId, text: text, 
            edited_at: strftime("%Y-%m-%dT%H:%M:%S", toUTC(new Date()))
        };
    }

    get event() { return 'edit_message'; }
}