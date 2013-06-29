var server;
var try_count = 10;
var connected = false;
var host = "localhost"
var port = "1234"
function connect() {
    if (try_count-- <= 0) {
        $("#status").html('Error Connecting')
        return;
    }
    server = new WebSocket("ws://" + host + ":" + port);
    server.onopen = function(e) { 
        connected = true;
        $("#status").html("Disconnect")
        server.onclose = function(e) { 
            $("#status").html('Reconnect');  
        }; 
    };
    server.onclose = function(e) { 
        connect();
    };
    server.onmessage = function(e) {
        add_request(e.data);
    };
}

function toggle_connection() {
    if (connected) {
        server.close()
        connected = false;
        $("#status").html('Reconnect')
    }

    else {
        connect();
    }
}

function add_request(data) {
    request = JSON.parse(data);
    partials = {
        'name_value': $("#name-value-template").html()
    }
    template = $("#request-template").html()
    var output = Mustache.render(template, request, partials);
    $("#requests").prepend(output);
}

function init() {
    $("#show-controls").on("click", function() {
        $("#controls").slideToggle();
    });

    $("#status").on("click", toggle_connection);
    $("#update-response").on("click", update_response);
    connect();
}

function update_response() {
    var response = $("#response").val();
    $.post("/update-response", {response: response}, function victory() {
        $("#controls").slideToggle();
    });
}


//this should modified to make it work in i.e.
$(document).ready(init);
