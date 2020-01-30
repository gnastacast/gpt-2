var text_reader = {
    'text_buffer': [],
    'colored_buffer': [],
    'delay_buffer': [],
    'text': "",
    'colored': false,
    'delay':0.3,
    'current_idx': 0,

    'new_text_cb': function() {
        var output = document.getElementById('output');
        while(output.childElementCount > 20){
            output.removeChild(output.firstElementChild); 
        }
        var tElement = document.createElement('span');
        if(this.colored){
            tElement.classList.add('color');
        }
        output.appendChild(tElement);
        current_idx = 0
    },

    'reset': function() {
        this.text_buffer=[];
        this.colored_buffer=[];
        this.delay_buffer=[];
        this.text = "";
        this.colored = false;
        this.delay = 0.3,
        this.current_idx = 0;
    },

    'get_next_buffer_text': function() {
        this.text = this.text_buffer.shift();
        this.colored = this.colored_buffer.shift();
        this.delay = this.delay_buffer.shift();
        this.current_idx = 0;
        this.new_text_cb();
    },

    'get_next_word': function() {
        if(this.current_idx >= this.text.length){
            if(this.text_buffer.length){
                this.get_next_buffer_text();
                return this.get_next_word();
            }
            return ""
        }
        var current_text = this.text.slice(this.current_idx);
        var next_letter = current_text.search(/[^\s]/g);
        var next_space = current_text.slice(next_letter).search(/[\s]/g);
        if(next_letter < 0 || next_space < 0)
        {
            this.current_idx = this.text.length;
            return current_text;
        }
        this.current_idx = this.current_idx + next_letter + next_space;

        return current_text.slice(next_letter, next_letter + next_space)
    },

    'get_old_text': function() {
        return this.text.slice(0, this.current_idx);
    },

    'get_total_words': function() {
        var total = 0;
        if(this.text) total += this.text.split(/\s/g).length;
        for(var text of this.text_buffer) total += text.split(/\s/g).length;
        return total;
    },

    'add_text': function(new_text, is_colored=false, delay=1, instant=false) {
        delay = Math.max(delay, 0.5)
        if(!instant)
        {
            this.text_buffer.push(new_text);
            this.colored_buffer.push(is_colored);
            this.delay_buffer.push(delay);
        }
        else
        {
            this.text_buffer = [new_text];
            this.colored_buffer = [is_colored];
            this.delay_buffer = [delay];
            this.get_next_buffer_text();
        }
    }
};


        // if(this.colored){
            
        //     beg[0].classList.add('color');
        //     end[0].classList.add('color');
        // }
        //  else{
        //     beg[0].classList.remove('color');
        //     end[0].classList.remove('color');
        // }

document.addEventListener("DOMContentLoaded", function(){
    //connect to the socket server.
    var socket = io.connect('http://' + document.domain + ':' + location.port);
    socket.on('generated_text', function(msg) {
        var data = msg.text.split('<|endoftext|>')[0];
        if(msg.instant) {
            text_reader.add_text(data, msg.color, msg.delay);
        } else {
            text_reader.add_text(data, msg.color, msg.delay);
        }
    });

    socket.on('fade', function(msg) {
        if(msg.value) document.getElementById('fader').classList.add('on');
        else          document.getElementById('fader').classList.remove('on');
    });

    socket.on('clear', function(msg) {
        text_reader.reset();
        while(output.childElementCount > 0){
            output.removeChild(output.firstChild); 
        }
    });

    function reader_thread(){
        var beg = document.getElementsByClassName('begin');
        var mid = document.getElementsByClassName('middle');
        var end = document.getElementsByClassName('end');
        var out = document.getElementById('output');
        var t = text_reader.get_next_word();
        var split = 4;
        if(t.length < 2) {
            split = 0;
        } else if(t.length < 6) {
            split = 1;
        }
        else if(t.length < 10) {
            split = 2;
        }
        else if(t.length < 14) {
            split = 3;
        }
        beg[0].textContent = t.slice(0        , split);
        mid[0].textContent = t.slice(split    , split + 1);
        end[0].textContent = t.slice(split + 1, t.length);
        var pause = 300;
        if(text_reader.get_total_words() > 0)
            pause =  text_reader.delay * 1000 / text_reader.get_total_words();
        if(out.lastChild != null)
            out.lastChild.textContent = text_reader.get_old_text();
        setTimeout(reader_thread, pause);
    } reader_thread();

});