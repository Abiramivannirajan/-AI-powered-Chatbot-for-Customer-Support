const express = require('express');// request(url)
const cors = require('cors');// access across the all origin
const bodyParser = require('body-parser'); // parse the request and response
const nodemailer = require('nodemailer');//send gmail using configuration
require('dotenv').config();//env set email or password
const app = express();
// const storage = multer.memoryStorage();
// const upload = multer({ storage });

app.use(cors()); // Enable CORS
app.use(express.json());
app.use(bodyParser.json());
app.use(bodyParser.urlencoded({ extended: false }));

// CORS Headers setup
app.use((req, res, next) => {
    res.setHeader("Access-Control-Allow-Origin", '*');
    res.setHeader("Access-Control-Allow-Methods", "GET, PUT, DELETE, POST");
    res.setHeader("Access-Control-Allow-Headers", "Content-Type");
    next();
});
app.listen(8000, () => console.log("Server running at http://localhost:8000"));


// Create Nodemailer transporter for sending email
const transporter = nodemailer.createTransport({
    service: 'gmail',
    auth: {
        user: process.env.EMAIL,
        pass: process.env.PASSWORD
    }
});
app.get('', async (req, res) => {
    res.status(200).json({ message: "Connection successful" })
})

// POST Request for sending email
app.post('/apply-job', async (req, res) => {
    const { name, age, gender, education, email } = req.body;  // Get email details from request body
    console.log(req.body);


    try {
        const info = await transporter.sendMail({
            from: `"DreamPath Job Portal" <${process.env.EMAIL}>`,
            to: email,
            subject: 'Job Application Received - Confirmation',
            text: `Dear ${name},\n\nThank you for applying for a job with us. We have successfully received your application.\n\nApplication Details:\n- Name: ${name}\n- Age: ${age}\n- Gender: ${gender}\n- Education: ${education}\n\nWe will review your application and contact you if there is a suitable opportunity.\n\nBest regards,\nRecruitment Team`,
            html: `
                <p>Dear ${name},</p>
                <p>Thank you for applying for a job with us. We have successfully received your application.</p>
                <h3>Application Details:</h3>
                <ul>
                    <li><strong>Name:</strong> ${name}</li>
                    <li><strong>Age:</strong> ${age}</li>
                    <li><strong>Gender:</strong> ${gender}</li>
                    <li><strong>Education:</strong> ${education}</li>
                </ul>
                <p>We will review your application and contact you if there is a suitable opportunity.</p>
                <p>Best regards,</p>
                <p><strong>Recruitment Team</strong></p>
            `
        });

        res.status(200).json({ message: 'Email sent successfully!', messageId: info.messageId });
    } catch (error) {
        res.status(500).json({ message: 'Error sending email', error: error.message });
    }
});