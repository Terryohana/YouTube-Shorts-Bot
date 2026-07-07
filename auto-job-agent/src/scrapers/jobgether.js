const puppeteer = require('puppeteer-extra');
const StealthPlugin = require('puppeteer-extra-plugin-stealth');
puppeteer.use(StealthPlugin());

async function scrapeJobgether(keyword) {
    const jobs = [];
    console.log(`Scraping Jobgether for ${keyword}...`);
    const browser = await puppeteer.launch({ headless: "new" });
    
    try {
        const page = await browser.newPage();
        const searchUrl = `https://jobgether.com/jobs?query=${encodeURIComponent(keyword)}`;
        await page.goto(searchUrl, { waitUntil: 'networkidle2' });
        
        // Jobgether relies heavily on Vue/React rendering. 
        // We'll look for generic link tags or common job card classes.
        await page.waitForSelector('a[href*="/job/"]', { timeout: 5000 }).catch(() => null);

        const listings = await page.$$eval('a[href*="/job/"]', elements => {
            return elements.map(el => {
                const title = el.innerText.trim().split('\n')[0]; // Attempt to grab title from the card
                return {
                    title: title || 'Jobgether Role',
                    company: 'Various (Jobgether)',
                    url: el.href,
                    platform: 'Jobgether'
                };
            }).filter(j => j.title.length > 0 && j.url);
        });
        
        jobs.push(...listings);
    } catch (error) {
        console.error(`Error scraping Jobgether: ${error.message}`);
    } finally {
        await browser.close();
    }
    
    return jobs;
}

module.exports = { scrapeJobgether };
