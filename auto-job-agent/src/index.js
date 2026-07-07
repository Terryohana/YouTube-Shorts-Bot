require('dotenv').config();
const { runScrapers } = require('./scraper');
const { evaluateJob } = require('./evaluator');
const { applyViaEmail } = require('./apply-email');
const { db, isJobProcessed, logJob } = require('./database');

const KEYWORDS = ["Salesforce Developer", "LWC Engineer", "Apex Developer", "Full Stack Developer", "Node.js Developer", "React Engineer", "Software Engineer"];

async function main() {
    console.log('--- Starting Job Acquisition Agent Run ---');
    console.log(`Time: ${new Date().toISOString()}`);
    
    // Step 1: Scrape
    const jobs = await runScrapers(KEYWORDS);
    
    console.log(`Found ${jobs.length} potential listings.`);

    for (const job of jobs) {
        if (!job.url) continue;

        // De-duplication
        const processed = await isJobProcessed(job.url);
        if (processed) {
            console.log(`Skipping already processed job: ${job.title} at ${job.company}`);
            continue;
        }

        // Step 2: Evaluate
        const evaluation = await evaluateJob(job);
        
        if (evaluation.isMatch) {
            console.log(`[MATCH] ${job.title} at ${job.company} (Score: ${evaluation.score})`);
            
            // Step 3: Branch A or B
            // For now, we simulate an email application if the platform isn't recognized
            const applyResult = await applyViaEmail(job);
            
            await logJob(job.company, job.title, job.platform, applyResult.status, 'Email App Sent/Drafted', job.url);
        } else {
            console.log(`[REJECT] ${job.title} at ${job.company} (Score: ${evaluation.score})`);
            await logJob(job.company, job.title, job.platform, 'Rejected', 'Score too low', job.url);
        }
    }
    
    console.log('--- Job Acquisition Agent Run Complete ---');
    
    // Optional: write logs to CSV logic would go here
}

main().catch(console.error);
