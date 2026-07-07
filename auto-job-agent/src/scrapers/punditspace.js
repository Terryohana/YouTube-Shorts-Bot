const puppeteer = require('puppeteer-extra');
const StealthPlugin = require('puppeteer-extra-plugin-stealth');
puppeteer.use(StealthPlugin());

async function scrapePunditspace(keyword) {
    const jobs = [];
    console.log(`Scraping Punditspace for ${keyword}...`);
    const browser = await puppeteer.launch({ headless: "new" });
    
    try {
        const page = await browser.newPage();
        // Punditspace might not have a URL query structure, so we just scrape the main jobs page 
        // and filter by keyword manually, or use their search if available.
        const searchUrl = `https://punditspace.com/jobs`; 
        await page.goto(searchUrl, { waitUntil: 'networkidle2' });
        
        // Wait for standard job listing elements (often article, .job-listing, or tr)
        await page.waitForSelector('a[href*="job"]', { timeout: 5000 }).catch(() => null);

        const listings = await page.$$eval('a[href*="job"]', (elements, kw) => {
            return elements.map(el => {
                const text = el.innerText.trim();
                return {
                    title: text || 'Punditspace Role',
                    company: 'Punditspace Employer',
                    url: el.href,
                    platform: 'Punditspace'
                };
            }).filter(j => j.title.toLowerCase().includes(kw.toLowerCase()));
        }, keyword);
        
        jobs.push(...listings);
    } catch (error) {
        console.error(`Error scraping Punditspace: ${error.message}`);
    } finally {
        await browser.close();
    }
    
    return jobs;
}

module.exports = { scrapePunditspace };
