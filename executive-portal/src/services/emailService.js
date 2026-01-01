/**
 * EmailJS Service for sending emails from the frontend.
 * Uses EmailJS free tier for automatic email sending.
 * 
 * Setup Instructions:
 * 1. Go to https://www.emailjs.com/ and create a free account
 * 2. Add an email service (Gmail, Outlook, etc.)
 * 3. Create an email template with variables: {{to_email}}, {{admin_username}}, {{temp_password}}, {{company_name}}
 * 4. Copy your Service ID, Template ID, and Public Key
 * 5. Update the constants below
 */

import emailjs from '@emailjs/browser';

// EmailJS Configuration - Replace with your actual values from emailjs.com
const EMAILJS_SERVICE_ID = 'service_xxxxxxx';  // Your EmailJS service ID
const EMAILJS_TEMPLATE_ID = 'template_xxxxxxx'; // Your EmailJS template ID
const EMAILJS_PUBLIC_KEY = 'xxxxxxxxxxxxxxx';   // Your EmailJS public key

// Initialize EmailJS
emailjs.init(EMAILJS_PUBLIC_KEY);

/**
 * Send admin invitation email using EmailJS
 * @param {Object} params - Email parameters
 * @param {string} params.toEmail - Recipient email address
 * @param {string} params.adminUsername - Admin username
 * @param {string} params.tempPassword - Temporary password
 * @param {string} params.companyName - Company name
 * @returns {Promise<boolean>} - True if email sent successfully
 */
export const sendAdminInviteEmail = async ({ toEmail, adminUsername, tempPassword, companyName }) => {
    try {
        const templateParams = {
            to_email: toEmail,
            admin_username: adminUsername,
            temp_password: tempPassword,
            company_name: companyName,
        };

        const response = await emailjs.send(
            EMAILJS_SERVICE_ID,
            EMAILJS_TEMPLATE_ID,
            templateParams
        );

        console.log('Email sent successfully:', response.status);
        return true;
    } catch (error) {
        console.error('Failed to send email:', error);
        return false;
    }
};

/**
 * Check if EmailJS is configured
 * @returns {boolean} - True if all required constants are set
 */
export const isEmailJSConfigured = () => {
    return (
        EMAILJS_SERVICE_ID !== 'service_xxxxxxx' &&
        EMAILJS_TEMPLATE_ID !== 'template_xxxxxxx' &&
        EMAILJS_PUBLIC_KEY !== 'xxxxxxxxxxxxxxx'
    );
};
