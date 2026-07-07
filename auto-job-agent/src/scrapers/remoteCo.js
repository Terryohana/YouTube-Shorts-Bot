const puppeteer = require('puppeteer-extra');
const StealthPlugin = require('puppeteer-extra-plugin-stealth');
puppeteer.use(StealthPlugin());

async function scrapeRemoteCo(keyword) {
    const jobs = [];
    console.log(`Scraping Remote.co for ${keyword}...`);
    const browser = await puppeteer.launch({ headless: "new" });
    
    try {
        const page = await browser.newPage();
        const searchUrl = `https://remote.co/remote-jobs/search/?search_keywords=${encodeURIComponent(keyword)}`;
        await page.goto(searchUrl, { waitUntil: 'networkidle2' });
        
        await page.waitForSelector('.job_listing', { timeout: 5000 }).catch(() => null);

        const listings = await page.$$eval('.job_listing', elements => {
            return elements.map(el => {
                const titleEl = el.querySelector('h3');
                const companyEl = el.querySelector('.company_and_position strong');
                const linkEl = el.querySelector('a');
                
                return {
                    title: titleEl ? titleEl.innerText.trim() : '',
                    company: companyEl ? companyEl.innerText.trim() : '',
                    url: linkEl ? linkEl.href : '',
                    platform: 'Remote.co'
                };
            });
        });
        
        jobs.push(...listings);
    } catch (error) {
        console.error(`Error scraping Remote.co: ${error.message}`);
    } finally {
        await browser.close();
    }
    
    return jobs;
}

module.exports = { scrapeRemoteCo };
