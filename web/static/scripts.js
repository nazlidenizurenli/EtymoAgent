document.getElementById('wordForm').addEventListener('submit', function(event) {
    event.preventDefault();
    
    const word = document.getElementById('wordInput').value;

    // Client-side validation
    if (!/^[a-zA-Z]+$/.test(word)) {
        alert('Please enter a valid English word (alphabetic characters only).');
        return;
    }
    
    fetch('/get_etymology', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: `word=${word}`
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            alert(data.error);
            return;
        }
        document.getElementById('wordOutput').textContent = data.word;
        document.getElementById('etymologyOutput').textContent = data.etymology;
        document.getElementById('responsePanel').style.display = 'block';
    });
});
