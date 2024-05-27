$(document).ready(function() {

    // Toggle the chat window display
    $('#chat-widget-button').click(function() {
        $('#chatbot-window').toggle();
    });
 $('#close-chatbot').click(function() {
        $('#chatbot-window').hide();
    });
    // Send message when the 'Send' button is clicked
    $('#chatbot-send-button').click(function() {
        var message = $('#chatbot-input').val().trim();
        if (message) {
            // Append the message to the chat window
            $('#chat-messages').append('<div class="chat-message user-message">' + message + '</div>');
            // Clear the input field after sending
            $('#chatbot-input').val('');
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
    $('#chatbot-input').on('keypress', function(e) {
        if (e.which === 13) { // Enter key
            $('#chatbot-send-button').click();
            return false; // Prevent the default behavior of the Enter key
        }
    });
});
