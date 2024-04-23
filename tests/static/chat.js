console.log("hello world!");


$(document).ready(function() {
    // Add event listener for the send button
    $('#send-button').click(function() {
        // Get the message from the input field
        var message = $('#chat-input').val().trim();

        // Check if the message is not empty
        if (message) {
            // Append the message to the chat window
            $('#chat-messages').append('<div class="chat-message user-message">' + message + '</div>');
            $('#chat-input').val(''); // Clear the input field

            // Send the message to the Rasa server using AJAX
            sendMessageToRasa(message);
        }
    });

    // Function to send the message to Rasa and handle the response
    function sendMessageToRasa(message) {
        $.ajax({
            url: 'http://localhost:5005/webhooks/rest/webhook', // Endpoint for the Rasa server
            type: 'POST',
            contentType: 'application/json',
            data: JSON.stringify({
                sender: 'user', // Sender ID, can be any string
                message: message // The message text
            }),
            success: function(response) {
                // Handle the successful response here
                if (response && response.length > 0) {
                    // Append the bot's response to the chat window
                    $('#chat-messages').append('<div class="chat-message bot-message">' + response[0].text + '</div>');
                    // Scroll to the bottom of the chat messages
                    $('#chat-messages').scrollTop($('#chat-messages')[0].scrollHeight);
                }
            },
            error: function(xhr, status, error) {
                // Handle errors here, such as displaying an error message
                console.error('An error occurred:', error);
            }
        });
    }

    // Add event listener for the Enter key in the input field
    $('#chat-input').on('keypress', function(e) {
        if (e.which === 13) { // Enter key
            $('#send-button').click();
            return false; // Prevent the default behavior of the Enter key
        }
    });
});
