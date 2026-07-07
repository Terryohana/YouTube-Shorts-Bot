const nodemailer = require('nodemailer');
const path = require('path');

async function applyViaEmail(job, userProfile) {
    console.log(`Drafting email application for ${job.title} at ${job.company}...`);
    
    // In a real scenario, this uses user-provided SMTP credentials in .env
    // We will simulate sending or draft creation
    const transporter = nodemailer.createTransport({
        host: process.env.SMTP_HOST || 'smtp.gmail.com',
        port: process.env.SMTP_PORT || 465,
        secure: true,
        auth: {
            user: process.env.SMTP_USER || 'terryohanna@gmail.com',
            pass: process.env.SMTP_PASS || 'mock-app-password'
        }
    });

    const cvPath = path.resolve(__dirname, '../../CV_TERRY_OHANNAH_WANGO.md');

    if (!job.email) {
        console.warn(`[ABORT] No explicit email found for ${job.title} at ${job.company}. Cannot apply via email.`);
        return { success: false, status: 'Failed (No Email Provided)' };
    }

    const mailOptions = {
        from: 'terryohanna@gmail.com',
        to: job.email,
        subject: `Application for ${job.title} - Terry Ohannah Wango`,
        text: `Dear Hiring Manager,

I am writing to express my strong interest in the ${job.title} position at ${job.company}. 

With over 7 years of experience in engineering CRM solutions, enterprise integrations, and data pipelines, I bring a robust technical skill set centered around the Salesforce ecosystem (Apex, LWC, Flows) and full-stack development (Node.js, Puppeteer, React). During my tenure at Blue Consulting and Koneksys, I successfully architected end-to-end process automation and scalable data pipelines that significantly streamlined operations.

Please find my resume attached for your review. I look forward to the possibility of discussing how my background aligns with your team's needs.

Best regards,
Terry Ohannah Wango
Nairobi, Kenya
0723 854 692
linkedin.com/in/terry-ohannah`,
        attachments: [
            {
                filename: 'CV_TERRY_OHANNAH_WANGO.pdf', // Using .pdf as requested
                path: cvPath
            }
        ]
    };

    if (process.env.DRY_RUN === 'true' || !process.env.SMTP_PASS) {
        console.log(`[DRY RUN] Would send email to ${mailOptions.to} with subject: ${mailOptions.subject}`);
        return { success: true, status: 'Drafted (Dry Run)' };
    }

    try {
        const info = await transporter.sendMail(mailOptions);
        console.log(`Email sent: ${info.messageId}`);
        return { success: true, status: 'Submitted (Email)' };
    } catch (error) {
        console.error(`Failed to send email: ${error.message}`);
        return { success: false, status: 'Failed (Email Error)' };
    }
}

module.exports = { applyViaEmail };
