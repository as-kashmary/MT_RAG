document.addEventListener('DOMContentLoaded', () => {

    // Get references to DOM elements
    const fileInput = document.getElementById('file-upload-input');
    // const fileNameInput = document.getElementById('file-name'); // Removed
    const fileTypeSelect = document.getElementById('file-type');
    const uploadButton = document.getElementById('upload-button');
    const messageDisplay = document.getElementById('message-display');
    const selectedFileInfo = document.getElementById('selected-file-info');
    const selectedFileNameDisplay = document.getElementById('selected-file-name-display');
    const selectedFileSizeDisplay = document.getElementById('selected-file-size-display');
    const loadingSpinner = document.getElementById('loading-spinner');
    const buttonText = document.getElementById('button-text');

    let selectedFile = null; // Variable to store the selected file object

    // Function to update message display
    function showMessage(text, isSuccess) {
        messageDisplay.textContent = text;
        if (isSuccess) {
            messageDisplay.classList.remove('text-red-600');
            messageDisplay.classList.add('text-green-600');
        } else {
            messageDisplay.classList.remove('text-green-600');
            messageDisplay.classList.add('text-red-600');
        }
    }

    // Handler for when a file is selected
    fileInput.addEventListener('change', (event) => {
        selectedFile = event.target.files[0]; // Get the first selected file
        if (selectedFile) {
            // Display selected file info
            selectedFileNameDisplay.textContent = selectedFile.name;
            selectedFileSizeDisplay.textContent = (selectedFile.size / 1024 / 1024).toFixed(2);
            selectedFileInfo.classList.remove('hidden');

            // Pre-fill file name input (without extension) - REMOVED
            // const nameWithoutExtension = selectedFile.name.split('.').slice(0, -1).join('.');
            // fileNameInput.value = nameWithoutExtension; // REMOVED

            // Attempt to infer file type from extension
            const extension = selectedFile.name.split('.').pop().toLowerCase();
            let inferredType = '';
            if (['png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp'].includes(extension)) {
                inferredType = 'image';
            } else if (['pdf'].includes(extension)) {
                inferredType = 'pdf';
            } else if (['doc', 'docx'].includes(extension)) {
                inferredType = 'docs';
            } else if (['csv', 'json', 'txt'].includes(extension)) {
                inferredType = 'dataset';
            } else if (['xls', 'xlsx'].includes(extension)) {
                inferredType = 'spreadsheet';
            } else if (['ppt', 'pptx'].includes(extension)) {
                inferredType = 'presentation';
            } else if (['db', 'sql'].includes(extension)) { // Example for database files
                inferredType = 'database';
            }
            fileTypeSelect.value = inferredType;
        } else {
            // Hide file info if no file is selected
            selectedFileInfo.classList.add('hidden');
            // fileNameInput.value = ''; // REMOVED
            fileTypeSelect.value = '';
        }
        showMessage(''); // Clear any previous messages
    });

    // Clear messages on input changes
    // fileNameInput.addEventListener('input', () => showMessage('')); // REMOVED
    fileTypeSelect.addEventListener('change', () => showMessage(''));

    // Handler for the upload button click
    uploadButton.addEventListener('click', async () => {
        // const fileName = fileNameInput.value.trim(); // REMOVED
        const fileType = fileTypeSelect.value;
        const admin_name = document.getElementById("admin-name").value;
        const productName = document.getElementById("product-name").value;
        const file_name= selectedFile.name;

        // Basic validation
        if (!selectedFile || !fileType || !admin_name || !productName) {
            showMessage('Please complete all fields and select a file.', false);
            return;
        }
        // if (!fileName) { // REMOVED
        // //     showMessage('Please enter a file name.', false); // REMOVED
        // //     return; // REMOVED
        // // } // REMOVED
        if (!fileType) {
            showMessage('Please select a file type.', false);
            return;
        }

        // Show loading indicator
        uploadButton.disabled = true; // Disable button
        uploadButton.classList.add('opacity-60', 'cursor-not-allowed');
        loadingSpinner.classList.remove('hidden');
        buttonText.textContent = 'Uploading...';

        // Simulate an API call for file upload
        console.log('Simulating file upload...');
        // console.log('File Name:', fileName); // REMOVED - using selectedFile.name instead
        console.log('Original File Name:', selectedFile.name);
        console.log('File Type:', fileType);
        console.log('Selected File:', selectedFile);

        // Simulate network delay
        const formData = new FormData();
        formData.append("admin_name", admin_name);
        formData.append("product_name", productName);
        formData.append("file_type", fileType);
        formData.append("uploaded_file", selectedFile);
        formData.append("file_name", selectedFile.name);

        try {
            const response = await fetch("/file/upload", {
            method: "POST",
            body: formData
            });

            const result = await response.json();

            if (response.ok) {
            showMessage(result.message, true);
            } else {
            showMessage(result.detail || "Upload failed.", false);
            }
        } catch (error) {
            showMessage("Error uploading file: " + error.message, false);
        } finally {
            uploadButton.disabled = false;
            loadingSpinner.classList.add('hidden');
            buttonText.textContent = 'Upload File';
            fileInput.value = '';
            fileTypeSelect.value = '';
            selectedFileInfo.classList.add('hidden');
            selectedFile = null;
        }
    });
});