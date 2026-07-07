const { scrapeRemoteCo } = require('./scrapers/remoteCo');
const { scrapeJobgether } = require('./scrapers/jobgether');
const { scrapePunditspace } = require('./scrapers/punditspace');

async function runScrapers(keywords) {
    let allJobs = [];
    for (let kw of keywords) {
        // Run scrapers sequentially or in parallel depending on resource constraints
        const remoteJobs = await scrapeRemoteCo(kw);
        const jobgetherJobs = await scrapeJobgether(kw);
        const punditJobs = await scrapePunditspace(kw);
        
        allJobs = allJobs.concat(remoteJobs, jobgetherJobs, punditJobs);
    }
    return allJobs;
}

module.exports = { runScrapers };
