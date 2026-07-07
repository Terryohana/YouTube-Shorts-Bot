const sqlite3 = require('sqlite3').verbose();
const path = require('path');

const dbPath = path.resolve(__dirname, '../jobs.sqlite');
const db = new sqlite3.Database(dbPath, (err) => {
  if (err) {
    console.error('Error opening database', err.message);
  } else {
    console.log('Connected to the SQLite database.');
    db.run(`CREATE TABLE IF NOT EXISTS applied_jobs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT,
        company TEXT,
        job_title TEXT,
        platform TEXT,
        status TEXT,
        action_taken TEXT,
        url TEXT UNIQUE
    )`, (err) => {
        if (err) console.error('Error creating table', err.message);
    });
  }
});

function isJobProcessed(url) {
    return new Promise((resolve, reject) => {
        db.get(`SELECT id FROM applied_jobs WHERE url = ?`, [url], (err, row) => {
            if (err) reject(err);
            resolve(!!row);
        });
    });
}

function logJob(company, job_title, platform, status, action_taken, url) {
    return new Promise((resolve, reject) => {
        const date = new Date().toISOString();
        db.run(
            `INSERT INTO applied_jobs (date, company, job_title, platform, status, action_taken, url) VALUES (?, ?, ?, ?, ?, ?, ?)`,
            [date, company, job_title, platform, status, action_taken, url],
            function(err) {
                if (err) reject(err);
                resolve(this.lastID);
            }
        );
    });
}

function getAllLogs() {
    return new Promise((resolve, reject) => {
        db.all(`SELECT * FROM applied_jobs ORDER BY date DESC`, [], (err, rows) => {
            if (err) reject(err);
            resolve(rows);
        });
    });
}

module.exports = {
    db,
    isJobProcessed,
    logJob,
    getAllLogs
};
