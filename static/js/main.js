document.addEventListener('DOMContentLoaded', function() {
    const uploadForm = document.getElementById('uploadForm');
    const queryForm = document.getElementById('queryForm');
    const answerDiv = document.getElementById('answer');

    uploadForm.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const formData = new FormData();
        const fileInput = document.getElementById('pdfFile');
        formData.append('file', fileInput.files[0]);

        try {
            const response = await fetch('/upload', {
                method: 'POST',
                body: formData
            });
            
            const result = await response.json();
            if (response.ok) {
                alert('दस्तऐवज यशस्वीरित्या अपलोड केला गेला!');
                fileInput.value = '';
            } else {
                alert('त्रुटी: ' + result.error);
            }
        } catch (error) {
            alert('अपलोड करताना त्रुटी आली: ' + error);
        }
    });

    queryForm.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const question = document.getElementById('question').value;

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
                alert('त्रुटी: ' + result.error);
            }
        } catch (error) {
            alert('प्रश्न विचारताना त्रुटी आली: ' + error);
        }
    });
});
