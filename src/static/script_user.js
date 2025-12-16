document.addEventListener('DOMContentLoaded', () => {
  // Wait for DOM to be fully loaded
  const productSelect = document.getElementById('product-select');
  const selectedProductDisplay = document.getElementById('selected-product-display');
  const queryTextarea = document.getElementById('query-textarea');
  const flagResponseCheckbox = document.getElementById('flag-response');
  const submitQueryBtn = document.getElementById('submit-query-btn');
  const queryResponseArea = document.getElementById('query-response-area'); // Get the response display area

  console.log('working');
  productSelect.addEventListener('change', () => {
      selectedProductDisplay.textContent = productSelect.value;
      console.log('Selected Product:', productSelect.value);
  });

  // Handle form submission
  submitQueryBtn.addEventListener('click', () => {
      const selectedProduct = productSelect.value;
      const queryText = queryTextarea.value.trim();
      const flagForReview = flagResponseCheckbox.checked;

      if (selectedProduct === 'None') {
          alertMessage('Please select a product before submitting your query.', 'warning');
          return;
      }

      if (queryText === '') {
          alertMessage('Please type your query before submitting.', 'warning');
          return;
      }

      // Display user's query in the chat-like interface
      appendMessage(queryText, 'user');
      console.log("Testing by me");
      console.log(selectedProduct);

      if (selectedProduct === 'Product A') {
          // Show loading state for the button
          submitQueryBtn.disabled = true;
          const originalButtonText = submitQueryBtn.textContent;
          submitQueryBtn.textContent = 'Processing...';
          console.log("A is working");

          const namespace="x200_namespace"

          fetch(`/generate-response?namespace=${encodeURIComponent(namespace)}&query=${encodeURIComponent(queryText)}`, {
            method: 'POST'
        })
              .then(response => {
                  if (!response.ok) {
                      // Try to get error message from backend if available
                      return response.json().then(errData => {
                          throw new Error(errData.detail || `HTTP error! Status: ${response.status}`);
                      }).catch(() => { // Fallback if response is not JSON or no detail
                          throw new Error(`HTTP error! Status: ${response.status}`);
                      });
                  }
                  return response.json();
              })
              .then(data => {
                  console.log('Response from backend:', data);
                  // Display the answer in the dedicated area instead of an alert
                  if (queryResponseArea) {
                      appendMessage(`Answer for ${data.response}`, 'bot');
                  }
                  // Optionally clear the query textarea after successful processing
                  queryTextarea.value = ''; // Clear the textarea
              })
              .catch(error => {
                  console.error('Error fetching query for Product A:', error);
                  console.log(queryText);
                  alertMessage(`Error: ${error.message}`, 'warning');

                  // If there's an error, you might want to remove the last user message or add an error message to the chat.
                  // For now, we'll just keep the alert.
              })
              .finally(() => {
                  submitQueryBtn.disabled = false;
                  submitQueryBtn.textContent = originalButtonText;
              });
          return;
      }

      if (selectedProduct === 'Product B') {
          // Show loading state for the button
          submitQueryBtn.disabled = true;
          const originalButtonText = submitQueryBtn.textContent;
          submitQueryBtn.textContent = 'Processing...';

          console.log("B is working");
          fetch(`/process-product-query?product_name=${encodeURIComponent('product_b')}&query=${encodeURIComponent(queryText)}`)
              .then(response => {
                  if (!response.ok) {
                      // Try to get error message from backend if available
                      return response.json().then(errData => {
                          throw new Error(errData.detail || `HTTP error! Status: ${response.status}`);
                      }).catch(() => { // Fallback if response is not JSON or no detail
                          throw new Error(`HTTP error! Status: ${response.status}`);
                      });
                  }
                  return response.json();
              })
              .then(data => {
                  console.log('Response from backend:', data);
                  // Display the answer in the dedicated area instead of an alert
                  if (queryResponseArea) {
                      appendMessage(`Answer for ${data.product_name_processed}: ${data.answer}`, 'bot');
                  }
                  // Optionally clear the query textarea after successful processing
                  queryTextarea.value = ''; // Clear the textarea
              })
              .catch(error => {
                  console.error('Error fetching query for Product A:', error);
                  alertMessage(`Error: ${error.message}`, 'warning');
                  // If there's an error, you might want to remove the last user message or add an error message to the chat.
                  // For now, we'll just keep the alert.
              })
              .finally(() => {
                  submitQueryBtn.disabled = false;
                  submitQueryBtn.textContent = originalButtonText;
              });
          return;
      }   
      
      if (selectedProduct === 'Product C') {
          // Show loading state for the button
          submitQueryBtn.disabled = true;
          const originalButtonText = submitQueryBtn.textContent;
          submitQueryBtn.textContent = 'Processing...';

          fetch(`/process-product-query?product_name=${encodeURIComponent('product_c')}&query=${encodeURIComponent(queryText)}`)
              .then(response => {
                  if (!response.ok) {
                      // Try to get error message from backend if available
                      return response.json().then(errData => {
                          throw new Error(errData.detail || `HTTP error! Status: ${response.status}`);
                      }).catch(() => { // Fallback if response is not JSON or no detail
                          throw new Error(`HTTP error! Status: ${response.status}`);
                      });
                  }
                  return response.json();
              })
              .then(data => {
                  console.log('Response from backend:', data);
                  // Display the answer in the dedicated area instead of an alert
                  if (queryResponseArea) {
                      appendMessage(`Answer for ${data.product_name_processed}: ${data.answer}`, 'bot');
                  }
                  // Optionally clear the query textarea after successful processing
                  queryTextarea.value = ''; // Clear the textarea
              })
              .catch(error => {
                  console.error('Error fetching query for Product A:', error);
                  alertMessage(`Error: ${error.message}`, 'warning');
                  // If there's an error, you might want to remove the last user message or add an error message to the chat.
                  // For now, we'll just keep the alert.
              })
              .finally(() => {
                  submitQueryBtn.disabled = false;
                  submitQueryBtn.textContent = originalButtonText;
              });
          return;
      }

    //   console.log('Form Submitted!');
    //   console.log('Selected Product:', selectedProduct);
    //   console.log('Query:', queryText);
    //   console.log('Flag for Review:', flagForReview);

      // Simulate a bot response for other products
    //   appendMessage(`Your query for "${selectedProduct}" has been received: "${queryText}". We'll get back to you shortly.`, 'bot');
    //   queryTextarea.value = ''; // Clear the textarea
    //   flagResponseCheckbox.checked = false; // Optionally clear the flag checkbox

      alertMessage('Query submitted successfully!', 'success');
  });

  function appendMessage(message, sender) {
      const messageElement = document.createElement('div');
      messageElement.classList.add('p-3', 'rounded-lg', 'max-w-xs', 'lg:max-w-md', 'mb-4', 'shadow');

      if (sender === 'user') {
          messageElement.classList.add('bg-blue-500', 'text-white', 'ml-auto'); // Align right for user
      } else {
          messageElement.classList.add('bg-gray-200', 'text-gray-800', 'mr-auto'); // Align left for bot
      }
      messageElement.textContent = message;
      queryResponseArea.appendChild(messageElement);
      queryResponseArea.scrollTop = queryResponseArea.scrollHeight; // Auto-scroll to the latest message
  }

  function alertMessage(message, type) {
      let alertDiv = document.getElementById('custom-alert');
      if (!alertDiv) {
          alertDiv = document.createElement('div');
          alertDiv.id = 'custom-alert';
          alertDiv.className = 'fixed top-4 left-1/2 transform -translate-x-1/2 px-6 py-3 rounded-lg shadow-lg text-white font-semibold z-50 transition-all duration-300 ease-in-out opacity-0';
          document.body.appendChild(alertDiv);
      }

      alertDiv.textContent = message;
      alertDiv.classList.remove('bg-green-500', 'bg-orange-500', 'opacity-0');

      if (type === 'success') {
          alertDiv.classList.add('bg-green-500');
      } else if (type === 'warning') {
          alertDiv.classList.add('bg-orange-500');
      }

      setTimeout(() => {
          alertDiv.classList.add('opacity-100');
      }, 10);

      setTimeout(() => {
          alertDiv.classList.remove('opacity-100');
          setTimeout(() => {
              alertDiv.classList.add('opacity-0');
          }, 300);
      }, 3000);
  }
});