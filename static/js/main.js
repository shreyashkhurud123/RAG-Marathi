document.addEventListener('DOMContentLoaded', function() {
    const queryForm = document.getElementById('queryForm');
    const answerDiv = document.getElementById('answer');

    queryForm.addEventListener('submit', async function(e) {
        e.preventDefault();

        const question = document.getElementById('question').value;
        answerDiv.textContent = 'प्रश्नाचे उत्तर शोधत आहे...';

        try {
            const response = await fetch('/query', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ question: question })
            });

            const result = await response.json();
            if (response.ok) {
                answerDiv.textContent = result.answer;
            } else {
                answerDiv.textContent = 'त्रुटी: ' + result.error;
            }
        } catch (error) {
            answerDiv.textContent = 'प्रश्न विचारताना त्रुटी आली: ' + error;
        }
    });
});