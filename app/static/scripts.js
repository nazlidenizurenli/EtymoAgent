document.getElementById('wordForm').addEventListener('submit', function(event) {
    event.preventDefault();
    
    const word = document.getElementById('wordInput').value;

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
        document.getElementById('wordOutput').textContent = `Most similar word: ${data.most_similar_word}`;
        document.getElementById('etymologyOutput1').textContent = `Similarity score: ${data.similarity_score}`;
        document.getElementById('etymologyOutput2').textContent = `Origin language: ${data.origin_language}`;
        document.getElementById('etymologyOutput3').textContent = `Noun meaning: ${data.noun_meaning}`;
        document.getElementById('etymologyOutput4').textContent = `Adjective meaning: ${data.adj_meaning}`;
        document.getElementById('etymologyOutput5').textContent = `Verb meaning: ${data.verb_meaning}`;
        document.getElementById('responsePanel').style.display = 'block';
    });
});
